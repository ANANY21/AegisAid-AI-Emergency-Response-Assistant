import React, { useState, useEffect } from 'react';
import { HospitalSearchResponse, MedicalFacility } from '../types';
import { getNearbyHospitals } from '../services/api';
import { HospitalCard } from '../components/HospitalCard';
import { MapPin, Search, Navigation, AlertCircle, RefreshCw, Hospital, Filter } from 'lucide-react';

export const HospitalFinderView: React.FC = () => {
  const [data, setData] = useState<HospitalSearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'emergency_only'>('all');
  const [coords, setCoords] = useState<{ lat?: number; lng?: number }>({});

  const loadFacilities = async (lat?: number, lng?: number) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await getNearbyHospitals(lat, lng);
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load medical facilities');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Attempt auto-location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          loadFacilities(pos.coords.latitude, pos.coords.longitude);
        },
        () => {
          // Default reference coordinates (San Francisco)
          loadFacilities();
        },
        { timeout: 5000 }
      );
    } else {
      loadFacilities();
    }
  }, []);

  const handleRefreshLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          loadFacilities(pos.coords.latitude, pos.coords.longitude);
        },
        () => {
          loadFacilities();
        }
      );
    } else {
      loadFacilities();
    }
  };

  const filteredFacilities = (data?.facilities || []).filter((f) => {
    const matchesSearch = f.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          f.address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || (filterType === 'emergency_only' && f.has_emergency_room);
    return matchesSearch && matchesType;
  });

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Hospital className="w-6 h-6 text-medic-teal" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Nearby Medical Facilities</h1>
          </div>
          <p className="text-xs text-slate-400">
            Authoritative hospital and trauma directory powered by OpenStreetMap healthcare registry.
          </p>
        </div>

        <button
          onClick={handleRefreshLocation}
          disabled={isLoading}
          className="px-4 py-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700 text-xs font-bold flex items-center gap-2 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-medic-teal' : ''}`} />
          <span>Refresh GPS</span>
        </button>
      </div>

      {/* Real-time Status Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-navy-900 border border-navy-800 text-xs text-slate-300 flex items-start gap-3">
        <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold text-white block">Facility Real-Time Disclaimer:</span>
          <p className="text-slate-400">
            Real-time emergency department wait times, bed availability, and specialized physician coverage cannot be verified via public automated feeds. Always call the facility directly or contact 911 / 112 for critical ambulance triage.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-navy-900 border border-navy-800 rounded-2xl p-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search facility name, trauma center, or street..."
            className="w-full bg-navy-950 border border-navy-700 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-medic-teal"
          />
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilterType('all')}
            className={`px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
              filterType === 'all'
                ? 'bg-medic-teal text-navy-950'
                : 'bg-navy-950 text-slate-400 hover:text-white'
            }`}
          >
            All Facilities ({data?.facilities.length || 0})
          </button>

          <button
            onClick={() => setFilterType('emergency_only')}
            className={`px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
              filterType === 'emergency_only'
                ? 'bg-emergency-600 text-white'
                : 'bg-navy-950 text-slate-400 hover:text-white'
            }`}
          >
            Emergency ER Only
          </button>
        </div>
      </div>

      {/* Facilities Grid */}
      {isLoading ? (
        <div className="text-center py-16 space-y-3">
          <div className="w-8 h-8 border-2 border-medic-teal/20 border-t-medic-teal rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-medium">Querying nearby hospitals & trauma centers...</p>
        </div>
      ) : errorMsg ? (
        <div className="p-6 rounded-2xl bg-emergency-950/40 border border-emergency-500/30 text-center text-xs text-emergency-400">
          {errorMsg}
        </div>
      ) : filteredFacilities.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-navy-900 border border-navy-800 rounded-2xl">
          No medical facilities matched your query.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredFacilities.map((facility) => (
            <HospitalCard key={facility.id} facility={facility} />
          ))}
        </div>
      )}

    </div>
  );
};
