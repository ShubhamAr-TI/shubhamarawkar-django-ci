from django.contrib.auth import get_user_model
from rest_framework import serializers

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
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    def create(self, validated_data):
        user = validated_data.pop('user')
        group = Group.objects.create(**validated_data)
        group.members.set([user])
        return group

    class Meta(object):
        model = Group
        fields = "__all__"
        extra_kwargs = {
            'members': {'read_only': True}
        }


class UserExpenseSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = UserExpense
        fields = ["user", "amount_owed", "amount_lent"]


class ExpenseSerializer(serializers.ModelSerializer):
    users = UserExpenseSerializer(source='userexpense_set', many=True)

    def create(self, validated_data):
        print(validated_data)
        expense_users = validated_data.pop('userexpense_set')
        expense = Expense.objects.create(**validated_data)
        print(expense_users)
        for eu in expense_users:
            UserExpense.objects.create(expense=expense, **eu)
        return expense

    class Meta(object):
        model = Expense
        fields = "__all__"
