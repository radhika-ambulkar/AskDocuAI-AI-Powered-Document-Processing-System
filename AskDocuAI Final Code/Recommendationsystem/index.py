from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

import os
import pymysql
import re
import json
import requests
import time
from PyPDF2 import PdfReader, PdfWriter
from transformers import pipeline
from .models import Recommendation, Feedback, ExtractedText
from .forms import FeedbackForm
#from Recommendationsystem.index import save_file, extract_text_from_pdf, process_pdf



# Database Connectivity
mydb = pymysql.connect(host="localhost", user="root", password="root", database="AI_Power_Document_Processing")

# Views
def index(request):
    return render(request, "index.html")

def about(request):
    return render(request, "about.html")

def team(request):
    return render(request, "team.html")

def chat_view(request):
    return render(request, 'chat.html')

def signup(request):
    return render(request, "signup.html")

def signin(request):
    return render(request, "signin.html")

def registration(request):
    return render(request, "registration.html")

def recommendation_list(request):
    recommendations = Recommendation.objects.all()
    return render(request, 'recommendations.html', {'recommendations': recommendations})

def feedback_page(request):
    recommendations = Recommendation.objects.all()
    return render(request, 'feedback.html', {'recommendations': recommendations})

@login_required
def feedback_view(request):
    return render(request, 'feedback.html')


