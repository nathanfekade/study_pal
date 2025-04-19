import time
import uuid
from rest_framework import serializers
from study_space.models import Book, Questionairre
from pypdf import PdfReader
from google import genai
import google.generativeai as generativeai
import os
from django.conf import settings
from django.core.cache import cache


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
    start_page = serializers.IntegerField(write_only=True, required=False)
    end_page = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Questionairre
        fields = ['book','user','question_answers_file','detail_level', 'start_page', 'end_page']
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

    def validate(self, data):
        start_page = data.get('start_page')
        end_page = data.get('end_page')
        if start_page is not None and end_page is not None:
            if start_page > end_page:
                raise serializers.ValidationError({"non_field_errors":"start page can not be greater than end page"})
        return data

    def create(self, validated_data):
        request = self.context.get('request')  
        user = request.user if request else None  
        book = validated_data.get('book')
        detail_level = validated_data.get('detail_level')
        start_page = validated_data.pop('start_page', None)
        end_page = validated_data.pop('end_page', None)
        question_file_path = self.generate_question_file(book, detail_level, start_page, end_page)

        
        return Questionairre.objects.create(
            user=user,
            book=book,
            detail_level=detail_level,
            question_answers_file=question_file_path

        )

    def generate_question_file(self, book, detail_level, start_page, end_page):
            questions = self.generate_question_answers(book, detail_level, start_page, end_page)

            filename = f"{book.title}_{detail_level}_{uuid.uuid4().hex[:8]}.txt"
            file_path = os.path.join("questions", filename)

            full_path = os.path.join(settings.MEDIA_ROOT, "questions")
            os.makedirs(full_path, exist_ok=True)

            with open(os.path.join(settings.MEDIA_ROOT, file_path), "w", encoding="utf-8") as f:
                f.write(questions)

            return file_path


    def generate_question_answers(self, book, detail_level, start_page, end_page):

        if detail_level == 'basic':
            return self.question_detail_level(book.file, 9, start_page, end_page)
        elif detail_level == 'intermediate':
            return self.question_detail_level(book.file, 5, start_page, end_page)
        elif detail_level == 'detailed':
            return self.question_detail_level(book.file, 3, start_page, end_page)

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
       
        while True:

            last_request_time = cache.get('last_gemini_request_time', 0)
            now = time.time()
            delay = 4

            if now - last_request_time >= delay:
                 
                response = client.models.generate_content(
                    model="gemini-2.0-flash", contents=prompt
                )
                cache.set('last_gemini_request_time', time.time())
                return response.text
            else:
                 time.sleep(delay - (now - last_request_time))


    def question_detail_level(self, path, page_count , start_page, end_page):
        
        reader = PdfReader(path)
        num_of_pages = len(reader.pages)
        question = 'can you provide well thought out questions and answers from the text below do not add any other thing and don\'t number the questions \n\n'        
        prompt = question 
        question_answer = ""
        count = page_count - 1

        if start_page != None and end_page != None:
            
            end_page = end_page + 1
            
            if start_page<1 or end_page>num_of_pages:
                raise serializers.ValidationError("Error: Please enter valid page number")
            
            start_page = start_page - 1
            if start_page == end_page:
                 page = reader.pages[start_page]
                 text = page.extract_text()
                 prompt = prompt + " " + text
                 if prompt.strip() == question.strip():
                      return "sorry i was unable to generate questions"
                 question_answer = question_answer + self.question_generator(prompt=prompt)
                 return question_answer

            if (end_page-start_page) <= count: 
                for i in range(start_page, end_page):
                     page = reader.pages[i]
                     text = page.extract_text()
                     prompt = prompt + " " + text
                if prompt.strip() == question.strip():
                     return "sorry i was unable to generate questions"
                question_answer = question_answer + self.question_generator(prompt=prompt)
                return question_answer  
            
            for i in range(start_page, end_page):

                page = reader.pages[i]
                text = page.extract_text()
                prompt = prompt + " " + text

                if i == count:
                     if self.under_token_limit(prompt=prompt)[0] == False:
                          raise serializers.ValidationError("Token limit exceeded")
                          break
                     question_answer = question_answer + self.question_generator(prompt=prompt)
                     prompt = question
                     count += page_count

                     
                elif end_page-1 == i and i < count:
                     if self.under_token_limit(prompt=prompt)[0] == False:
                          raise serializers.ValidationError("Token limit exceeded")

                          break
                     question_answer = question_answer + self.question_generator(prompt=prompt)
                     prompt = question

            return question_answer
                 
        else:
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
                prompt = prompt + " " + text

                if i == count:
                    if self.under_token_limit(prompt=prompt)[0] == False:
                            raise serializers.ValidationError("Token limit exceeded")
                            break
                    question_answer = question_answer + self.question_generator(prompt=prompt)
                    prompt = question
                    
                    count += page_count

                elif num_of_pages-1 == i and i < count:
                    if self.under_token_limit(prompt=prompt)[0] == False:
                            raise serializers.ValidationError("Token limit exceeded")
                            break
                    
                    question_answer = question_answer + self.question_generator(prompt=prompt)
                    prompt = question

                    
            return question_answer


