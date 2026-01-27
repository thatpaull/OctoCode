

---

# 🐙 OctoCode – AI-Based Learning Platform

OctoCode is an AI-powered learning platform designed to provide personalized tutoring, adaptive exercises, and intelligent learning recommendations. This repository contains the **local development setup** for running OctoCode on your machine.

---

## 🚀 Features

* 🤖 **AI Tutor** (Q&A support)
* 🧠 **AI-generated exercises**
* 📈 **Adaptive difficulty**
* 🎯 **Personalized topic recommendations**
* 🧑‍🏫 **Teacher & Admin dashboards**
* 📊 **Student progress tracking**

---

## 🏗️ Tech Stack

### Backend

* **Python 3.10+**
* **Flask**

### AI Services

* **Groq AI** (LLM-powered tutoring & content generation)

### Database

* **SQLite** (default)
* Easily replaceable with **PostgreSQL** or **MySQL**

### Frontend

* HTML, CSS, JavaScript
* Served statically or via Flask

### Project Management

* **Azure DevOps** (Scrum, Boards, Sprints)

---

## 🧰 Prerequisites

Make sure the following tools are installed:

* Python **3.10+**
* `pip`
* `git`
* (Optional) `virtualenv`

Check installations:

```bash
python --version
pip --version
git --version
```

---

## 📁 Project Structure

```
OctoCode/
├── .venv/                  # Python virtual environment
├── instance/               # Flask instance configs
├── static/                 # Frontend assets
│   ├── img/
│   ├── uploads/
│   ├── *.html
│   ├── *.css
│   └── *.js
├── .env                    # Environment variables
├── .gitignore
├── app.py                  # Flask backend entry point
└── database.db             # SQLite database
```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/thatpaull/OctoCode.git
cd OctoCode
```

### 2️⃣ Create & Activate Virtual Environment

```bash
python -m venv .venv
```

**Activate it:**

* **Windows**

```bash
.venv\Scripts\activate
```

* **macOS / Linux**

```bash
source .venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Application

Start the Flask backend:

```bash
python app.py
```

---

## 🌐 Access the App

Open your browser and visit:

```
http://127.0.0.1:5001
```

---

## 🧠 AI Configuration

OctoCode uses **Groq AI** for all AI-based features.

### Requirements

* Valid `GROQ_API_KEY`
* Active internet connection

### Environment Variables (`.env`)

```env
GROQ_API_KEY=your_api_key_here
```

---

## 🛠️ Common Issues & Fixes

### ❌ AI Not Responding

* Check that `GROQ_API_KEY` is set correctly
* Ensure you have an active internet connection

### ❌ Port Already in Use

Change the port in `app.py`:

```python
app.run(port=5002)
```

---

## 📌 Notes

* This setup is intended for **local development**
* SQLite is used by default for simplicity
* Frontend files are located in `/static`

---

## 📄 License

This project is for educational and development purposes.
Add a license file if you plan to open-source it.

---

