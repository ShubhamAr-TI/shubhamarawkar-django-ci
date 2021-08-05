# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)


class Group(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User)


class UserExpense(models.Model):
    name = models.CharField(max_length=255)
    users = models.ForeignKey(User, on_delete=models.CASCADE)
    paid = models.DecimalField(decimal_places=3, max_digits=12)
    share = models.DecimalField(decimal_places=3, max_digits=12)

    @property
    def amount(self):
        return self.paid - self.share


class Expense(models.Model):
    description = models.CharField(max_length=200, default="default description")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=None)
    total_amount = models.IntegerField(default=0)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, default=None)
    users = models.ManyToManyField(UserExpense)
