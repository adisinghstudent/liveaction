"""
Pipecat integration for ScreenKnow
Simple voice conversation with screenshot analysis
"""

import os
import asyncio
import aiohttp
from PIL import Image
import mss
import base64
import io

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.vad.silero import SileroVADAnalyzer

import google.generativeai as genai

class ScreenKnowPipecatBot:
    """Simple Pipecat bot that handles voice + screenshot analysis"""
    
    def __init__(self, gemini_api_key: str, deepgram_api_key: str, openai_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.deepgram_api_key = deepgram_api_key
        self.openai_api_key = openai_api_key
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def take_screenshot(self) -> str:
        """Take a screenshot and return base64 encoded image"""
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[0])
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return img_str
    
    async def analyze_with_gemini(self, question: str) -> str:
        """Take screenshot and analyze with Gemini"""
        try:
            # Take screenshot
            screenshot_path = "screenshot_temp.png"
            with mss.mss() as sct:
                sct.shot(output=screenshot_path)
            
            # Load and analyze with Gemini
            img = Image.open(screenshot_path)
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                [question, img]
            )
            
            # Cleanup
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            
            return response.text
        except Exception as e:
            print(f"Error in Gemini analysis: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def create_pipeline(self, websocket):
        """Create a simple Pipecat pipeline for voice conversation"""
        
        # Services
        stt_service = DeepgramSTTService(api_key=self.deepgram_api_key)
        
        # Simple VAD for detecting when user stops speaking
        vad = SileroVADAnalyzer()
        
        # For TTS, you can use OpenAI
        # tts_service = OpenAITTSService(api_key=self.openai_api_key, voice="alloy")
        
        # Create a minimal pipeline
        pipeline = Pipeline([
            stt_service,  # Speech to text
            # Add your custom processor here for screenshot + Gemini
            # tts_service,  # Text to speech (optional)
        ])
        
        return pipeline


# Simpler WebSocket-only approach (no Daily.co dependency)
class SimpleVoiceHandler:
    """Simplified voice handler without Daily.co - just WebSocket + Pipecat services"""
    
    def __init__(self, gemini_api_key: str, deepgram_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.deepgram_api_key = deepgram_api_key
        
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def handle_voice_conversation(self, websocket):
        """Handle voice conversation via WebSocket"""
        from pipecat.services.deepgram import DeepgramSTTService
        
        # Initialize Deepgram for transcription
        stt = DeepgramSTTService(api_key=self.deepgram_api_key)
        
        try:
            async for message in websocket.iter_text():
                # Receive audio chunks
                # Transcribe with Deepgram
                # Take screenshot
                # Query Gemini
                # Send response back
                pass
        except Exception as e:
            print(f"Error in voice handler: {e}")

