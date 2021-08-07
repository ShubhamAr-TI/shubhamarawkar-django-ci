# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework import status, filters
# Create your views here.
from rest_framework import viewsets
from rest_framework.decorators import action
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

    @action(detail=False, methods=['put'], url_path="members")
    def members(self, request, pk=None):
        group = Group.objects.filter(group_id=pk).first()

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
    filter_backends = [filters.SearchFilter]
    search_fields = ['description']

    def get_queryset(self):
        """
        This view should return a list of all the Expenses
        for the currently authenticated user.
        """
        user = self.request.user
        return Expense.objects.filter(userexpense__in=user.userexpense_set.all())


class UserExpenseViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = UserExpense.objects.all()
    serializer_class = UserExpenseSerializer
