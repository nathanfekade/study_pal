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
    """
    API view to list all books for the authenticated user or create a new book.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, format=None):
        """Returns a list of books owned by the current user."""

        books = Book.objects.filter(user= request.user)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(request_body=BookSerializer, content_type='multipart/form-data' , responses={201: BookSerializer})
    def post(self, request, format=None):
        """
        Creates a new book for the authenticated user.

        This endpoint expects multipart/form-data input including the book title and file.
        If the data is valid, the book is saved with the current user as the owner.

        Parameters:
        request (Request): The HTTP request object containing the book data.
        format (str, optional): The format of the response (not used).

        Returns:
        Response: Serialized book data on success (201), or validation errors (400).
        """

        serializer = BookSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class BookDetail(APIView):
    """
    API view to retrieve, update, or delete a specific book owned by the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser]


        
    def get(self, request, current_title, format=None):
        """
        Retrieves details of a specific book by its current title.

        The book must belong to the authenticated user. The title comparison is case-insensitive.

        Parameters:
        request (Request): The HTTP request object.
        current_title (str): The current title of the book to retrieve.
        format (str, optional): The format of the response (not used).

        Returns:
        Response: Serialized book data on success (200), or "book not found" (404).
        """

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
        """
        Updates a specific book by its current title.

        Allows partial updates (e.g., title or file). The book must belong to the authenticated user.
        The title comparison is case-insensitive.

        Parameters:
        request (Request): The HTTP request object containing the updated data.
        current_title (str): The current title of the book to update.
        format (str, optional): The format of the response (not used).

        Returns:
        Response: Serialized updated book data on success (200), or error messages (404 or 400).
        """

        book = Book.objects.filter(title__iexact=current_title, user=request.user).first()
        
        if not book:
            return Response({"error": "Book not found with the given current title."}, status=status.HTTP_404_NOT_FOUND)
        

        serializer = BookSerializer(book, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()  
        
        return Response(serializer.data, status=status.HTTP_200_OK)

   

    
    def delete(self, request, current_title, format=None):
        """
        Deletes a specific book by its current title.

        The book file is removed from the filesystem, and the database record is deleted.
        The book must belong to the authenticated user. The title comparison is case-insensitive.

        Parameters:
        request (Request): The HTTP request object.
        current_title (str): The current title of the book to delete.
        format (str, optional): The format of the response (not used).

        Returns:
        Response: No content on success (204), or "book not found" (404).
        """

        book = Book.objects.filter(title__iexact=current_title, user=request.user).first()
        if not book:   
            return Response("book not found",status.HTTP_404_NOT_FOUND)
        os.remove(book.file.path)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionairreList(APIView):
    """
    API view to list all questionnaires for the authenticated user or create a new one.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, format=None):
        """
        Returns a list of questionnaires owned by the current user.

        Parameters:
        request (Request): The HTTP request object.
        format (str, optional): The format of the response (not used).

        Returns:
        Response: Serialized list of questionnaires (200).
        """

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
        """
        Creates a new questionnaire for the authenticated user.

        Expects data including the associated book and detail level. The questionnaire is saved
        with the current user as the owner.

        Parameters:
        request (Request): The HTTP request object containing the questionnaire data.
        format (str, optional): The format of the response (not used).

        Returns:
        Response: Serialized questionnaire data on success (201), or validation errors (400).
        """

        serializer = QuestionairreSerializer(data=request.data, context={"request": request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
                

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionairreDetail(APIView):
    """
    API view to retrieve (download) or delete a specific questionnaire owned by the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]



    
    def get(self, request, pk, format= None):
        """
        Downloads the question answers file for a specific questionnaire.

        The questionnaire must belong to the authenticated user. Returns the file as an attachment
        if it exists.

        Parameters:
        request (Request): The HTTP request object.
        pk (int): The primary key of the questionnaire to retrieve.
        format (str, optional): The format of the response (not used).

        Returns:
        HttpResponse: File download response on success (200), or error messages (404 or 400).
        """

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
        """
        Deletes a specific questionnaire by its primary key.

        The associated question answers file is removed from the filesystem if it exists,
        and the database record is deleted. The questionnaire must belong to the authenticated user.

        Parameters:
        request (Request): The HTTP request object.
        pk (int): The primary key of the questionnaire to delete.
        format (str, optional): The format of the response (not used).

        Returns:
        Response: No content on success (204), or error messages (404, 400, or 500).
        """

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
        