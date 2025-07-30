
# 🧠 AI-Powered Job Matching CLI - Document Similarity & Ranking System


This CLI-based prototype implements a **Multi-Agent Recruitment System** that automates the comparison and ranking of consultant profiles against job descriptions (JDs). It is designed to reduce manual screening time and improve the accuracy of candidate-job matching by leveraging a custom-built **Agent-to-Agent (A2A) Protocol** and **Google Gemini AI**.

### ✨ Key Features

* 🧠 **AI-Powered Document Similarity** using Google Gemini
* ⚖️ **Weighted Candidate Ranking** (skills, experience, context)
* 📧 **Automated Email Notifications** to AR requestors
* 🔁 **Custom A2A Protocol** for seamless agent communication
* 🔒 **Explainable AI**: Score breakdowns and justifications

---

## 🧪 System Architecture

This CLI version simulates the real-world architecture using:

* **Comparison Agent** → Evaluates similarity between JD and consultant profiles.
* **Ranking Agent** → Scores and ranks profiles based on weighted criteria.
* **Communication Agent** → Sends emails to AR requestors with top 3 matches.

All agents interact through a **custom A2A message protocol** built from scratch, without any external brokers.

---

## ⚙️ Technologies Used

* **Python 3.12**
* **SQLite** (for CLI prototype)
* **Gemini AI API** (document analysis)
* **smtplib / email** for email delivery
* **NLTK** / **PyPDF2** / **python-docx** for text processing

---


## 🚀 Getting Started

### 📦 Prerequisites

* Python 3.8+
* Gemini API Key (set in `.env` or `config.py`)
* SMTP Credentials for sending emails


### ▶️ Run the CLI

```bash
python main.py
```

You’ll be guided through:

1. **Creating/Uploading a Job Description (JD)**
2. **Running Document Comparison**
3. **Ranking Consultant Profiles**
4. **Sending Results via Email**
5. **Viewing Logs and Explanations**

---

## 🧠 How It Works

| Step | Agent         | Description                                    |
| ---- | ------------- | ---------------------------------------------- |
| 1    | Comparison    | Compares JD to all profiles using Gemini AI    |
| 2    | Ranking       | Applies weighted scoring to similarity results |
| 3    | Communication | Sends top 3 matches to AR requestor via email  |

The entire process is orchestrated through a **custom A2A message flow** with heartbeat monitoring, retries, and message correlation.

---

## 📊 Scoring Criteria

| Factor        | Weight |
| ------------- | ------ |
| Skills Match  | 40%    |
| Experience    | 30%    |
| Context Match | 20%    |
| Other Factors | 10%    |

---

## 🧪 Sample Data & Demo

* Sample JD and consultant profiles are preloaded in the `/data/` folder.
* You can also upload `.pdf` or `.docx` resumes for processing.

---

## 🔒 Security (Prototype-Level)

* Email sending is simulated in dev mode.
* No external message brokers or queues used.
* Logs are maintained for message flow and agent health.

---
