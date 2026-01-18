from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Resume

import requests
import PyPDF2

import json
import os
import time
from requests.exceptions import RequestException


# --- Utility Functions (No Change) ---

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        return text
    except PyPDF2.errors.PdfReadError:
        print(f"Error: Invalid or corrupted PDF file at {file_path}")
        return ""
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_file(file_path):
    """Extract text based on file type"""
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)

    elif file_path.endswith('.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT file: {e}")
            return ""
    return ""


# --- Django Views ---

def index(request):
    """Main page view"""
    resumes = Resume.objects.all()
    return render(request, 'resumes/index.html', {'resumes': resumes})


@csrf_exempt
def rank_resumes(request):
    """Rank resumes based on job role using Gemini API to extract info and rank"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON body'})

        job_role = data.get('job_role', '')

        if not job_role:
            return JsonResponse({'success': False, 'message': 'Job role is required'})

        # Get all resumes from database
        resumes = Resume.objects.all()

        if not resumes:
            return JsonResponse({'success': False, 'message': 'No resumes available in the system'})

        # Extract text from all resumes
        resume_data = []
        for resume in resumes:
            file_path = resume.file.path
            text = extract_text_from_file(file_path)
            if text:
                resume_data.append({
                    'id': resume.id,
                    'text': text,
                    'filename': os.path.basename(resume.file.name)
                })

        if not resume_data:
            return JsonResponse({'success': False, 'message': 'Could not extract text from any uploaded resume files.'})


        API_KEY = "AIzaSyDdnmwQpIbetUt1mg8BloV-qt3luohz74E"
        GEMINI_MODEL = "gemini-2.5-flash"
        API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"


        system_instruction = "You are a recruitment expert and an efficient JSON generator. Your task is to extract required information from the provided resumes and rank them based on a given job role."


        user_query = f"""
I have {len(resume_data)} resumes and need you to:
1. Extract key information from each resume (Name, Years of Experience, Skills).
2. Rank them based on how well they match the job role: "{job_role}".

For each resume, you MUST extract the following from the resume text itself:
- Name: The candidate's actual name from the resume
- Years of Experience: Calculate or extract the total years of professional experience
- Key Skills: List the top 5 most relevant skills for this job role
- Match Score: Rate 0-100 on how well they match the "{job_role}" position
- Ranking Reason: Brief explanation of why this ranking

Here are the resumes to analyze:
"""
        for idx, resume in enumerate(resume_data, 1):
            user_query += f"\n{'=' * 50}\nRESUME {idx} (DB ID: {resume['id']}):\n{'=' * 50}\n{resume['text']}\n"

        user_query += f"""\n\nIMPORTANT: Extract the actual name from each resume text. Do NOT use generic names.
Provide your response ONLY as a JSON array of objects, sorted by match_score (highest first).
"""


        response_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "resume_id": {
                        "type": "integer",
                        "description": "The unique ID of the resume from the input."
                    },
                    "name": {
                        "type": "string",
                        "description": "The candidate's full name extracted from the resume text."
                    },
                    "years_of_experience": {
                        "type": "integer",
                        "description": "The total years of professional experience."
                    },
                    "skills": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Top 5 skills relevant to the job role."
                    },
                    "match_score": {
                        "type": "integer",
                        "description": "Match score between 0 and 100."
                    },
                    "ranking_reason": {
                        "type": "string",
                        "description": "Brief explanation for the match score and ranking."
                    }
                },
                "required": ["resume_id", "name", "years_of_experience", "skills", "match_score", "ranking_reason"]
            }
        }


        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": user_query}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": system_instruction}
                ]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": response_schema
            }
        }

        headers = {"Content-Type": "application/json"}


        max_retries = 5
        base_delay = 1

        for attempt in range(max_retries):
            try:

                response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                response.raise_for_status()


                result = response.json()

                if (result.get('candidates') and
                        result['candidates'][0].get('content') and
                        result['candidates'][0]['content'].get('parts') and
                        result['candidates'][0]['content']['parts'][0].get('text')):

                    json_text = result['candidates'][0]['content']['parts'][0]['text']
                    ranked_resumes = json.loads(json_text)

                    # Add resume filename to each result
                    for ranked_resume in ranked_resumes:
                        resume_obj = Resume.objects.get(id=ranked_resume['resume_id'])
                        ranked_resume['resume_filename'] = resume_obj.file.name

                    return JsonResponse({
                        'success': True,
                        'ranked_resumes': ranked_resumes,
                        'job_role': job_role
                    })

                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'AI response was successful but contained no content or an unexpected structure.'
                    })

            except requests.exceptions.HTTPError as e:
                error_detail = ""
                retry_after = None

                try:
                    error_response = response.json()
                    error_detail = error_response


                    if response.status_code == 429:

                        for detail in error_response.get('error', {}).get('details', []):
                            if detail.get('@type') == 'type.googleapis.com/google.rpc.RetryInfo':
                                retry_delay_str = detail.get('retryDelay', '0s')
                                retry_after = int(retry_delay_str.rstrip('s')) + 1
                                break
                except:
                    error_detail = response.text

                print(f"HTTP Error: {e}")
                print(f"Response: {error_detail}")

                if attempt < max_retries - 1:

                    if retry_after and response.status_code == 429:
                        delay = min(retry_after, 60)
                        print(f"Rate limit hit. Retrying in {delay}s as suggested by API...")
                    else:
                        delay = base_delay * (2 ** attempt)
                        print(f"API Request failed. Retrying in {delay}s...")

                    time.sleep(delay)
                    continue
                else:

                    if response.status_code == 429:
                        return JsonResponse({
                            'success': False,
                            'message': 'API rate limit exceeded. Please wait a minute and try again, or check your API quota at https://ai.dev/usage'
                        })
                    return JsonResponse({
                        'success': False,
                        'message': f'Failed to communicate with the Gemini API: {str(e)}'
                    })

            except RequestException as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"API Request failed ({e}). Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Failed to communicate with the Gemini API after multiple retries: {str(e)}'
                    })

            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}. Raw text: {json_text if 'json_text' in locals() else 'N/A'}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error parsing AI response JSON. The AI returned malformed data: {str(e)}'
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'An unexpected server error occurred: {str(e)}'
                })

    return JsonResponse({'success': False, 'message': 'Invalid request method or format'})