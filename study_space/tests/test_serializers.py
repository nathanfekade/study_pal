from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from study_space.models import Book, Questionairre
from study_space.serializers import BookSerializer, QuestionairreSerializer
import os
import shutil
from django.conf import settings
from unittest.mock import patch
from django.test import RequestFactory

class BookSerializerTest(APITestCase):

    def setUp(self):
        self.created_files = []
        self.user = User.objects.create_user(username='testuser', password='testpass')
        with open('study_space/tests/files/Chapter_7.pdf', 'rb') as f:
        
            self.valid_pdf = SimpleUploadedFile(
                name='test.pdf', 
                content=f.read(),
                content_type='application/pdf'
            )
        
        self.text_file = SimpleUploadedFile(
            name='test.txt',
            content=b'Plain text content',
            content_type='text/plain'
        )
        self.invalid_pdf = SimpleUploadedFile(
            name='bad.pdf',
            content=b'Not a pdf',
            content_type='application/pdf'
        )
        self.unknown_file = SimpleUploadedFile(
            name='test.xyz',
            content=b'Random bytes',
            content_type='application/octet-stream'
        )
        self.book = Book.objects.create(
            title='Test Book',
            user=self.user,
            file=self.valid_pdf
        )
        self.created_files.append(self.book.file.path)

        
    def tearDown(self):

        try:
            for model in [Book, Questionairre]:
                for obj in model.objects.all():
                    if hasattr(obj, 'file') and obj.file and obj.file.name:
                        file_path = obj.file.path
                        if os.path.isfile(file_path):
                            try:
                                os.remove(file_path)
                            except(OSError, PermissionError) as e:
                                print(f"Failed to delete {file_path}: {e}")
                    
                    if hasattr(obj, 'question_answers_file') and obj.question_answers_file and obj.question_answers_file.name:
                        file_path = obj.question_answers_file.path
                        if os.path.isfile(file_path):
                            try:
                                os.remove(file_path)
                            except (OSError, PermissionError) as e:
                                print(f"Failed to delete {file_path}: {e}")

        except Exception as e:
            print(f"Error querying objects: {e}")
        

        for file_path in self.created_files:
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except (OSError, PermissionError) as e:
                    print(f"Failed to delete {file_path}: {e}")

    def test_serialize_book(self):

        serializer = BookSerializer(self.book)
        data = serializer.data
        self.assertEqual(data['title'], 'Test Book')
        self.assertEqual(data['user'], self.user.id)
        self.assertTrue(data['file'].endswith('.pdf'))
    
    def test_deserialize_valid_data(self):

        data = {
            'title': 'New Book',
            'file': self.valid_pdf
        }

        serializer = BookSerializer(data=data, context={'request':None})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        book = serializer.save(user=self.user)
        self.created_files.append(book.file.path)
        self.assertEqual(book.title, 'New Book')
        self.assertEqual(book.user, self.user)
        self.assertTrue(book.file.name.startswith('files/test'))
        self.assertEqual(Book.objects.count(), 2)
    
    def test_deserialize_invalid_title(self):

        data = {
            'title': 'A' * 51,
            'file': self.valid_pdf
        }

        serializer = BookSerializer(data=data, context={'request': None})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_deserialize_non_pdf(self):
        data = {
            'title': 'Test Book',
            'file': self.text_file
        }
        serializer = BookSerializer(data=data, context={'request': None})
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
        self.assertEqual(str(serializer.errors['file'][0]), 'File type not Known')
    
    def test_deserialize_invalid_pdf(self):

        data = {
            'title': 'Test Book',
            'file': self.invalid_pdf
        }
        serializer = BookSerializer(data=data, context={'request': None})
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
    
    def test_deserialize_unkown_file(self):

        data = {
            'title': 'Test Book',
            'file': self.unknown_file
            }
        serializer = BookSerializer(data=data, context={'request': None})
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
        self.assertEqual(str(serializer.errors['file'][0]), 'File type not Known')
    
    def test_user_read_only(self):
        
        data = {
            'title': 'New Book',
            'file': self.valid_pdf,
            'user': 888
        }
        serializer = BookSerializer(data=data, context={'request': None})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        book = serializer.save(user=self.user)
        self.created_files.append(book.file.path)
        self.assertEqual(book.user, self.user)
        self.assertNotEqual(book.user.id, 888)
    
    def test_update_book(self):

        data = {
            'title': 'Updated Book',
            'file': self.valid_pdf
        }
        serializer = BookSerializer(instance=self.book, data=data, context={'request': None})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_book = serializer.save()
        self.created_files.append(updated_book.file.path)
        self.assertEqual(updated_book.title, 'Updated Book')
        self.assertEqual(updated_book.user, self.user)
        self.assertTrue(updated_book.file.name.startswith('files/test'))

    
    def test_pdf_too_many_pages(self):
        pass

