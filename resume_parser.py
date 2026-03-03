import PyPDF2
import json
from groq import Groq

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not installed. DOCX support disabled.")


def extract_text_from_pdf(file_path):
    # First try PyPDF2
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        if text.strip():
            return text
    except Exception as e:
        print(f"PyPDF2 failed: {e}")

    # Fallback to pypdf
    try:
        from pypdf import PdfReader
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file, strict=False)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        if text.strip():
            return text
    except Exception as e:
        print(f"pypdf failed: {e}")

    print(f"Could not extract text from {file_path}")
    return ""


def extract_text_from_docx(file_path):
    if not DOCX_AVAILABLE:
        return ""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""


def extract_text_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT file: {e}")
        return ""


def extract_text_from_file(file_path):
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_from_docx(file_path)
    elif file_path.endswith('.txt'):
        return extract_text_from_txt(file_path)
    return ""


def parse_resume_with_groq(resume_text, api_key):
    client = Groq(api_key=api_key)

    def call_groq(messages):
        return client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.0,
            max_tokens=2000,
        ).choices[0].message.content

    # First attempt
    raw_text = call_groq([
        {
            "role": "system",
            "content": "You are a JSON-only resume parser. Your entire response must be a valid JSON object starting with { and ending with }. No text before or after."
        },
        {
            "role": "user",
            "content": f"""Convert this resume into a JSON object with these fields:
name, email, phone, location, address, dob (YYYY-MM-DD or null), passport_details, passport_status,
current_company, previous_companies (array of {{company, role, duration}}), domain,
years_of_experience (integer), professional_summary, skills (array),
education (array of {{degree, institution, year, field_of_study}}),
projects (array of {{title, description, technologies}}),
patents (array), publications (array), research_papers (array).

RESUME:
{resume_text}

RESPOND WITH JSON ONLY. START WITH {{ END WITH }}"""
        }
    ])

    raw_text = raw_text.strip()

    # If response is not JSON, force it with a second call
    if not raw_text.startswith('{'):
        print("First attempt returned plain text, forcing JSON with second call...")
        raw_text = call_groq([
            {
                "role": "system",
                "content": "You convert text into JSON. Respond only with valid JSON."
            },
            {
                "role": "user",
                "content": f"""Convert this text into a JSON object with fields:
name, email, phone, location, address, dob, passport_details, passport_status,
current_company, previous_companies, domain, years_of_experience, professional_summary,
skills, education, projects, patents, publications, research_papers.

TEXT TO CONVERT:
{raw_text}

Return only the JSON object."""
            }
        ])
        raw_text = raw_text.strip()

    try:
        raw_text = raw_text.replace('```json', '').replace('```', '').strip()
        metadata = json.loads(raw_text)

        defaults = {
            'phone': '', 'address': '', 'location': '', 'dob': None,
            'passport_details': '', 'passport_status': '', 'current_company': '',
            'previous_companies': [], 'domain': '', 'years_of_experience': 0,
            'professional_summary': '', 'skills': [], 'education': [],
            'projects': [], 'patents': [], 'publications': [], 'research_papers': []
        }
        for key, default_value in defaults.items():
            metadata.setdefault(key, default_value)

        skills = metadata.get('skills', [])
        metadata['skills_text'] = ", ".join(skills) if isinstance(skills, list) else str(skills)

        try:
            metadata['years_of_experience'] = int(metadata.get('years_of_experience', 0))
        except:
            metadata['years_of_experience'] = 0

        return metadata

    except Exception as e:
        print(f"Parsing error: {e}")
        print(f"Raw response: {raw_text[:500]}")
        return None


def parse_resume_file(file_path, api_key):
    resume_text = extract_text_from_file(file_path)
    if not resume_text:
        print(f"Could not extract text from {file_path}")
        return None
    return parse_resume_with_groq(resume_text, api_key)
