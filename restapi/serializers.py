from abc import ABC

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from restapi.models import Category, Group, UserExpense, Expense

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    # def create(self, validated_data):
    #     user = User.objects.create_user(**validated_data)
    #     return user

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    class Meta(object):
        model = User
        fields = ('id', 'username', 'password')

        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }


class CategorySerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Category
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    def create(self, validated_data):
        user = validated_data.pop('user')
        group = Group.objects.create(**validated_data)
        group.members.set([user])
        return group

    class Meta(object):
        model = Group
        fields = '__all__'
        extra_kwargs = {
            'members': {'read_only': True}
        }


class UserIdsSerializer(serializers.Serializer):
    user_id = serializers.ListField(child=UserSerializer())

class GroupMembersSerializer(serializers.Serializer):
    add = UserIdsSerializer()
    remove = UserIdsSerializer()


class UserExpenseSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = UserExpense
        fields = ['user', 'amount_owed', 'amount_lent']


def additional_validation(validated_data):
    expense_users = validated_data.get('userexpense_set')
    total_owed = total_paid = validated_data.get('total_amount')
    if total_owed < 0:
        raise ValidationError("Amount should not be Negative")
    uid_set = set()
    for eu in expense_users:
        uid_set.add(eu.get('user'))
        if eu.get('amount_lent') < 0 or eu.get('amount_owed'):
            raise ValidationError("Amount should not be Negative")
        total_paid -= eu.get('amount_lent')
        total_owed -= eu.get('amount_owed')
    if len(uid_set) != len(expense_users):
        raise ValidationError("User Expenses must be unique")
    if abs(total_paid) > 0.00000000000001 or abs(total_owed) > 0.000000000000001:
        raise ValidationError("Expenses are not adding up")


class ExpenseSerializer(serializers.ModelSerializer):
    users = UserExpenseSerializer(source='userexpense_set', many=True)

    def create(self, validated_data):
        additional_validation(validated_data)
        expense_users = validated_data.pop('userexpense_set')
        expense = Expense.objects.create(**validated_data)
        for eu in expense_users:
            UserExpense.objects.create(expense=expense, **eu)
        return expense

    def update(self, expense, validated_data):
        additional_validation(validated_data)
        expense_users = validated_data.pop('userexpense_set')
        expense.category = validated_data.get('category')
        expense.description = validated_data.get('description')
        expense.total_amount = validated_data.get('total_amount')
        expense.group = validated_data.get('group')
        expense.userexpense_set.all().delete()
        for eu in expense_users:
            UserExpense.objects.create(expense=expense, **eu)
        expense.save()
        return expense

    class Meta(object):
        model = Expense
        fields = '__all__'
