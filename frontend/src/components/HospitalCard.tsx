import React from 'react';
import { MedicalFacility } from '../types';
import { MapPin, Phone, Navigation, AlertCircle, Building2, Flame } from 'lucide-react';

interface HospitalCardProps {
  facility: MedicalFacility;
}

export const HospitalCard: React.FC<HospitalCardProps> = ({ facility }) => {
  const isEmergency = facility.has_emergency_room;

  return (
    <div className={`rounded-xl border p-5 transition-all bg-navy-900 ${
      isEmergency 
        ? 'border-emergency-500/30 hover:border-emergency-500/60 shadow-lg shadow-emergency-600/5' 
        : 'border-navy-700 hover:border-slate-500'
    }`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Building2 className={`w-4 h-4 ${isEmergency ? 'text-emergency-500' : 'text-medic-teal'}`} />
            <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full ${
              isEmergency 
                ? 'bg-emergency-600/20 text-emergency-400 border border-emergency-500/30' 
                : 'bg-navy-800 text-slate-300'
            }`}>
              {isEmergency ? 'Emergency Trauma / ED' : 'Clinic / Urgent Care'}
            </span>
          </div>
          <h3 className="text-base font-bold text-white tracking-tight leading-snug">{facility.name}</h3>
        </div>
        
        <div className="text-right shrink-0">
          <span className="text-lg font-black text-medic-teal font-mono">{facility.distance_km}</span>
          <span className="text-xs text-slate-400 block font-medium">km away</span>
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
        <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-500" />
        <span className="truncate">{facility.address}</span>
      </div>

      {/* Real-time verification notice */}
      <div className="p-2.5 rounded-lg bg-navy-950 border border-navy-800 text-[11px] text-slate-400 flex items-start gap-2 mb-4">
        <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
        <span>{facility.real_time_status_note}</span>
      </div>

      {/* Action Buttons: Telephone & Directions */}
      <div className="flex items-center gap-2.5">
        {facility.phone ? (
          <a
            href={`tel:${facility.phone}`}
            className="flex-1 py-2 px-3 rounded-lg bg-emergency-600/20 hover:bg-emergency-600/30 text-emergency-400 border border-emergency-500/30 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
          >
            <Phone className="w-3.5 h-3.5" />
            <span>Call Facility</span>
          </a>
        ) : (
          <a
            href="tel:911"
            className="flex-1 py-2 px-3 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-300 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
          >
            <Phone className="w-3.5 h-3.5" />
            <span>Call 911 / 112</span>
          </a>
        )}

        <a
          href={facility.directions_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 py-2 px-3 rounded-lg bg-medic-teal hover:bg-medic-teal/90 text-navy-950 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
        >
          <Navigation className="w-3.5 h-3.5" />
          <span>Directions</span>
        </a>
      </div>
    </div>
  );
};
