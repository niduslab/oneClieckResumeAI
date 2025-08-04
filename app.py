from flask import Flask, request, jsonify
from cvparser import parse_resume_with_openai, extract_text_from_pdf, client
from generate_documents import generate_tailored_resume_json
from coverlatter import CoverLetterGenerator

app = Flask(__name__)

def api_response(success: bool, data=None, message="", status=200):
    return jsonify({
        "success": success,
        "message": message,
        "data": data
    }), status

@app.route("/generate_resume", methods=["POST"])
def generate_resume():
    resume_file = request.files.get("resume")
    job_description = request.form.get("job_description")
    if not resume_file or not job_description:
        return api_response(False, None, "Missing resume file or job description", 400)

    try:
        resume_text = extract_text_from_pdf(resume_file.read())
        parsed_profile = parse_resume_with_openai(resume_text)
        tailored_resume_json = generate_tailored_resume_json(parsed_profile, job_description)

        # Optionally extract position/company from JD
        position = "the position"
        company = "your company"

        generator = CoverLetterGenerator()
        cover_letter_json = generator.generate_cover_letter(
            parsed_profile,
            job_description,
            position=position,
            company=company
        )

        return api_response(
            True,
            {
                "tailored_resume": tailored_resume_json,
                "cover_letter": cover_letter_json
            },
            "Resume and cover letter generated successfully."
        )
    except Exception as e:
        return api_response(False, None, f"Internal server error: {str(e)}", 500)

if __name__ == "__main__":
    app.run(debug=True)