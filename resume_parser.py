"""
Resume Parser Utility
Extracts metadata from resume files using Gemini API
"""

import PyPDF2
import requests
import json
from datetime import datetime


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        return text
    except PyPDF2.errors.PdfReadError as e:
        print(f"Error: Invalid or corrupted PDF file at {file_path}: {e}")
        return ""
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT file: {e}")
        return ""


def extract_text_from_file(file_path):
    """Extract text based on file type"""
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.txt'):
        return extract_text_from_txt(file_path)
    return ""


def parse_resume_with_gemini(resume_text, api_key):
    """
    Parse resume text using Gemini API to extract structured metadata

    """

    GEMINI_MODEL = "gemini-2.0-flash-exp"
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    system_instruction = """You are an expert resume parser. 
Extract information from resumes flexibly. 
Not all resumes will have all fields - that's okay! 
Extract what's available and use empty values for missing fields.
Different resume types (engineer, researcher, manager) will have different fields."""

    user_query = f"""
Extract information from this resume. 

IMPORTANT: 
- Extract ONLY fields that are actually present in the resume
- For missing fields, use: empty string ("") for text, empty array ([]) for lists, null for dates
- Don't make up information that isn't in the resume
- Different resume types will have different fields

RESUME TEXT:
{resume_text}

Extract these fields (if available):
- Personal: name, email, phone, address, location, dob, passport_details, passport_status
- Professional: current_company, previous_companies (array), domain, years_of_experience, professional_summary
- Skills & Education: skills (array), education (array)
- For Engineers: projects (array)
- For Researchers: patents (array), publications (array), research_papers (array)

FORMATS:
- previous_companies: [{{"company": "Microsoft", "role": "Engineer", "duration": "2018-2020"}}, ...]
- education: [{{"degree": "B.Tech", "institution": "IIT", "year": "2020", "field_of_study": "CS"}}, ...]
- projects: [{{"title": "Project Name", "description": "...", "technologies": "Python, Django"}}, ...]
- patents: [{{"title": "Patent Title", "patent_number": "US12345", "year": "2022"}}, ...]
- publications: [{{"title": "Paper Title", "journal": "Nature", "year": "2023", "citations": "50"}}, ...]
- research_papers: [{{"title": "Paper Title", "conference": "CVPR", "year": "2023"}}, ...]
"""

    # Define response schema for structured output
    response_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "address": {"type": "string"},
            "location": {"type": "string"},
            "dob": {"type": ["string", "null"]},
            "passport_details": {"type": "string"},
            "passport_status": {"type": "string"},
            "current_company": {"type": "string"},
            "previous_companies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "company": {"type": "string"},
                        "role": {"type": "string"},
                        "duration": {"type": "string"}
                    }
                }
            },
            "domain": {"type": "string"},
            "years_of_experience": {"type": "integer"},
            "professional_summary": {"type": "string"},
            "skills": {
                "type": "array",
                "items": {"type": "string"}
            },
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "degree": {"type": "string"},
                        "institution": {"type": "string"},
                        "year": {"type": "string"},
                        "field_of_study": {"type": "string"}
                    }
                }
            },
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "technologies": {"type": "string"}
                    }
                }
            },
            "patents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "patent_number": {"type": "string"},
                        "year": {"type": "string"}
                    }
                }
            },
            "publications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "journal": {"type": "string"},
                        "year": {"type": "string"},
                        "citations": {"type": "string"}
                    }
                }
            },
            "research_papers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "conference": {"type": "string"},
                        "year": {"type": "string"}
                    }
                }
            }
        },
        "required": ["name", "email"]  # Only name and email are required
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

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()

        #if Gemini returned data, we succeeded
        json_text = result['candidates'][0]['content']['parts'][0]['text']
        metadata = json.loads(json_text)

        # Set defaults for all optional fields that might be missing
        defaults = {
            'phone': '',
            'address': '',
            'location': '',
            'dob': None,
            'passport_details': '',
            'passport_status': '',
            'current_company': '',
            'previous_companies': [],
            'domain': '',
            'years_of_experience': 0,
            'professional_summary': '',
            'skills': [],
            'education': [],
            'projects': [],
            'patents': [],
            'publications': [],
            'research_papers': []
        }

        # Fill in missing fields with defaults
        for key, default_value in defaults.items():
            metadata.setdefault(key, default_value)

        # Convert skills array to comma-separated string for storage
        if isinstance(metadata.get('skills'), list):
            metadata['skills_text'] = ', '.join(metadata['skills'])
        else:
            metadata['skills_text'] = ''

        return metadata

    except Exception as e:
        # Any error = extraction failed
        print(f"Extraction failed: {e}")
        return None


def parse_resume_file(file_path, api_key):
    """
    Complete resume parsing pipeline
    """
    # Step 1: Extract text from file
    resume_text = extract_text_from_file(file_path)

    if not resume_text:
        print(f"Could not extract text from {file_path}")
        return None

    # Step 2: Parse with Gemini
    metadata = parse_resume_with_gemini(resume_text, api_key)

    if metadata:
        # Add the full resume text to metadata
        metadata['resume_text'] = resume_text
        return metadata

    return None
