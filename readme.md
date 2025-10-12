# ScreenKnow

## Overview

ScreenKnow is a full-stack application that allows you to ask questions about the content on your screen. It uses a FastAPI backend to capture a screenshot and query the Google Gemini API for an analysis, and a Next.js frontend to provide a user interface.

Whatever you see screenknow captures and allows for true context when learning or just browsing.

<img width="1512" height="982" alt="image" src="https://github.com/user-attachments/assets/63decee1-ff47-489c-a9d4-748c9792ac3f" />

Whether you need to ask questions of what things are going to look like or realtime explanations of what you are already seeing, Youtube videos or Design templates.

<img width="1512" height="982" alt="image" src="https://github.com/user-attachments/assets/aa38a5f9-4fe2-4c7a-802b-8ae636509439" />

You can find a short yet simple demo of these two features of Screennow in this youtube video:

https://youtu.be/QeckwpBIptw

## Prerequisites

Before you begin, ensure you have the following installed:
- [uv](https://github.com/astral-sh/uv): An extremely fast Python package installer and resolver.
- [Bun](https://bun.sh/): An incredibly fast JavaScript runtime, bundler, test runner, and package manager.

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd screenknow
```

### 2. Configure API Key

The backend requires a Google Gemini API key. The application is configured to read the key from an environment variable named `GEMINI_API_KEY`.

**Export the environment variable in your terminal:**
```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```
*Note: You will need to do this in each new terminal session where you run the backend, or add it to your shell's profile file (e.g., `.zshrc`, `.bash_profile`).*

### 3. Backend Setup

Navigate to the backend directory and install the required Python packages using `uv`.

```bash
cd backend
uv pip install -r requirements.txt
```

### 4. Frontend Setup

Navigate to the frontend directory and install the required packages using `bun`.

```bash
cd ../frontend
bun install
```

## Running the Application

You will need to run the backend and frontend servers in two separate terminals.

### Terminal 1: Run the Backend

```bash
# Make sure you are in the `backend` directory
cd backend

# Run the FastAPI server using uvicorn
uv run uvicorn main:app --reload
```
The backend will be running at `http://localhost:8000`.

### Terminal 2: Run the Frontend

```bash
# Make sure you are in the `frontend` directory
cd frontend

# Run the Next.js development server with Bun
bun run dev
```
The frontend will be running at `http://localhost:3000`.

## How to Use

1. Open your web browser and navigate to `http://localhost:3000`.
2. Type a question into the text box.
3. Click the "Ask" button and wait for the response.

### macOS Permissions Note ! Important
The first time the backend takes a screenshot, your Mac may prompt you to grant accessibility permissions to your terminal or IDE. You must grant these permissions for the screenshot functionality to work.

## Live application

The screennow app is live on liveaction.vercel.app!
powered by liveaction.onrender.com
! However since this does not ask for screen permission natively, the screen application feature is incorrect and will hallucinate, it does however get you familiar with the interface.
