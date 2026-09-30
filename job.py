from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# Temporary database
jobs = []


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Job Application Tracker</title>

    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #08080d;
            color: white;
        }

        header {
            background: linear-gradient(135deg, #4c1d95, #9333ea);
            padding: 30px 20px;
            text-align: center;
        }

        header h1 {
            margin: 0;
            font-size: 32px;
        }

        header p {
            color: #ddd;
        }

        .container {
            max-width: 1100px;
            margin: auto;
            padding: 25px;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }

        .stat {
            background: #15151f;
            border: 1px solid #333;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }

        .stat h2 {
            margin: 0;
            font-size: 32px;
            color: #c084fc;
        }

        .card {
            background: #15151f;
            border: 1px solid #333;
            border-radius: 18px;
            padding: 25px;
            margin-bottom: 25px;
        }

        .card h2 {
            margin-top: 0;
        }

        input,
        textarea,
        select {
            width: 100%;
            padding: 14px;
            margin-top: 8px;
            margin-bottom: 15px;
            border-radius: 10px;
            border: 1px solid #444;
            background: #0d0d14;
            color: white;
            font-size: 15px;
        }

        textarea {
            min-height: 120px;
            resize: vertical;
        }

        button {
            padding: 13px 20px;
            border: none;
            border-radius: 10px;
            background: #7c3aed;
            color: white;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            background: #9333ea;
        }

        .job {
            background: #0d0d14;
            border-left: 5px solid #8b5cf6;
            border-radius: 12px;
            padding: 18px;
            margin-top: 15px;
        }

        .job h3 {
            margin-top: 0;
            color: #c084fc;
        }

        .status {
            display: inline-block;
            padding: 7px 12px;
            border-radius: 20px;
            background: #2e1065;
            color: #d8b4fe;
        }

        .delete {
            background: #dc2626;
            margin-left: 8px;
        }

        .delete:hover {
            background: #ef4444;
        }

        #aiResult {
            margin-top: 20px;
            background: #0d0d14;
            padding: 20px;
            border-radius: 12px;
            white-space: pre-wrap;
            line-height: 1.6;
        }

        .empty {
            text-align: center;
            color: #999;
            padding: 30px;
        }

        @media(max-width: 700px) {
            .stats {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>

<body>

<header>
    <h1>🤖 AI Job Application Tracker</h1>
    <p>Track applications • Manage deadlines • AI Career Assistant</p>
</header>


<div class="container">

    <!-- STATISTICS -->

    <div class="stats">

        <div class="stat">
            <h2 id="total">0</h2>
            <p>Total Applications</p>
        </div>

        <div class="stat">
            <h2 id="applied">0</h2>
            <p>Applied</p>
        </div>

        <div class="stat">
            <h2 id="interview">0</h2>
            <p>Interviews</p>
        </div>

        <div class="stat">
            <h2 id="offer">0</h2>
            <p>Offers</p>
        </div>

    </div>


    <!-- ADD APPLICATION -->

    <div class="card">

        <h2>➕ Add Job Application</h2>

        <label>Company Name</label>

        <input
            id="company"
            placeholder="Example: Google"
        >


        <label>Job Role</label>

        <input
            id="role"
            placeholder="Example: AI Engineer"
        >


        <label>Application Deadline</label>

        <input
            id="deadline"
            type="date"
        >


        <label>Status</label>

        <select id="status">

            <option value="Applied">
                Applied
            </option>

            <option value="Interview">
                Interview
            </option>

            <option value="Rejected">
                Rejected
            </option>

            <option value="Offer">
                Offer
            </option>

        </select>


        <label>Job Description</label>

        <textarea
            id="description"
            placeholder="Paste the job description here..."
        ></textarea>


        <button onclick="addJob()">
            Save Application
        </button>

    </div>


    <!-- AI ASSISTANT -->

    <div class="card">

        <h2>✨ AI Career Assistant</h2>

        <p>
            Ask the AI assistant for career-related help.
        </p>

        <textarea
            id="aiPrompt"
            placeholder="Example: Write a cover letter for an AI Engineer position..."
        ></textarea>

        <button onclick="generateAI()">
            Generate AI Response
        </button>

        <div id="aiResult">
            AI response will appear here.
        </div>

    </div>


    <!-- APPLICATION LIST -->

    <div class="card">

        <h2>📋 My Applications</h2>

        <div id="jobList">
            Loading...
        </div>

    </div>

</div>


<script>


// ------------------------------------
// ADD JOB
// ------------------------------------

async function addJob() {

    const company =
        document.getElementById("company").value;

    const role =
        document.getElementById("role").value;

    const deadline =
        document.getElementById("deadline").value;

    const status =
        document.getElementById("status").value;

    const description =
        document.getElementById("description").value;


    if (!company || !role) {

        alert("Please enter company name and job role.");

        return;
    }


    const response = await fetch(
        "/api/jobs",
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                company,
                role,
                deadline,
                status,
                description
            })
        }
    );


    if (response.ok) {

        document.getElementById("company").value = "";

        document.getElementById("role").value = "";

        document.getElementById("deadline").value = "";

        document.getElementById("description").value = "";

        loadJobs();

        alert("Application saved successfully!");

    }

}


