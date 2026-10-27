import os
import sqlite3
import unittest
import numpy as np
import pandas as pd
import torch

from config import Config
from ml.graph_builder import build_district_graph
from ml.temporal_dataset import TemporalDataPipeline, TemporalConfig
from utils.st_gnn_predictor import (
    load_st_gnn_model,
    load_st_gnn_scaler,
    load_st_gnn_graph,
    forecast_district_emissions,
    predict_with_st_gnn,
    FEATURE_COLUMNS,
    TARGET_MEAN,
    TARGET_SCALE
)

try:
    import app
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


class TestSTGNNInference(unittest.TestCase):
    """
    Comprehensive test suite verifying the ST-GNN inference remediation:
    - Scaler parity with benchmark training partition
    - Feature and node ordering alignment
    - Tensor dimensions and spatial graph edge connectivity
    - Target de-standardization and numeric output bounds
    - Explicit rejection of missing or manufactured history
    - Flask dual-mode integration (Household Calculator & District Intelligence)
    - Preservation of historical SQLite prediction records (Record #20)
    """

    def test_scaler_parity_with_training(self):
        """Verify that loaded ST-GNN feature scaler matches the exact 70% benchmark train partition."""
        scaler_meta = load_st_gnn_scaler()
        scaler = scaler_meta["scaler"]

        # Re-derive pipeline directly on benchmark CSV
        df = pd.read_csv(Config.BENCHMARK_DATA_PATH)
        cfg = TemporalConfig(
            lookback=6, forecast_horizon=1,
            train_ratio=0.7, validation_ratio=0.15, test_ratio=0.15,
            missing_strategy="interpolate", scale_target=True
        )
        pipe = TemporalDataPipeline(cfg)
        pipe.prepare(df)

        # Assert feature scaler means and scale factors match within numerical precision
        np.testing.assert_allclose(scaler.mean_, pipe.scaler.mean_, rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(scaler.scale_, pipe.scaler.scale_, rtol=1e-5, atol=1e-5)

        # Assert target scaler parameters match
        np.testing.assert_allclose(scaler_meta["target_mean"], pipe.target_scaler.mean_[0], rtol=1e-5)
        np.testing.assert_allclose(scaler_meta["target_scale"], pipe.target_scaler.scale_[0], rtol=1e-5)

    def test_feature_and_node_ordering(self):
        """Verify that ST-GNN uses exactly the 10 training features and 30 district nodes."""
        expected_features = [
            'Population_Density', 'Electricity_kWh', 'Petrol_Liters', 'Diesel_Liters', 'LPG_kg',
            'Public_Transport_km', 'Waste_Generated_kg', 'Solar_Energy_kWh', 'Tree_Cover_Percent', 'AQI'
        ]
        self.assertEqual(FEATURE_COLUMNS, expected_features)

        graph = load_st_gnn_graph()
        districts = graph["districts"]
        self.assertEqual(len(districts), 30)
        self.assertIn("Ariyalur", districts)
        self.assertIn("Chengalpattu", districts)
        self.assertIn("Coimbatore", districts)
        self.assertIn("Madurai", districts)
        self.assertIn("Virudhunagar", districts)

    def test_tensor_dimensions_and_graph_edges(self):
        """Verify spatial graph topology (286 edges) and that inference produces 30 district forecasts."""
        graph = load_st_gnn_graph()
        edge_index = graph["edge_index"]
        edge_weight = graph["edge_weight"]

        self.assertEqual(edge_index.dim(), 2)
        self.assertEqual(edge_index.shape[0], 2)
        self.assertEqual(edge_index.shape[1], 286, "Tamil Nadu 150km graph should contain exactly 286 directed edges")
        self.assertEqual(edge_weight.shape[0], 286)

        forecast = forecast_district_emissions()
        self.assertEqual(len(forecast["districts"]), 30)
        self.assertEqual(forecast["total_districts"], 30)

    def test_output_inverse_scaling_and_finite_values(self):
        """Verify predictions are finite, strictly positive, and de-standardized to physical kg CO2/month."""
        forecast = forecast_district_emissions()
        self.assertTrue(np.isfinite(forecast["state_total_emission"]))
        self.assertTrue(np.isfinite(forecast["state_avg_emission"]))
        self.assertGreater(forecast["state_total_emission"], 10000.0)

        for d in forecast["districts"]:
            emission = d["predicted_emission"]
            self.assertTrue(np.isfinite(emission))
            self.assertGreaterEqual(emission, 10.0)
            self.assertLess(emission, 5000.0)
            self.assertIn(d["emission_category"], ["Low", "Moderate", "High", "Very High"])

        self.assertTrue(forecast["is_synthetic_benchmark"])
        self.assertIn("synthetic spatiotemporal proxy", forecast["disclaimer"])

    def test_missing_history_and_missing_checkpoint_behavior(self):
        """Verify explicit validation errors when history is insufficient or checkpoints are missing."""
        # Case 1: Incomplete history periods (< 6)
        dummy_df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=3, freq="ME").repeat(30),
            "district": ["Ariyalur"] * 90,
            **{f: [100.0] * 90 for f in FEATURE_COLUMNS}
        })
        with self.assertRaises(ValueError) as ctx:
            forecast_district_emissions(lookback_df=dummy_df)
        self.assertIn("ST-GNN requires exactly 6 historical monthly time periods", str(ctx.exception))

        # Case 2: Missing district coverage (fewer than 30 districts)
        dummy_df_6 = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=6, freq="ME").repeat(2),
            "district": ["Ariyalur", "Chennai"] * 6,
            **{f: [100.0] * 12 for f in FEATURE_COLUMNS}
        })
        with self.assertRaises(ValueError) as ctx2:
            forecast_district_emissions(lookback_df=dummy_df_6)
        self.assertIn("missing districts", str(ctx2.exception))

        # Case 3: Missing checkpoint file raises FileNotFoundError
        from unittest.mock import patch
        with patch.object(Config, "ST_GNN_MODEL_PATH", "non_existent_stgnn_model.pt"):
            real_exists = os.path.exists
            def mock_exists(p):
                if "st_gnn_model" in str(p) or "stgnn_ckpt" in str(p):
                    return False
                return real_exists(p)
            with patch("os.path.exists", side_effect=mock_exists):
                import utils.st_gnn_predictor as pred_mod
                pred_mod._st_gnn_model = None
                with self.assertRaises(FileNotFoundError):
                    load_st_gnn_model()
                pred_mod._st_gnn_model = None

    @unittest.skipUnless(HAS_FLASK, "Flask required for route integration tests.")
    def test_flask_integration_in_both_operating_modes(self):
        """Verify web routes for Household Carbon Calculator and District Climate Intelligence."""
        flask_app = app.app
        flask_app.config['TESTING'] = True
        client = flask_app.test_client()

        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test Mode User'
            sess['user_email'] = 'mode@carbon.ai'

        # Mode 1: Household Carbon Calculator (GET and POST /predict)
        get_res = client.get('/predict')
        self.assertEqual(get_res.status_code, 200)
        get_html = get_res.get_data(as_text=True)
        self.assertIn('Household Carbon Footprint Calculator', get_html)
        self.assertIn('Switch to District Intelligence', get_html)

        demo_payload = {
            'district': 'Chennai',
            'place': 'Guindy',
            'area_type': 'Urban',
            'population_density': '16500',
            'aqi': '95',
            'region_emission_factor': '0.82',
            'electricity_kwh': '420',
            'petrol_liters': '55',
            'diesel_liters': '25',
            'lpg_kg': '18',
            'public_transport_km': '220',
            'waste_generated_kg': '35',
            'solar_energy_kwh': '120',
            'tree_cover_percent': '18'
        }
        post_res = client.post('/predict', data=demo_payload, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)
        post_html = post_res.get_data(as_text=True)
        self.assertIn('Linear Regression Model Contributions', post_html)
        self.assertIn('529.81', post_html)

        # Mode 2: District Climate Intelligence (GET /district-intelligence)
        dist_res = client.get('/district-intelligence')
        self.assertEqual(dist_res.status_code, 200)
        dist_html = dist_res.get_data(as_text=True)
        self.assertIn('District Climate Intelligence', dist_html)
        self.assertIn('Statewide Forecast Total', dist_html)
        self.assertIn('Research-Grade Spatio-Temporal Model & Synthetic Benchmark Disclosure', dist_html)
        self.assertIn('Chengalpattu', dist_html)
        self.assertIn('Coimbatore', dist_html)

    def test_preservation_of_existing_historical_records(self):
        """Verify that existing historical prediction record #20 is intact and unmodified."""
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        row20 = conn.execute("SELECT * FROM predictions WHERE id = 20").fetchone()
        conn.close()

        self.assertIsNotNone(row20, "Historical record 20 must exist.")
        self.assertAlmostEqual(row20['predicted_emission'], 574.43, places=2)
        self.assertEqual(row20['environmental_score'], 28)


if __name__ == "__main__":
    unittest.main()
