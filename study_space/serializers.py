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
import logging


class BookSerializer(serializers.ModelSerializer):
    """
    Serializer for the Book model.

    This serializer handles the conversion of Book model instances to and from
    JSON format. It includes all fields from the model but marks the 'user' field
    as read-only to prevent modification through the API.
    """

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
        fields = ['id','book','user','question_answers_file','detail_level', 'start_page', 'end_page']
        read_only_fields = ['user', 'question_answers_file']

    def __init__(self, *args, **kwargs):
        """
        Initializes the serializer instance.

        Filters the queryset for the 'book' field to only include books owned by the
        current authenticated user.

        Parameters:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments, including 'context' which may contain the request.
        """

        super().__init__(*args, **kwargs)
        request = self.context.get("request")  
        user = request.user if request else None  

        if user:
            self.fields['book'].queryset = Book.objects.filter(user=user)  

    def validate_book(self, book):
        """
        Validates the selected book.

        Ensures that the book belongs to the current authenticated user.

        Parameters:
        book (Book): The book instance to validate.

        Returns:
        Book: The validated book instance.

        Raises:
        ValidationError: If the book does not belong to the user.
        """

        request = self.context.get("request")  
        user = request.user if request else None  

        if book.user != user:
            raise serializers.ValidationError("You do not have permission to access this book.")
        
        return book

    def validate(self, data):
        """
        Validates the serializer data.

        Checks that start_page is not greater than end_page if both are provided.

        Parameters:
        data (dict): The data to validate.

        Returns:
        dict: The validated data.

        Raises:
        ValidationError: If start_page > end_page.
        """

        start_page = data.get('start_page')
        end_page = data.get('end_page')
        if start_page is not None and end_page is not None:
            if start_page > end_page:
                raise serializers.ValidationError({"non_field_errors":"start page can not be greater than end page"})
        return data

    def create(self, validated_data):
        """
        Creates a new Questionairre instance.

        Generates a question-answer file using AI based on the book's PDF, detail level,
        and optional page range. Associates the file with the new Questionairre instance.

        Parameters:
        validated_data (dict): Validated data for creating the instance.

        Returns:
        Questionairre: The created Questionairre instance.
        """

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
        """
        Generates a file containing question-answer pairs.

        Calls the AI to generate questions and answers, then saves them to a text file
        in the media directory.

        Parameters:
        book (Book): The book instance from which to generate questions.
        detail_level (str): The detail level ('basic', 'intermediate', 'detailed').
        start_page (int, optional): Starting page for question generation.
        end_page (int, optional): Ending page for question generation.

        Returns:
        str: The relative path to the generated file.
        """
            
        questions = self.generate_question_answers(book, detail_level, start_page, end_page)

        filename = f"{book.title}_{uuid.uuid4().hex[:8]}.txt"
        file_path = os.path.join("questions", filename)

        full_path = os.path.join(settings.MEDIA_ROOT, "questions")
        os.makedirs(full_path, exist_ok=True)

        with open(os.path.join(settings.MEDIA_ROOT, file_path), "w", encoding="utf-8") as f:
            f.write(questions)

        return file_path


    def generate_question_answers(self, book, detail_level, start_page, end_page):
        """
        Generates question-answer pairs based on detail level.

        Maps detail_level to a page chunk size and calls the detail level handler.

        Parameters:
        book (Book): The book instance.
        detail_level (str): The detail level.
        start_page (int, optional): Starting page.
        end_page (int, optional): Ending page.

        Returns:
        str: The generated question-answer text.
        """

        if detail_level == 'basic':
            return self.question_detail_level(book.file, 9, start_page, end_page)
        elif detail_level == 'intermediate':
            return self.question_detail_level(book.file, 5, start_page, end_page)
        elif detail_level == 'detailed':
            return self.question_detail_level(book.file, 3, start_page, end_page)

    def under_token_limit(self, prompt, model_name="gemini-2.0-flash", max_tokens=1048000):
        """
        Checks if the prompt is under the token limit for the AI model.

        Uses the Generative AI model to count tokens in the prompt.

        Parameters:
        prompt (str): The prompt to check.
        model_name (str, optional): The model name to use for token counting.
        max_tokens (int, optional): The maximum allowed tokens.

        Returns:
        tuple: (bool, int) - Whether under limit and the token count.

        Raises:
        Logs an error if token counting fails.
        """

        try:
            generativeai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
            
            model = generativeai.GenerativeModel(model_name)
            input_tokens = model.count_tokens(prompt).total_tokens
            if input_tokens > max_tokens:
                return False, input_tokens
            else:
                return True, input_tokens

        except Exception as e:
            logging.error(f"An error occured during token limit check: {e}")
            return False, 0


    def question_generator(self, prompt):
        """
        Generates content using the Google Gemini AI model.

        Implements rate limiting using Django cache to avoid exceeding API limits.

        Parameters:
        prompt (str): The prompt for content generation.

        Returns:
        str: The generated text from the AI model.
        """

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
        """
        Generates question-answer pairs from PDF pages in chunks.

        Reads the PDF, builds prompts in chunks of 'page_count' pages, checks token limits,
        and generates Q&A using the AI. Handles optional page ranges.

        Parameters:
        path (FileField): The path to the PDF file.
        page_count (int): The number of pages per chunk.
        start_page (int, optional): Starting page (1-indexed).
        end_page (int, optional): Ending page (1-indexed).

        Returns:
        str: Concatenated question-answer pairs.

        Raises:
        ValidationError: If invalid page numbers, token limit exceeded, or unable to generate questions.
        """

        reader = PdfReader(path)
        num_of_pages = len(reader.pages)
        question = 'Generate well-thought-out question and answer pairs based solely on the text below. Format each pair as a single line with the question and answer separated by a semicolon (;). If a question or answer contains multiple lines, replace newline characters with <br> to preserve formatting for Anki. Do not add numbering, extra text, or any other content beyond the question and answer pairs. Ensure semicolons do not appear within the question or answer text by replacing any existing semicolons with commas.'
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