// ------------------------------------
// LOAD JOBS
// ------------------------------------

async function loadJobs() {

    const response =
        await fetch("/api/jobs");

    const data =
        await response.json();


    document.getElementById("total").innerText =
        data.length;


    document.getElementById("applied").innerText =
        data.filter(
            job => job.status === "Applied"
        ).length;


    document.getElementById("interview").innerText =
        data.filter(
            job => job.status === "Interview"
        ).length;


    document.getElementById("offer").innerText =
        data.filter(
            job => job.status === "Offer"
        ).length;


    const list =
        document.getElementById("jobList");


    if (data.length === 0) {

        list.innerHTML =
            '<div class="empty">No applications added yet.</div>';

        return;
    }


    let html = "";


    data.forEach(job => {

        html += `

        <div class="job">

            <h3>
                ${job.company}
            </h3>

            <p>
                <b>Role:</b>
                ${job.role}
            </p>

            <p>
                <b>Deadline:</b>
                ${job.deadline || "Not specified"}
            </p>

            <p>
                <span class="status">
                    ${job.status}
                </span>
            </p>

            <p>
                ${job.description || ""}
            </p>

            <button
                class="delete"
                onclick="deleteJob('${job.id}')"
            >
                Delete
            </button>

        </div>

        `;

    });


    list.innerHTML = html;

}


// ------------------------------------
// DELETE JOB
// ------------------------------------

async function deleteJob(id) {

    await fetch(
        "/api/jobs/" + id,
        {
            method: "DELETE"
        }
    );

    loadJobs();

}


// ------------------------------------
// AI ASSISTANT
// ------------------------------------

async function generateAI() {

    const prompt =
        document.getElementById("aiPrompt").value;


    if (!prompt) {

        alert("Enter your question.");

        return;
    }


    const result =
        document.getElementById("aiResult");


    result.innerText =
        "🤖 AI is generating a response...";


    const response =
        await fetch(
            "/api/ai",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    prompt
                })
            }
        );


    const data =
        await response.json();


    result.innerText =
        data.response;

}


// Load applications when page opens

loadJobs();

</script>

</body>
</html>
"""


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():

    return render_template_string(HTML)


# =====================================================
# ADD JOB
# =====================================================

@app.route("/api/jobs", methods=["POST"])
def add_job():

    data = request.json

    job = {

        "id": len(jobs) + 1,

        "company":
            data.get("company", ""),

        "role":
            data.get("role", ""),

        "deadline":
            data.get("deadline", ""),

        "status":
            data.get("status", "Applied"),

        "description":
            data.get("description", ""),

        "created":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    }


    jobs.append(job)


    return jsonify({
        "message":
            "Application added successfully"
    })


# =====================================================
# GET JOBS
# =====================================================

@app.route("/api/jobs", methods=["GET"])
def get_jobs():

    return jsonify(jobs)


# =====================================================
# DELETE JOB
# =====================================================

@app.route(
    "/api/jobs/<int:job_id>",
    methods=["DELETE"]
)
def delete_job(job_id):

    global jobs

    jobs = [
        job
        for job in jobs
        if job["id"] != job_id
    ]

    return jsonify({
        "message":
            "Application deleted"
    })


# =====================================================
# AI SIMULATION
# =====================================================

@app.route("/api/ai", methods=["POST"])
def ai():

    data = request.json

    prompt = data.get("prompt", "")


    # Simple local AI-style response
    # Replace this function with Gemini API
    # when deploying on GCP.

    response = f"""
AI Career Assistant

Your request:
{prompt}

Suggested approach:

1. Understand the job requirements carefully.
2. Identify the important technical skills.
3. Match your projects and experience with those skills.
4. Highlight relevant achievements in your resume.
5. Customize your cover letter for the company.
6. Prepare interview questions based on the job description.

For the production GCP version, this section
will use Gemini to generate personalized
career recommendations and application drafts.
"""


    return jsonify({
        "response": response
    })


# =====================================================
# RUN SERVER
# =====================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )