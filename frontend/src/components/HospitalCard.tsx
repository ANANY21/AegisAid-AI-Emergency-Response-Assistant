import React, { useState } from 'react';
import { MedicalFacility } from '../types';
import { 
  MapPin, Phone, Navigation, AlertCircle, Building2, 
  Star, Clock, Globe, ExternalLink, Info, CheckCircle2, Map
} from 'lucide-react';

interface HospitalCardProps {
  facility: MedicalFacility;
  index: number;
  isSelected?: boolean;
  onFocusOnMap?: () => void;
}

export const HospitalCard: React.FC<HospitalCardProps> = ({ 
  facility, 
  index, 
  isSelected = false,
  onFocusOnMap 
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const isEmergency = facility.has_emergency_room;
  const hasPhone = Boolean(facility.phone && facility.phone.trim() && facility.phone !== 'None');
  const hasRating = facility.rating !== null && facility.rating !== undefined;

  return (
    <div 
      className={`rounded-2xl border p-5 transition-all bg-navy-900 space-y-4 ${
        isSelected
          ? 'border-medic-teal ring-2 ring-medic-teal/40 bg-navy-850 shadow-xl'
          : isEmergency 
          ? 'border-emergency-500/30 hover:border-emergency-500/60 shadow-lg shadow-emergency-600/5' 
          : 'border-navy-800 hover:border-slate-700'
      }`}
    >
      {/* Top Header: Badge, Name, Distance & Travel Time */}
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-navy-950 border border-navy-700 text-slate-300 font-mono text-[11px] font-bold flex items-center justify-center shrink-0">
              {index + 1}
            </span>
            <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full border ${
              isEmergency 
                ? 'bg-emergency-600/20 text-emergency-400 border-emergency-500/30' 
                : 'bg-sky-600/20 text-sky-300 border-sky-500/30'
            }`}>
              {isEmergency ? 'Emergency Trauma / Hospital' : 'Clinic / Urgent Care'}
            </span>

            {facility.is_open_now !== null && facility.is_open_now !== undefined && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                facility.is_open_now 
                  ? 'bg-emerald-500/20 text-emerald-300' 
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {facility.is_open_now ? 'Open Now' : 'Closed'}
              </span>
            )}
          </div>

          <h3 className="text-base font-extrabold text-white tracking-tight leading-snug">
            {facility.name}
          </h3>
        </div>
        
        {/* Distance & Travel Time Badge */}
        <div className="text-right shrink-0 bg-navy-950 px-3 py-1.5 rounded-xl border border-navy-800">
          <div className="flex items-baseline justify-end gap-1">
            <span className="text-lg font-black text-medic-teal font-mono">
              {facility.road_distance_km !== null && facility.road_distance_km !== undefined
                ? facility.road_distance_km
                : facility.distance_km}
            </span>
            <span className="text-xs text-slate-400 font-medium">km</span>
          </div>

          <span className="text-[10px] text-slate-400 block font-medium">
            {facility.driving_duration_text || 
             (facility.road_distance_km ? `${facility.road_distance_km} km road` : 'straight-line')}
          </span>
        </div>
      </div>

      {/* Address */}
      <div className="flex items-start gap-2 text-xs text-slate-300">
        <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-500 mt-0.5" />
        <span className="leading-relaxed">{facility.address}</span>
      </div>

      {/* Provider Details Strip: Rating, Phone, Hours */}
      <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-navy-800 text-slate-300">
        {/* Rating */}
        <div className="flex items-center gap-1.5">
          <Star className={`w-3.5 h-3.5 shrink-0 ${hasRating ? 'text-amber-400 fill-amber-400' : 'text-slate-600'}`} />
          {hasRating ? (
            <span className="font-mono">
              <strong className="text-white">{facility.rating?.toFixed(1)}</strong>
              {facility.user_ratings_total && <span className="text-slate-400 text-[10px]"> ({facility.user_ratings_total})</span>}
            </span>
          ) : (
            <span className="text-[11px] text-slate-500">Rating not available from provider</span>
          )}
        </div>

        {/* Contact Phone */}
        <div className="flex items-center gap-1.5">
          <Phone className={`w-3.5 h-3.5 shrink-0 ${hasPhone ? 'text-emerald-400' : 'text-slate-600'}`} />
          {hasPhone ? (
            <span className="font-mono text-emerald-300 truncate">{facility.phone}</span>
          ) : (
            <span className="text-[11px] text-slate-500">Phone not available from provider</span>
          )}
        </div>
      </div>

      {/* Emergency Capacity Notice */}
      <div className="p-2.5 rounded-xl bg-navy-950 border border-navy-800 text-[11px] text-slate-400 flex items-start gap-2">
        <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
        <span>{facility.real_time_status_note}</span>
      </div>

      {/* Expanded Place Details Drawer */}
      {showDetails && (
        <div className="p-3.5 rounded-xl bg-navy-950 border border-navy-800 text-xs space-y-2 text-slate-300 animate-fadeIn">
          <div className="flex items-center justify-between pb-2 border-b border-navy-800">
            <span className="font-bold text-white text-[11px] uppercase tracking-wider">Facility Metadata</span>
            <span className="text-[10px] font-mono text-slate-500">Provider: {facility.data_provider}</span>
          </div>

          {facility.place_id && (
            <div className="text-[11px]">
              <span className="text-slate-400">Place ID:</span>{' '}
              <span className="font-mono text-slate-300">{facility.place_id}</span>
            </div>
          )}

          <div className="text-[11px]">
            <span className="text-slate-400">Coordinates:</span>{' '}
            <span className="font-mono text-slate-300">{facility.latitude.toFixed(4)}° N, {facility.longitude.toFixed(4)}° E</span>
          </div>

          <div className="text-[11px]">
            <span className="text-slate-400">Distance Metric:</span>{' '}
            <span>
              {facility.road_distance_km !== null && facility.road_distance_km !== undefined
                ? `${facility.road_distance_km} km actual road distance via Routes API (${facility.straight_line_distance_km} km straight-line)`
                : `${facility.straight_line_distance_km} km straight-line distance`}
            </span>
          </div>

          {facility.website && (
            <div className="pt-1">
              <a
                href={facility.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-medic-teal hover:underline flex items-center gap-1 font-bold text-[11px]"
              >
                <Globe className="w-3 h-3" />
                <span>Visit Hospital Official Website</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
          )}

          {facility.osm_directions_url && (
            <div className="pt-0.5">
              <a
                href={facility.osm_directions_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-400 hover:underline flex items-center gap-1 font-bold text-[11px]"
              >
                <ExternalLink className="w-3 h-3" />
                <span>View Route on OpenStreetMap.org</span>
              </a>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        {/* Call Hospital button (only if phone available) */}
        {hasPhone ? (
          <a
            href={`tel:${facility.phone}`}
            className="flex-1 min-w-[120px] py-2 px-3 rounded-xl bg-emergency-600/20 hover:bg-emergency-600/30 text-emergency-400 border border-emergency-500/30 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
          >
            <Phone className="w-3.5 h-3.5" />
            <span>Call Hospital</span>
          </a>
        ) : (
          <a
            href="tel:112"
            className="flex-1 min-w-[120px] py-2 px-3 rounded-xl bg-navy-950 hover:bg-navy-800 text-slate-400 border border-navy-800 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
            title="Hospital telephone not in provider registry. Call 112 emergency helpline."
          >
            <Phone className="w-3.5 h-3.5 text-emergency-500" />
            <span>Call 112 (No Phone)</span>
          </a>
        )}

        {/* View on Map Button */}
        {onFocusOnMap && (
          <button
            onClick={onFocusOnMap}
            className="py-2 px-3 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-300 font-bold text-xs flex items-center justify-center gap-1.5 border border-navy-700 transition-colors"
            title="Focus hospital on map"
          >
            <Map className="w-3.5 h-3.5 text-medic-teal" />
            <span className="hidden sm:inline">View on Map</span>
          </button>
        )}

        {/* Directions via OpenStreetMap & Google Maps */}
        {facility.osm_directions_url && (
          <a
            href={facility.osm_directions_url}
            target="_blank"
            rel="noopener noreferrer"
            className="py-2 px-3 rounded-xl bg-emerald-950/70 hover:bg-emerald-900/80 text-emerald-300 font-bold text-xs flex items-center justify-center gap-1.5 border border-emerald-600/40 transition-colors"
            title="Open turn-by-turn route in OpenStreetMap"
          >
            <ExternalLink className="w-3.5 h-3.5 text-emerald-400" />
            <span>OSM Route</span>
          </a>
        )}

        {/* Directions button */}
        <a
          href={facility.directions_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 min-w-[120px] py-2 px-3 rounded-xl bg-medic-teal hover:bg-medic-teal-light text-navy-950 font-black text-xs flex items-center justify-center gap-1.5 shadow-md transition-all"
        >
          <Navigation className="w-3.5 h-3.5" />
          <span>Directions</span>
        </a>

        {/* Details Toggle */}
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="p-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-400 hover:text-white border border-navy-700 text-xs transition-colors"
          title="Toggle facility details"
        >
          <Info className="w-4 h-4" />
        </button>
      </div>

    </div>
  );
};
