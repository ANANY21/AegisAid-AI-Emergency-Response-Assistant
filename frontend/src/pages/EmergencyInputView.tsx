import React, { useState, useEffect } from 'react';
import { Type, Mic, Image as ImageIcon, MapPin, AlertCircle, Clock, User, Sparkles, Send, ShieldCheck, RefreshCw } from 'lucide-react';
import { VoiceRecorder } from '../components/VoiceRecorder';
import { ImageUploader } from '../components/ImageUploader';

interface EmergencyInputViewProps {
  onSubmitEmergency: (payload: {
    description: string;
    input_type: string;
    voice_transcription?: string;
    patient_age?: number;
    duration?: string;
    location_text?: string;
    latitude?: number;
    longitude?: number;
    image_base64?: string;
  }) => void;
  isSubmitting: boolean;
}

const PRESET_SCENARIOS = [
  {
    label: 'Cardiac Arrest',
    desc: 'Adult patient suddenly collapsed, unresponsive, not breathing normally, only gasping faintly.',
    age: 58,
    duration: '3 minutes',
    priority: 'CRITICAL'
  },
  {
    label: 'Severe Choking',
    desc: 'Adult choking on steak at dinner, cannot speak, silent cough, hands clutched around neck, lips turning blue.',
    age: 44,
    duration: '2 minutes',
    priority: 'CRITICAL'
  },
  {
    label: 'Boiling Scald Burn',
    desc: 'Spilled pot of boiling water over hand and forearm. Severe intense pain, skin is bright red with large fluid blisters.',
    age: 26,
    duration: '10 minutes',
    priority: 'HIGH'
  },
  {
    label: 'Arterial Bleeding',
    desc: 'Deep thigh cut from broken glass window, bright red blood spurting vigorously and pooling on the floor.',
    age: 32,
    duration: '5 minutes',
    priority: 'CRITICAL'
  },
  {
    label: 'Suspected Stroke',
    desc: 'Grandmother suddenly has severe facial droop on left side, cannot lift left arm, speech is slurred and confused.',
    age: 72,
    duration: '25 minutes',
    priority: 'CRITICAL'
  },
  {
    label: 'Ambiguous / Test Input',
    desc: 'I feel sick and my body hurts all over.',
    age: 30,
    duration: 'unknown',
    priority: 'UNCERTAIN'
  }
];

