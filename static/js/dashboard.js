document.addEventListener("DOMContentLoaded", function () {
  // Chart 1: Average Emission by District
  const districtCanvas = document.getElementById("chartDistrict");
  if (districtCanvas) {
    fetch("/api/district-summary")
      .then((res) => res.json())
      .then((data) => {
        const labels = data.map((d) => d.district);
        const emissions = data.map((d) => d.avg_emission);

        new Chart(districtCanvas, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [{
              label: "Avg CO₂ Emission (kg)",
              data: emissions,
              backgroundColor: "rgba(5, 150, 105, 0.75)",
              borderColor: "#059669",
              borderWidth: 1,
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: { beginAtZero: true }
            }
          }
        });
      });
  }

  // Fetch all predictions for remaining charts
  fetch("/api/predictions")
    .then((res) => res.json())
    .then((predictions) => {
      // Chart 2: Category Distribution
      const categoryCanvas = document.getElementById("chartCategory");
      if (categoryCanvas) {
        const catCounts = { Low: 0, Moderate: 0, High: 0, "Very High": 0 };
        predictions.forEach((p) => {
          if (catCounts[p.emission_category] !== undefined) {
            catCounts[p.emission_category]++;
          }
        });

        new Chart(categoryCanvas, {
          type: "doughnut",
          data: {
            labels: Object.keys(catCounts),
            datasets: [{
              data: Object.values(catCounts),
              backgroundColor: ["#10b981", "#f59e0b", "#f97316", "#ef4444"],
              borderWidth: 2,
              borderColor: "#ffffff"
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "bottom" }
            }
          }
        });
      }

      // Chart 3: Score Distribution
      const scoreCanvas = document.getElementById("chartScore");
      if (scoreCanvas) {
        const scoreRanges = { "80-100 (Excellent)": 0, "60-79 (Good)": 0, "40-59 (Moderate)": 0, "0-39 (Poor/Critical)": 0 };
        predictions.forEach((p) => {
          const s = p.environmental_score;
          if (s >= 80) scoreRanges["80-100 (Excellent)"]++;
          else if (s >= 60) scoreRanges["60-79 (Good)"]++;
          else if (s >= 40) scoreRanges["40-59 (Moderate)"]++;
          else scoreRanges["0-39 (Poor/Critical)"]++;
        });

        new Chart(scoreCanvas, {
          type: "polarArea",
          data: {
            labels: Object.keys(scoreRanges),
            datasets: [{
              data: Object.values(scoreRanges),
              backgroundColor: ["#10b981", "#0284c7", "#f59e0b", "#ef4444"]
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "bottom" }
            }
          }
        });
      }

      // Chart 4: Emission Trend
      const trendCanvas = document.getElementById("chartTrend");
      if (trendCanvas) {
        const sorted = [...predictions].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        const labels = sorted.map((p) => p.timestamp.split(" ")[0]);
        const emissions = sorted.map((p) => p.predicted_emission);

        new Chart(trendCanvas, {
          type: "line",
          data: {
            labels: labels,
            datasets: [{
              label: "Emission (kg CO₂)",
              data: emissions,
              borderColor: "#0284c7",
              backgroundColor: "rgba(2, 132, 199, 0.1)",
              fill: true,
              tension: 0.3,
              pointRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: { beginAtZero: true }
            }
          }
        });
      }
    });
});
