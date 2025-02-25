import time
from rest_framework import serializers
from study_space.models import Book, Questionairre
from pypdf import PdfReader
from google import genai
from pypdf import PdfReader
import google.generativeai as generativeai
import os


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



        # question_answers = self.generate_question_answers(book, detail_level)
        question_file_path = self.generate_question_file(book, detail_level)

        return Questionairre.objects.create(
            user=user,
            book=book,
            detail_level=detail_level,
            # question_answers=question_answers
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
            # generativeai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            generativeai.configure(api_key="AIzaSyB8sByhFGfgOFRnOKw82xC0T-SJEd2xIz8")
            
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
        client = genai.Client(api_key="AIzaSyB8sByhFGfgOFRnOKw82xC0T-SJEd2xIz8")
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
            
            question_answer = question_answer + self.question_generator(prompt=prompt)
            return question_answer

        for i in range(num_of_pages):
            page = reader.pages[i]
            
            text = page.extract_text()
            prompt = prompt + text


            
            if i == count:
                print(count)
                print(self.under_token_limit(prompt=prompt))
                if self.under_token_limit(prompt=prompt)[0] == False:
                        self.intermediate(path)
                        break
                question_answer = question_answer + self.question_generator(prompt=prompt)
                print(question_answer)
                
                count +=10

            elif num_of_pages-1 == i and i < count:
                print(num_of_pages)
                print(self.under_token_limit(prompt=prompt))
                if self.under_token_limit(prompt=prompt)[0] == False:
                        self.intermediate(path)
                        break
                
            
                # question_answer = question_answer + self.question_generator(prompt=prompt)
                # print(question_answer)  
                # f = open(f"./media/questions", "a")
                # f.write("Now the file has more content!")
                # f.close()     
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
            
            question_answer = question_answer + self.question_generator(prompt=prompt)
            return question_answer


        for i in range(num_of_pages):
            page = reader.pages[i]
            
            text = page.extract_text()
            prompt = prompt + text
            
            if i == count:
                print(count)
                print(self.under_token_limit(prompt=prompt))
                count +=6
                if self.under_token_limit(prompt=prompt)[0] == False:
                        self.detailed(path)
                        break

            elif num_of_pages-1 == i and i < count:
                print(num_of_pages)
                print(self.under_token_limit(prompt=prompt))
                if self.under_token_limit(prompt=prompt)[0] == False:
                        self.detailed(path)
                        break


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
            
            question_answer = question_answer + self.question_generator(prompt=prompt)
            return question_answer

        for i in range(num_of_pages):
            page = reader.pages[i]
            
            text = page.extract_text()
            prompt = prompt + text
            
            if i == count:
                print(count)
                print(self.under_token_limit(prompt=prompt))
                count +=3
                if self.under_token_limit(prompt=prompt)[0] == False:
                        if prompt.endswith(text):
                            prompt = prompt[:-len(text)]
            
            elif num_of_pages-1 == i  and i < count:
                print(num_of_pages)
                print(self.under_token_limit(prompt=prompt))
                if self.under_token_limit(prompt=prompt)[0] == False:
                        if prompt.endswith(text):
                            prompt = prompt[:-len(text)]





