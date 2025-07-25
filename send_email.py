from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load .env file
load_dotenv()
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('show_shortlisted'))

# Show all shortlisted candidates
@app.route('/shortlisted')
def show_shortlisted():
    conn = sqlite3.connect("job_screening.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, email, match_score FROM shortlisted_candidates")
    rows = cursor.fetchall()
    conn.close()

    candidates = [
        {"name": row[0], "email": row[1], "job_title": row[2]}
        for row in rows
    ]

    return render_template("shortlisted.html", candidates=candidates)

# Send email on POST request
@app.route('/send_email', methods=['POST'])
def trigger_email():
    to_email = request.form['email']
    candidate_name = request.form['name']
    job_title = request.form['job_title']
    test_link = request.form.get('test_link')

    if send_email(to_email, candidate_name, job_title, test_link):
        return f"✅ Email sent to {to_email}"
    else:
        return f"❌ Failed to send email to {to_email}"

# Function to send email
def send_email(to_email, candidate_name, job_title, test_link=None):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = f"Interview Opportunity for {job_title}"

        body = f"""
        Dear {candidate_name},<br><br>
        🎉 <strong>Congratulations!</strong><br><br>
        You have been shortlisted for the role of <strong>{job_title}</strong> based on your resume and skill alignment.<br><br>
        Please confirm your interest by replying to this email.
        {f"<br><br>Additionally, please complete the test using this link: <a href='{test_link}'>Click Here</a>" if test_link else ""}
        <br><br>Best regards,<br>
        Talent Acquisition Team
        """
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

# Run app
if __name__ == "__main__":
    app.run(debug=True)
