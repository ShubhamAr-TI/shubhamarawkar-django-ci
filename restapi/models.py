# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import get_user_model

from django.db import models

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=255)


class Group(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User)


class Expense(models.Model):
    description = models.CharField(
        max_length=200, default="default description")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        default=None)
    total_amount = models.IntegerField(default=0)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        default=None)


class UserExpense(models.Model):
    users = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_lent = models.DecimalField(decimal_places=3, max_digits=12)
    amount_owed = models.DecimalField(decimal_places=3, max_digits=12)
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        default=None)

    @property
    def amount(self):
        return self.amount_lent - self.amount_owed
