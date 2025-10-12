'use client';

import { useState, useRef, useEffect } from 'react';

const MicrophoneIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 14a2 2 0 0 1-2-2V6a2 2 0 1 1 4 0v6a2 2 0 0 1-2 2z" />
    <path d="M17 12a5 5 0 0 0-10 0H5a7 7 0 0 1 14 0h-2z" />
    <path d="M12 19a4 4 0 0 1-4-4h-2a6 6 0 0 0 12 0h-2a4 4 0 0 1-4 4z" />
  </svg>
);

interface ResponsePart {
  type: 'text' | 'image' | 'error';
  data: string;
  mime_type?: string;
}

export default function Home() {
  const [responseParts, setResponseParts] = useState<ResponsePart[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState('');
  
  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  useEffect(() => {
    return () => {
      socketRef.current?.close();
      mediaRecorderRef.current?.stop();
    };
  }, []);

  const handleTranscription = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      return;
    }

    setError('');
    setResponseParts([]);
    setIsRecording(true);
    setIsTranscribing(false);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      socketRef.current = new WebSocket('ws://localhost:8000/api/audio-stream');

      socketRef.current.onopen = () => {
        console.log("WebSocket connection opened.");
        mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });

        mediaRecorderRef.current.ondataavailable = (event) => {
          if (event.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(event.data);
          }
        };

        mediaRecorderRef.current.onstop = () => {
          console.log("MediaRecorder stopped.");
          if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send("END_OF_STREAM");
          }
          stream.getTracks().forEach(track => track.stop());
          setIsTranscribing(true);
        };

        socketRef.current.onmessage = (event) => {
          const message: ResponsePart = JSON.parse(event.data);
          if (message.type === 'error') {
            setError(message.data);
            return;
          }

          setResponseParts(prevParts => {
            // For streaming text, append to the last text part if it exists
            const lastPart = prevParts[prevParts.length - 1];
            if (message.type === 'text' && lastPart?.type === 'text') {
              const newParts = [...prevParts];
              newParts[newParts.length - 1] = { ...lastPart, data: lastPart.data + message.data };
              return newParts;
            }
            // Otherwise, add a new part
            return [...prevParts, message];
          });
        };

        socketRef.current.onerror = (event) => {
          console.error("WebSocket error:", event);
          setError("WebSocket connection error. See console for details.");
        };

        socketRef.current.onclose = () => {
          console.log("WebSocket connection closed.");
          setIsTranscribing(false);
        };

        mediaRecorderRef.current.start(1000);
      };

    } catch (err) {
      console.error("Error getting user media:", err);
      setError("Could not access microphone. Please ensure permission is granted.");
      setIsRecording(false);
    }
  };

  const getButtonState = () => {
    if (isRecording) return "Stop Recording";
    if (isTranscribing) return "Transcribing...";
    return "Start Recording";
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 md:p-24 bg-transparent text-black">
      <div className="w-full max-w-2xl rounded-2xl border border-white/20 dark:border-white/10 bg-white/10 dark:bg-white/5 backdrop-blur-xl shadow-xl">
        <h1 className="text-4xl font-bold text-center mb-8 pt-8">ScreenKnow</h1>
        
        <div className="w-full text-center">
            <button 
              type="button"
              onClick={handleTranscription}
              disabled={isTranscribing}
              className={`p-4 rounded-full transition-all duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center mx-auto w-48 border text-black ${
                isRecording
                  ? 'bg-white hover:bg-white/90 border-black'
                  : 'bg-white hover:bg-white/80 border-black/40'
              }`}
            >
              <MicrophoneIcon className="h-6 w-6 mr-2" />
              <span>{getButtonState()}</span>
            </button>
        </div>

        {error && (
          <div className="mt-8 p-4 rounded-lg bg-white/10 dark:bg-white/5 border border-white/20 text-black backdrop-blur-xl">
            <p className="font-bold">Error:</p>
            <p>{error}</p>
          </div>
        )}

        {responseParts.length > 0 && (
          <div className="mt-8 p-4 rounded-lg bg-white/10 dark:bg-white/5 border border-white/20 space-y-4 backdrop-blur-xl text-black">
            <p className="font-bold">Answer:</p>
            {responseParts.map((part, index) => {
              if (part.type === 'text') {
                return <p key={index} className="whitespace-pre-wrap">{part.data}</p>;
              }
              if (part.type === 'image') {
                return <img key={index} src={`data:${part.mime_type};base64,${part.data}`} alt="Generated image" className="rounded-lg" />;
              }
              return null;
            })}
          </div>
        )}
        <div className="h-8" />
      </div>
    </main>
  );
}
