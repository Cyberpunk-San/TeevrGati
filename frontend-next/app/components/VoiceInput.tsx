'use client';
import { useState } from 'react';
import { Mic, MicOff } from 'lucide-react';

export function VoiceInput({ onTranscript }: { onTranscript: (text: string) => void }) {
  const [isListening, setIsListening] = useState(false);

  const startListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      if (text) {
        onTranscript(text);
      }
    };

    recognition.start();
  };

  return (
    <button
      type="button"
      onClick={startListening}
      className={`p-2 rounded-lg border transition-all cursor-pointer flex items-center justify-center ${
        isListening
          ? 'bg-rose-500/20 border-rose-500 text-rose-400 animate-pulse'
          : 'bg-[#0d1527] border-[#2e374a] text-[#94a3b8] hover:border-[#00f5d4] hover:text-white'
      }`}
      disabled={isListening}
      title={isListening ? 'Listening...' : 'Voice Input'}
    >
      {isListening ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
    </button>
  );
}
