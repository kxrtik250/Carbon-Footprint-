document.addEventListener("DOMContentLoaded", function () {
  const mapContainer = document.getElementById("map");
  if (!mapContainer) return;

  // Initialize Leaflet map centered over Tamil Nadu
  const map = L.map("map").setView([11.1271, 78.6569], 7);

  // OpenStreetMap Tiles with attribution
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | Carbon Monitoring'
  }).addTo(map);

  // Color mapper for markers
  function getColor(category) {
    switch (category) {
      case "Low": return "#10b981";
      case "Moderate": return "#f59e0b";
      case "High": return "#f97316";
      case "Very High": return "#ef4444";
      default: return "#64748b";
    }
  }

  // Custom Circle Marker Generator
  function createMarker(item) {
    const color = getColor(item.category);
    const marker = L.circleMarker([item.latitude, item.longitude], {
      radius: 10,
      fillColor: color,
      color: "#ffffff",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.85
    });

    const popupContent = `
      <div style="font-family: sans-serif; padding: 4px; min-width: 180px;">
        <h4 style="margin:0 0 6px 0; color:#0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom:4px;">
          ${item.district} - ${item.place}
        </h4>
        <p style="margin:4px 0; font-size:0.85rem;"><strong>Area Type:</strong> ${item.area_type}</p>
        <p style="margin:4px 0; font-size:0.85rem;"><strong>Predicted CO₂:</strong> ${item.emission} kg CO₂</p>
        <p style="margin:4px 0; font-size:0.85rem;"><strong>Environmental Score:</strong> ${item.score}/100</p>
        <div style="margin-top:6px;">
          <span style="background:${color}; color:#fff; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:bold;">
            ${item.category} Emission
          </span>
        </div>
      </div>
    `;

    marker.bindPopup(popupContent);
    return marker;
  }

  // Fetch map data from API
  fetch("/api/map-data")
    .then((res) => res.json())
    .then((data) => {
      const markersGroup = L.featureGroup();

      data.forEach((item) => {
        const marker = createMarker(item);
        marker.addTo(map);
        markersGroup.addLayer(marker);
      });

      // If target lat/lon specified in URL parameters (e.g. from prediction result page)
      const urlParams = new URLSearchParams(window.location.search);
      const targetLat = parseFloat(urlParams.get("lat"));
      const targetLng = parseFloat(urlParams.get("lng"));

      if (!isNaN(targetLat) && !isNaN(targetLng)) {
        map.setView([targetLat, targetLng], 12);
      }
    })
    .catch((err) => {
      console.error("Error loading map data:", err);
    });
});
