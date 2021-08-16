# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Counter(models.Model):
    COUNTER_CHOICES = (
        ('PROCESS_ID', 'process_id'), ('PROCESS_ID2', 'process_id2'))
    counter_type = models.CharField(max_length=1000, choices=COUNTER_CHOICES)
    counter = models.SmallIntegerField(default=0)


class Category(models.Model):
    simplification_cat = None
    name = models.CharField(max_length=255)

    @classmethod
    def get_simplification_cat(cls):
        if cls.simplification_cat is None:
            cls.simplification_cat = Category.objects.filter(id=-1).first()
        if cls.simplification_cat is None:
            cls.simplification_cat = Category.objects.create(id=-1, name="Simplification")
        return cls.simplification_cat


class Group(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User)


class Expense(models.Model):
    description = models.CharField(
        max_length=200, default='default description')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        default=None)
    total_amount = models.DecimalField(decimal_places=2, max_digits=10)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        default=None)


class UserExpense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_lent = models.DecimalField(decimal_places=2, max_digits=10)
    amount_owed = models.DecimalField(decimal_places=2, max_digits=10)
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        default=None)

    @property
    def amount(self):
        return self.amount_lent - self.amount_owed