def Reg(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        password = request.POST.get('password')
        sql = "INSERT INTO registration(name,email,contact,password) VALUES (%s,%s,%s,%s)"
        values = (name, email, contact, password)
        cur = mydb.cursor()
        cur.execute(sql, values)
        mydb.commit()
        return redirect('login.html')

def login(request):
    return render(request, "login.html")

def dologin(request):
    user_email = request.POST.get('email')
    passw = request.POST.get('password')
    sql = "SELECT * FROM registration"
    c1 = mydb.cursor()
    c1.execute(sql)
    rows = c1.fetchall()
   
    for x in rows:
        if user_email == x[2] and passw == x[4]:
            name = x[1]
            request.session['uname'] = name
            return render(request, "Dashboard.html")
    return redirect('login')


def Dashboard(request):
    return render(request, "Dashboard.html")


# Load summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_text(text, chunk_size=512):  # Reduce chunk size to 512
    """Splits long text into chunks and summarizes each chunk separately."""
    
    # Handle empty input case
    if not text.strip():
        return "Error: No text extracted from PDF."
    
    # Split text into chunks
    words = text.split()
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    
    print(f"Total Chunks: {len(chunks)}")  # Debugging
    for idx, chunk in enumerate(chunks):
        print(f"Chunk {idx + 1}: {len(chunk.split())} words")  # Print chunk size
    
    # Summarize each chunk
    summaries = []
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=150, min_length=50, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        except Exception as e:
            print(f"Error summarizing chunk: {e}")
            summaries.append(chunk[:200])  # Return partial text instead of failing
    
    # Combine all summarized chunks
    final_summary = " ".join(summaries)
    
    return final_summary

def up(request):
    summary_text = ""
    questions_with_answers = []

    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')

        if pdf_file:
            file_path = save_file(pdf_file)  # Save uploaded PDF

            # Initialize progress
            cache.set('progress', 10)  

            extracted_text_list = extract_text_from_pdf(file_path)  # Extract text
            extracted_text = " ".join(extracted_text_list)

            cache.set('progress', 30)  

            # Summarize extracted text
            summary_text = summarize_text(extracted_text)

            cache.set('progress', 60)  

            # Generate questions & answers
            questions_with_answers = process_pdf(file_path)

            cache.set('progress', 90)

		# Check if the user is authenticated before saving it
            if request.user.is_authenticated:
                user = request.user
            else:
                user = None  # Anonymous users  

            # Save summary instead of full text
            extracted_text_obj = ExtractedText.objects.create(
                user=user,
                document_name=pdf_file.name,
                text=summary_text
            )

            cache.set('progress', 100)  # Mark as complete

            return render(request, "up.html", {
                'extracted_text': summary_text,
                'questions_with_answers': questions_with_answers,
                'extracted_text_id': extracted_text_obj.id,
            })

    return render(request, "up.html", {
        'extracted_text': summary_text,
        'questions_with_answers': questions_with_answers,
    })

def check_progress(request):
    """Returns the current progress for the progress bar."""
    progress = cache.get('progress', 0)  # Default to 0 if no progress is stored
    return JsonResponse({'progress': progress})


def save_file(pdf_file):
    file_path = f'temp/{pdf_file.name}'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb+') as destination:
        for chunk in pdf_file.chunks():
            destination.write(chunk)
    return file_path

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            cleaned_text = remove_header_footer(page_text)
            text.append(cleaned_text)
    return text

def remove_header_footer(text):
    lines = text.splitlines()
    if len(lines) > 2:
        return "\n".join(lines[1:-1])
    return text

def process_pdf(file_path):
    questions_with_answers = []
    text_data = extract_text_from_pdf(file_path)  # Extract text from each page

    for text in text_data:
        questions = generate_unique_question(text)  # Generates multiple questions

        if not questions:  # Check if questions are generated
            print("No questions generated for text:", text[:100])  # Debugging
            continue  # Skip this page if no questions are generated

        for question_text in questions:
            answer = extract_answer(text, question_text)
            questions_with_answers.append({
                'question': question_text,
                'answer': answer
            })

    return questions_with_answers

def generate_unique_question(text):
    question_generator = pipeline("text2text-generation", model="valhalla/t5-small-qg-hl")
    try:
        questions = question_generator(text, max_length=50, num_return_sequences=5, num_beams=5)
        if not questions:  
            return []  # Return an empty list if no questions are generated
        return [q['generated_text'] for q in questions if 'generated_text' in q]  # Extract text safely
    except Exception as e:
        print("Error generating questions:", e)  # Log errors for debugging
        return []  # Return empty list to avoid undefined variable

def extract_answer(text, question):
    sentences = re.split(r'(?<=[.!?]) +', text)
    normalized_question = question.lower().strip()
    best_answer = "No answer found."
    highest_relevance = 0

    for sentence in sentences:
        relevance_score = calculate_relevance(normalized_question, sentence.lower().strip())
        if relevance_score > highest_relevance:
            highest_relevance = relevance_score
            best_answer = sentence.strip() if relevance_score > 0 else best_answer

    return best_answer

# Generate your Groq API key and replace it with your actual key
# GROQ_API_KEY = "your_new_groq_api_key"

#@csrf_exempt
def chatbot_query(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_query = data.get("query")
            document_id = data.get("document_id")

            # Fetch the extracted text object without filtering by user
            extracted_text_obj = ExtractedText.objects.filter(id=document_id).first()
            if not extracted_text_obj:
                return JsonResponse({"error": "Document not found"}, status=404)

            extracted_text = extracted_text_obj.text[:4000]  # Truncate if needed

            # Prepare the prompt for the Groq API
            prompt = f"Based on the following document, answer the query: {user_query}\n\nDocument:\n{extracted_text}"

            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-70b-8192",  # Corrected the model name
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            # Send the request to the Groq API
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                answer = response.json()["choices"][0]["message"]["content"]
                return JsonResponse({"answer": answer})
            else:
                error_message = response.json().get("error", {}).get("message", "Unknown error occurred.")
                print(f"Error from Groq API: {error_message}")
                return JsonResponse({"error": f"Failed to get response: {error_message}"}, status=500)

        except Exception as e:
            print(f"Exception occurred: {e}")
            return JsonResponse({"error": "An error occurred while processing your request."}, status=500)		
           
def calculate_relevance(question, sentence):
    question_words = set(re.findall(r'\w+', question))
    sentence_words = set(re.findall(r'\w+', sentence))
    return len(question_words.intersection(sentence_words))


@login_required
def submit_feedback(request, user_id):
    if request.method == "POST":
        feedback_text = request.POST.get("feedback_text")
        
        # Ensure user is authenticated
        if request.user.is_authenticated:
            feedback, created = Feedback.objects.update_or_create(
                user=request.user,  # Use request.user instead of user_id
                defaults={"feedback_text": feedback_text},
            )
            return redirect("feedback_success")
        else:
            return redirect("login")  # Redirect if user is not logged in

    return render(request, "feedback.html")

def View(request):
    return render(request, "View.html")