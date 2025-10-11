import google.generativeai as genai
import mss
import os
from PIL import Image
import sys
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB4yPcHciQ1qmiUBPnihDh3UQFMqNpTX70")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found. Please set it as an environment variable.")
    sys.exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    sys.exit(1)

# --- FastAPI App Initialization ---
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class DescriptionRequest(BaseModel):
    question: str

# --- Helper Functions ---
def take_screenshot():
    """Takes a screenshot and saves it as screenshot.png."""
    with mss.mss() as sct:
        filename = sct.shot(output="screenshot.png")
        print(f"Screenshot saved as {filename}")
        return filename

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "ScreenKnow Backend is running"}

async def stream_gemini_response(question: str, image_path: str):
    """Generator function to stream responses from Gemini."""
    try:
        print("Analyzing screenshot for streaming...")
        img = Image.open(image_path)
        response_stream = model.generate_content([question, img], stream=True)
        
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
                await asyncio.sleep(0.05) # Small delay to simulate typing and prevent overwhelming the client

    except Exception as e:
        print(f"An error occurred during streaming: {e}")
        yield f"Error: {str(e)}"
    finally:
        # Clean up the screenshot file
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"Removed screenshot file: {image_path}")

@app.post("/api/describe")
async def describe_screen(request: DescriptionRequest):
    """
    Takes a screenshot and streams the Gemini description based on the provided question.
    """
    print(f"Received request with question: {request.question}")
    screenshot_path = "screenshot.png"
    
    try:
        take_screenshot()
        if not os.path.exists(screenshot_path):
            raise HTTPException(status_code=500, detail="Failed to take screenshot.")
            
        return StreamingResponse(stream_gemini_response(request.question, screenshot_path), media_type="text/plain")

    except Exception as e:
        # This will catch errors before the stream starts, like failing to take the screenshot
        print(f"An error occurred before streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))