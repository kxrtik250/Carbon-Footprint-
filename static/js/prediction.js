document.addEventListener("DOMContentLoaded", function () {
  const districtSelect = document.getElementById("district");
  const placeSelect = document.getElementById("place");
  const areaTypeInput = document.getElementById("area_type");
  const loadPresetBtn = document.getElementById("load_preset_btn");

  if (districtSelect && placeSelect) {
    districtSelect.addEventListener("change", function () {
      const selectedDistrict = this.value;
      if (!selectedDistrict) {
        placeSelect.innerHTML = '<option value="">-- Select District First --</option>';
        return;
      }

      placeSelect.innerHTML = '<option value="">Loading places...</option>';

      fetch(`/get_places/${encodeURIComponent(selectedDistrict)}`)
        .then((response) => response.json())
        .then((places) => {
          placeSelect.innerHTML = '<option value="">-- Select Place --</option>';
          places.forEach((p) => {
            const option = document.createElement("option");
            option.value = p.place;
            option.textContent = p.place;
            option.dataset.areaType = p.area_type;
            placeSelect.appendChild(option);
          });
        })
        .catch((err) => {
          console.error("Error fetching places:", err);
          placeSelect.innerHTML = '<option value="">Error loading places</option>';
        });
    });

    placeSelect.addEventListener("change", function () {
      const selectedOption = this.options[this.selectedIndex];
      if (selectedOption && selectedOption.dataset.areaType && areaTypeInput) {
        areaTypeInput.value = selectedOption.dataset.areaType;
      }
    });
  }

  // Load Preset Button for quick demo
  if (loadPresetBtn) {
    loadPresetBtn.addEventListener("click", function () {
      document.getElementById("population_density").value = 12500;
      document.getElementById("electricity_kwh").value = 420;
      document.getElementById("petrol_liters").value = 55;
      document.getElementById("diesel_liters").value = 25;
      document.getElementById("lpg_kg").value = 18;
      document.getElementById("public_transport_km").value = 220;
      document.getElementById("waste_generated_kg").value = 35;
      document.getElementById("solar_energy_kwh").value = 120;
      document.getElementById("tree_cover_percent").value = 18;
      document.getElementById("aqi").value = 95;
    });
  }

  // Client Validation for inputs
  const form = document.getElementById("predictionForm");
  if (form) {
    form.addEventListener("submit", function (e) {
      const numericInputs = form.querySelectorAll('input[type="number"]');
      let hasError = false;

      numericInputs.forEach((input) => {
        const val = parseFloat(input.value);
        if (isNaN(val) || val < 0) {
          input.style.borderColor = "#ef4444";
          hasError = true;
        } else {
          input.style.borderColor = "#e2e8f0";
        }
      });

      if (hasError) {
        e.preventDefault();
        alert("Please ensure all parameters contain non-negative numbers.");
      }
    });
  }
});
