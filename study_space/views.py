from django.shortcuts import render
from rest_framework.views import APIView
from study_space.models import Book, Questionairre
from study_space.serializers import BookSerializer,QuestionairreSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import Http404





class BookList(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, format=None):
        books = Book.objects.filter(user= request.user)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(request_body=BookSerializer, content_type='multipart/form-data' , responses={201: BookSerializer})
    def post(self, request, format=None):

        serializer = BookSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class BookDetail(APIView):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk, user):
        try:
            return Book.objects.get(pk=pk, user=user)
        except Book.DoesNotExist:
            raise Http404
        
    def get(self, request, pk, format=None):
        book = self.get_object(pk=pk,user=request.user)
        serializer = BookSerializer(book)
        return Response(serializer.data)
    
    @swagger_auto_schema(request_body=BookSerializer, responses={200: BookSerializer})
    def put(self, request, pk, format=None):
        book = self.get_object(pk=pk, user= request.user)
        serializer = BookSerializer(book, request= request.data)
        if serializer.is_valid():
            serializer.save(user= request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk, format=None):
        book = self.get_object(pk=pk, user= request.user)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionairreList(APIView):

    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        questionairre = Questionairre.objects.filter(user= request.user)
        serializer = QuestionairreSerializer(questionairre, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(request_body=QuestionairreSerializer, responses={201: QuestionairreSerializer})    
    def post(self, request, format=None):
        serializer = QuestionairreSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save(user= request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuestionairreDetail(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        
        try:    
            return Questionairre.objects.get(pk= pk, user= user)
        except Questionairre.DoesNotExist:
            raise Http404
    
    def get(self, request, pk, format= None):

        questionairre = self.get_object(pk=pk, user=request.user)
        serializer = QuestionairreSerializer(questionairre)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=QuestionairreSerializer, responses={200: QuestionairreSerializer})
    def put(self, request, pk,format= None):

        questionairre = self.get_object(pk=pk, user=request.user) 
        serializer = QuestionairreSerializer(questionairre, data= request.data)

        if serializer.is_valid():
            serializer.save(user= request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk, format=None):

        questionairre = self.get_object(pk, user= request.user)
        questionairre.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)