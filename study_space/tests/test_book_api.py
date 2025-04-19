from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from study_space.models import Book
from django.core.files.uploadedfile import SimpleUploadedFile
import os

class BookAPITests(APITestCase):
    def setUp(self):

        self.files_to_clean = []

        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
        self.other_token = Token.objects.create(user=self.other_user)
        
        book_file = SimpleUploadedFile('test.pdf', b'file_content', content_type='application/pdf')
        self.book = Book.objects.create(
            title='Test Book',
            user=self.user,
            file=book_file
        )
        self.files_to_clean.append(self.book.file.path)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)


        self.valid_pdf_path = os.path.join('study_space', 'tests', 'files', 'Chapter_7.pdf')

    def tearDown(self):

        for file_path in self.files_to_clean:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    # print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Failed to delete file {file_path}: e")

    def test_get_book_list_authenticated(self):

        response = self.client.get('/book/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Book')
    
    def test_get_book_list_unauthenticated(self):
        self.client.credentials()
        response = self.client.get('/book/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_post_book_valid(self):
        with open(self.valid_pdf_path, 'rb' ) as f:
            data = {
                'title': 'New Book',
                'file': f
            }
            response = self.client.post('/book/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)
        self.assertEqual(Book.objects.last().title, 'New Book')
        book = Book.objects.last()
        self.files_to_clean.append(book.file.path)
    
    def test_post_book_missing_title(self):
        with open(self.valid_pdf_path, 'rb') as f:
            data = {
                'file': f
            }
            response = self.client.post('/book/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
    
    def test_get_book_detail_authenticated(self):
        response = self.client.get('/book/Test%20Book/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Book')
    
    def test_get_book_detail_case_insensitive(self):
        response = self.client.get('/book/test%20book/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Book')
    
    def test_get_book_detail_not_found(self):
        response = self.client.get('/book/Nonexistent%20Book/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "book not found")
    
    def test_get_book_detail_other_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_token.key)
        response = self.client.get('/book/Test%20Book/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_put_book_detail_update_title(self):
        data = {
            'title': 'Updated Book'
        }
        response = self.client.put('/book/Test%20Book/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, 'Updated Book')
    
    def test_put_book_detail_update_file(self):
        with open(self.valid_pdf_path, 'rb') as f:
            data = {
                'file': f
            }
            response = self.client.put('/book/Test%20Book/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.files_to_clean.append(self.book.file.path)
        self.assertTrue(self.book.file.name.endswith('.pdf'))
    
    def test_put_book_detail_update_both(self):
        with open(self.valid_pdf_path, 'rb') as f:
            data = {
                'title': 'Updated Both',
                'file': f 
            }
            response = self.client.put('/book/Test%20Book/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.files_to_clean.append(self.book.file.path)
        self.assertEqual(self.book.title, 'Updated Both')
        self.assertTrue(self.book.file.name.endswith('.pdf'))
    
    def test_put_book_detail_not_found(self):
        data = {
            'title': 'updated Book'
        }
        response = self.client.put('/book/Nonexistent%20Book/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_put_book_detail_other_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_token.key)
        data = {
            'title': 'Trying to Update'
        }
        response = self.client.put('/book/Test%20Book/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        