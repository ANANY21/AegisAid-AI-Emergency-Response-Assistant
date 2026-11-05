import { EmergencyResponse, HospitalSearchResponse, HistorySession, BenchmarkReport } from '../types';

const API_BASE = '/api';

export async function analyzeEmergency(payload: {
  description: string;
  input_type?: string;
  voice_transcription?: string;
  patient_age?: number;
  duration?: string;
  location_text?: string;
  latitude?: number;
  longitude?: number;
  image_base64?: string;
}): Promise<EmergencyResponse> {
  const resp = await fetch(`${API_BASE}/emergency/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(errorData.message || `Server error: ${resp.status}`);
  }
  return resp.json();
}

export async function getNearbyHospitals(lat?: number, lng?: number): Promise<HospitalSearchResponse> {
  const params = new URLSearchParams();
  if (lat !== undefined && lng !== undefined) {
    params.append('lat', lat.toString());
    params.append('lng', lng.toString());
  }
  const resp = await fetch(`${API_BASE}/hospitals/nearby?${params.toString()}`);
  if (!resp.ok) throw new Error('Failed to load nearby medical facilities');
  return resp.json();
}

export async function getHistory(): Promise<HistorySession[]> {
  const resp = await fetch(`${API_BASE}/history`);
  if (!resp.ok) throw new Error('Failed to load session history');
  return resp.json();
}

export async function deleteHistorySession(sessionId: string): Promise<void> {
  const resp = await fetch(`${API_BASE}/history/${sessionId}`, { method: 'DELETE' });
  if (!resp.ok) throw new Error('Failed to delete session');
}

export async function transcribeAudioFile(audioBlob: Blob, translateToEnglish: boolean = true): Promise<{ success: boolean; transcription: string; error?: string }> {
  const formData = new FormData();
  formData.append('audio_file', audioBlob, 'emergency_recording.webm');
  formData.append('translate', translateToEnglish ? 'true' : 'false');

  const resp = await fetch(`${API_BASE}/emergency/transcribe-audio`, {
    method: 'POST',
    body: formData,
  });
  if (!resp.ok) {
    throw new Error('Audio transcription service unavailable');
  }
  return resp.json();
}

export async function translateSpeechText(text: string): Promise<{ processed_text: string; detected_language: string }> {
  const resp = await fetch(`${API_BASE}/emergency/translate-speech`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!resp.ok) {
    throw new Error('Speech translation request failed');
  }
  return resp.json();
}

export async function clearAllHistory(): Promise<void> {
  const resp = await fetch(`${API_BASE}/history`, { method: 'DELETE' });
  if (!resp.ok) throw new Error('Failed to clear history');
}

export async function getBenchmarkReport(): Promise<BenchmarkReport> {
  const resp = await fetch(`${API_BASE}/evaluation/report`);
  if (!resp.ok) throw new Error('Failed to load system evaluation benchmarks');
  return resp.json();
}

export async function checkSystemHealth(): Promise<any> {
  const resp = await fetch(`${API_BASE}/health`);
  return resp.json();
}