class QuestionairreSerializerTest(APITestCase):

    def setUp(self):
        self.created_files = []
        self.user = User.objects.create_user(username='testuser', email='testuser@emailcom', password='testpass')
        self.other_user = User.objects.create_user(username='other', email='other@email.com', password='otherpass')
        with open('study_space/tests/files/Chapter_7.pdf', 'rb') as f:
            self.valid_pdf = SimpleUploadedFile(
                name='test.pdf',
                content=f.read(),
                content_type='application/pdf'
            )

        self.book = Book.objects.create(
            title='Test Book',
            user=self.user,
            file=self.valid_pdf
        )
        self.created_files.append(self.book.file.path)
        self.factory = RequestFactory()
        self.request = self.factory.get('/fake-path')
        self.request.user = self.user
        self.context = {'request': self.request}
        
        self.other_book = Book.objects.create(
            title='Other Book',
            user=self.other_user,
            file=self.valid_pdf
        )

        self.created_files.append(self.other_book.file.path)
        self.questionairre = Questionairre.objects.create(
            book = self.book,
            user=self.user,
            detail_level='basic'
        )
    
    def tearDown(self):

        try:
            for model in [Book, Questionairre]:
                for obj in model.objects.all():
                    if hasattr(obj, 'file') and obj.file and obj.file.name:
                        file_path = obj.file.path
                        if os.path.isfile(file_path):
                            try:
                                os.remove(file_path)
                            except(OSError, PermissionError) as e:
                                print(f"Failed to delete {file_path}: {e}")
                        if hasattr(obj, 'question_answers_file') and obj.question_answers_file and obj.question_answers_file.name:
                            file_path = obj.question_answers_file.path
                            if os.path.isfile(file_path):
                                try:
                                    os.remove(file_path)
                                except(OSError, PermissionError) as e:
                                    print(f"Failed to delete {file_path}: {e}")
        
        except Exception as e:
            print(f"Error querying objects: {e}")
        

        for file_path in self.created_files:
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except (OSError, PermissionError) as e:
                    print(f"Failed to delete {file_path}: {e}")
    
    def test_serialize_questionairre(self):
        serializer = QuestionairreSerializer(self.questionairre, context=self.context)
        data = serializer.data
        self.assertEqual(data['book'], 'Test Book')
        self.assertEqual(data['user'], self.user.id)
        self.assertEqual(data['detail_level'], 'basic')
        self.assertIsNone(data['question_answers_file'])

    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_deserialize_valid_data(self, mock_generator):
        mock_generator.return_value = 'Q: What is this? A: A test.'
        data = {
            'book': 'Test Book',
            'detail_level': 'basic',
            'start_page': 1,
            'end_page': 2
        }
        serializer = QuestionairreSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        questionairre = serializer.save(user=self.user)
        self.created_files.append(questionairre.question_answers_file.path)
        self.assertEqual(questionairre.book, self.book)
        self.assertEqual(questionairre.user, self.user)
        self.assertEqual(questionairre.detail_level, 'basic')
        self.assertTrue(questionairre.question_answers_file.name.startswith('questions/Test Book_basic_'))
        self.assertEqual(Questionairre.objects.count(), 2)

    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_deserialize_without_page_range(self, mock_generator):
        mock_generator.return_value = 'Q: What is this? A: A test.'
        data = {
            'book': 'Test Book',
            'detail_level': 'intermediate'
        }
        serializer = QuestionairreSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        questionairre = serializer.save(user=self.user)
        self.created_files.append(questionairre.question_answers_file.path)
        self.assertEqual(questionairre.book, self.book)
        self.assertEqual(questionairre.detail_level, 'intermediate')
        self.assertTrue(questionairre.question_answers_file.name.startswith('questions/Test Book_intermediate_'))

    def test_deserialize_invalid_book_permission(self):
        data = {
            'book': 'Other Book',
            'detail_level': 'basic'
        }

        serializer = QuestionairreSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('book', serializer.errors)
        self.assertEqual(str(serializer.errors['book'][0]), 'Object with title=Other Book does not exist.')
    
    def test_deseriailize_invalid_detail_level(self):
        data ={
            'book': 'Test Book',
            'detail_level': 'invalid'
        }
        serializer = QuestionairreSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('detail_level', serializer.errors)
    
    def test_read_only_fields(self):
        data = {
            'book': 'Test Book',
            'detail_level': 'basic',
            'user': self.other_user.id,
            'question_answers_file': SimpleUploadedFile('test.txt', b'Ignore')
        }
        serializer = QuestionairreSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        questionairrre = serializer.save(user=self.user)
        self.created_files.append(questionairrre.question_answers_file.path)
        self.assertEqual(questionairrre.user, self.user)
        self.assertNotEqual(questionairrre.question_answers_file.name, 'test.txt')
    
    @patch('study_space.serializers.QuestionairreSerializer.generate_question_answers')
    def test_invalid_page_range(self, mock_generator):
        data = {
            'book': 'Test Book',
            'detail_level': 'basic',
            'start_page': 5,
            'end_page': 2
        }

        serializer = QuestionairreSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertEqual(str(serializer.errors['non_field_errors'][0]),'start page can not be greater than end page')
