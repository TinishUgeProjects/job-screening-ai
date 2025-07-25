document.addEventListener("DOMContentLoaded", function () {
    const jobForm = document.getElementById("jobForm");
    const resumeForm = document.getElementById("resumeForm");
    const matchForm = document.getElementById("matchForm");
    const resultDiv = document.getElementById("matchScore"); // Ensure the correct ID
    const API_BASE_URL = "http://127.0.0.1:5000"; // Backend URL

    // 📝 Upload Job Description
    jobForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const jobTitle = document.getElementById("jobTitle").value.trim();
        const description = document.getElementById("description").value.trim();

        if (!jobTitle || !description) {
            alert("Please enter a job title and description.");
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/upload_job`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_title: jobTitle, description: description }),
            });

            const data = await response.json();
            alert(data.message);
        } catch (error) {
            console.error("Error uploading job:", error);
            alert("Failed to upload job description. Try again.");
        }
    });

    // 📄 Upload Resume
    resumeForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const fileInput = document.getElementById("resumeFile");

        if (!fileInput.files.length) {
            alert("Please select a PDF resume.");
            return;
        }

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        try {
            const response = await fetch(`${API_BASE_URL}/upload_resume`, {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            alert(data.message);
            sessionStorage.setItem("resumeText", data.extracted_text);
        } catch (error) {
            console.error("Error uploading resume:", error);
            alert("Failed to upload resume. Ensure your backend is running.");
        }
    });

    // 🎯 Match Resume with Job
    matchForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const jobId = document.getElementById("jobId").value.trim();
        const resumeText = sessionStorage.getItem("resumeText");

        if (!jobId) {
            alert("Please enter a Job ID.");
            return;
        }

        if (!resumeText) {
            alert("Please upload a resume first.");
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/match_resume`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_id: jobId, resume_text: resumeText }),
            });

            const data = await response.json();

            if (data.error) {
                alert(data.error);
            } else {
                resultDiv.innerHTML = `<p><strong>Match Score:</strong> ${data.match_score}%</p>`;
            }
        } catch (error) {
            console.error("Error matching resume:", error);
            alert("Failed to match resume. Try again.");
        }
    });
});
