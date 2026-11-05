import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Check, Edit2, Volume2, AlertCircle, Globe, Sparkles, RefreshCw } from 'lucide-react';
import { translateSpeechText, transcribeAudioFile } from '../services/api';

interface VoiceRecorderProps {
  onTranscriptionComplete: (text: string) => void;
  initialText?: string;
}

const SUPPORTED_LANGUAGES = [
  { code: 'en-US', name: 'English (US)' },
  { code: 'en-GB', name: 'English (UK)' },
  { code: 'en-IN', name: 'English (India)' },
  { code: 'es-ES', name: 'Spanish / Español' },
  { code: 'fr-FR', name: 'French / Français' },
  { code: 'de-DE', name: 'German / Deutsch' },
  { code: 'hi-IN', name: 'Hindi / हिन्दी' },
  { code: 'zh-CN', name: 'Chinese / 中文' },
  { code: 'ar-SA', name: 'Arabic / العربية' },
  { code: 'pt-BR', name: 'Portuguese / Português' },
  { code: 'ja-JP', name: 'Japanese / 日本語' },
  { code: 'it-IT', name: 'Italian / Italiano' },
];

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onTranscriptionComplete, initialText = '' }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState(initialText);
  const [selectedLang, setSelectedLang] = useState('en-US');
  const [isEditable, setIsEditable] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [detectedLang, setDetectedLang] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const transcriptRef = useRef(transcript);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Keep transcriptRef synchronized
  useEffect(() => {
    transcriptRef.current = transcript;
  }, [transcript]);

  // Initialize SpeechRecognition on mount or language change
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErrorMessage('Speech Recognition is not supported in this browser. Please use the text tab or audio file upload.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = selectedLang;

      recognition.onstart = () => {
        setIsRecording(true);
        setErrorMessage(null);
        setStatusMessage('Listening... Speak clearly into your microphone.');
      };

      recognition.onresult = (event: any) => {
        let accumulated = '';
        for (let i = 0; i < event.results.length; i++) {
          accumulated += event.results[i][0].transcript + ' ';
        }
        const cleaned = accumulated.trim();
        if (cleaned) {
          setTranscript(cleaned);
          transcriptRef.current = cleaned;
          onTranscriptionComplete(cleaned);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('SpeechRecognition event error:', event.error);
        if (event.error === 'not-allowed') {
          setErrorMessage('Microphone access was denied. Please allow microphone permissions in your browser URL bar.');
        } else if (event.error === 'no-speech') {
          setStatusMessage('No speech detected. Tap microphone and try speaking again.');
        } else if (event.error === 'network') {
          setErrorMessage('Speech network service error. Please check your internet connection or type directly.');
        }
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
        if (transcriptRef.current) {
          onTranscriptionComplete(transcriptRef.current);
          setStatusMessage('Recording captured. You can edit or translate to English below.');
        }
      };

      recognitionRef.current = recognition;
    } catch (e: any) {
      console.error('Failed to initialize speech recognition:', e);
    }

    return () => {
      try {
        recognitionRef.current?.abort();
      } catch (_) {}
    };
  }, [selectedLang]);

  const startRecording = async () => {
    setErrorMessage(null);
    setStatusMessage(null);
    setTranscript('');
    transcriptRef.current = '';

    // Also start MediaRecorder for audio backup
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };
        mediaRecorder.start();
        mediaRecorderRef.current = mediaRecorder;
      } catch (err: any) {
        console.warn('MediaRecorder audio stream access error:', err);
      }
    }

    try {
      recognitionRef.current?.start();
    } catch (err) {
      console.warn('Recognition start exception:', err);
      setIsRecording(true);
    }
  };

  const stopRecording = () => {
    try {
      recognitionRef.current?.stop();
    } catch (_) {}

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }

    setIsRecording(false);
    if (transcriptRef.current) {
      onTranscriptionComplete(transcriptRef.current);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Translate foreign speech to English
  const handleTranslateToEnglish = async () => {
    if (!transcript.trim()) return;
    setIsTranslating(true);
    setErrorMessage(null);
    try {
      const res = await translateSpeechText(transcript.trim());
      setTranscript(res.processed_text);
      transcriptRef.current = res.processed_text;
      setDetectedLang(res.detected_language);
      onTranscriptionComplete(res.processed_text);
      setStatusMessage('Speech successfully translated and normalized into English medical terms.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Translation service temporarily unavailable.');
    } finally {
      setIsTranslating(false);
    }
  };

  const handleConfirmText = () => {
    onTranscriptionComplete(transcript);
    setIsEditable(false);
    setStatusMessage('Transcription confirmed and applied to emergency description.');
  };

  return (
    <div className="bg-navy-900 border border-navy-700 rounded-2xl p-6 shadow-xl space-y-5">
      
      {/* Header and Language Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-navy-800 pb-3">
        <div className="flex items-center gap-2">
          <Volume2 className="w-5 h-5 text-emergency-500" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Voice Emergency Dictation & Translation</h3>
        </div>

        {/* Spoken Language Dropdown */}
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-medic-teal shrink-0" />
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            disabled={isRecording}
            className="bg-navy-950 border border-navy-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-medic-teal"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="flex items-start gap-2 p-3.5 rounded-xl bg-emergency-950/60 border border-emergency-500/40 text-emergency-300 text-xs">
          <AlertCircle className="w-4 h-4 text-emergency-500 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Status Banner */}
      {statusMessage && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-navy-950 border border-medic-teal/30 text-medic-teal text-xs">
          <Check className="w-3.5 h-3.5 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Microphone Control Button */}
      <div className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-navy-700 hover:border-navy-600 rounded-2xl bg-navy-950/60 transition-colors">
        <button
          type="button"
          onClick={toggleRecording}
          className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
            isRecording
              ? 'bg-emergency-600 text-white animate-pulse ring-8 ring-emergency-500/30 shadow-xl shadow-emergency-600/50'
              : 'bg-navy-800 hover:bg-navy-700 text-slate-100 border border-navy-600 hover:border-emergency-500 hover:scale-105 shadow-lg'
          }`}
        >
          {isRecording ? <MicOff className="w-10 h-10" /> : <Mic className="w-10 h-10 text-emergency-500" />}
        </button>

        <span className="text-sm font-bold text-white mt-4">
          {isRecording ? 'Listening... Tap to Stop & Save' : 'Tap Microphone to Speak Emergency'}
        </span>
        <span className="text-xs text-slate-400 mt-1">
          {isRecording ? 'Speak clearly about symptoms, location, and condition' : `Configured for ${SUPPORTED_LANGUAGES.find(l => l.code === selectedLang)?.name}`}
        </span>

        {/* Visual Audio Frequency Waves Animation */}
        {isRecording && (
          <div className="flex items-end gap-1.5 h-8 mt-4">
            <span className="w-1.5 h-3 bg-emergency-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1.5 h-6 bg-emergency-500 rounded-full animate-bounce [animation-delay:-0.1s]" />
            <span className="w-1.5 h-8 bg-emergency-400 rounded-full animate-bounce" />
            <span className="w-1.5 h-5 bg-emergency-500 rounded-full animate-bounce [animation-delay:-0.2s]" />
            <span className="w-1.5 h-7 bg-emergency-400 rounded-full animate-bounce [animation-delay:-0.4s]" />
            <span className="w-1.5 h-4 bg-emergency-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
          </div>
        )}
      </div>

      {/* Recognized Transcription Area & Translation Controls */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Recognized Emergency Description (Live):
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsEditable(!isEditable)}
              className="text-xs text-medic-teal hover:underline flex items-center gap-1 font-semibold"
            >
              <Edit2 className="w-3 h-3" />
              {isEditable ? 'Lock Editing' : 'Edit Text'}
            </button>
          </div>
        </div>

        <textarea
          value={transcript}
          onChange={(e) => {
            setTranscript(e.target.value);
            transcriptRef.current = e.target.value;
            onTranscriptionComplete(e.target.value);
          }}
          disabled={!isEditable && !isRecording}
          rows={3}
          className="w-full bg-navy-950 border border-navy-700 rounded-xl p-3.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-medic-teal transition-all"
          placeholder="Spoken emergency symptoms will transcribe here in real-time..."
        />

        {/* Action Buttons: Translate to English + Confirm */}
        {transcript && (
          <div className="flex flex-wrap items-center justify-between gap-2 pt-2">
            <button
              type="button"
              onClick={handleTranslateToEnglish}
              disabled={isTranslating || isRecording}
              className="px-3.5 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/40 text-xs font-bold flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 text-blue-400 ${isTranslating ? 'animate-spin' : ''}`} />
              <span>{isTranslating ? 'Translating to English...' : '🌐 Translate to English for Triage'}</span>
            </button>

            <button
              type="button"
              onClick={handleConfirmText}
              className="px-4 py-2 rounded-xl bg-medic-teal hover:bg-medic-teal/90 text-navy-950 font-extrabold text-xs flex items-center gap-1.5 transition-colors"
            >
              <Check className="w-4 h-4" />
              <span>Confirm & Use in Description</span>
            </button>
          </div>
        )}
      </div>

    </div>
  );
};
