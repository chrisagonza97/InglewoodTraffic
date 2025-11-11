// src/maps/corridors.js

// Helper to build a simple straight polyline between two points.
// If you want the exact street geometry later, we can replace
// this with a snapped route (would require a routing API).
function straightSegment(lat1, lng1, lat2, lng2, steps = 5) {
    const line = [];
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      line.push([
        lat1 + (lat2 - lat1) * t,
        lng1 + (lng2 - lng1) * t,
      ]);
    }
    return line;
  }
  
  // Build a no-key Google Maps Directions URL for live traffic
  export function directionsUrl(origin, destination) {
    const o = `${origin.lat},${origin.lng}`;
    const d = `${destination.lat},${destination.lng}`;
    return `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(o)}&destination=${encodeURIComponent(d)}&travelmode=driving`;
  }
  
  // NOTE: You had a small copy/paste glitch in the first "from" line.
  // I’m using: (33.945505501340314, -118.35378793108521) → (33.945495096216895, -118.32644419667365)
  
  export const CUSTOM_CORRIDORS = {
    corridorA: {
      label: "Century Blvd (≈ east–west)",
      origin: { lat: 33.945505501340314, lng: -118.35378793108521 },
      destination: { lat: 33.945495096216895, lng: -118.32644419667365 },
      polyline: straightSegment(
        33.945505501340314, -118.35378793108521,
        33.945495096216895, -118.32644419667365,
        12
      ),
    },
  
    corridorB: {
      label: "Praire Ave (≈ north–south)",
      origin: { lat: 33.9309709043882, lng: -118.34389564135788 },
      destination: { lat: 33.97110588763626, lng: -118.34403015407818 },
      polyline: straightSegment(
        33.9309709043882, -118.34389564135788,
        33.97110588763626, -118.34403015407818,
        12
      ),
    },
  };
  