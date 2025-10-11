'use client';

import { useState, useRef, useEffect } from 'react';

const MicrophoneIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 14a2 2 0 0 1-2-2V6a2 2 0 1 1 4 0v6a2 2 0 0 1-2 2z" />
    <path d="M17 12a5 5 0 0 0-10 0H5a7 7 0 0 1 14 0h-2z" />
    <path d="M12 19a4 4 0 0 1-4-4h-2a6 6 0 0 0 12 0h-2a4 4 0 0 1-4 4z" />
  </svg>
);

export default function Home() {
  const [response, setResponse] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState('');
  
  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  useEffect(() => {
    // Cleanup function to close WebSocket and MediaRecorder on component unmount
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
    setResponse('');
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
          stream.getTracks().forEach(track => track.stop()); // Stop microphone access
          setIsTranscribing(true);
        };

        socketRef.current.onmessage = (event) => {
          setResponse(prev => prev + event.data);
        };

        socketRef.current.onerror = (event) => {
          console.error("WebSocket error:", event);
          setError("WebSocket connection error. See console for details.");
        };

        socketRef.current.onclose = () => {
          console.log("WebSocket connection closed.");
          setIsTranscribing(false);
        };

        mediaRecorderRef.current.start(1000); // Send data every 1000ms (1 second)
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
    <main className="flex min-h-screen flex-col items-center justify-center p-6 md:p-24 bg-gray-900 text-white">
      <div className="w-full max-w-2xl">
        <h1 className="text-4xl font-bold text-center mb-8">ScreenKnow (Audio)</h1>
        
        <div className="w-full text-center">
            <button 
              type="button"
              onClick={handleTranscription}
              disabled={isTranscribing}
              className={`p-4 rounded-full transition-all duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center mx-auto ${isRecording ? 'bg-red-600 hover:bg-red-700 w-48' : 'bg-blue-600 hover:bg-blue-700 w-48'}`}
            >
              <MicrophoneIcon className="h-6 w-6 mr-2" />
              <span>{getButtonState()}</span>
            </button>
        </div>

        {error && (
          <div className="mt-8 p-4 rounded-lg bg-red-900 border border-red-700 text-red-200">
            <p className="font-bold">Error:</p>
            <p>{error}</p>
          </div>
        )}

        {response && (
          <div className="mt-8 p-4 rounded-lg bg-gray-800 border border-gray-700">
            <p className="font-bold">Answer:</p>
            <p className="mt-2 whitespace-pre-wrap">{response}</p>
          </div>
        )}
      </div>
    </main>
  );
}
