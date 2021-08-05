# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
# from django.shortcuts import render

# Create your views here.
from rest_framework import status, viewsets
from rest_framework.authtoken.admin import User
from rest_framework.response import Response

from restapi.models import Category, Expense, UserExpense
from restapi.serializers import UserSerializer, CategorySerializer, ExpenseSerializer, UserExpenseSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


def index(request):
    return HttpResponse("Hello, world. You're at Rest.")


class Logout(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            request.user.auth_token.delete()
        return Response(status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing User.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer


class UserExpenseViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = UserExpense.objects.all()
    serializer_class = UserExpenseSerializer
