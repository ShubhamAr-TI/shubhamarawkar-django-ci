# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse
from rest_framework import status
# Create your views here.
from rest_framework import viewsets, mixins
from rest_framework.authtoken.admin import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from restapi.models import Category, Expense, UserExpense, Group
from restapi.serializers import UserSerializer, CategorySerializer, ExpenseSerializer, UserExpenseSerializer, \
    GroupSerializer


# from django.shortcuts import render


def index(request):
    return HttpResponse("Hello, world. You're at Rest.")


class Logout(APIView):

    def post(self, request):
        if request.user.is_authenticated:
            request.user.auth_token.delete()
            return Response(status=status.HTTP_201_CREATED)


class Balances(APIView):
    def get(self, request):
        print("wassup")


class UserViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


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
