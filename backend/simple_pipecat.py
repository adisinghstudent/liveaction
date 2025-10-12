"""
SIMPLEST Pipecat Setup for ScreenKnow
Just handles: Audio In -> Transcribe -> Screenshot + Gemini -> Text Out
"""

import os
import asyncio
from fastapi import WebSocket
from PIL import Image
import mss
import google.generativeai as genai

# Optional: Add if you want text-to-speech
# from pipecat.services.openai import OpenAITTSService
from pipecat.services.deepgram import DeepgramSTTService


class SimplePipecatHandler:
    """Minimal Pipecat integration - just STT + your existing logic"""
    
    def __init__(self):
        # Get API keys from environment
        self.deepgram_key = os.environ.get("DEEPGRAM_API_KEY", "")
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")
        
        # Setup Gemini
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def handle_conversation(self, websocket: WebSocket):
        """
        Simple flow:
        1. Receive audio from WebSocket
        2. Transcribe with Deepgram (via Pipecat)
        3. Take screenshot
        4. Ask Gemini
        5. Stream response back
        """
        
        # Initialize Deepgram STT
        if not self.deepgram_key:
            await websocket.send_json({"type": "error", "data": "Deepgram API key not set"})
            return
        
        stt = DeepgramSTTService(api_key=self.deepgram_key)
        
        audio_buffer = bytearray()
        
        try:
            while True:
                # Receive audio chunks from browser
                data = await websocket.receive()
                
                if data.get("type") == "websocket.disconnect":
                    break
                
                if data.get("type") == "websocket.receive":
                    if isinstance(data.get("bytes"), bytes):
                        audio_buffer.extend(data["bytes"])
                    
                    elif data.get("text") == "END_OF_STREAM":
                        # User stopped recording
                        await websocket.send_json({"type": "text", "data": "\n\n🎯 Analyzing your screen...\n\n"})
                        
                        # Transcribe the audio (this is where Pipecat helps)
                        # Note: For full Pipecat integration, you'd set up a pipeline
                        # For now, we can use Deepgram directly or keep your current approach
                        
                        # Take screenshot
                        screenshot_path = "temp_screenshot.png"
                        with mss.mss() as sct:
                            sct.shot(output=screenshot_path)
                        
                        # Analyze with Gemini (you can pass a transcribed question here)
                        img = Image.open(screenshot_path)
                        question = "What do you see on this screen?" # You'd replace with transcribed audio
                        
                        response = await asyncio.to_thread(
                            self.model.generate_content,
                            [question, img]
                        )
                        
                        # Stream response back
                        for chunk in response.text.split():
                            await websocket.send_json({"type": "text", "data": chunk + " "})
                            await asyncio.sleep(0.05)
                        
                        # Cleanup
                        if os.path.exists(screenshot_path):
                            os.remove(screenshot_path)
                        
                        audio_buffer.clear()
                        break
        
        except Exception as e:
            print(f"Error: {e}")
            await websocket.send_json({"type": "error", "data": str(e)})


# Even simpler: Use Pipecat ONLY for the pieces you need
# This is the recommended approach for your app:

async def simple_voice_to_screen_analysis(
    audio_data: bytes,
    deepgram_key: str,
    gemini_key: str
) -> str:
    """
    Ultra-simple function using Pipecat for STT only
    
    Flow:
    1. audio_data -> Deepgram (via Pipecat) -> text
    2. Take screenshot
    3. Send text + screenshot to Gemini
    4. Return response
    """
    
    # Use Pipecat's Deepgram service for transcription
    stt = DeepgramSTTService(api_key=deepgram_key)
    
    # Transcribe (you'd need to format audio properly)
    # transcript = await stt.transcribe(audio_data)
    
    # For now, placeholder:
    transcript = "What's on my screen?"
    
    # Take screenshot
    with mss.mss() as sct:
        screenshot_path = "temp_screenshot.png"
        sct.shot(output=screenshot_path)
    
    # Query Gemini
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    img = Image.open(screenshot_path)
    
    response = await asyncio.to_thread(
        model.generate_content,
        [transcript, img]
    )
    
    # Cleanup
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)
    
    return response.text

