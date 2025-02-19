from rest_framework import serializers
from study_space.models import Book, Questionairre

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ['user']

class QuestionairreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionairre
        fields = '__all__'
        read_only_fields = ['user', 'question_answers']

