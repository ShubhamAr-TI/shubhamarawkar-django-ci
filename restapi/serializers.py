from django.contrib.auth import get_user_model
from django.http import Http404
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


class GroupMembersSerializer(serializers.Serializer):
    add = UserSerializer(many=True)
    remove = UserSerializer(many=True)


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
        if eu.get('amount_lent') < 0 or eu.get('amount_owed') < 0:
            raise ValidationError("Amount should not be Negative")
        total_paid -= eu.get('amount_lent')
        total_owed -= eu.get('amount_owed')
    if len(uid_set) != len(expense_users):
        raise ValidationError("User Expenses must be unique")
    if total_paid != 0 or total_owed != 0:
        raise ValidationError("Expenses are not adding up")


def group_validation(validated_data):
    user = validated_data.get('user')
    group = validated_data.get('group')
    expense_users = validated_data.get('userexpense_set')
    if group:
        if not user.group_set.all().filter(id=group.id):
            raise Http404
        for eu in expense_users:
            if not eu['user'].group_set.all().filter(id=group.id):
                raise ValidationError("User not in group")
    else:
        contains = False
        for eu in expense_users:
            contains = contains or eu['user'] == user
        if not contains:
            raise ValidationError("User cannot create expense for others")


class ExpenseSerializer(serializers.ModelSerializer):
    users = UserExpenseSerializer(source='userexpense_set', many=True)

    def create(self, validated_data):
        validated_data.pop('user')
        expense_users = validated_data.pop('userexpense_set')
        expense = Expense.objects.create(**validated_data)
        for eu in expense_users:
            UserExpense.objects.create(expense=expense, **eu)
        return expense

    def update(self, expense, validated_data):
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

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = self.context['request'].user
        expense_users = attrs.get('userexpense_set')
        total_amount = attrs.get('total_amount')
        total_owed = sum([x.get('amount_owed') for x in expense_users])
        total_paid = sum([x.get('amount_lent') for x in expense_users])
        users = [x.get('user') for x in expense_users]
        group = attrs.get('group')
        try:
            assert total_owed == total_paid == total_amount
            assert min([x.get('amount_owed') for x in expense_users]) >= 0
            assert min([x.get('amount_lent') for x in expense_users]) >= 0
            assert len(set(users)) == len(users)
            if group:
                for user in users:
                    assert group in user.group_set.all()
            else:
                assert user in users
        except AssertionError as ae:
            raise ValidationError("Data Validation Failed")
        return attrs

    class Meta(object):
        model = Expense
        fields = '__all__'

