from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    title = models.CharField(max_length=50)
    user = models.ForeignKey(User, related_name='book_user', on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['title','user'], name='unique_book_title_user')
        ]

class Questionairre(models.Model):

    DETAIL_CHOICE = [
        ('basic', 'BASIC'),
        ('intermediate', 'INTERMEDIATE'),
        ('in-depth', 'IN-DEPTH'),
    ]

    book = models.ForeignKey(Book, related_name='questionairre_book', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='questionairre_user', on_delete=models.CASCADE)
    question_answers = models.TextField()
    detail_level = models.CharField(max_length=20, choices=DETAIL_CHOICE, default='basic')


