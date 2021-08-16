# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import io
import logging
import os
import socket
import urllib
from collections import defaultdict
from logging.handlers import SysLogHandler

import boto3
import pandas as pd
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.db.models import Q, Sum, F
from django.http import HttpResponse, Http404
from rest_framework import status, filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from restapi.models import Category, Expense, UserExpense, Group, Counter
from restapi.serializers import UserSerializer, CategorySerializer, ExpenseSerializer, UserExpenseSerializer, \
    GroupSerializer
from restapi.tasks import bulk_expenses, bulk_simplify

# Create your views here.
User = get_user_model()


class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


syslog = SysLogHandler(address=('logs3.papertrailapp.com', 42305))
syslog.addFilter(ContextFilter())
format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(syslog)
logger.setLevel(logging.INFO)


def index(request):
    return HttpResponse('Hello, world. You\'re at Rest.' + request.user)


validate = URLValidator()


class Logout(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Balances(APIView):
    def get(self, request):
        print(request.user)
        ue = request.user.userexpense_set.all()
        ux = Expense.objects.filter(userexpense__in=ue).all();
        # Group expenses
        all_balances = []
        for expense in ux.all():
            amounts = expense.userexpense_set.all().values('user_id').annotate(
                amount=Sum('amount_lent') - Sum('amount_owed')).order_by('amount')
            all_balances.append(get_balances(amounts))

        user_balances = defaultdict(lambda: 0)
        for balances in all_balances:
            for item in balances:
                if item['amount'] == 0:
                    continue
                if request.user.id == item["from_user"]:
                    user_balances[item["to_user"]] += float(-1 * item["amount"])
                if request.user.id == item["to_user"]:
                    user_balances[item["to_user"]] += float(item["amount"])
        return Response([{"user": user, "amount": balance} for user, balance in user_balances.items()],
                        status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class CategoryViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing User.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


def validate_query(data):
    for method in ['add', 'remove']:
        if method in data:
            if 'user_ids' not in data[method]:
                raise ValidationError("user_ids are absent")
            user_ids = data[method]['user_ids']
            if len(user_ids) == 0 or len(user_ids) > len(set(user_ids)):
                raise ValidationError("user_ids are incorrect")


def get_balances(amounts):
    n_amounts = []
    for am in amounts:
        if am['amount'] == 0:
            continue
        n_amounts.append(am)
    amounts = n_amounts
    balances = []
    left, right = 0, len(amounts) - 1
    while left < right:
        if abs(amounts[left]['amount']) < amounts[right]['amount']:
            balances.append({
                "from_user": amounts[left]['user_id'],
                "to_user": amounts[right]['user_id'],
                "amount": abs(amounts[left]['amount'])})

            amounts[right]['amount'] -= abs(amounts[left]['amount'])
            amounts[left]['amount'] = 0
            left += 1
        else:
            balances.append({
                "from_user": amounts[left]['user_id'],
                "to_user": amounts[right]['user_id'],
                "amount": abs(amounts[right]['amount'])})
            amounts[left]['amount'] += abs(amounts[right]['amount'])
            amounts[right]['amount'] = 0
            right -= 1
    return balances


def group_balances(group):
    amounts = group.expense_set.all().values('userexpense__user_id').annotate(
        amount=Sum('userexpense__amount_lent') - Sum('userexpense__amount_owed')).order_by('amount')
    amounts = [
        {'user_id': amount['userexpense__user_id'], 'amount': amount['amount']}
        for amount in amounts
    ]
    return get_balances(amounts)


def get_balances_all(ux):
    all_balances = []
    for expense in ux.all():
        amounts = expense.userexpense_set.all().values('user_id').annotate(
            amount=Sum('amount_lent') - Sum('amount_owed')).order_by('amount')
        all_balances += get_balances(amounts)
    agg_balances = defaultdict(lambda: 0)
    for balance in all_balances:
        if balance['from_user'] > balance['to_user']:
            balance['from_user'], balance['to_user'] = balance['to_user'], balance['from_user']
            balance['amount'] *= -1
        agg_balances[(balance['to_user'], balance['from_user'])] += balance['amount']

    balances = []
    for (to, frm), amount in agg_balances.items():
        if amount == 0:
            continue
        balance = {"to_user": to, "from_user": frm, "amount": amount}
        if amount < 0:
            balance["to_user"] = frm
            balance["from_user"] = to
            balance["amount"] = -1 * amount
        balance['amount'] = "{:.02f}".format(balance['amount'])
        balances.append(balance)
    return balances

def group_simplify(pk):
    group = Group.objects.filter(id=pk).first()
    if group is None:
        raise Http404("group doesn't exists")
    amounts = group.expense_set.all().values('userexpense__user_id').annotate(
        amount=Sum('userexpense__amount_lent') -
               Sum('userexpense__amount_owed')).order_by('amount')
    amounts = [
        {'user_id': amount['userexpense__user_id'], 'amount': amount['amount']}
        for amount in amounts
    ]
    print(amounts)
    amounts = list(filter(lambda x: x['amount'], amounts))
    simplification_cat = Category.get_simplification_cat()
    expenses = Expense.objects.filter(group_id=pk).all()
    balances = get_balances_all(expenses)
    for balance in balances:
        exp = Expense.objects.create(description="simplification", total_amount=balance['amount'], group=group,
                                     category=simplification_cat)
        UserExpense.objects.create(expense=exp, user_id=balance['to_user'], amount_owed=balance['amount'],
                                   amount_lent=0)
        UserExpense.objects.create(expense=exp, user_id=balance['from_user'], amount_lent=balance['amount'],
                                   amount_owed=0)

    if len(amounts):
        total_amount = sum([amount['amount'] if amount['amount'] > 0 else 0 for amount in amounts])
        exp = Expense.objects.create(description="simplification", total_amount=total_amount,
                                     category=simplification_cat)
        for amount in amounts:
            if amount['amount'] == 0:
                continue
            transaction = {}
            if amount['amount'] > 0:
                transaction['amount_owed'] = amount['amount']
                transaction['amount_lent'] = 0
            else:
                transaction['amount_owed'] = 0
                transaction['amount_lent'] = abs(amount['amount'])
            UserExpense.objects.create(user_id=amount['user_id'], expense=exp, **transaction)

class GroupViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing User.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        """
        This view should return a list of all the Groups
        for the currently authenticated user.
        """
        user = self.request.user
        return user.group_set.all()

    def perform_create(self, serializer):
        kwargs = {
            'user': self.request.user
        }
        serializer.save(**kwargs)

    @action(detail=True, methods=['put'], url_path="members")
    def members(self, request, pk=None):
        print(request.data, request.user, request.user.id)
        group = Group.objects.filter(id=pk).first()
        members = set([x.id for x in group.members.all()])
        new_users = []
        validate_query(request.data)
        if 'add' in request.data:
            for user_id in request.data['add']['user_ids']:
                if user_id not in members:
                    members.add(user_id)

        if 'remove' in request.data:
            for user_id in request.data['remove']['user_ids']:
                if user_id not in members:
                    raise ValidationError("Member not preset in group")
                members.remove(user_id)
        group.members.set(User.objects.filter(id__in=list(members)))
        group.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path="expenses")
    def expenses(self, request, pk=None):
        expenses = Expense.objects.filter(group_id=pk).filter(category_id__gte=0).all()
        serializer = ExpenseSerializer(instance=expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path="balances")
    def balances(self, request, pk=None):
        grp = Group.objects.filter(pk=pk).first()
        if grp is None:
            raise Http404("group doesn't exists")
        ux = Expense.objects.filter(group_id=pk)
        balances = get_balances_all(ux)
        return Response(balances, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path="simplify")
    def simplify(self, request, pk=None):
        group_simplify(pk)
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'], url_path="simplify")
    def simplify_bulk(self, request):
        counter, _ = Counter.objects.get_or_create(counter_type='process_id')
        process_id = counter.counter
        counter.counter = F("counter") + 1
        counter.save(update_fields=["counter"])
        for grp in request.user.group_set.all():
            group_simplify(grp.id)
        bulk_simplify.delay(request.user.username)
        return Response({"id": process_id + 1}, status=status.HTTP_202_ACCEPTED)


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Expense.objects.filter(category_id__gte=0).all()
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        """
        This view should return a list of all the Expenses
        for the currently authenticated user.
        """
        user = self.request.user
        expenses = Expense.objects.filter(
            Q(userexpense__in=user.userexpense_set.all())
            | Q(group__in=user.group_set.all()))

        if self.request.query_params.get('q', None) is not None:
            expenses = expenses.filter(
                description__icontains=self.request.query_params.get(
                    'q', None))
        return expenses

    @action(methods=["post"], detail=False, url_path="bulk")
    def bulk(self, request):
        if 'url' not in request.data:
            raise ValidationError("URL is a necessary field")
        if request.accepted_media_type != "application/json":
            raise ValidationError("Only application/json is supported")
        s3_csv_url = request.data['url']
        try:
            validate(s3_csv_url)
        except Exception as e:
            raise ValidationError("Bad URL")
        s3 = boto3.client('s3')

        with urllib.request.urlopen(s3_csv_url) as f:
            data = f.read()
            b = io.BytesIO(data)
            c = io.BytesIO(data)
            s3.upload_fileobj(
                b,
                os.environ.get("S3_BUCKET_NAME"),
                "transactions.csv")
            x = pd.read_csv(c)
            bulk_expenses.delay(x.fillna(0).to_dict('records'))

        presigned_url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': os.environ.get('S3_BUCKET_NAME'),
                'Key': 'transactions.csv'},
        )
        return Response({"url": presigned_url},
                        status=status.HTTP_202_ACCEPTED)


class UserExpenseViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = UserExpense.objects.all()
    serializer_class = UserExpenseSerializer