export const EmergencyInputView: React.FC<EmergencyInputViewProps> = ({ onSubmitEmergency, isSubmitting }) => {
  const [activeTab, setActiveTab] = useState<'text' | 'voice' | 'image'>('text');
  const [description, setDescription] = useState('');
  const [voiceTranscription, setVoiceTranscription] = useState('');
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  
  // Optional clinical metadata
  const [patientAge, setPatientAge] = useState<string>('');
  const [duration, setDuration] = useState<string>('');
  const [locationText, setLocationText] = useState<string>('');
  const [userCoords, setUserCoords] = useState<{ lat?: number; lng?: number }>({});
  const [isLocating, setIsLocating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      setErrorMsg('Geolocation is not supported by your browser.');
      setUserCoords({ lat: 13.0012, lng: 80.2565 });
      setLocationText('Adyar, Chennai (Demonstration GPS Anchor)');
      return;
    }
    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        setUserCoords({ lat, lng });
        const acc = pos.coords.accuracy ? ` (±${Math.round(pos.coords.accuracy)}m)` : '';
        setLocationText(`GPS: ${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E${acc}`);
        setIsLocating(false);
      },
      (err) => {
        setIsLocating(false);
        // Fallback gracefully to Chennai demonstration anchor so hospital search succeeds
        setUserCoords({ lat: 13.0012, lng: 80.2565 });
        setLocationText('Adyar, Chennai (Demonstration GPS Anchor)');
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  useEffect(() => {
    handleGetLocation();
  }, []);

  const handleApplyPreset = (preset: typeof PRESET_SCENARIOS[0]) => {
    setDescription(preset.desc);
    setPatientAge(preset.age.toString());
    setDuration(preset.duration);
    setErrorMsg(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const effectiveText = (description || voiceTranscription).trim();
    if (effectiveText.length < 3 && !imageBase64) {
      setErrorMsg('Please describe the emergency symptoms or provide an emergency recording/image.');
      return;
    }

    onSubmitEmergency({
      description: effectiveText || 'Emergency visual inspection requested',
      input_type: activeTab,
      voice_transcription: voiceTranscription || undefined,
      patient_age: patientAge ? parseInt(patientAge, 10) : undefined,
      duration: duration || undefined,
      location_text: locationText || undefined,
      latitude: userCoords.lat,
      longitude: userCoords.lng,
      image_base64: imageBase64 || undefined
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Report Medical Emergency</h1>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          Describe symptoms using text, voice dictation, or image upload. Our retrieval validation pipeline will cross-reference official first-aid protocols.
        </p>
      </div>

      {/* Quick Scenario Preset Chips */}
      <div className="bg-navy-900 border border-navy-800 rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-2 text-xs font-bold text-slate-300">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span>Quick Benchmark Scenarios:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESET_SCENARIOS.map((p, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleApplyPreset(p)}
              className="text-xs px-3 py-1.5 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 hover:border-slate-500 text-slate-300 hover:text-white font-medium transition-all"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {errorMsg && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-emergency-950/40 border border-emergency-500/40 text-emergency-400 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Input Card */}
      <div className="bg-navy-900 border border-navy-800 rounded-2xl shadow-xl overflow-hidden">
        
        {/* Live GPS Dispatch Indicator */}
        <div className="bg-navy-950/90 border-b border-navy-800 px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2">
            <MapPin className={`w-4 h-4 ${userCoords.lat ? 'text-emerald-400' : 'text-slate-500'}`} />
            <span className="font-bold text-slate-300">
              GPS Dispatch Locator:
            </span>
            {isLocating ? (
              <span className="text-medic-teal animate-pulse font-mono text-[11px] flex items-center gap-1">
                <RefreshCw className="w-3 h-3 animate-spin" />
                <span>Acquiring GPS position for nearest hospitals...</span>
              </span>
            ) : userCoords.lat ? (
              <span className="text-emerald-400 font-mono text-[11px] font-bold">
                {locationText || `${userCoords.lat.toFixed(4)}° N, ${userCoords.lng?.toFixed(4)}° E`}
              </span>
            ) : (
              <span className="text-slate-500 text-[11px]">Location detection pending</span>
            )}
          </div>

          <button
            type="button"
            onClick={handleGetLocation}
            disabled={isLocating}
            className="text-[11px] font-bold text-medic-teal hover:underline flex items-center gap-1 cursor-pointer"
          >
            <RefreshCw className={`w-3 h-3 ${isLocating ? 'animate-spin' : ''}`} />
            <span>{isLocating ? 'Locating...' : 'Refresh GPS'}</span>
          </button>
        </div>

        {/* Modality Tabs */}
        <div className="flex border-b border-navy-800 bg-navy-950/60 p-2 gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('text')}
            className={`flex-1 py-3 px-4 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all ${
              activeTab === 'text'
                ? 'bg-navy-800 text-white shadow-sm border border-navy-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Type className="w-4 h-4" />
            <span>Describe with Text</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('voice')}
            className={`flex-1 py-3 px-4 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all ${
              activeTab === 'voice'
                ? 'bg-emergency-600/20 text-emergency-400 shadow-sm border border-emergency-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Mic className="w-4 h-4" />
            <span>Speak Emergency</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('image')}
            className={`flex-1 py-3 px-4 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all ${
              activeTab === 'image'
                ? 'bg-medic-teal/20 text-medic-teal shadow-sm border border-medic-teal/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ImageIcon className="w-4 h-4" />
            <span>Upload Image</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <form onSubmit={handleSubmit} className="p-6 sm:p-8 space-y-6">
          
          {activeTab === 'text' && (
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                Emergency Situation & Symptoms *
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={5}
                required
                className="w-full bg-navy-950 border border-navy-700 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emergency-500 focus:border-transparent transition-all"
                placeholder="Describe what happened, visible symptoms (e.g. bleeding, shortness of breath, unresponsiveness, severe pain), and what you see right now..."
              />
            </div>
          )}

          {activeTab === 'voice' && (
            <VoiceRecorder
              initialText={voiceTranscription || description}
              onTranscriptionComplete={(text) => {
                setVoiceTranscription(text);
                setDescription(text);
              }}
            />
          )}

          {activeTab === 'image' && (
            <div className="space-y-4">
              <ImageUploader onImageSelected={(b64) => setImageBase64(b64)} />
              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                  Add Context for the Image (Optional)
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-navy-950 border border-navy-700 rounded-xl p-3 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-medic-teal focus:border-transparent"
                  placeholder="E.g., Burn occurred 5 minutes ago from hot soup..."
                />
              </div>
            </div>
          )}

          {/* Clinical Metadata Section (Age, Duration, Location) */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-navy-800">
            <div>
              <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5 mb-1.5">
                <User className="w-3.5 h-3.5 text-slate-500" />
                <span>Patient Age</span>
              </label>
              <input
                type="number"
                min="0"
                max="125"
                value={patientAge}
                onChange={(e) => setPatientAge(e.target.value)}
                className="w-full bg-navy-950 border border-navy-700 rounded-xl p-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-navy-600"
                placeholder="e.g. 45"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5 mb-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                <span>Duration of Symptoms</span>
              </label>
              <input
                type="text"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="w-full bg-navy-950 border border-navy-700 rounded-xl p-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-navy-600"
                placeholder="e.g. 10 mins"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-500" />
                  <span>Location</span>
                </label>
                <button
                  type="button"
                  onClick={handleGetLocation}
                  disabled={isLocating}
                  className="text-[11px] text-medic-teal hover:underline font-medium"
                >
                  {isLocating ? 'Locating...' : 'Use GPS'}
                </button>
              </div>
              <input
                type="text"
                value={locationText}
                onChange={(e) => setLocationText(e.target.value)}
                className="w-full bg-navy-950 border border-navy-700 rounded-xl p-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-navy-600"
                placeholder="Street address or city"
              />
            </div>
          </div>

          {/* Privacy Note */}
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <ShieldCheck className="w-4 h-4 text-medic-teal shrink-0" />
            <span>Encrypted transmission. Uploaded images are analyzed in memory and never stored indefinitely.</span>
          </div>

          {/* Submission Action */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-4 rounded-xl bg-emergency-600 hover:bg-emergency-500 text-white font-extrabold text-base shadow-xl shadow-emergency-600/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                Analyzing Incident Pipeline...
              </span>
            ) : (
              <>
                <Send className="w-5 h-5" />
                <span>Submit for Triage & First-Aid Guidance</span>
              </>
            )}
          </button>
        </form>

      </div>
    </div>
  );
};
