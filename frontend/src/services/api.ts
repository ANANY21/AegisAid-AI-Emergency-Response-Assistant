import {
  EmergencyResponse, HospitalSearchResponse, HistorySession, BenchmarkReport,
  SHAPExplanationResponse, GlobalSHAPResponse, MedicalSourceProvenance, SourceRegistryMetrics,
  PlaceDetailsResponse, RouteDirectionsResponse, ReverseGeocodeResponse, ChennaiPreset
} from '../types';

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

export async function getNearbyHospitals(options?: {
  lat?: number;
  lng?: number;
  radius_km?: number;
  sort_by?: string;
  filter_type?: string;
  limit?: number;
  auto_expand?: boolean;
}): Promise<HospitalSearchResponse> {
  const params = new URLSearchParams();
  if (options?.lat !== undefined && options?.lng !== undefined) {
    params.append('lat', options.lat.toString());
    params.append('lng', options.lng.toString());
  }
  if (options?.radius_km !== undefined) {
    params.append('radius_km', options.radius_km.toString());
  }
  if (options?.sort_by) {
    params.append('sort_by', options.sort_by);
  }
  if (options?.filter_type) {
    params.append('filter_type', options.filter_type);
  }
  if (options?.limit !== undefined) {
    params.append('limit', options.limit.toString());
  }
  if (options?.auto_expand !== undefined) {
    params.append('auto_expand', options.auto_expand ? 'true' : 'false');
  }
  const resp = await fetch(`${API_BASE}/hospitals/nearby?${params.toString()}`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to load nearby medical facilities');
  }
  return resp.json();
}

export async function getHospitalDiagnostics(): Promise<any> {
  const resp = await fetch(`${API_BASE}/hospitals/diagnostics`);
  if (!resp.ok) {
    throw new Error('Failed to fetch hospital diagnostics');
  }
  return resp.json();
}

export async function getHospitalDetails(placeId: string): Promise<PlaceDetailsResponse> {
  const resp = await fetch(`${API_BASE}/hospitals/${encodeURIComponent(placeId)}`);
  if (!resp.ok) {
    throw new Error('Failed to load facility details');
  }
  return resp.json();
}

export async function getHospitalDirections(
  placeId: string,
  originLat: number,
  originLng: number,
  destLat: number,
  destLng: number
): Promise<RouteDirectionsResponse> {
  const params = new URLSearchParams({
    origin_lat: originLat.toString(),
    origin_lng: originLng.toString(),
    dest_lat: destLat.toString(),
    dest_lng: destLng.toString()
  });
  const resp = await fetch(`${API_BASE}/hospitals/${encodeURIComponent(placeId)}/directions?${params.toString()}`);
  if (!resp.ok) {
    throw new Error('Failed to calculate road route directions');
  }
  return resp.json();
}

export async function reverseGeocodeLocation(lat: number, lng: number): Promise<ReverseGeocodeResponse> {
  const resp = await fetch(`${API_BASE}/location/reverse-geocode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lat, lng })
  });
  if (!resp.ok) {
    throw new Error('Failed to reverse geocode location');
  }
  return resp.json();
}

export async function getChennaiPresets(): Promise<ChennaiPreset[]> {
  const resp = await fetch(`${API_BASE}/location/chennai-presets`);
  if (!resp.ok) {
    throw new Error('Failed to load Chennai presets');
  }
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

export async function explainIncidentPrediction(payload: {
  text: string;
  age?: number;
  duration_minutes?: number;
  has_breathing_difficulty?: number;
  has_unconsciousness?: number;
  has_severe_bleeding?: number;
  has_chest_pain?: number;
  has_stroke_symptoms?: number;
  has_anaphylaxis_symptoms?: number;
  has_severe_trauma?: number;
  has_altered_mental_status?: number;
  target_class?: string;
}): Promise<SHAPExplanationResponse> {
  const resp = await fetch(`${API_BASE}/explainability/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to compute SHAP explanation');
  }
  return resp.json();
}

export async function getGlobalSHAPExplanation(): Promise<GlobalSHAPResponse> {
  const resp = await fetch(`${API_BASE}/explainability/global`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to load global SHAP summary');
  }
  return resp.json();
}

export async function getMedicalSources(status?: string, category?: string): Promise<MedicalSourceProvenance[]> {
  const params = new URLSearchParams();
  if (status && status !== 'all') params.append('status', status);
  if (category && category !== 'all') params.append('category', category);
  const resp = await fetch(`${API_BASE}/sources?${params.toString()}`);
  if (!resp.ok) throw new Error('Failed to load registered medical sources');
  return resp.json();
}

export async function getSourceRegistryMetrics(): Promise<SourceRegistryMetrics> {
  const resp = await fetch(`${API_BASE}/sources/metrics`);
  if (!resp.ok) throw new Error('Failed to load medical source metrics');
  return resp.json();
}

export async function updateSourceReview(
  documentId: string,
  payload: { review_status: string; reviewer_notes?: string; reviewed_by?: string }
): Promise<any> {
  const resp = await fetch(`${API_BASE}/sources/${documentId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) throw new Error('Failed to update protocol review status');
  return resp.json();
}
