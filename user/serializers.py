from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model used for registration and profile updates.

    Handles creation of new users with secure password hashing and validation of
    unique email addresses. Also supports partial updates to user profile data.
    
    - `password`: Write-only field (not returned in responses).
    - `email`: Required and must be unique across all users.
    - `username`: Required by Django's User model.
    """

    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ['username', 'email' , 'password']
    
    def valildate_email(self, value):
        """
        Validate the email field.

        Ensures:
        1. Email is not empty.
        2. Email is unique (except when updating the same user's email).

        Parameters:
        value (str): The email address to validate.

        Returns:
        str: The validated email.

        Raises:
        ValidationError: If email is empty or already in use by another user.
        """

        if not value:
            raise serializers.ValidationError("Email address is required")
        
        if User.objects.filter(email=value).exists():
            
            if self.instance and self.instance.email != value():
                raise serializers.ValidationError("A user with this email alreay exists")
            elif not self.instance:
                raise serializers.ValidationError("A user with this email already exists")
            return value

    def create(self, validated_data):
        """
        Create a new User instance.

        Extracts the password from validated data, hashes it using Django's
        `set_password()` method, and saves the user.

        Parameters:
        validated_data (dict): Validated data containing username, email, and password.

        Returns:
        User: The newly created User instance.
        """

        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """
        Update an existing User instance.

        Updates allowed fields (username, email). If a new password is provided,
        it is securely hashed before saving.

        Parameters:
        instance (User): The User instance being updated.
        validated_data (dict): Validated data with fields to update.

        Returns:
        User: The updated User instance.
        """

        password = validated_data.pop('password')

        for attr, value in validated_data.items():

            setattr(instance, attr, value)
            if password:
                instance.set_password(password)
            instance.save()
            return instance
