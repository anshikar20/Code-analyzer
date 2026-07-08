# Omni Analyzer (CodePulse AI)

![Omni Analyzer](https://img.shields.io/badge/Status-Active-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20VS%20Code-blue)
![Language](https://img.shields.io/badge/Languages-Python%20%7C%20Java%20%7C%20C++-yellow)

**Omni Analyzer** is an enterprise-grade, AI-augmented source code analysis platform designed to fundamentally transform the way modern software development teams write, review, and maintain code. 

By replacing subjective, time-consuming manual code reviews with deterministic, rule-based analysis supplemented by Google's Gemini AI, Omni Analyzer reduces the Mean Time to Review (MTTR) while democratizing security scanning and enforcing code quality standards.

🌐 **[Visit the Live Dashboard](https://code-analyzer-eight.vercel.app/)**

---

## 🚀 Key Features

* **Real-time IDE Integration:** A local VS Code extension that provides sub-second diagnostic feedback directly in your editor via a Language Server Protocol (LSP).
* **AI-Powered Code Review:** Powered by Google's Gemini 2.5 models to offer intelligent refactoring suggestions, catch logical bugs, and generate missing docstrings.
* **Comprehensive Static Analysis:** Seamlessly integrates standard tools (Pylint, Flake8, Bandit, MyPy) with custom semantic rule sets.
* **Multi-Language Support:** First-class analysis for **Python**, **Java**, and **C++**.
* **Centralized Dashboard:** A rich React/Vite single-page application for historical analytics, security tracking, and code review trends.

---

## 🏗️ System Architecture

The platform operates across three distinct delivery channels:

1. **Frontend Dashboard (React/Vite):** Hosted on Vercel's edge network for lightning-fast delivery. Includes Monaco Editor integration for web-based code scanning and visualization.
2. **Backend API (FastAPI):** Hosted on Render. It handles the core parsing engine, dynamic rule execution, and AI orchestration.
3. **VS Code Extension:** A locally-installable `.vsix` package that communicates with the local/cloud ecosystem to prevent technical debt directly at the source.

---

## 📦 How to Install the VS Code Extension

You do not need to clone this repository to use the extension! Just grab the compiled `.vsix` file from the **Releases** page.

1. Go to the [Releases](../../releases) section of this repository.
2. Download the latest `omni-analyzer-X.X.X.vsix` file.
3. Open **VS Code**.
4. Open the Command Palette by pressing `Ctrl + Shift + P` (Windows/Linux) or `Cmd + Shift + P` (Mac).
5. Type and select **`Extensions: Install from VSIX...`**.
6. Choose the downloaded `.vsix` file and reload VS Code.

---

## 💻 Local Development Setup

If you wish to contribute or run the full platform locally:

### Prerequisites
* Python 3.10+
* Node.js & npm (for the frontend dashboard)
* A Google Gemini API Key

### 1. Backend (FastAPI)
```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt

# Create a .env file and add your GEMINI_API_KEY
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Run the server
uvicorn main:app --reload
```

### 2. Frontend (React/Vite)
```bash
# Navigate to the dashboard directory
cd dashboard

# Install dependencies
npm install

# Start the development server
npm run dev
```

---

## 📄 Documentation

For an in-depth look at the development, architecture, ROI analysis, and implementation details of Omni Analyzer, please refer to the detailed project reports included in this repository:
* `Project_Report.md` / `Project_Report.pdf`
* `Evaluation_Report.md` / `Evaluation_Report.pdf`

---

**Developed by:** Anshika Rai  
**Mentorship:** Tech Mahindra (May - July 2026)
