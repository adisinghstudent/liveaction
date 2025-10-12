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
    # Two-model pipeline: multimodal text + image generation
    model_text = genai.GenerativeModel('gemini-2.5-flash')
    model_image = genai.GenerativeModel('gemini-2.5-flash-image')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    sys.exit(1)

# --- FastAPI App Initialization ---
app = FastAPI()

origins_env = os.environ.get("ALLOWED_ORIGINS")
origins = [o.strip() for o in origins_env.split(",")] if origins_env else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---
DISABLE_SCREENSHOT = os.environ.get("DISABLE_SCREENSHOT", "false").lower() == "true"

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
    audio_mime_type = None
    
    try:
        while True:
            data = await websocket.receive()
            if 'bytes' in data:
                audio_buffer.write(data['bytes'])
            elif 'text' in data:
                # Handle control or config messages from the client
                text = data['text']
                if text == "END_OF_STREAM":
                    print("End of audio stream signal received.")
                    break
                # Try parse JSON config for mime type, ignore if not JSON
                try:
                    obj = json.loads(text)
                    if isinstance(obj, dict) and obj.get('type') == 'config':
                        audio_mime_type = obj.get('audio_mime_type') or audio_mime_type
                        print(f"Configured client audio mime type: {audio_mime_type}")
                except Exception:
                    pass
        
        audio_data = audio_buffer.getvalue()
        if not audio_data:
            message = {"type": "error", "data": "No audio data received."}
            await websocket.send_text(json.dumps(message))
            return

        print(f"Received {len(audio_data)} bytes of audio data.")
        img = None
        if not DISABLE_SCREENSHOT:
            print("Taking screenshot...")
            try:
                take_screenshot()
                if os.path.exists(screenshot_path):
                    img = Image.open(screenshot_path)
                else:
                    print("Screenshot file not found after capture; continuing without image.")
            except Exception as e:
                print(f"Screenshot capture failed: {e}. Continuing without image.")

        print("Sending inputs to Gemini (audio" + (" + screenshot" if img else " only") + ")...")
        # Default to audio/webm if client did not provide mime type
        gemini_audio_file = {'mime_type': audio_mime_type or 'audio/webm', 'data': audio_data}

        prompt = (
            "You are a multi-modal assistant. Analyze the user's audio and the screenshot. "
            "Provide a helpful text answer. If a visual image would significantly help, end your response with a single line: "
            "IMAGE_PROMPT: <very concise text-to-image prompt>."
        )
        # Ask for a streamed response so we can surface text progressively and collect an image prompt.
        parts = [prompt, gemini_audio_file]
        if img is not None:
            parts.append(img)
        response_stream = model_text.generate_content(parts, stream=True)

        print("--- Waiting for Gemini Response ---")
        collected_text = ""

        async def process_text(text: str):
            nonlocal collected_text
            if not text:
                return
            collected_text += text
            message = {"type": "text", "data": text}
            await websocket.send_text(json.dumps(message))

        for chunk in response_stream:
            print(f"DEBUG: Received chunk: {chunk}")
            # Newer SDKs can deliver text via chunk.text and data via parts/inline_data.
            # Prefer parts if available, otherwise fall back to chunk.text when present.
            parts = getattr(chunk, 'parts', None)
            if not parts and getattr(chunk, 'text', None):
                await process_text(chunk.text)
                continue

            if not parts:
                continue

            print(f"DEBUG: Chunk parts: {parts}")
            for part in parts:
                if part.text:
                    print(f"DEBUG: Found text part: {part.text}")
                    await process_text(part.text)
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

        # Attempt follow-up image generation with gemini-2.5-flash-image if IMAGE_PROMPT was provided.
        try:
            image_prompt = None
            for line in collected_text.splitlines():
                if line.strip().upper().startswith("IMAGE_PROMPT:"):
                    image_prompt = line.split(":", 1)[1].strip()
                    break
            if image_prompt:
                print(f"Found IMAGE_PROMPT. Generating image with flash-image: {image_prompt}")
                img_response = model_image.generate_content([image_prompt])
                parts = getattr(img_response, 'parts', None)
                if not parts:
                    # Fallback: some SDK versions put data under candidates[0].content.parts
                    candidates = getattr(img_response, 'candidates', [])
                    if candidates:
                        parts = candidates[0].content.parts
                if parts:
                    for part in parts:
                        if getattr(part, 'inline_data', None):
                            mime_type = part.inline_data.mime_type or 'image/png'
                            image_bytes = part.inline_data.data
                            with open(generated_image_path, "wb") as f:
                                f.write(image_bytes)
                            base64_image = base64.b64encode(image_bytes).decode('utf-8')
                            await websocket.send_text(json.dumps({
                                "type": "image",
                                "mime_type": mime_type,
                                "data": base64_image,
                            }))
                            break
                else:
                    print("No inline image data returned from image model.")
        except Exception as e:
            print(f"Image generation follow-up failed: {e}")

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
            try:
                os.remove(screenshot_path)
                print(f"Removed screenshot file: {screenshot_path}")
            except Exception as e:
                print(f"Failed to remove screenshot file: {e}")
        await websocket.close()
        print("WebSocket connection closed.")
