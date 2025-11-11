import { MapContainer, TileLayer, Polyline, Marker, Popup } from "react-leaflet";

export default function MapPanel({ polyline, center, originLabel="Start", destLabel="End", height=240 }) {
  if (!polyline || polyline.length === 0) return null;
  const mid = center || polyline[Math.floor(polyline.length / 2)];

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden", marginTop: 8 }}>
      <MapContainer center={mid} zoom={14} style={{ height, width: "100%" }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={polyline} />
        <Marker position={polyline[0]}><Popup>{originLabel}</Popup></Marker>
        <Marker position={polyline[polyline.length - 1]}><Popup>{destLabel}</Popup></Marker>
      </MapContainer>
    </div>
  );
}
