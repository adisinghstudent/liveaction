# Pipecat Integration Guide for ScreenKnow

## What is Pipecat?

Pipecat is a framework for building **real-time voice and multimodal AI applications**. Think of it as "plumbing for voice AI" - it handles the complex parts of audio streaming, transcription, TTS, and connecting multiple AI services together.

## Do You Need Pipecat?

### ✅ Use Pipecat When:
- You want **bidirectional voice conversations** (like a phone call with AI)
- You need to chain multiple AI services together
- You want built-in integrations with transport layers (Daily.co, Twilio, WebRTC)
- You're building complex voice pipelines with multiple steps
- You want production-ready voice AI with minimal setup

### 🤔 You Might NOT Need Pipecat (Yet) If:
- Your app is simple: record → transcribe → respond
- You're okay with non-streaming transcription
- You just need basic voice input/output

## Simplest Pipecat Setup for ScreenKnow

### Option 1: Just Use Deepgram (No Full Pipecat)

This is the **easiest** approach - just replace browser speech recognition with Deepgram:

```bash
# Install
pip install httpx

# Get Deepgram API key
# https://deepgram.com (free tier: 45,000 minutes/year!)

# Set environment variable
export DEEPGRAM_API_KEY="your_key_here"
```

See `pipecat_simple_endpoint.py` for the `ultra_simple_voice_endpoint` function.

**Pros:**
- No new framework to learn
- Very reliable transcription (much better than browser API)
- Works offline for browser, transcription in cloud
- Simple to implement

**Cons:**
- Not using Pipecat's full power
- Have to handle audio formats yourself

---

### Option 2: Use Pipecat's Deepgram Service

Slightly more structured, uses Pipecat's abstraction:

```bash
# Install
pip install pipecat-ai pipecat-ai[deepgram]

export DEEPGRAM_API_KEY="your_key"
```

See `pipecat_simple_endpoint.py` for the `pipecat_voice_endpoint` function.

**Pros:**
- Better audio handling
- Can easily add VAD (Voice Activity Detection)
- Easy to extend with other Pipecat services later

**Cons:**
- Slightly more complex setup
- Adds a dependency

---

### Option 3: Full Pipecat Pipeline (Advanced)

For when you want the full power - real-time streaming, multiple AI services, complex workflows:

```bash
# Install with all services
pip install pipecat-ai
pip install pipecat-ai[deepgram]
pip install pipecat-ai[openai]  # For GPT and TTS
pip install pipecat-ai[daily]   # If using Daily.co for WebRTC
```

**Example Pipeline:**
```
User Voice → Deepgram STT → LLM (GPT/Gemini) → Screenshot Analysis → TTS → User Audio
```

This is overkill for your current app but great for scaling up!

---

## Recommended Approach for ScreenKnow

**Start with Option 1** (Just Deepgram API directly):

1. It's the simplest
2. Huge quality improvement over browser speech recognition
3. Easy to upgrade to full Pipecat later if needed
4. No framework learning curve

### Implementation Steps:

1. **Get Deepgram API Key**
   ```bash
   # Sign up at https://deepgram.com
   # Free tier: 45,000 minutes/year (125 min/day)
   export DEEPGRAM_API_KEY="your_key"
   ```

2. **Update your backend** (add to `main.py`):
   ```python
   from pipecat_simple_endpoint import ultra_simple_voice_endpoint
   
   @app.websocket("/api/voice-deepgram")
   async def voice_deepgram(websocket: WebSocket):
       await ultra_simple_voice_endpoint(websocket)
   ```

3. **Update frontend** (change WebSocket URL):
   ```typescript
   // In page.tsx
   socketRef.current = new WebSocket('ws://localhost:8000/api/voice-deepgram');
   ```

4. **That's it!** Much better transcription quality.

---

## When to Upgrade to Full Pipecat

Upgrade when you want:
- **Real-time conversations** (voice in → immediate voice out)
- **Phone/video call integration** (Daily.co, Twilio)
- **Complex workflows** (multiple AI services chained)
- **Production-ready voice AI** with minimal code

## Resources

- [Pipecat Docs](https://docs.pipecat.ai/)
- [Deepgram Docs](https://developers.deepgram.com/)
- [Example Pipecat Apps](https://github.com/pipecat-ai/pipecat/tree/main/examples)

---

## TL;DR

**For ScreenKnow right now:**
- Just use Deepgram API directly (see `ultra_simple_voice_endpoint`)
- 10x better than browser speech recognition
- Simple to implement
- Can upgrade to full Pipecat later when you need advanced features

