import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from cvparser import parse_resume_with_openai, extract_text_from_pdf, client
from coverlatter import CoverLetterGenerator
from collections import OrderedDict

def save_as_json(data: Dict[str, Any], filepath: Path) -> None:
    """Save data as a pretty-printed JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_job_details(job_description: str) -> dict:
    # TODO: Implement actual extraction logic
    return {}  # Always return a dict, not None

def generate_tailored_resume_json(user_profile: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    schema = """
{
  "full_name": string,
  "email": string,
  "phone": string,
  "address": string,
  "linkedin": string,
  "github": string,
  "portfolio": string,
  "summary": string,
  "education": list,
  "certifications": list,
  "employment": list,
  "projects": list,
  "technical_skills": list,
  "soft_skills": list,
  "languages": list,
  "publications": list,
  "awards": list,
  "interests": list,
  "references": list
}
    """
    prompt = f"""
You are an AI resume assistant. Your job is to generate a tailored resume in JSON format for a job application.

Instructions:
- Carefully read the candidate profile and job description below.
- In the technical_skills and soft_skills sections, **merge the candidate's existing skills with ALL relevant skills found in the job description**, especially from sections titled 'Required Skills & Qualifications', 'Preferred Qualifications (Bonus)', 'Key Responsibilities', and 'Technologies / Tools Used','Requirements', 'Responsibilities & Context', 'Key AI Technologies and Tools','Additional Requirements'.
- **Explicitly list EVERY skill, technology, or tool mentioned in those sections, even if the candidate did not list them.**
- Do not remove existing relevant skills from the candidate profile.
- Update other sections (summary, employment, etc.) to better match the job description if possible.
- Output the resume in the following JSON schema:

{schema} 

Candidate Profile:
{json.dumps(user_profile, ensure_ascii=False, indent=2)}

Job Description:
{job_description}

If any field is missing, set its value to null or an empty list.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates tailored resumes in JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

def order_resume_fields(resume_json):
    field_order = [
        "full_name", "email", "phone", "address", "linkedin", "github", "portfolio", "summary",
        "education", "certifications", "employment", "projects", "technical_skills", "soft_skills",
        "languages", "publications", "awards", "interests", "references"
    ]
    return OrderedDict((k, resume_json.get(k)) for k in field_order if k in resume_json)

def main():
    try:
        print("=== Resume Parser & Document Generator ===\n")
        resume_path = input("Enter path to your resume PDF: ").strip('"').strip()
        if not Path(resume_path).is_file():
            print(f"Error: File not found at '{resume_path}'")
            return

        print("\n=== Job Description ===")
        print("Paste the job description (press Enter, then Ctrl+Z and Enter when done):")
        job_description_lines = []
        try:
            while True:
                line = input()
                job_description_lines.append(line)
        except EOFError:
            pass
        job_description = '\n'.join(job_description_lines).strip()
        if not job_description:
            print("Error: Job description cannot be empty")
            return

        print("\nExtracting text from resume...")
        with open(resume_path, 'rb') as f:
            resume_text = extract_text_from_pdf(f.read())
        if not resume_text:
            print("Error: Could not extract text from the PDF")
            return

        print("Parsing resume with AI...")
        parsed_profile = parse_resume_with_openai(resume_text)

        print("\nGenerating tailored resume JSON...")
        tailored_resume_json = generate_tailored_resume_json(parsed_profile, job_description)
        tailored_resume_json = order_resume_fields(tailored_resume_json)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output") / f"documents_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        profile_path = output_dir / "parsed_profile.json"
        save_as_json(parsed_profile, profile_path)

        resume_json_path = output_dir / "tailored_resume.json"
        ordered_tailored_resume_json = order_resume_fields(tailored_resume_json)
        save_as_json(ordered_tailored_resume_json, resume_json_path)

        job_details = extract_job_details(job_description)
        position = job_details.get('position', '').strip()
        if not position or len(position) < 2:
            first_line = job_description.split('\n')[0].strip()
            position = first_line if len(first_line) > 10 else 'the position'
        company = job_details.get('company', 'your company').strip()

        generator = CoverLetterGenerator()
        cover_letter_json = generator.generate_cover_letter(
            parsed_profile,
            job_description,
            position=position,
            company=company
        )

        cover_letter_path = output_dir / "cover_letter.json"
        save_as_json(cover_letter_json, cover_letter_path)

        job_desc_path = output_dir / "job_description.json"
        job_desc_data = {
            "job_description": job_description,
            "parsed_at": datetime.now().isoformat()
        }
        save_as_json(job_desc_data, job_desc_path)

        print(f"\n=== DOCUMENTS GENERATED SUCCESSFULLY ===")
        print(f"Output directory: {output_dir}")
        print(f"- Parsed Profile: {profile_path}")
        print(f"- Tailored Resume JSON: {resume_json_path}")
        print(f"- Cover Letter: {cover_letter_path}")
        print(f"- Job Description: {job_desc_path}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
