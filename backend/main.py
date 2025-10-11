import google.generativeai as genai
import mss
import os
from PIL import Image
import sys
import asyncio
import io
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB4yPcHciQ1qmiUBPnihDh3UQFMqNpTX70")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found. Please set it as an environment variable.")
    sys.exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)
    # This model will be used for the multi-modal (audio, image, text) request.
    model = genai.GenerativeModel('gemini-2.5-flash') # Using user-specified model
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    sys.exit(1)

# --- FastAPI App Initialization ---
app = FastAPI()

origins = ["http://localhost:3000", "http://localhost"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---
def take_screenshot():
    """Takes a screenshot and saves it as screenshot.png."""
    with mss.mss() as sct:
        filename = sct.shot(output="screenshot.png")
        print(f"Screenshot saved as {filename}")
        return filename

# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"status": "ScreenKnow Backend is running"}

# --- WebSocket Endpoint for Audio & Vision Streaming ---
@app.websocket("/api/audio-stream")
async def audio_stream(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established.")
    audio_buffer = io.BytesIO()
    screenshot_path = "screenshot.png"
    
    try:
        while True:
            data = await websocket.receive()
            if 'bytes' in data:
                audio_buffer.write(data['bytes'])
            elif 'text' in data and data['text'] == "END_OF_STREAM":
                print("End of audio stream signal received.")
                break
        
        audio_data = audio_buffer.getvalue()
        if not audio_data:
            await websocket.send_text("Error: No audio data received.")
            return

        print(f"Received {len(audio_data)} bytes of audio data.")
        
        # 2. Take screenshot for additional context
        print("Taking screenshot...")
        take_screenshot()
        
        if not os.path.exists(screenshot_path):
            await websocket.send_text("Error: Failed to take screenshot.")
            return

        print("Sending audio and screenshot to Gemini...")
        img = Image.open(screenshot_path)
        gemini_audio_file = {
            'mime_type': 'audio/webm',
            'data': audio_data
        }

        # 3. Create multi-modal prompt and send to Gemini
        prompt = "Analyze the user's question from the audio in the context of the attached screen image and provide a concise answer."
        response_stream = model.generate_content([prompt, gemini_audio_file, img], stream=True)

        # 4. Stream response back to client
        for chunk in response_stream:
            if chunk.text:
                await websocket.send_text(chunk.text)

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"An error occurred in WebSocket: {e}")
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        # 5. Cleanup
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            print(f"Removed screenshot file: {screenshot_path}")
        await websocket.close()
        print("WebSocket connection closed.")