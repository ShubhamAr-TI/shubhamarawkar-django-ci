# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django.http import HttpResponse
from rest_framework import status, filters
# Create your views here.
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from restapi.models import Category, Expense, UserExpense, Group
from restapi.serializers import UserSerializer, CategorySerializer, ExpenseSerializer, UserExpenseSerializer, \
    GroupSerializer

User = get_user_model()


# from django.shortcuts import render

def index(request):
    return HttpResponse('Hello, world. You\'re at Rest.' + request.user)


class Logout(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Balances(APIView):
    def get(self, request):
        print(request.user)
        ue = request.user.userexpense_set.all()
        ux = Expense.objects.filter(userexpense__in=ue).all();
        ux = UserExpense.objects.all().filter(expense__in=ux)
        amounts = ux.values('user_id').annotate(amount=Sum('amount_lent') - Sum('amount_owed')).order_by('amount')
        print(amounts)
        balances = get_balances(amounts)
        resp = []
        for item in balances:
            if item['amount'] == 0:
                continue
            if request.user.id == item["from_user"]:
                resp.append({"user": item["to_user"], "amount": int(-1 * item["amount"])})
            if request.user.id == item["to_user"]:
                resp.append({"user": item["from_user"], "amount": int(item["amount"])})
        return Response(resp, status=status.HTTP_200_OK)


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
        expenses = Expense.objects.filter(group_id=pk).all()
        serializer = ExpenseSerializer(instance=expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path="balances")
    def balances(self, request, pk=None):
        group = Group.objects.filter(id=pk).first()
        amounts = group.expense_set.all().values('userexpense__user_id').annotate(
            amount=Sum('userexpense__amount_lent') - Sum('userexpense__amount_owed')).order_by('amount')
        amounts = [
            {'user_id': amount['userexpense__user_id'], 'amount': amount['amount']}
            for amount in amounts
        ]
        print(amounts)
        balances = get_balances(amounts)
        for balance in balances:
            balance['amount'] = "{:.02f}".format(balance['amount'])
        return Response(balances, status=status.HTTP_200_OK)


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Expense.objects.all()
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
            expenses = expenses.filter(description__icontains=self.request.query_params.get('q', None))
        return expenses


class UserExpenseViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = UserExpense.objects.all()
    serializer_class = UserExpenseSerializer
