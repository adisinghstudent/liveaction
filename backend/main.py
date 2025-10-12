import google.generativeai as genai
import mss
import os
from PIL import Image
import sys
import asyncio
import io
import json
import base64
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# --- Configuration ---
# Load environment variables from a .env file in the backend directory (if present)
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found. Please set it as an environment variable.")
    sys.exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use default text response configuration; inline binary images are not supported via response_mime_type here.
    model = genai.GenerativeModel('gemini-2.5-flash')
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

# --- WebSocket Endpoint for Multi-modal Streaming ---
@app.websocket("/api/audio-stream")
async def audio_stream(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established.")
    audio_buffer = io.BytesIO()
    screenshot_path = "screenshot.png"
    generated_image_path = "generated_image.png"
    
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
            message = {"type": "error", "data": "No audio data received."}
            await websocket.send_text(json.dumps(message))
            return

        print(f"Received {len(audio_data)} bytes of audio data.")
        print("Taking screenshot...")
        take_screenshot()
        
        if not os.path.exists(screenshot_path):
            message = {"type": "error", "data": "Failed to take screenshot."}
            await websocket.send_text(json.dumps(message))
            return

        print("Sending audio and screenshot to Gemini...")
        img = Image.open(screenshot_path)
        gemini_audio_file = {'mime_type': 'audio/webm', 'data': audio_data}

        prompt = (
            "You are a multi-modal assistant. Analyze the user's audio and the screenshot. "
            "If helpful, produce an illustrative image (diagram, markup, or visual aid). "
            "Otherwise, respond with text."
        )
        # Ask for a streamed response so we can surface text progressively and any image when produced.
        response_stream = model.generate_content([prompt, gemini_audio_file, img], stream=True)

        print("--- Waiting for Gemini Response ---")
        for chunk in response_stream:
            print(f"DEBUG: Received chunk: {chunk}")
            # Newer SDKs can deliver text via chunk.text and data via parts/inline_data.
            # Prefer parts if available, otherwise fall back to chunk.text when present.
            parts = getattr(chunk, 'parts', None)
            if not parts and getattr(chunk, 'text', None):
                message = {"type": "text", "data": chunk.text}
                await websocket.send_text(json.dumps(message))
                continue

            if not parts:
                continue

            print(f"DEBUG: Chunk parts: {parts}")
            for part in parts:
                if part.text:
                    print(f"DEBUG: Found text part: {part.text}")
                    message = {"type": "text", "data": part.text}
                    await websocket.send_text(json.dumps(message))
                elif part.inline_data:
                    print("DEBUG: Found image part!")
                    image_bytes = part.inline_data.data
                    
                    # Save the image to a file for debugging
                    print(f"DEBUG: Saving generated image to {generated_image_path}")
                    with open(generated_image_path, "wb") as f:
                        f.write(image_bytes)

                    base64_image = base64.b64encode(image_bytes).decode('utf-8')
                    mime_type = part.inline_data.mime_type or 'image/png'
                    message = {"type": "image", "mime_type": mime_type, "data": base64_image}
                    await websocket.send_text(json.dumps(message))
        print("--- Finished Processing Gemini Response ---")

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"An error occurred in WebSocket. Type: {type(e).__name__}")
        traceback.print_exc()
        message = {"type": "error", "data": f"A backend error occurred. Check server logs. Type: {type(e).__name__}"}
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as send_e:
            print(f"Failed to send error to client: {send_e}")
    finally:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            print(f"Removed screenshot file: {screenshot_path}")
        await websocket.close()
        print("WebSocket connection closed.")
