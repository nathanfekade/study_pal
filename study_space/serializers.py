import time
from rest_framework import serializers
from study_space.models import Book, Questionairre
from pypdf import PdfReader
from google import genai
import google.generativeai as generativeai
import os
from django.conf import settings


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ['user']

class QuestionairreSerializer(serializers.ModelSerializer):
    
    book = serializers.SlugRelatedField(
        queryset=Book.objects.all(),
        slug_field='title'  
    )
    
    class Meta:
        model = Questionairre
        fields = '__all__'
        read_only_fields = ['user', 'question_answers_file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")  
        user = request.user if request else None  

        if user:
            self.fields['book'].queryset = Book.objects.filter(user=user)  

    def validate_book(self, book):
        request = self.context.get("request")  
        user = request.user if request else None  

        if book.user != user:
            raise serializers.ValidationError("You do not have permission to access this book.")
        
        return book


    def create(self, validated_data):
        request = self.context.get('request')  
        user = request.user if request else None  

        book = validated_data.get('book')
        detail_level = validated_data.get('detail_level')



        question_file_path = self.generate_question_file(book, detail_level)

        return Questionairre.objects.create(
            user=user,
            book=book,
            detail_level=detail_level,
            question_answers_file=question_file_path

        )

    def generate_question_file(self, book, detail_level):
            questions = self.generate_question_answers(book, detail_level)

            filename = f"{book.title}_{detail_level}_{int(time.time())}.txt"
            file_path = os.path.join("media/questions", filename)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(questions)

            return file_path


    def generate_question_answers(self, book, detail_level):

        if detail_level == 'basic':
            return self.basic(book.file)
        elif detail_level == 'intermediate':
            return self.intermediate(book.file)
        elif detail_level == 'detailed':
            return self.detailed(book.file)

    def under_token_limit(self, prompt, model_name="gemini-2.0-flash", max_tokens=1048000):
        try:
            generativeai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
            
            model = generativeai.GenerativeModel(model_name)
            input_tokens = model.count_tokens(prompt).total_tokens
            if input_tokens > max_tokens:
                return False, input_tokens
            else:
                return True, input_tokens

        except Exception as e:
            print(f"An error occurred: {e}")
            return False, 0


    def question_generator(self, prompt):
        client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        return response.text


    def basic(self, path):

        reader = PdfReader(path)
        num_of_pages = len(reader.pages)
        question = 'can you provide well thougt out questions and answers from the text below do not add any other thing and don\'t number the questions \n\n'        
        prompt = question 
        question_answer = ""

        count = 9

        if num_of_pages <= count:
            for i in range(num_of_pages):
                page = reader.pages[i]
                
                text = page.extract_text()
                prompt = prompt + " " + text

            if prompt.strip() == question.strip():
                return "sorry i was unable to generate questions"

            question_answer = question_answer + self.question_generator(prompt=prompt)
            return question_answer

        for i in range(num_of_pages):
            page = reader.pages[i]
            
            text = page.extract_text()
            prompt = prompt + text


            
            if i == count:
                # self.under_token_limit(prompt=prompt)
                if self.under_token_limit(prompt=prompt)[0] == False:
                        self.intermediate(path)
                        break
                question_answer = question_answer + self.question_generator(prompt=prompt)
                prompt = question
                
                count +=10

            elif num_of_pages-1 == i and i < count:
                # self.under_token_limit(prompt=prompt)
                if self.under_token_limit(prompt=prompt)[0] == False:
                        self.intermediate(path)
                        break
                
                question_answer = question_answer + self.question_generator(prompt=prompt)
                prompt = question
                
        return question_answer

    def intermediate(self, path):

        reader = PdfReader(path)
        num_of_pages = len(reader.pages)
        question = 'can you provide well thougt out questions and answers from the text below do not add any other text into it and don\'t number the questions \n\n'        
        prompt = question 
        question_answer = ""
        
        count = 5

        if num_of_pages <= count:
            for i in range(num_of_pages):
                page = reader.pages[i]
                
                text = page.extract_text()
                prompt = prompt + " " + text
            
            
            if prompt.strip() == question.strip():
                return "sorry i was unable to generate questions"
            
            question_answer = question_answer + self.question_generator(prompt=prompt)
            return question_answer


        for i in range(num_of_pages):
            page = reader.pages[i]
            
            text = page.extract_text()
            prompt = prompt + text
            
            if i == count:
                # self.under_token_limit(prompt=prompt)
                if self.under_token_limit(prompt=prompt)[0] == False:
                        self.detailed(path)
                        break
                question_answer = question_answer + self.question_generator(prompt=prompt)
                prompt = question
                
                count +=6
                
            elif num_of_pages-1 == i and i < count:
                # self.under_token_limit(prompt=prompt)
                if self.under_token_limit(prompt=prompt)[0] == False:
                        self.detailed(path)
                        break
                
                question_answer = question_answer + self.question_generator(prompt=prompt)
                prompt = question
        return question_answer

    def detailed(self, path):

        reader = PdfReader(path)
        num_of_pages = len(reader.pages)
        question = 'can you provide well thougt out questions and answers from the text below do not add any other text into it and don\'t number the questions \n\n'        
        prompt = question 
        question_answer = ""
        
        count = 2

        if num_of_pages <= count:
            for i in range(num_of_pages):
                page = reader.pages[i]
                
                text = page.extract_text()
                prompt = prompt + " " + text
            if prompt.strip() == question.strip():
                return "sorry i was unable to generate questions"
            question_answer = question_answer + self.question_generator(prompt=prompt)
            return question_answer

        for i in range(num_of_pages):
            page = reader.pages[i]
            
            text = page.extract_text()
            prompt = prompt + text
            
            if i == count:
                # self.under_token_limit(prompt=prompt)
                if self.under_token_limit(prompt=prompt)[0] == False:
                        if prompt.endswith(text):
                            prompt = prompt[:-len(text)]
                question_answer = question_answer + self.question_generator(prompt=prompt)
                prompt = question
                
                count +=3
            
            elif num_of_pages-1 == i  and i < count:
                # self.under_token_limit(prompt=prompt)
                if self.under_token_limit(prompt=prompt)[0] == False:
                        if prompt.endswith(text):
                            prompt = prompt[:-len(text)]

                question_answer = question_answer + self.question_generator(prompt=prompt)
                prompt = question

        return question_answer

