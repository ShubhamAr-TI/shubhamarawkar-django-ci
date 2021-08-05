# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
# from django.shortcuts import render

# Create your views here.
from rest_framework import status, viewsets
from rest_framework.authtoken.admin import User
from rest_framework.response import Response
from restapi.serializers import UserSerializer


def index(request):
    return HttpResponse("Hello, world. You're at Rest.")


from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class Logout(APIView):
    def get(self, request):
        # simply delete the token to force a login
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
