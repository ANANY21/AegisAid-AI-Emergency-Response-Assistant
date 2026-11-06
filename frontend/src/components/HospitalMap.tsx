import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { MedicalFacility } from '../types';
import { ExternalLink, Navigation, Crosshair } from 'lucide-react';

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
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const routeLayerRef = useRef<L.Polyline | null>(null);
  const userMarkerRef = useRef<L.Marker | null>(null);
  const accuracyCircleRef = useRef<L.Circle | null>(null);

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

      // CartoDB Dark Matter tile layer for premium medical navy theme
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(map);

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
          <div style="color: #0d9488; margin-bottom: 2px;">Your Current Location</div>
          <div style="font-size: 10px; color: #64748b; font-weight: normal;">
            ${userAccuracy ? `Accuracy: ±${Math.round(userAccuracy)}m` : 'GPS Position'}
          </div>
        </div>
      `)
      .addTo(map);

    if (userAccuracy && userAccuracy > 15) {
      accuracyCircleRef.current = L.circle([userLat, userLng], {
        radius: userAccuracy,
        color: '#0d9488',
        fillColor: '#0d9488',
        fillOpacity: 0.08,
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

    const bounds = L.latLngBounds([]);
    if (userLat !== undefined && userLng !== undefined) {
      bounds.extend([userLat, userLng]);
    }

    facilities.forEach((fac, idx) => {
      const isSelected = selectedFacility?.id === fac.id;
      const isER = fac.has_emergency_room;

      bounds.extend([fac.latitude, fac.longitude]);

      const markerColor = isSelected ? '#e11d48' : (isER ? '#dc2626' : '#0284c7');
      const markerSize = isSelected ? 34 : 28;

      const hospitalIcon = L.divIcon({
        className: 'custom-hospital-marker',
        html: `
          <div style="
            position: relative; 
            width: ${markerSize}px; 
            height: ${markerSize}px; 
            border-radius: 50%; 
            background: ${markerColor}; 
            color: #ffffff; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: ${isSelected ? '12px' : '11px'}; 
            font-weight: 800; 
            border: 2px solid #ffffff; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            cursor: pointer;
            transition: transform 0.2s;
            ${isSelected ? 'transform: scale(1.15);' : ''}
          ">
            ${idx + 1}
          </div>
        `,
        iconSize: [markerSize, markerSize],
        iconAnchor: [markerSize / 2, markerSize / 2],
      });

      const marker = L.marker([fac.latitude, fac.longitude], { icon: hospitalIcon })
        .bindPopup(`
          <div style="font-family: sans-serif; font-size: 12px; color: #0f172a; max-width: 220px;">
            <div style="font-weight: 800; font-size: 13px; margin-bottom: 2px;">
              [#${idx + 1}] ${fac.name}
            </div>
            <div style="font-size: 11px; color: #475569; margin-bottom: 4px;">
              ${fac.address}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; border-top: 1px solid #e2e8f0; padding-top: 4px;">
              <span style="font-weight: bold; color: #0d9488;">
                ${fac.road_distance_km ? `${fac.road_distance_km} km (road)` : `${fac.distance_km} km`}
              </span>
              ${fac.driving_duration_text ? `<span style="color: #64748b;">${fac.driving_duration_text}</span>` : ''}
            </div>
            ${fac.phone ? `<div style="font-size: 10px; color: #2563eb; margin-top: 3px;">Tel: ${fac.phone}</div>` : ''}
          </div>
        `);

      marker.on('click', () => {
        onSelectFacility(fac);
      });

      markersLayer.addLayer(marker);
    });

    // Auto-fit bounds if facilities present and not focused on specific selection
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

      // Draw dashed trajectory line between user and selected hospital
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

  return (
    <div className="relative w-full h-[400px] sm:h-[480px] rounded-2xl overflow-hidden border border-navy-700 shadow-xl bg-navy-950">
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Floating Center on User Button */}
      {userLat !== undefined && userLng !== undefined && (
        <button
          onClick={handleCenterUser}
          className="absolute top-3 right-3 z-10 p-2.5 rounded-xl bg-navy-900/90 hover:bg-navy-800 text-medic-teal border border-navy-700 shadow-lg backdrop-blur-sm transition-all"
          title="Recenter on current location"
        >
          <Crosshair className="w-4 h-4" />
        </button>
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
