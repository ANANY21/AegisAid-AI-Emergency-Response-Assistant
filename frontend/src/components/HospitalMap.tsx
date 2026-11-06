import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { MedicalFacility } from '../types';
import { ExternalLink, Navigation, Crosshair, Layers, Key, Check, ShieldCheck } from 'lucide-react';

interface HospitalMapProps {
  userLat?: number;
  userLng?: number;
  userAccuracy?: number | null;
  facilities: MedicalFacility[];
  selectedFacility: MedicalFacility | null;
  onSelectFacility: (facility: MedicalFacility) => void;
  radiusKm?: number;
}

export const HospitalMap: React.FC<HospitalMapProps> = ({
  userLat,
  userLng,
  userAccuracy,
  facilities,
  selectedFacility,
  onSelectFacility,
  radiusKm = 5,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const currentTileLayerRef = useRef<L.TileLayer | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const routeLayerRef = useRef<L.Polyline | null>(null);
  const userMarkerRef = useRef<L.Marker | null>(null);
  const accuracyCircleRef = useRef<L.Circle | null>(null);

  // OpenStreetMap Tile & API Key State
  const [osmApiKey, setOsmApiKey] = useState<string>(() => {
    return localStorage.getItem('aegisaid_osm_api_key') || ((import.meta as any).env?.VITE_OSM_API_KEY as string) || '';
  });
  const [tileStyle, setTileStyle] = useState<'osm-standard' | 'osm-navy' | 'osm-key'>(() => {
    const saved = localStorage.getItem('aegisaid_osm_style');
    return (saved as any) || 'osm-standard';
  });
  const [showSettings, setShowSettings] = useState(false);
  const [keySavedMessage, setKeySavedMessage] = useState(false);

  // Helper to get tile configuration based on style and OSM API key
  const getTileConfig = (style: 'osm-standard' | 'osm-navy' | 'osm-key', key: string) => {
    const trimmedKey = key.trim();
    if (style === 'osm-key' && trimmedKey) {
      // 1. LocationIQ OSM Tiles (starts with pk.)
      if (trimmedKey.startsWith('pk.')) {
        return {
          url: `https://{s}-tiles.locationiq.com/v3/streets/r/{z}/{x}/{y}.png?key=${trimmedKey}`,
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://locationiq.com/">LocationIQ</a>',
          subdomains: 'abc',
        };
      }
      // 2. Thunderforest OSM Tiles
      if (trimmedKey.length === 32) {
        return {
          url: `https://tile.thunderforest.com/transport/{z}/{x}/{y}.png?apikey=${trimmedKey}`,
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://www.thunderforest.com/">Thunderforest</a>',
          subdomains: 'abc',
        };
      }
      // 3. Generic Geoapify / Stadia OSM tile with API Key
      return {
        url: `https://maps.geoapify.com/v1/tile/osm-carto/{z}/{x}/{y}.png?apiKey=${trimmedKey}`,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; Geoapify',
        subdomains: 'abc',
      };
    }

    if (style === 'osm-navy') {
      return {
        url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
      };
    }

    // Default: Official OpenStreetMap Standard Tiles
    return {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      subdomains: 'abc',
    };
  };

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const initialLat = userLat || 13.0012;
      const initialLng = userLng || 80.2565;

      const map = L.map(mapContainerRef.current, {
        center: [initialLat, initialLng],
        zoom: 13,
        zoomControl: true,
      });

      const config = getTileConfig(tileStyle, osmApiKey);
      const tileLayer = L.tileLayer(config.url, {
        attribution: config.attribution,
        subdomains: config.subdomains,
        maxZoom: 19,
      }).addTo(map);

      currentTileLayerRef.current = tileLayer;
      markersLayerRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Tile Layer when tileStyle or osmApiKey changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (currentTileLayerRef.current) {
      map.removeLayer(currentTileLayerRef.current);
    }

    const config = getTileConfig(tileStyle, osmApiKey);
    const newLayer = L.tileLayer(config.url, {
      attribution: config.attribution,
      subdomains: config.subdomains,
      maxZoom: 19,
    }).addTo(map);

    currentTileLayerRef.current = newLayer;
  }, [tileStyle, osmApiKey]);

  // Update User Location Marker & Accuracy Circle
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || userLat === undefined || userLng === undefined) return;

    if (userMarkerRef.current) {
      userMarkerRef.current.remove();
    }
    if (accuracyCircleRef.current) {
      accuracyCircleRef.current.remove();
    }

    // Custom pulsing user location icon
    const userIcon = L.divIcon({
      className: 'custom-user-marker',
      html: `
        <div style="position: relative; width: 22px; height: 22px;">
          <div style="position: absolute; width: 22px; height: 22px; border-radius: 50%; background: rgba(13, 148, 136, 0.35); animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
          <div style="position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; border-radius: 50%; background: #0d9488; border: 2.5px solid #ffffff; box-shadow: 0 0 10px rgba(13, 148, 136, 0.8);"></div>
        </div>
      `,
      iconSize: [22, 22],
      iconAnchor: [11, 11],
    });

    userMarkerRef.current = L.marker([userLat, userLng], { icon: userIcon })
      .bindPopup(`
        <div style="font-family: sans-serif; font-size: 12px; font-weight: bold; color: #0f172a;">
          <div style="color: #0d9488; margin-bottom: 2px;">Your Current GPS Position</div>
          <div style="font-size: 10px; color: #64748b; font-weight: normal;">
            ${userAccuracy ? `Accuracy: ±${Math.round(userAccuracy)}m` : 'GPS Position'}
          </div>
        </div>
      `)
      .addTo(map);

    if (userAccuracy && userAccuracy > 0 && userAccuracy < 2000) {
      accuracyCircleRef.current = L.circle([userLat, userLng], {
        radius: userAccuracy,
        color: '#0d9488',
        fillColor: '#0d9488',
        fillOpacity: 0.1,
        weight: 1,
      }).addTo(map);
    }
  }, [userLat, userLng, userAccuracy]);

  // Update Hospital Markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();

    if (facilities.length === 0) return;

    const bounds = L.latLngBounds([]);
    if (userLat !== undefined && userLng !== undefined) {
      bounds.extend([userLat, userLng]);
    }

    facilities.forEach((fac, index) => {
      bounds.extend([fac.latitude, fac.longitude]);

      const isSelected = selectedFacility?.id === fac.id;
      const hasEr = fac.has_emergency_room;
      const markerBg = hasEr ? '#dc2626' : '#0284c7';
      const borderCol = isSelected ? '#fbbf24' : '#ffffff';
      const scale = isSelected ? 'scale(1.25)' : 'scale(1)';

      const markerHtml = `
        <div style="
          transform: ${scale};
          transition: transform 0.2s ease;
          background: ${markerBg};
          color: white;
          width: 26px;
          height: 26px;
          border-radius: 50%;
          border: 2.5px solid ${borderCol};
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 11px;
          box-shadow: 0 4px 10px rgba(0,0,0,0.5);
          cursor: pointer;
        ">
          ${index + 1}
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-hospital-marker',
        html: markerHtml,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });

      const osmRouteUrl = fac.osm_directions_url || `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${userLat}%2C${userLng}%3B${fac.latitude}%2C${fac.longitude}`;

      const popupHtml = `
        <div style="font-family: sans-serif; font-size: 12px; color: #0f172a; min-width: 190px;">
          <div style="font-weight: 800; font-size: 13px; color: #0f172a; margin-bottom: 3px;">
            ${index + 1}. ${fac.name}
          </div>
          <div style="font-size: 11px; color: #475569; margin-bottom: 6px;">
            ${fac.address || 'Address registered in directory'}
          </div>
          <div style="display: flex; gap: 6px; font-size: 11px; margin-bottom: 8px;">
            <span style="font-weight: bold; color: #0d9488;">${fac.distance_km} km</span>
            ${fac.driving_duration_text ? `<span style="color: #64748b;">• ${fac.driving_duration_text}</span>` : ''}
            ${hasEr ? '<span style="background: #fee2e2; color: #b91c1c; padding: 1px 4px; border-radius: 4px; font-weight: bold; font-size: 10px;">24/7 ER</span>' : ''}
          </div>
          <div style="display: flex; gap: 8px; margin-top: 6px;">
            <a href="${osmRouteUrl}" target="_blank" rel="noopener noreferrer" style="color: #059669; font-weight: bold; text-decoration: underline; font-size: 11px;">
              OpenStreetMap Route →
            </a>
          </div>
        </div>
      `;

      const marker = L.marker([fac.latitude, fac.longitude], { icon: customIcon })
        .bindPopup(popupHtml);

      marker.on('click', () => {
        onSelectFacility(fac);
      });

      markersLayer.addLayer(marker);
    });

    if (!selectedFacility && facilities.length > 0 && map) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    }
  }, [facilities, selectedFacility]);

  // Center on Selected Facility & Draw Trajectory Line
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (routeLayerRef.current) {
      routeLayerRef.current.remove();
      routeLayerRef.current = null;
    }

    if (selectedFacility) {
      map.flyTo([selectedFacility.latitude, selectedFacility.longitude], 15, {
        duration: 0.8,
      });

      if (userLat !== undefined && userLng !== undefined) {
        routeLayerRef.current = L.polyline(
          [
            [userLat, userLng],
            [selectedFacility.latitude, selectedFacility.longitude],
          ],
          {
            color: '#0d9488',
            weight: 3.5,
            opacity: 0.85,
            dashArray: '6, 8',
          }
        ).addTo(map);
      }
    }
  }, [selectedFacility, userLat, userLng]);

  const handleCenterUser = () => {
    if (mapInstanceRef.current && userLat !== undefined && userLng !== undefined) {
      mapInstanceRef.current.flyTo([userLat, userLng], 14, { duration: 0.8 });
    }
  };

  const handleSaveOsmApiKey = (newKey: string) => {
    setOsmApiKey(newKey);
    localStorage.setItem('aegisaid_osm_api_key', newKey);
    if (newKey.trim()) {
      setTileStyle('osm-key');
      localStorage.setItem('aegisaid_osm_style', 'osm-key');
    }
    setKeySavedMessage(true);
    setTimeout(() => setKeySavedMessage(false), 2500);
  };

  return (
    <div className="relative w-full h-[400px] sm:h-[480px] rounded-2xl overflow-hidden border border-navy-700 shadow-xl bg-navy-950">
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Floating Action Buttons */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
        {/* OpenStreetMap Layer & Key Settings */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          className={`p-2.5 rounded-xl border shadow-lg backdrop-blur-sm transition-all flex items-center gap-1.5 text-xs font-bold ${
            osmApiKey.trim()
              ? 'bg-emerald-950/90 text-emerald-300 border-emerald-600/50'
              : 'bg-navy-900/90 text-slate-300 border-navy-700 hover:bg-navy-800'
          }`}
          title="OpenStreetMap layer and API key settings"
        >
          <Layers className="w-4 h-4 text-medic-teal" />
          <span className="hidden sm:inline">OSM Map</span>
          {osmApiKey.trim() && <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />}
        </button>

        {/* Center on User */}
        {userLat !== undefined && userLng !== undefined && (
          <button
            onClick={handleCenterUser}
            className="p-2.5 rounded-xl bg-navy-900/90 hover:bg-navy-800 text-medic-teal border border-navy-700 shadow-lg backdrop-blur-sm transition-all"
            title="Recenter on current GPS location"
          >
            <Crosshair className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* OpenStreetMap Configuration Modal Overlay */}
      {showSettings && (
        <div className="absolute top-14 right-3 z-20 w-80 sm:w-96 p-4 rounded-2xl bg-navy-900/95 border border-navy-700 shadow-2xl backdrop-blur-md text-xs text-slate-300 space-y-3 animate-fadeIn">
          <div className="flex items-center justify-between pb-2 border-b border-navy-800">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-medic-teal" />
              <span className="font-bold text-white text-sm">OpenStreetMap Settings</span>
            </div>
            <button
              onClick={() => setShowSettings(false)}
              className="text-slate-400 hover:text-white p-1 text-sm font-bold"
            >
              ✕
            </button>
          </div>

          {/* Tile Style Picker */}
          <div>
            <label className="block text-[11px] font-bold text-slate-400 mb-1.5">MAP TILE SOURCE</label>
            <div className="grid grid-cols-3 gap-1.5">
              <button
                onClick={() => {
                  setTileStyle('osm-standard');
                  localStorage.setItem('aegisaid_osm_style', 'osm-standard');
                }}
                className={`py-1.5 px-2 rounded-lg text-center font-bold text-[11px] border transition-all ${
                  tileStyle === 'osm-standard'
                    ? 'bg-medic-teal/20 text-medic-teal border-medic-teal/60'
                    : 'bg-navy-950 text-slate-400 border-navy-800 hover:text-slate-200'
                }`}
              >
                OSM Standard
              </button>
              <button
                onClick={() => {
                  setTileStyle('osm-navy');
                  localStorage.setItem('aegisaid_osm_style', 'osm-navy');
                }}
                className={`py-1.5 px-2 rounded-lg text-center font-bold text-[11px] border transition-all ${
                  tileStyle === 'osm-navy'
                    ? 'bg-medic-teal/20 text-medic-teal border-medic-teal/60'
                    : 'bg-navy-950 text-slate-400 border-navy-800 hover:text-slate-200'
                }`}
              >
                Medical Navy
              </button>
              <button
                onClick={() => {
                  setTileStyle('osm-key');
                  localStorage.setItem('aegisaid_osm_style', 'osm-key');
                }}
                className={`py-1.5 px-2 rounded-lg text-center font-bold text-[11px] border transition-all ${
                  tileStyle === 'osm-key'
                    ? 'bg-emerald-600/20 text-emerald-400 border-emerald-500/60'
                    : 'bg-navy-950 text-slate-400 border-navy-800 hover:text-slate-200'
                }`}
              >
                OSM API Key
              </button>
            </div>
          </div>

          {/* OpenStreetMap API Key Input */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-bold text-slate-400 flex items-center gap-1">
                <Key className="w-3 h-3 text-amber-400" />
                <span>OPENSTREETMAP API KEY</span>
              </label>
              {keySavedMessage && (
                <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                  <Check className="w-3 h-3" /> Saved!
                </span>
              )}
            </div>
            <div className="flex gap-1.5">
              <input
                type="text"
                value={osmApiKey}
                onChange={(e) => setOsmApiKey(e.target.value)}
                placeholder="Paste OSM / LocationIQ / Geoapify Key..."
                className="flex-1 bg-navy-950 border border-navy-700 rounded-xl px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-medic-teal"
              />
              <button
                onClick={() => handleSaveOsmApiKey(osmApiKey)}
                className="px-3 py-1.5 rounded-xl bg-medic-teal hover:bg-medic-teal-light text-navy-950 font-bold text-xs shrink-0 transition-colors"
              >
                Save
              </button>
            </div>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              Accepts <strong>LocationIQ</strong> (pk.xxx), <strong>Thunderforest</strong>, <strong>Geoapify</strong>, or <strong>Stadia Maps</strong> OSM API keys. Standard OSM tiles work without an API key.
            </p>
          </div>

          <div className="pt-2 border-t border-navy-800 flex items-center justify-between text-[11px] text-slate-400">
            <span className="flex items-center gap-1 text-emerald-400 font-bold">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Map data &copy; OpenStreetMap contributors</span>
            </span>
            <a
              href="https://www.openstreetmap.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-medic-teal hover:underline flex items-center gap-1"
            >
              <span>OSM.org</span>
              <ExternalLink className="w-2.5 h-2.5" />
            </a>
          </div>
        </div>
      )}

      {/* Map Legend Overlay */}
      <div className="absolute bottom-3 left-3 z-10 px-3 py-2 rounded-xl bg-navy-950/90 border border-navy-700 shadow-lg backdrop-blur-md text-[11px] text-slate-300 flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-medic-teal inline-block shadow-sm shadow-medic-teal/50" />
          <span>You</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emergency-600 inline-block" />
          <span>Emergency ER</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-sky-500 inline-block" />
          <span>Clinic</span>
        </div>
        <span className="text-slate-500 font-mono text-[10px]">Radius: {radiusKm} km</span>
      </div>
    </div>
  );
};
