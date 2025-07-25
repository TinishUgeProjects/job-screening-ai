from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import ollama
import logging
import os
import fitz  # PyMuPDF for PDF reading
import docx
import re
import json
from send_email import send_email

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logging.basicConfig(level=logging.INFO)

def connect_db():
    return sqlite3.connect("job_screening.db")

# Create tables if not exist
def init_db():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS job_descriptions (
                          id INTEGER PRIMARY KEY, content TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
                          id INTEGER PRIMARY KEY, resume TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS job_listings (
                          id INTEGER PRIMARY KEY, title TEXT, description TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS shortlisted_candidates (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          phone TEXT,
                          email TEXT,
                          reason TEXT,
                          match_score INTEGER
                          )''')
        conn.commit()

init_db()

# Homepage route
def get_job_listings_from_db():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, description FROM job_listings LIMIT 10")
        job_listings = [{"id": row[0], "title": row[1], "description": row[2]} for row in cursor.fetchall()]
    return job_listings

@app.route("/")
def home():
    job_listings = get_job_listings_from_db()
    return render_template("index.html", job_listings=job_listings)

app.secret_key = 'supersecret'  # required for using session

# Feed Less, But Cleaner Resume Input
def clean_resume_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove excessive whitespace
    text = re.sub(r'(Page \d+ of \d+)', '', text, flags=re.I)  # Remove page headers
    return text.strip()

# Upload Resume
@app.route("/upload_resume/<int:job_id>", methods=["POST"])
def upload_resume(job_id):
    if 'resume' not in request.files:
        return "No resume file uploaded.", 400

    file = request.files['resume']
    if file.filename == '':
        return "No selected file.", 400

    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()

    try:
        if file_ext == '.txt':
            resume_content = file.read().decode('utf-8', errors='ignore')
        elif file_ext == '.pdf':
            resume_content = extract_text_from_pdf(file)
        elif file_ext in ['.doc', '.docx']:
            resume_content = extract_text_from_docx(file)
        else:
            return "Unsupported file format", 400
    except Exception as e:
        return f"Error reading file: {str(e)}", 500

    resume_content = clean_resume_text(resume_content)
    # resume_content = "Lorem Ipsum"


    # Fetch JD content from DB
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM job_listings WHERE id = ?", (job_id,))
        jd_row = cursor.fetchone()
        if not jd_row:
            return "Job not found.", 404
        jd_content = jd_row[0]

    # Summarize JD
    jd_response = ollama.chat(model="phi",
                              messages=[{"role": "system", "content": "Summarize this job description: " + jd_content}])
    jd_summary = jd_response.get("message", {}).get("content", "")

    # Match resume with job summary
    match_prompt = (
        "You are an AI Resume Evaluator. Given a job summary and a candidate resume, extract relevant data from the resume "
        "and evaluate how well the candidate matches the job summary.\n\n"
        "Respond ONLY with a valid JSON object in this structure:\n"
        "{\n"
        "  \"match_score\": integer between 0 and 100,\n"
        "  \"skills\": list of strings,\n"
        "  \"experience\": string,\n"
        "  \"education\": string,\n"
        "  \"summary\": string,\n"
        "  \"objective\": string\n"
        "}\n\n"
        "Do not include explanations, markdown, or any text outside of the JSON object."
    )

    response = ollama.chat(model="phi", messages=[
        {"role": "system", "content": match_prompt},
        {"role": "user", "content": f"Resume: {resume_content}\n\nJob Summary: {jd_summary}\n\nReturn only the JSON."}
    ])

    response_text = response.get("message", {}).get("content", "")
    logging.info(f"\U0001F50D RAW AI RESPONSE:\n{response_text}")

    # Extract JSON content
    try:
        # Try to extract JSON directly from response
        json_text = re.search(r"\{.*\}", response_text, re.DOTALL).group(0)
        result = json.loads(json_text)
    except Exception as e:
        logging.error(f"❌ Failed to parse JSON: {e}\nRaw response:\n{response_text}")
        result = {
            "match_score": "Error parsing AI response",
            "skills": "Error parsing AI response",
            "experience": "Error parsing AI response",
            "education": "Error parsing AI response",
            "summary": "Error parsing AI response",
            "objective": "Error parsing AI response",
        }

    try:
        result = json.loads(json_text)
    except json.JSONDecodeError:
        logging.error("❌ Failed to parse JSON! Returning error response.")
        result = {
            "match_score": "Error parsing AI response",
            "skills": "Error parsing AI response",
            "experience": "Error parsing AI response",
            "education": "Error parsing AI response",
            "summary": "Error parsing AI response",
            "objective": "Error parsing AI response",
        }

    session['match_result'] = result
    return redirect(url_for("match_result"))

@app.route("/match_result")
def match_result():
    result = session.get("match_result", {})
    return render_template("match_result.html", result=result)

@app.route("/store_job_listings", methods=["POST"])
def store_job_listings():
    data = request.json
    job_listings = data.get("job_listings", [])
    if not job_listings:
        return jsonify({"error": "Job listings are required"}), 400

    with connect_db() as conn:
        cursor = conn.cursor()
        for job in job_listings:
            cursor.execute("INSERT INTO job_listings (title, description) VALUES (?, ?)",
                           (job["title"], job["description"]))
        conn.commit()

    return jsonify({"message": "Job listings stored successfully"})

@app.route("/get_job_listings", methods=["GET"])
def get_job_listings():
    job_listings = get_job_listings_from_db()
    return jsonify({"job_listings": job_listings})

@app.route("/summarize_jd", methods=["POST"])
def summarize_jd():
    data = request.json
    jd_content = data.get("jd_content", "")
    if not jd_content:
        return jsonify({"error": "Job description content is required"}), 400

    response = ollama.chat(model="phi",
                           messages=[{"role": "system", "content": "Summarize this job description: " + jd_content}])
    summary = response.get("message", {}).get("content", "")
    return jsonify({"summary": summary})

@app.route("/match_candidates", methods=["POST"])
def match_candidates():
    data = request.json
    jd_summary = data.get("jd_summary", "")
    resume = data.get("resume", "")
    if not jd_summary or not resume:
        return jsonify({"error": "Job description summary and resume are required"}), 400

    response = ollama.chat(model="phi", messages=[
        {"role": "system", "content": f"Match this resume: {resume} with job summary: {jd_summary} and return a score."}])
    match_score = response.get("message", {}).get("content", "0")

    return jsonify({"match_score": match_score})

@app.route('/shortlisted')
def shortlisted_candidates():
    conn = sqlite3.connect('job_screening.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, job_title FROM shortlisted_candidates")
    candidates = cursor.fetchall()
    conn.close()

    sent_emails = session.get('sent_emails', [])
    return render_template('shortlisted.html', candidates=candidates, sent_emails=sent_emails)


@app.route("/schedule_interview", methods=["POST"])
def schedule_interview():
    data = request.json
    email = data.get("candidate_email", "")
    name = data.get("candidate_name", "")

    if not email:
        return jsonify({"error": "Candidate email is required"}), 400

    subject = f"Interview Invitation from YourCompany"
    body = f"""
Hi {name},

Congratulations! 🎉

You've been shortlisted for the next round for the job role you applied to. Please be available for an interview this week.

We will share further details shortly.

Best regards,
HR Team
YourCompany
    """

    status = send_email(to=email, subject=subject, body=body)

    if status:
        return jsonify({"message": f"Interview invitation sent to {email}"})
    else:
        return jsonify({"error": "Failed to send email"}), 500


def extract_text_from_pdf(file):
    file_bytes = file.read()
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


@app.route("/submit_details", methods=["POST"])
def submit_details():
    phone = request.form.get("phone")
    email = request.form.get("email")
    reason = request.form.get("reason")
    match_score = request.form.get("match_score")

    if not (phone and email and reason and match_score):
        return "All fields are required.", 400

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO shortlisted_candidates (phone, email, reason, match_score)
            VALUES (?, ?, ?, ?)
        ''', (phone, email, reason, int(match_score)))
        conn.commit()

    return render_template("thank_you.html")

@app.route('/send_email', methods=['POST'])
def handle_send_email():
    email = request.form['email']
    name = request.form['name']
    job_title = request.form['job_title']
    test_link = "https://example.com/interview"

    success = send_email(email, name, job_title, test_link)

    # Track sent emails
    if success:
        if 'sent_emails' not in session:
            session['sent_emails'] = []
        if email not in session['sent_emails']:
            session['sent_emails'].append(email)

    return redirect(url_for('shortlisted_candidates'))

if __name__ == "__main__":
    app.run(debug=True)
