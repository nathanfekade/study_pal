from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from study_space.models import Book, Questionairre
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
import os
from unittest.mock import patch

class QuestionairreAPITests(APITestCase):

    def setUp(self):
       
        self.files_to_clean = []
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.get_or_create(user=self.user)[0]

        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
        self.other_token = Token.objects.get_or_create(user=self.other_user)[0]
        self.assertTrue(Token.objects.filter(key=self.other_token.key).exists(), "Other user token not in database")

        book_file = SimpleUploadedFile('book.pdf', b'book_content', content_type='application/pdf')
        self.book = Book.objects.create(
            title='Test Book',
            user=self.user,
            file=book_file
        )
        self.files_to_clean.append(self.book.file.path)

        other_book_file = SimpleUploadedFile('other_book.pdf', b'other_book_content', content_type='application/pdf')
        self.other_book = Book.objects.create(
            title='Other Book',
            user=self.other_user,
            file=other_book_file
        )
        self.files_to_clean.append(self.other_book.file.path)

        question_file = SimpleUploadedFile('questions.txt', b'questions_content', content_type='text/plain')
        self.questionairre = Questionairre.objects.create(
            book=self.book,
            user=self.user,
            question_answers_file=question_file,
            detail_level='basic'
        )
        self.files_to_clean.append(self.questionairre.question_answers_file.path)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    
    def tearDown(self):
        
        for file_path in self.files_to_clean:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    # print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Failed to delete fiel {file_path}: {e}")

    def mock_generate_question_answers(self, book, detail_level, start_page, end_page):
        return "Mocked questions and answers"
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_get_questionairre_list_authenticated(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        response = self.client.get('/questionairre/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['book'], 'Test Book')
        self.assertEqual(response.data[0]['detail_level'], 'basic')
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_get_questionairre_list_unauthenticated(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        self.client.credentials()
        response = self.client.get('/questionairre/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_post_questionairre_valid_with_pages(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        data = {
            'book': 'Test Book',
            'detail_level': 'intermediate',
            'start_page': 1,
            'end_page': 2
        }
        response = self.client.post('/questionairre/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Questionairre.objects.count(), 2)
        questionairre = Questionairre.objects.last()
        self.assertEqual(questionairre.book, self.book)
        self.files_to_clean.append(questionairre.question_answers_file.path)
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_post_questionairre_valid_no_pages(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        data = {
            'book': 'Test Book', 
            'detail_level': 'detailed'
        }
        response = self.client.post('/questionairre/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Questionairre.objects.count(), 2)
        questionairre = Questionairre.objects.last()
        self.assertEqual(questionairre.book, self.book)
        self.assertEqual(questionairre.user, self.user)
        self.assertEqual(questionairre.detail_level, 'detailed')
        self.files_to_clean.append(questionairre.question_answers_file.path)
        self.assertTrue(questionairre.question_answers_file.name.endswith('.txt'))


    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_post_questionairre_missing_book(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        data = {
            'detail_level': 'basic',
            'start_page': 1,
            'end_page': 2
        }
        response = self.client.post('/questionairre/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response.data)
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_post_questionairre_invalid_book(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        data = {
            'book': 'Nonexistent Book',
            'detail_level': 'basic',
            'start_page': 1,
            'end_page': 2
        }
        response = self.client.post('/questionairre/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response.data)

    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_post_questionairre_other_user_book(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        data = {
            'book': 'Other Book',
            'detail_level': 'basic',
            'start_page': 1,
            'end_page': 2
        }
        response = self.client.post('/questionairre/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response.data)
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_post_questionairre_invalid_page_range(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        data = {
            'book': 'Test Book', 
            'detail_level': 'basic',
            'start_page': 3,
            'end_page': 1
        }
        response = self.client.post('/questionairre/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_get_questionairre_detail_authenticated(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        response = self.client.get(f'/questionairre/{self.questionairre.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['book'], 'Test Book')
        self.assertEqual(response.data['detail_level'], 'basic')
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_get_questionairre_detail_not_found(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        response = self.client.get('/questionairre/55')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, 'questionairre not found')
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_get_questionairre_detail_other_user(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_token.key)
        response = self.client.get(f'/questionairre/{self.questionairre.pk}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, 'questionairre not found')
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_delete_questionairre_valid(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        file_path = self.questionairre.question_answers_file.path
        self.assertTrue(os.path.exists(file_path))
        response = self.client.delete(f'/questionairre/{self.questionairre.pk}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Questionairre.objects.filter(pk=self.questionairre.pk).exists())
        self.assertFalse(os.path.exists(file_path), "File was not Delete")
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_delete_questionairre_not_found(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        response = self.client.delete('/questionairre/55')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, 'questionairre not found')
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_delete_questionairre_other_user(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_token.key)
        response = self.client.delete(f'/questionairre/{self.questionairre.pk}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, 'questionairre not found')
        self.assertTrue(Questionairre.objects.filter(pk=self.questionairre.pk).exists(), "Questionairre was incorrectly deleted")

    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_delete_questionairre_file_missing(self, mock_generate):
        mock_generate.return_value = self.mock_generate_question_answers(None, None, None, None)
        file_path = self.questionairre.question_answers_file.path
        if os.path.exists(file_path):
            os.remove(file_path)
        response = self.client.delete(f'/questionairre/{self.questionairre.pk}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, 'File not found ')
        self.assertTrue(Questionairre.objects.filter(pk=self.questionairre.pk).exists(), "Questionairre was incorrectly deleted")

