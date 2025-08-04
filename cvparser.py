import io
import json
import yaml
from typing import Dict, Any
from PyPDF2 import PdfReader
from openai import OpenAI
from pydantic import BaseModel
from decouple import config
from coverlatter import CoverLetterGenerator

client = OpenAI(api_key=config("OPENAI_API_KEY"))


# === Resume Parsing Logic ===
def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        pdf_reader = PdfReader(io.BytesIO(file_content))
        text_parts = [
            page.extract_text() for page in pdf_reader.pages if page.extract_text()
        ]
        return "\n".join(text_parts).strip()
    except Exception as e:
        raise ValueError(f"Error reading PDF: {e}")


def parse_resume_with_openai(resume_text: str) -> Dict[str, Any]:
    prompt = """
You are an AI bot designed to parse professional resumes. Extract all relevant information in structured JSON format with the following keys:

1. full_name (string): Full name of the candidate
2. email (string): Email address
3. phone (string, optional): Phone number if available
4. address (string, optional): Candidate's location or mailing address
5. linkedin (string, optional): LinkedIn profile URL
6. github (string, optional): GitHub profile URL
7. portfolio (string, optional): Portfolio or personal website URL
8. summary (string, optional): Professional summary or career objective

9. education (list): List of education entries, each with:
    - degree (string)
    - field_of_study (string)
    - institution (string)
    - start_date (string, optional)
    - end_date (string, optional)
    - grade_or_gpa (string, optional)

10. certifications (list): List of certifications with:
    - name (string)
    - issuer (string, optional)
    - issue_date (string, optional)
    - expiration_date (string, optional)

11. employment (list): List of employment history with:
    - company (string)
    - position (string)
    - start_date (string, optional)
    - end_date (string, optional)
    - responsibilities (string, optional)

12. projects (list, optional): List of relevant projects with:
    - title (string)
    - description (string)
    - technologies_used (list of strings, optional)
    - link (string, optional)

13. technical_skills (list): List of technical skills (e.g., programming languages, frameworks, tools)

14. soft_skills (list): List of soft skills (e.g., communication, leadership, teamwork)

15. languages (list, optional): List of spoken/written languages with proficiency levels

16. publications (list, optional): List of academic or industry publications (title, publication, date)

17. awards (list, optional): List of awards or recognitions

18. interests (list, optional): List of personal interests or hobbies

19. references (list, optional): List of references, each with:
    - name (string)
    - position (string, optional)
    - contact_info (string, optional)

Return the extracted information in valid JSON format only. If any field is missing or not found, set its value to `null` or use empty lists where appropriate.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts resume data and returns structured JSON.",
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nResume Content:\n{resume_text}",
                },
            ],
            temperature=0.0,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"Failed to parse resume: {e}")

def generate_tailored_resume(user_profile: Dict[str, Any], job_description: str) -> str:
    """
    Generate a tailored, ATS-friendly resume for a new job description using the user's profile.
    """
    generator = CoverLetterGenerator()
    return generator.generate_resume(user_profile, job_description)

def generate_cover_letter(user_profile: Dict[str, Any], job_description: str, position: str = 'the position', company: str = 'your company') -> str:
    """
    Generate a personalized cover letter for a new job description using the user's profile.
    """
    generator = CoverLetterGenerator()
    return generator.generate_cover_letter(user_profile, job_description, position, company)

def save_documents(user_profile: Dict[str, Any], job_description: str, position: str = 'the position', company: str = 'your company', output_dir: str = 'output') -> None:
    """
    Generate and save tailored resume and cover letter as individual files for a given job description and user profile.
    """
    import os
    from datetime import datetime
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    resume_content = generate_tailored_resume(user_profile, job_description)
    cover_letter_content = generate_cover_letter(user_profile, job_description, position, company)

    resume_path = os.path.join(output_dir, f'tailored_resume_{timestamp}.txt')
    cover_letter_path = os.path.join(output_dir, f'cover_letter_{timestamp}.txt')

    with open(resume_path, 'w', encoding='utf-8') as f:
        f.write(resume_content)
    with open(cover_letter_path, 'w', encoding='utf-8') as f:
        f.write(cover_letter_content)
    print(f'Resume saved to: {resume_path}')
    print(f'Cover letter saved to: {cover_letter_path}')
