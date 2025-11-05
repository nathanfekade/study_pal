from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from django.http import Http404
from .serializers import UserSerializer
from rest_framework.authentication import TokenAuthentication


class UserList(APIView):
    """
    API view to create a new user (registration).

    This endpoint allows anyone (unauthenticated users) to register a new user account.
    The GET method to list all users is currently disabled.
    """

# TO GET ALL USERS
    # def get(self, request, format=None):
    #     users = User.objects.all()
    #     serializer = UserSerializer(users, many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    @swagger_auto_schema(request_body=UserSerializer, responses={201: UserSerializer})
    def post(self, request, format=None):
        """
        Create a new user account.

        Validates and saves user data from the request. On success, returns the created
        user data with a 201 status. On validation failure, returns error details with 400.

        Parameters:
        request (Request): The HTTP request containing user registration data.
        format (str, optional): Format suffix for content negotiation (unused).

        Returns:
        Response: Serialized user data on success (201), or validation errors (400).
        """

        serializer = UserSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status= status.HTTP_201_CREATED)
        return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    """
    API view to retrieve, update, or delete the authenticated user's profile.

    Requires token authentication. Only the authenticated user can access or modify
    their own profile.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]


    def get(self, request, format=None):
        """
        Retrieve the profile of the currently authenticated user.

        Returns the serialized data of the user making the request.

        Parameters:
        request (Request): The HTTP request from the authenticated user.
        format (str, optional): Format suffix for content negotiation (unused).

        Returns:
        Response: Serialized user data (200).
        """

        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(request_body=UserSerializer, responses={200: UserSerializer})    
    def put(self, request, format=None):
        """
        Update the authenticated user's profile.

        Allows partial updates (e.g., changing username or email). Validates input and
        saves changes if valid.

        Parameters:
        request (Request): The HTTP request containing updated user data.
        format (str, optional): Format suffix for content negotiation (unused).

        Returns:
        Response: Serialized updated user data on success (200), or validation errors (400).
        """

        serializer = UserSerializer(request.user, data= request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user= request.user)
            return Response(serializer.data, status.HTTP_200_OK)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, format=None):
        """
        Delete the authenticated user's account.

        Permanently removes the user from the database. Returns 204 No Content on success.

        Parameters:
        request (Request): The HTTP request from the user to be deleted.
        format (str, optional): Format suffix for content negotiation (unused).

        Returns:
        Response: No content (204) on successful deletion.
        """

        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)