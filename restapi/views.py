# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse, Http404
from rest_framework import status, generics, filters
# Create your views here.
from rest_framework import viewsets
from rest_framework.authtoken.admin import User
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
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
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Balances(APIView):
    def get(self, request):
        print("wassup")


class UserViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    # def get_permissions(self):
    #     """
    #     Instantiates and returns the list of permissions that this view requires.
    #     """
    #     if self.action == 'create':
    #         permission_classes = [AllowAny]
    #     else:
    #         permission_classes = [IsAuthenticated]
    #     return [permission() for permission in permission_classes]


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
            'user': self.request.user  # Change 'user' to you model user field.
        }
        serializer.save(**kwargs)

    # def update(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     if not instance.members.filter(id=request.user.id):
    #         raise PermissionDenied({"message": "You don't have permission to access",
    #                                 "object_id": instance.id})
    #     self.perform_update(instance)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.members.filter(id=request.user.id):
            raise PermissionDenied({"message": "You don't have permission to access",
                                    "object_id": instance.id})
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)






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
