from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from django.http import Http404
from .serializers import UserSerializer


class UserList(APIView):
    # permission_classes = [AllowAny]

# TO GET ALL
    def get(self, request, format=None):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    @swagger_auto_schema(request_body=UserSerializer, responses={201: UserSerializer})
    def post(self, request, format=None):

        serializer = UserSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status= status.HTTP_201_CREATED)
        return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):

        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(request_body=UserSerializer, responses={200: UserSerializer})    
    def put(self, request, format=None):

        serializer = UserSerializer(request.user, data= request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user= request.user)
            return Response(serializer.data, status.HTTP_200_OK)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, format=None):
        
        request.user.delete()
        return Response(status.HTTP_204_NO_CONTENT)