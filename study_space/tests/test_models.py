from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from study_space.models import Book, Questionairre
import os

class BookModelTest(APITestCase):
    def setUp(self):
        self.created_files = []
        self.user = User.objects.create_user(username='testuser', email='testuser@email.com',password='testpass')
        with open('study_space/tests/files/Chapter_7.pdf', 'rb') as f:

            self.valid_pdf = SimpleUploadedFile(
                name = 'test.pdf',
                content =f.read(),
                content_type = 'application/pdf'
            )

        self.text_file = SimpleUploadedFile(
            name = 'test.txt',
            content=b'Plain text content \nMore text\n',
            content_type='text/plain'
        )
    
        self.invalid_pdf = SimpleUploadedFile(
            name='bad.pdf',
            content=b'Not a PDF',
            content_type='application/pdf'
        )
        
        self.unknown_file = SimpleUploadedFile(
            name='test.xyz',
            content=b'Random bytes',
            content_type='application/octet-stream'
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
                    

    def test_create_valid_book(self):
        book = Book.objects.create(
            title='Test Book',
            user = self.user,
            file=self.valid_pdf
        )
        self.created_files.append(book.file.path)
        self.assertEqual(book.title, 'Test Book')
        self.assertEqual(book.user, self.user)
        self.assertTrue(book.file.name.startswith('files/test'))
        self.assertEqual(Book.objects.count(), 1)
    
    def test_title_exact_length(self):
        book = Book(title='A' * 50, user=self.user, file= self.valid_pdf)
        book.full_clean()
        book.save()
        self.created_files.append(book.file.path)
        self.assertEqual(Book.objects.count(),1)


    def test_title_max_length(self):

        long_title = 'A' * 51
        book = Book(title=long_title, user=self.user, file=self.valid_pdf)
        with self.assertRaises(ValidationError):
            book.full_clean()
    
    def test_user_foreign_key_required(self):
        book = Book(title= 'Test Book', file=self.valid_pdf)
        with self.assertRaises(ValidationError):
            book.full_clean()
    
    def test_user_cascade_delete(self):
        book = Book.objects.create(
            title = 'Test Book',
            user = self.user,
            file = self.valid_pdf
        )
        self.created_files.append(book.file.path)
        self.assertEqual(Book.objects.count(), 1)
        self.user.delete()
        self.assertEqual(Book.objects.count(), 0)

    def test_unique_constraint_title_user(self):
        book = Book.objects.create(
            title='Test Book',
            user=self.user,
            file=self.valid_pdf
        )
        self.created_files.append(book.file.path)
        duplicate_book = Book(
            title='Test Book',
            user=self.user,
            file=self.valid_pdf
        )

        with self.assertRaises(ValidationError):
            duplicate_book.full_clean()
    
    def test_different_users_same_title(self):

        other_user = User.objects.create_user(username='otheruser', password='otherpass')
        book1 = Book.objects.create(
            title= 'Test Book',
            user=self.user,
            file=self.valid_pdf
        )
        book2 = Book.objects.create(
            title='Test Book',
            user=other_user,
            file=self.valid_pdf
        )
        self.created_files.append(book1.file.path)
        self.created_files.append(book2.file.path)
        self.assertEqual(Book.objects.count(), 2)

    def test_valid_pdf(self):
        book = Book(
            title='Test Book',
            user=self.user,
            file=self.valid_pdf
        )
        try:
            book.full_clean()
            book.save()
            self.created_files.append(book.file.path)
            self.assertTrue(book.file.name.startswith('files/test'))
        except ValidationError as e:
            self.fail(f"Valid PDF raised ValidationError: {e}")
    
    def test_non_pdf_file(self):
        book = Book(
            title='Test Book',
            user=self.user,
            file=self.text_file
        )

        with self.assertRaisesMessage(ValidationError, 'File type not Known'):
            book.full_clean()
        
    def test_invalid_pdf(self):
        book = Book(
            title = 'Test Book', 
            user= self.user,
            file=self.invalid_pdf
        )

        with self.assertRaises(ValidationError):
            book.full_clean()
    
    def test_unknown_file_type(self):
        book = Book(
            title = 'Test Book',
            user=self.user,
            file=self.unknown_file
        )
        with self.assertRaisesMessage(ValidationError, 'File type not Known'):
            book.full_clean()
    
    
class QuestionairreModelTest(APITestCase):

    def setUp(self):
        self.created_files = []
        self.user = User.objects.create_user(username='testuser', email='testuser@email.com', password='testpass')
        with open('study_space/tests/files/Chapter_7.pdf', 'rb') as f:
            self.valid_pdf = SimpleUploadedFile(
                name='test.pdf',
                content=f.read(),
                content_type='application/pdf'
            )
        self.book = Book.objects.create(
            title='Test Book',
            user= self.user,
            file=self.valid_pdf
        )
        self.created_files.append(self.book.file.path)
        self.question_file = SimpleUploadedFile(
            name='questions.txt',
            content=b'Q: What? A: Something.',
            content_type='text/plain'
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
    
    def test_create_questionairre(self):
        questionairre = Questionairre.objects.create(
            book=self.book,
            user=self.user,
            detail_level='basic',
            question_answers_file=self.question_file
        )
        self.created_files.append(questionairre.question_answers_file.path)
        self.assertEqual(questionairre.book, self.book)
        self.assertEqual(questionairre.user, self.user)
        self.assertEqual(questionairre.detail_level, 'basic')
        self.assertTrue(questionairre.question_answers_file.name.startswith('questions/questions'))
        self.assertEqual(Questionairre.objects.count(), 1)
    
    def test_book_foreign_key_required(self):
        
        questionairre = Questionairre(
            user=self.user,
            detail_level='basic'
        )

        with self.assertRaises(ValidationError):
            questionairre.full_clean()
    
    def test_user_foreign_key_required(self):
        questionairre = Questionairre(
            book=self.book,
            detail_level='basic'
        )
        with self.assertRaises(ValidationError):
            questionairre.full_clean()
        
    def test_book_cascade_delete(self):
        questionairre = Questionairre.objects.create(
            book = self.book,
            user=self.user,
            detail_level = 'basic'
        )
        self.assertEqual(Questionairre.objects.count(), 1)
        self.book.delete()
        self.assertEqual(Questionairre.objects.count(), 0)
    
    def test_user_cascade_delete(self):
        questionairre = Questionairre.objects.create(
            book= self.book,
            user=self.user,
            detail_level='basic'
        )
        self.assertEqual(Questionairre.objects.count(), 1)
        self.user.delete()
        self.assertEqual(Questionairre.objects.count(), 0)
    
    def test_detail_level_choices(self):
        questionairre = Questionairre(
            book=self.book,
            user=self.user,
            detail_level='invalid'
        )
        with self.assertRaises(ValidationError):
            questionairre.full_clean()
    
    def test_question_answers_file_nullable(self):
        questionairre = Questionairre.objects.create(
            book=self.book,
            user=self.user,
            detail_level='basic'
        )
        self.assertFalse(questionairre.question_answers_file)
        self.assertEqual(Questionairre.objects.count(), 1)

    