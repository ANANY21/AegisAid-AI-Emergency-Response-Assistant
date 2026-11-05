import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LandingView } from './pages/LandingView';
import { EmergencyInputView } from './pages/EmergencyInputView';
import { ProcessingView } from './pages/ProcessingView';
import { ResultView } from './pages/ResultView';
import { HospitalFinderView } from './pages/HospitalFinderView';
import { HistoryView } from './pages/HistoryView';
import { AdminDashboardView } from './pages/AdminDashboardView';
import { EmergencyResponse } from './types';
import { analyzeEmergency, checkSystemHealth } from './services/api';

export function App() {
  const [currentTab, setCurrentTab] = useState<'landing' | 'emergency' | 'hospitals' | 'history' | 'admin'>('landing');
  const [pipelineState, setPipelineState] = useState<'idle' | 'processing' | 'result'>('idle');
  const [processingStage, setProcessingStage] = useState(0);
  const [emergencyResult, setEmergencyResult] = useState<EmergencyResponse | null>(null);
  const [systemHealthy, setSystemHealthy] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    checkSystemHealth()
      .then((res) => {
        setSystemHealthy(res.status === 'healthy');
      })
      .catch(() => {
        setSystemHealthy(false);
      });
  }, []);

  const handleStartEmergency = () => {
    setPipelineState('idle');
    setEmergencyResult(null);
    setCurrentTab('emergency');
  };

  const handleSubmitEmergency = async (payload: {
    description: string;
    input_type: string;
    voice_transcription?: string;
    patient_age?: number;
    duration?: string;
    location_text?: string;
    latitude?: number;
    longitude?: number;
    image_base64?: string;
  }) => {
    setIsSubmitting(true);
    setPipelineState('processing');
    setProcessingStage(0);

    // Realistic visual stage progression
    const interval = setInterval(() => {
      setProcessingStage((prev) => {
        if (prev < 5) return prev + 1;
        return prev;
      });
    }, 450);

    try {
      const response = await analyzeEmergency(payload);
      clearInterval(interval);
      setProcessingStage(6);

      // Brief delay so user sees final stage complete
      setTimeout(() => {
        setEmergencyResult(response);
        setPipelineState('result');
        setIsSubmitting(false);
      }, 500);

    } catch (err: any) {
      clearInterval(interval);
      setIsSubmitting(false);
      setPipelineState('idle');
      alert(`Emergency processing error: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100 flex flex-col font-sans selection:bg-medic-teal selection:text-white">
      
      {/* Top Navbar */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={(tab) => {
          setCurrentTab(tab);
          if (tab === 'emergency' && pipelineState === 'result') {
            // keep result or reset if user clicks tab again
          }
        }}
        systemHealthy={systemHealthy}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
        
        {currentTab === 'landing' && (
          <LandingView
            onStartEmergency={handleStartEmergency}
            onFindHospitals={() => setCurrentTab('hospitals')}
            onViewAdmin={() => setCurrentTab('admin')}
          />
        )}

        {currentTab === 'emergency' && (
          <>
            {pipelineState === 'idle' && (
              <EmergencyInputView
                onSubmitEmergency={handleSubmitEmergency}
                isSubmitting={isSubmitting}
              />
            )}

            {pipelineState === 'processing' && (
              <ProcessingView
                currentStage={processingStage}
                isBypassingDelays={processingStage >= 4}
              />
            )}

            {pipelineState === 'result' && emergencyResult && (
              <ResultView
                response={emergencyResult}
                onNewEmergency={() => {
                  setPipelineState('idle');
                  setEmergencyResult(null);
                }}
                onFindHospitals={() => setCurrentTab('hospitals')}
              />
            )}
          </>
        )}

        {currentTab === 'hospitals' && (
          <HospitalFinderView />
        )}

        {currentTab === 'history' && (
          <HistoryView />
        )}

        {currentTab === 'admin' && (
          <AdminDashboardView />
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-navy-900 bg-navy-950/80 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 space-y-1">
          <p>© {new Date().getFullYear()} AegisAid — AI Emergency Response Assistant. Grounded Medical Decision Support.</p>
          <p className="text-[11px] text-slate-600">
            Compliant with WHO First-Aid Guidelines & American Heart Association BLS Protocols. Zero autonomous agents.
          </p>
        </div>
      </footer>

    </div>
  );
}

export default App;
