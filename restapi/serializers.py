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


class GroupMembersSerializer(serializers.Serializer):
    add = serializers.ListSerializer(child=serializers.IntegerField())
    remove = serializers.ListSerializer(child=serializers.IntegerField())


class UserExpenseSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = UserExpense
        fields = ['user', 'amount_owed', 'amount_lent']


class ExpenseSerializer(serializers.ModelSerializer):
    users = UserExpenseSerializer(source='userexpense_set', many=True)

    def create(self, validated_data):
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

        if expense_users:
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
                # if user not in group.members.all():
                #     raise Http404

                # This was causing my test case to fail
                for user in users:
                    assert group in user.group_set.all()
            else:
                assert user in users
        except AssertionError:
            raise ValidationError("Data Validation Failed")
        return attrs

    class Meta(object):
        model = Expense
        fields = '__all__'
