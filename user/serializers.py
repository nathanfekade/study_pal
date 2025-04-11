from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ['username', 'email' , 'password']
    
    def valildate_email(self, value):

        if not value:
            raise serializers.ValidationError("Email address is required")
        
        if User.objects.filter(email=value).exists():
            
            if self.instance and self.instance.email != value():
                raise serializers.ValidationError("A user with this email alreay exists")
            elif not self.instance:
                raise serializers.ValidationError("A user with this email already exists")
            return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):

        password = validated_data.pop('password')

        for attr, value in validated_data.items():

            setattr(instance, attr, value)
            if password:
                instance.set_password(password)
            instance.save()
            return instance