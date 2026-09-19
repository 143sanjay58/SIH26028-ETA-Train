import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip } from 'react-leaflet';
import { Train as TrainIcon } from 'lucide-react';
import type { Station, TrainPosition } from '../../types';

export function RailwayMap({ stations, position }: { stations: Station[]; position?: TrainPosition }) {
  const points = stations.filter((s) => Number.isFinite(s.latitude) && Number.isFinite(s.longitude)).map((s) => ({
    lat: s.latitude,
    lng: s.longitude,
    name: s.name,
    code: s.code,
  }));

  const hasTrain = position && Number.isFinite(position.latitude) && Number.isFinite(position.longitude);
  const routePoints = points.map((p) => [p.lat, p.lng] as [number, number]);

  return (
    <div className="relative h-[320px] sm:h-[400px] w-full rounded-xl overflow-hidden border border-white/[0.06]">
      <MapContainer center={[13.0, 78.5]} zoom={7} scrollWheelZoom={false} className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {routePoints.length > 1 && (
          <Polyline positions={routePoints} pathOptions={{ color: 'rgba(0,212,255,0.45)', weight: 2 }} />
        )}
        {points.map((p, i) => (
          <CircleMarker
            key={i}
            center={[p.lat, p.lng]}
            radius={5}
            pathOptions={{ color: '#00d4ff', fillColor: 'rgba(0,212,255,0.5)', fillOpacity: 0.5, weight: 1 }}
          >
            <Tooltip direction="top" offset={[0, -5]} opacity={1}>
              <span className="text-xs font-medium">{p.name} ({p.code})</span>
            </Tooltip>
          </CircleMarker>
        ))}
        {hasTrain && (
          <CircleMarker
            center={[position!.latitude, position!.longitude]}
            radius={10}
            pathOptions={{ color: '#8b5cf6', fillColor: '#8b5cf6', fillOpacity: 0.9, weight: 2 }}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={1}>
              <span className="text-xs font-semibold">Train Position</span>
            </Tooltip>
          </CircleMarker>
        )}
      </MapContainer>

      {hasTrain && (
        <div className="absolute bottom-3 left-3 inline-flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-surface-200/90 border border-white/10 backdrop-blur-sm">
          <TrainIcon className="h-3.5 w-3.5 text-violet-400" />
          <span className="text-xs font-mono text-gray-200">
            {position!.latitude.toFixed(4)}, {position!.longitude.toFixed(4)}
          </span>
        </div>
      )}
    </div>
  );
}