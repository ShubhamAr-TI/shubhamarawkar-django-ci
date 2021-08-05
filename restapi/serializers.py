from rest_framework import serializers
from rest_framework.authtoken.admin import User


class UserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = ['id','username', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }


