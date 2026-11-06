import React, { useState, useEffect, useRef } from 'react';
import { 
  HospitalSearchResponse, MedicalFacility, ChennaiPreset, ReverseGeocodeResponse 
} from '../types';
import { 
  getNearbyHospitals, reverseGeocodeLocation, getChennaiPresets 
} from '../services/api';
import { HospitalCard } from '../components/HospitalCard';
import { HospitalMap } from '../components/HospitalMap';
import { 
  MapPin, Search, Navigation, AlertCircle, RefreshCw, Hospital, 
  Filter, PhoneCall, ShieldAlert, CheckCircle2, Clock, Crosshair, 
  Map, List, Compass, ChevronDown, ExternalLink
} from 'lucide-react';

export const HospitalFinderView: React.FC = () => {
  const [data, setData] = useState<HospitalSearchResponse | null>(null);
  const [facilities, setFacilities] = useState<MedicalFacility[]>([]);
  const [selectedFacility, setSelectedFacility] = useState<MedicalFacility | null>(null);
  const [chennaiPresets, setChennaiPresets] = useState<ChennaiPreset[]>([]);
  
  // Geolocation & Status
  const [gpsStatus, setGpsStatus] = useState<'idle' | 'detecting' | 'granted' | 'denied' | 'timeout' | 'unavailable'>('detecting');
  const [locationType, setLocationType] = useState<'gps' | 'manual'>('gps');
  const [coords, setCoords] = useState<{ lat?: number; lng?: number }>({});
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [localityName, setLocalityName] = useState<string>('Detecting locality...');
  const [fullAddress, setFullAddress] = useState<string>('');

  // Filters & Controls
  const [searchRadiusKm, setSearchRadiusKm] = useState<number>(5.0);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filterType, setFilterType] = useState<'all' | 'emergency_only' | 'has_phone'>('all');
  const [sortBy, setSortBy] = useState<'distance' | 'travel_time' | 'rating'>('distance');
  const [viewMode, setViewMode] = useState<'split' | 'map' | 'list'>('split');
  const [showPresetsMenu, setShowPresetsMenu] = useState<boolean>(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load presets on mount
  useEffect(() => {
    getChennaiPresets()
      .then(setChennaiPresets)
      .catch((err) => console.error('Failed to load presets:', err));
  }, []);

  // Primary Facility Discovery Function
  const loadFacilities = async (
    lat?: number, 
    lng?: number, 
    radius: number = searchRadiusKm,
    sort: string = sortBy,
    filter: string = filterType
  ) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await getNearbyHospitals({
        lat,
        lng,
        radius_km: radius,
        sort_by: sort,
        filter_type: filter
      });
      setData(res);
      setFacilities(res.facilities);
      if (res.facilities.length > 0 && !selectedFacility) {
        setSelectedFacility(res.facilities[0]);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to query medical facilities.');
      setFacilities([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Browser Geolocation Detection
  const requestGpsLocation = () => {
    setGpsStatus('detecting');
    setLocationType('gps');
    setErrorMsg(null);

    if (!navigator.geolocation) {
      setGpsStatus('unavailable');
      setErrorMsg('Geolocation is not supported by your browser. Please select a demonstration locality below.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        const acc = pos.coords.accuracy;

        setCoords({ lat, lng });
        setAccuracy(acc);
        setGpsStatus('granted');
        setLastUpdated(new Date().toLocaleTimeString());

        // Reverse geocode to get human-readable locality
        try {
          const geo = await reverseGeocodeLocation(lat, lng);
          setLocalityName(geo.locality || 'Current Location');
          setFullAddress(geo.formatted_address || `${lat.toFixed(4)}, ${lng.toFixed(4)}`);
        } catch (e) {
          setLocalityName(`${lat.toFixed(3)}, ${lng.toFixed(3)}`);
          setFullAddress(`Near coordinates ${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E`);
        }

        loadFacilities(lat, lng, searchRadiusKm, sortBy, filterType);
      },
      (err) => {
        console.warn('Geolocation error:', err.code, err.message);
        if (err.code === err.PERMISSION_DENIED) {
          setGpsStatus('denied');
        } else if (err.code === err.TIMEOUT) {
          setGpsStatus('timeout');
        } else {
          setGpsStatus('unavailable');
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  };

  // Initial trigger
  useEffect(() => {
    requestGpsLocation();
  }, []);

  // Manual Locality Selection (e.g. Chennai presets or user selection)
  const handleSelectPreset = async (preset: ChennaiPreset) => {
    setLocationType('manual');
    setGpsStatus('idle');
    setCoords({ lat: preset.latitude, lng: preset.longitude });
    setAccuracy(null);
    setLocalityName(preset.locality);
    setFullAddress(`${preset.locality}, Tamil Nadu, India`);
    setLastUpdated(new Date().toLocaleTimeString());
    setShowPresetsMenu(false);

    loadFacilities(preset.latitude, preset.longitude, searchRadiusKm, sortBy, filterType);
  };

  // Radius change handler
  const handleRadiusChange = (newRadius: number) => {
    setSearchRadiusKm(newRadius);
    if (coords.lat !== undefined && coords.lng !== undefined) {
      loadFacilities(coords.lat, coords.lng, newRadius, sortBy, filterType);
    }
  };

  // Sort change handler
  const handleSortChange = (newSort: 'distance' | 'travel_time' | 'rating') => {
    setSortBy(newSort);
    if (coords.lat !== undefined && coords.lng !== undefined) {
      loadFacilities(coords.lat, coords.lng, searchRadiusKm, newSort, filterType);
    }
  };

  // Filter change handler
  const handleFilterChange = (newFilter: 'all' | 'emergency_only' | 'has_phone') => {
    setFilterType(newFilter);
    if (coords.lat !== undefined && coords.lng !== undefined) {
      loadFacilities(coords.lat, coords.lng, searchRadiusKm, sortBy, newFilter);
    }
  };

  // Filter facilities by in-memory text search
  const filteredFacilities = facilities.filter((f) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return f.name.toLowerCase().includes(term) || f.address.toLowerCase().includes(term);
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      
      {/* Top Header & Emergency 112 Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Hospital className="w-6 h-6 text-medic-teal" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Real-Time Hospital Discovery
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Real GPS-driven medical facility locator with road distances, driving times, and direct navigation.
          </p>
        </div>

        {/* Immediate 112 Call Option */}
        <div className="flex items-center gap-3">
          <a
            href="tel:112"
            className="px-5 py-2.5 rounded-xl bg-emergency-600 hover:bg-emergency-500 text-white font-black text-xs flex items-center gap-2 shadow-lg shadow-emergency-600/30 transition-all shrink-0 animate-pulse"
          >
            <PhoneCall className="w-4 h-4" />
            <span>Call 112 (Emergency)</span>
          </a>

          <button
            onClick={requestGpsLocation}
            disabled={isLoading || gpsStatus === 'detecting'}
            className="px-3.5 py-2.5 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700 text-xs font-bold flex items-center gap-2 transition-colors"
            title="Refresh GPS coordinates"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${gpsStatus === 'detecting' || isLoading ? 'animate-spin text-medic-teal' : ''}`} />
            <span className="hidden sm:inline">Refresh GPS</span>
          </button>
        </div>
      </div>

      {/* Prominent Emergency Safety Disclaimer */}
      <div className="p-4 rounded-2xl bg-emergency-950/40 border border-emergency-500/30 text-xs text-emergency-200 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-emergency-500 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-bold text-white block">Medical Emergency Capacity Notice:</span>
          <p className="text-[11px] text-emergency-300 leading-relaxed">
            Hospital location information does not guarantee emergency department availability, open beds, or treatment capacity. Call the hospital or emergency services (112) to confirm. In acute life-or-death situations, immediately call 112 for ambulance transport.
          </p>
        </div>
      </div>

      {/* Current Location & GPS Accuracy Card */}
      <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 space-y-4 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-medic-teal/10 border border-medic-teal/30 text-medic-teal">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-400">Your Current Location</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                  locationType === 'gps'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}>
                  {locationType === 'gps' ? 'Live GPS Detected' : 'Manual Locality Selection'}
                </span>
              </div>
              <h3 className="text-base font-extrabold text-white mt-0.5">{localityName}</h3>
              {fullAddress && <p className="text-xs text-slate-400 leading-snug">{fullAddress}</p>}
            </div>
          </div>

          {/* Coordinate & Accuracy Details */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {coords.lat !== undefined && coords.lng !== undefined && (
              <div className="px-3 py-1.5 rounded-xl bg-navy-950 border border-navy-800 font-mono text-[11px] text-slate-300">
                {coords.lat.toFixed(4)}° N, {coords.lng.toFixed(4)}° E
                {accuracy !== null && (
                  <span className="text-medic-teal ml-1.5 font-bold">(&plusmn;{Math.round(accuracy)}m)</span>
                )}
              </div>
            )}

            {lastUpdated && (
              <span className="text-[10px] text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {lastUpdated}
              </span>
            )}
          </div>
        </div>

        {/* GPS Permission Denied / Error Banner with Demonstration Fallback Buttons */}
        {(gpsStatus === 'denied' || gpsStatus === 'timeout' || gpsStatus === 'unavailable') && (
          <div className="p-4 rounded-xl bg-amber-950/50 border border-amber-500/40 text-xs space-y-3">
            <div className="flex items-center gap-2 text-amber-300 font-bold">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                {gpsStatus === 'denied' 
                  ? 'Location Access Denied in Browser' 
                  : 'GPS Location Timed Out or Unavailable'}
              </span>
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              We never silently fabricate a fake location. To view real nearby hospitals, enable GPS permission in your browser or select a demonstration locality below:
            </p>

            {/* Quick Chennai Locality Preset Chips */}
            <div className="flex flex-wrap gap-2 pt-1">
              {chennaiPresets.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => handleSelectPreset(preset)}
                  className="px-3 py-1.5 rounded-lg bg-navy-900 hover:bg-navy-800 text-slate-200 border border-navy-700 text-xs font-semibold transition-colors flex items-center gap-1"
                >
                  <MapPin className="w-3 h-3 text-medic-teal" />
                  <span>{preset.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Locality Selector Dropdown for Demonstration */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-navy-800 text-xs">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-slate-400" />
            <span className="text-slate-400">Chennai Demonstration Presets:</span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            {['Adyar', 'Guindy', 'Tambaram', 'Velachery', 'Anna Nagar', 'OMR'].map((name) => {
              const p = chennaiPresets.find((item) => item.name === name);
              if (!p) return null;
              const isSelected = localityName.includes(name);
              return (
                <button
                  key={name}
                  onClick={() => handleSelectPreset(p)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                    isSelected 
                      ? 'bg-medic-teal text-navy-950 shadow'
                      : 'bg-navy-950 text-slate-400 hover:text-white border border-navy-800'
                  }`}
                >
                  {name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Search, Filter, Radius & View Controls Bar */}
      <div className="bg-navy-900 border border-navy-800 rounded-2xl p-4 space-y-3 shadow-lg">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Text Search */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search hospital name, trauma center, or street..."
              className="w-full bg-navy-950 border border-navy-700 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-medic-teal"
            />
          </div>

          {/* Search Radius Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-bold hidden sm:inline">Radius:</span>
            {[3, 5, 10, 20].map((r) => (
              <button
                key={r}
                onClick={() => handleRadiusChange(r)}
                className={`px-3 py-2 rounded-xl text-xs font-bold transition-all ${
                  searchRadiusKm === r
                    ? 'bg-medic-teal text-navy-950 shadow-md'
                    : 'bg-navy-950 text-slate-400 hover:text-white border border-navy-800'
                }`}
              >
                {r} km
              </button>
            ))}
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center bg-navy-950 p-1 rounded-xl border border-navy-800">
            <button
              onClick={() => setViewMode('split')}
              className={`p-1.5 rounded-lg text-xs transition-colors ${
                viewMode === 'split' ? 'bg-navy-800 text-medic-teal' : 'text-slate-400 hover:text-white'
              }`}
              title="Split View (Map + Cards)"
            >
              <span className="font-bold px-1">Split</span>
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`p-1.5 rounded-lg text-xs transition-colors ${
                viewMode === 'map' ? 'bg-navy-800 text-medic-teal' : 'text-slate-400 hover:text-white'
              }`}
              title="Map View Only"
            >
              <Map className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg text-xs transition-colors ${
                viewMode === 'list' ? 'bg-navy-800 text-medic-teal' : 'text-slate-400 hover:text-white'
              }`}
              title="List View Only"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter Pills & Sorting */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-navy-800 text-xs">
          {/* Filters */}
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-500 mr-1" />
            <button
              onClick={() => handleFilterChange('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                filterType === 'all'
                  ? 'bg-navy-800 text-white border border-navy-700'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              All Facilities ({facilities.length})
            </button>

            <button
              onClick={() => handleFilterChange('emergency_only')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                filterType === 'emergency_only'
                  ? 'bg-emergency-600/30 text-emergency-400 border border-emergency-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Emergency ER Only
            </button>

            <button
              onClick={() => handleFilterChange('has_phone')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                filterType === 'has_phone'
                  ? 'bg-emerald-600/30 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              With Contact Phone
            </button>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-2">
            <span className="text-slate-500 text-[11px]">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value as any)}
              className="px-2.5 py-1 rounded-lg bg-navy-950 border border-navy-800 text-slate-200 text-xs focus:outline-none focus:border-medic-teal"
            >
              <option value="distance">Road Distance</option>
              <option value="travel_time">Fastest Travel Time</option>
              <option value="rating">Highest Rated</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Interactive Map & Facilities Display */}
      {isLoading ? (
        <div className="text-center py-20 space-y-3 bg-navy-900 border border-navy-800 rounded-3xl">
          <div className="w-10 h-10 border-2 border-medic-teal/20 border-t-medic-teal rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-semibold">
            Querying Google Places & Routes APIs for verified hospitals within {searchRadiusKm} km...
          </p>
        </div>
      ) : errorMsg ? (
        <div className="p-8 rounded-3xl bg-emergency-950/40 border border-emergency-500/30 text-center text-xs text-emergency-400 space-y-3">
          <p className="font-bold">{errorMsg}</p>
          {data?.google_maps_search_url && (
            <a
              href={data.google_maps_search_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emergency-600 text-white font-bold text-xs"
            >
              <span>Search on Google Maps Directly</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {/* Interactive Map (Shown in 'split' or 'map' view) */}
          {(viewMode === 'split' || viewMode === 'map') && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span className="font-bold text-white flex items-center gap-1.5">
                  <Map className="w-4 h-4 text-medic-teal" />
                  <span>Interactive Hospital Navigation Map</span>
                </span>
                <span className="font-mono text-[11px] text-slate-400">
                  {filteredFacilities.length} facilities plotted
                </span>
              </div>

              <HospitalMap
                userLat={coords.lat}
                userLng={coords.lng}
                userAccuracy={accuracy}
                facilities={filteredFacilities}
                selectedFacility={selectedFacility}
                onSelectFacility={(fac) => setSelectedFacility(fac)}
                radiusKm={searchRadiusKm}
              />
            </div>
          )}

          {/* Facilities Cards Grid (Shown in 'split' or 'list' view) */}
          {(viewMode === 'split' || viewMode === 'list') && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span className="font-bold text-white flex items-center gap-1.5">
                  <Hospital className="w-4 h-4 text-medic-teal" />
                  <span>Verified Medical Facilities ({filteredFacilities.length})</span>
                </span>
                <span className="text-[11px] text-slate-400">
                  Provider: <strong className="text-slate-300">{data?.data_provider || 'Google Places API'}</strong>
                </span>
              </div>

              {filteredFacilities.length === 0 ? (
                <div className="p-12 text-center text-xs text-slate-400 bg-navy-900 border border-navy-800 rounded-3xl space-y-3">
                  <p className="font-bold text-white">No medical facilities found within {searchRadiusKm} km.</p>
                  <p className="text-slate-500 max-w-md mx-auto text-[11px]">
                    Try expanding the search radius to 10 km or 20 km, or search on Google Maps directly.
                  </p>
                  <div className="flex justify-center gap-2 pt-2">
                    <button
                      onClick={() => handleRadiusChange(10)}
                      className="px-3 py-1.5 rounded-xl bg-navy-800 hover:bg-navy-700 text-medic-teal font-bold text-xs"
                    >
                      Expand to 10 km
                    </button>
                    {data?.google_maps_search_url && (
                      <a
                        href={data.google_maps_search_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-xl bg-medic-teal text-navy-950 font-black text-xs inline-flex items-center gap-1"
                      >
                        <span>Open Google Maps</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {filteredFacilities.map((facility, idx) => (
                    <HospitalCard
                      key={facility.id}
                      facility={facility}
                      index={idx}
                      isSelected={selectedFacility?.id === facility.id}
                      onFocusOnMap={() => {
                        setSelectedFacility(facility);
                        if (viewMode === 'list') setViewMode('split');
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Attribution & Legal Notice */}
      <div className="p-4 rounded-2xl bg-navy-950 border border-navy-800 text-[11px] text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
        <div>
          <div className="flex flex-wrap items-center gap-2 justify-center sm:justify-start">
            <span className="font-bold text-slate-400">{data?.provider_attribution || 'Map data © OpenStreetMap contributors'}</span>
            {data?.osm_api_key_configured && (
              <span className="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60 text-[10px] font-bold">
                OSM API Key Active
              </span>
            )}
          </div>
          <p className="text-[10px] text-slate-600 mt-0.5">
            Geospatial coordinates & facility records powered by OpenStreetMap & Healthcare Registries.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {data?.osm_search_url && (
            <a
              href={data.osm_search_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 hover:underline flex items-center gap-1 font-bold text-xs"
            >
              <span>Explore on OpenStreetMap</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
          {data?.google_maps_search_url && (
            <a
              href={data.google_maps_search_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-medic-teal hover:underline flex items-center gap-1 font-bold text-xs"
            >
              <span>Google Maps</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>

    </div>
  );
};
