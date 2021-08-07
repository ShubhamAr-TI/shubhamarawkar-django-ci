# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db.models import Q
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
    GroupSerializer, GroupMembersSerializer

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
        print('wassup', request.user)


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
    if 'add' not in data and 'remove' not in data:
        raise ValidationError("add or remove is required field")

    for method in ['add', 'remove']:
        if method in data:
            print(data[method])
            if 'user_ids' not in data[method]:
                raise ValidationError("user_ids are absent")
            user_ids = data[method]['user_ids']
            if len(user_ids) == 0 or len(user_ids) > len(set(user_ids)):
                raise ValidationError("user_ids are incorrect")

    if 'add' in data and 'remove' in data:
        if set(data['add']['user_ids']).intersection(set(data['remove']['user_ids'])):
            raise ValidationError("add and remove cannot intersect")




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
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def balances(self, request, pk=None):
        pass


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
