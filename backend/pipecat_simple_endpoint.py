"""
SIMPLEST PIPECAT INTEGRATION FOR SCREENKNOW

This shows the minimal way to use Pipecat in your app.
Just add this endpoint to your FastAPI app.

What you get:
- Audio transcription via Deepgram (much better than browser speech recognition!)
- Screenshot analysis via Gemini
- Streaming responses back to frontend

Setup:
1. pip install pipecat-ai pipecat-ai[deepgram]
2. Get a Deepgram API key: https://deepgram.com
3. Set environment variable: export DEEPGRAM_API_KEY="your_key"
4. Add this to your main.py
"""

import os
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from PIL import Image
import mss
import google.generativeai as genai
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.serializers.protobuf import ProtobufFrameSerializer


async def pipecat_voice_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint using Pipecat for voice transcription
    
    Frontend sends: Audio chunks (WebM format)
    Backend returns: Transcribed text + Gemini analysis (JSON)
    """
    
    await websocket.accept()
    
    # Initialize services
    deepgram_key = os.environ.get("DEEPGRAM_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if not deepgram_key:
        await websocket.send_json({
            "type": "error", 
            "data": "DEEPGRAM_API_KEY not set. Get one at https://deepgram.com"
        })
        await websocket.close()
        return
    
    if not gemini_key:
        await websocket.send_json({
            "type": "error",
            "data": "GEMINI_API_KEY not set"
        })
        await websocket.close()
        return
    
    # Setup Gemini
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Setup Deepgram with Pipecat
    stt = DeepgramSTTService(
        api_key=deepgram_key,
        url="wss://api.deepgram.com/v1/listen",
        encoding="linear16",
        sample_rate=16000,
    )
    
    # Optional: Voice Activity Detection
    # vad = SileroVADAnalyzer()
    
    transcript = ""
    
    try:
        while True:
            data = await websocket.receive()
            
            # Handle audio bytes
            if "bytes" in data:
                audio_chunk = data["bytes"]
                # In a full implementation, you'd process this through Pipecat's pipeline
                # For simplicity, we're showing the concept
                
            # Handle end of recording
            elif "text" in data and data["text"] == "END_OF_STREAM":
                # At this point, you'd have the full transcript from Deepgram
                # For this example, let's use a placeholder
                transcript = "What can you see on my screen?"
                
                # Send status update
                await websocket.send_json({
                    "type": "text",
                    "data": f"📝 You said: {transcript}\n\n🔍 Analyzing screenshot...\n\n"
                })
                
                # Take screenshot
                screenshot_path = "temp_screenshot.png"
                with mss.mss() as sct:
                    sct.shot(output=screenshot_path)
                
                # Analyze with Gemini
                img = Image.open(screenshot_path)
                response_stream = model.generate_content([transcript, img], stream=True)
                
                # Stream response back
                for chunk in response_stream:
                    if chunk.text:
                        await websocket.send_json({
                            "type": "text",
                            "data": chunk.text
                        })
                        await asyncio.sleep(0.05)
                
                # Cleanup
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                
                break
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.send_json({"type": "error", "data": str(e)})
    finally:
        # Cleanup
        pass


"""
TO USE THIS IN YOUR MAIN.PY:

from pipecat_simple_endpoint import pipecat_voice_endpoint

@app.websocket("/api/pipecat-voice")
async def pipecat_voice(websocket: WebSocket):
    await pipecat_voice_endpoint(websocket)


EVEN SIMPLER: Just use Deepgram's API directly (no Pipecat)
Pipecat is most useful when you need:
1. Complex multi-step pipelines
2. Real-time bidirectional audio (phone calls, video calls)
3. Multiple AI services chained together
4. Built-in transport layers (Daily.co, Twilio, etc.)

For your use case (record -> transcribe -> analyze -> respond),
you might not need Pipecat's full power yet.
"""


# MINIMAL EXAMPLE: Just Deepgram + Your Current Code
async def ultra_simple_voice_endpoint(websocket: WebSocket):
    """
    The ABSOLUTE simplest way without Pipecat's full framework
    Just uses Deepgram's SDK directly
    """
    import httpx
    
    await websocket.accept()
    
    deepgram_key = os.environ.get("DEEPGRAM_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    audio_buffer = bytearray()
    
    try:
        while True:
            data = await websocket.receive()
            
            if "bytes" in data:
                audio_buffer.extend(data["bytes"])
            
            elif "text" in data and data["text"] == "END_OF_STREAM":
                # Transcribe with Deepgram
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.deepgram.com/v1/listen",
                        headers={
                            "Authorization": f"Token {deepgram_key}",
                            "Content-Type": "audio/webm"
                        },
                        content=bytes(audio_buffer)
                    )
                    result = response.json()
                    transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
                
                # Now use your existing Gemini code
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                
                screenshot_path = "temp_screenshot.png"
                with mss.mss() as sct:
                    sct.shot(output=screenshot_path)
                
                img = Image.open(screenshot_path)
                response_stream = model.generate_content([transcript, img], stream=True)
                
                for chunk in response_stream:
                    if chunk.text:
                        await websocket.send_json({"type": "text", "data": chunk.text})
                        await asyncio.sleep(0.05)
                
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                
                break
    
    except Exception as e:
        await websocket.send_json({"type": "error", "data": str(e)})

