from rest_framework.views import APIView
from study_space.models import Book, Questionairre
from study_space.serializers import BookSerializer,QuestionairreSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg import openapi
from rest_framework.authentication import TokenAuthentication
import os
from django.http import HttpResponse
from wsgiref.util import FileWrapper
from pathlib import Path

class BookList(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
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
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser]


        
    def get(self, request, current_title, format=None):
        book = Book.objects.filter(title__iexact=current_title, user=request.user).first()
        if not book:   
            return Response("book not found",status.HTTP_404_NOT_FOUND)
        serializer = BookSerializer(book)
        return Response(serializer.data)


    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'title',
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False, 
                description='New title (optional)',
                min_length=1,
                max_length=50,
            ),
            openapi.Parameter(
                'file',
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,  
                description='New file (optional)',
            ),
        ],
        responses={200: BookSerializer},
    )
    def put(self, request, current_title, format=None):
        book = Book.objects.filter(title__iexact=current_title, user=request.user).first()
        
        if not book:
            return Response({"error": "Book not found with the given current title."}, status=status.HTTP_404_NOT_FOUND)
        

        serializer = BookSerializer(book, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()  
        
        return Response(serializer.data, status=status.HTTP_200_OK)

   

    
    def delete(self, request, current_title, format=None):
        book = Book.objects.filter(title__iexact=current_title, user=request.user).first()
        if not book:   
            return Response("book not found",status.HTTP_404_NOT_FOUND)
        os.remove(book.file.path)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionairreList(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, format=None):
        questionairre = Questionairre.objects.filter(user= request.user)
        serializer = QuestionairreSerializer(questionairre, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(request_body=QuestionairreSerializer,
        responses={
        201: openapi.Response
            (description='File downloaded successfully',
              schema=openapi.Schema(type=openapi.TYPE_FILE,
                description='Text file containing the questionnaire')),
                 
        400: openapi.Response(description='Validation error', schema=QuestionairreSerializer)})    
    def post(self, request, format=None):
        
        serializer = QuestionairreSerializer(data=request.data, context={"request": request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
                

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionairreDetail(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]



    
    def get(self, request, pk, format= None):

        questionairre = Questionairre.objects.filter(pk=pk, user=request.user).first()
        if not questionairre:
            return Response("questionairre not found", status=status.HTTP_404_NOT_FOUND)
        # serializer = QuestionairreSerializer(questionairre)
        file_path = Path(questionairre.question_answers_file.path)
        if file_path.is_file():
            with open(file_path, 'rb') as file_obj:
                response = HttpResponse(FileWrapper(file_obj), content_type='text/plain')
                filename = file_path.name
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        else:
            return Response("File not found", status=status.HTTP_400_BAD_REQUEST)





    # @swagger_auto_schema(request_body=QuestionairreSerializer, responses={200: QuestionairreSerializer})
    # def put(self, request, pk,format= None):

    #     questionairre = self.get_object(pk=pk, user=request.user) 
    #     serializer = QuestionairreSerializer(questionairre, data= request.data)

    #     if serializer.is_valid():
    #         serializer.save(user= request.user)
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk, format=None):
        questionairre = Questionairre.objects.filter(pk= pk, user=request.user).first()
        if not questionairre:
            return Response('questionairre not found', status=status.HTTP_404_NOT_FOUND)
        try:
            file_path = questionairre.question_answers_file.path


            if os.path.exists(file_path):
                os.remove(file_path)
                questionairre.delete()
            else:
                return Response("File not found ", status=status.HTTP_400_BAD_REQUEST)
            

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(f"Error deleting file: {str(e)}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)