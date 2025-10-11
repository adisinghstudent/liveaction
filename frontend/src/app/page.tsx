'use client';

import { useState, useRef, useEffect } from 'react';

// A simple microphone icon component
const MicrophoneIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 14a2 2 0 0 1-2-2V6a2 2 0 1 1 4 0v6a2 2 0 0 1-2 2z" />
    <path d="M17 12a5 5 0 0 0-10 0H5a7 7 0 0 1 14 0h-2z" />
    <path d="M12 19a4 4 0 0 1-4-4h-2a6 6 0 0 0 12 0h-2a4 4 0 0 1-4 4z" />
  </svg>
);

export default function Home() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState('');
  const recognitionRef = useRef<any>(null);

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError('Speech recognition is not supported in this browser.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.interimResults = true;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };
    recognition.onerror = (event) => {
      if (event.error === 'not-allowed') {
        setError('Microphone access denied. Please enable it in your browser site settings.');
      } else {
        setError(`Speech recognition error: ${event.error}`);
      }
      setIsListening(false);
    };
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0])
        .map(result => result.transcript)
        .join('');
      setQuestion(transcript);
    };

    recognition.start();
  };

  const handleListenClick = async () => {
    setError('');
    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }

    try {
      // @ts-ignore
      const permissionStatus = await navigator.permissions.query({ name: 'microphone' });
      if (permissionStatus.state === 'denied') {
        setError("Microphone access was denied. Please enable it in your browser's site settings for localhost:3000.");
        return;
      }
      startListening();
    } catch (e) {
      console.error("Permissions API not supported, falling back to standard start.", e);
      startListening(); // Fallback for browsers that don't support Permissions API for microphone
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);
    setResponse('');
    setError('');

    try {
      const res = await fetch('http://localhost:8000/api/describe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      if (!res.ok || !res.body) {
        const errorData = res.statusText;
        throw new Error(errorData || 'An unknown error occurred');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setResponse(prev => prev + chunk);
      }

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 md:p-24 bg-gray-900 text-white">
      <div className="w-full max-w-2xl">
        <h1 className="text-4xl font-bold text-center mb-8">ScreenKnow</h1>
        
        <form onSubmit={handleSubmit} className="w-full">
          <div className="relative">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Type or click the mic to ask about your screen..."
              className="w-full p-4 pr-12 rounded-lg bg-gray-800 border border-gray-700 focus:ring-2 focus:ring-blue-500 focus:outline-none transition duration-200"
              rows={4}
              disabled={isLoading}
            />
            <button 
              type="button"
              onClick={handleListenClick}
              className={`absolute right-3 top-3 p-2 rounded-full transition-colors ${isListening ? 'bg-red-500 text-white' : 'bg-gray-700 hover:bg-gray-600'}`}
              title="Toggle voice input"
            >
              <MicrophoneIcon className="h-6 w-6" />
            </button>
          </div>
          <button 
            type="submit"
            disabled={isLoading || isListening}
            className="w-full mt-4 p-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 disabled:cursor-not-allowed font-bold transition duration-200"
          >
            {isLoading ? 'Analyzing...' : 'Ask'}
          </button>
        </form>

        {isListening && <p className="text-center mt-4 text-blue-400">Listening...</p>}

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