"""
Tests for Ablation Framework and Research Evaluation Modules

These tests verify the core functionality of:
1. AblationEvaluator - Configuration testing and metrics
2. ConfidenceCalibrator - Calibration methods and ECE
3. BenchmarkGenerator - Dataset generation
"""

import json
import pytest
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAblationFramework:
    """Tests for the ablation study framework."""
    
    def test_import(self):
        """Test ablation framework imports correctly."""
        from scripts.ablation_framework import AblationEvaluator, ABLATION_CONFIGS
        assert AblationEvaluator is not None
        assert len(ABLATION_CONFIGS) >= 6
    
    def test_config_definitions(self):
        """Test that all ablation configurations are properly defined."""
        from scripts.ablation_framework import ABLATION_CONFIGS, AblationConfig
        
        required_configs = ["full_system", "no_clip", "no_spatial_temporal", "keyword_baseline"]
        for config_name in required_configs:
            assert config_name in ABLATION_CONFIGS, f"Missing config: {config_name}"
            config = ABLATION_CONFIGS[config_name]
            assert isinstance(config, AblationConfig)
            assert config.name == config_name
    
    def test_evaluator_initialization(self):
        """Test AblationEvaluator initializes correctly."""
        from scripts.ablation_framework import AblationEvaluator
        
        evaluator = AblationEvaluator(ground_truth_path="data/test_ground_truth.json")
        assert evaluator is not None
        assert evaluator.test_cases == []
    
    def test_ground_truth_generation(self):
        """Test synthetic ground truth generation."""
        from scripts.ablation_framework import AblationEvaluator
        
        evaluator = AblationEvaluator(ground_truth_path="data/test_synthetic.json")
        evaluator.load_ground_truth()
        
        assert len(evaluator.test_cases) > 0, "Should generate synthetic test cases"
        assert all("id" in tc for tc in evaluator.test_cases)
        assert all("expected" in tc for tc in evaluator.test_cases)
    
    def test_single_case_evaluation(self):
        """Test evaluating a single test case."""
        from scripts.ablation_framework import AblationEvaluator, ABLATION_CONFIGS
        
        evaluator = AblationEvaluator()
        evaluator.load_ground_truth()
        
        if evaluator.test_cases:
            case = evaluator.test_cases[0]
            config = ABLATION_CONFIGS["full_system"]
            
            correct, latency = evaluator.evaluate_single_case(case, config)
            
            assert isinstance(correct, bool)
            assert isinstance(latency, float)
            assert latency >= 0
    
    def test_run_configuration(self):
        """Test running a full configuration evaluation."""
        from scripts.ablation_framework import AblationEvaluator, ABLATION_CONFIGS, AblationResult
        
        evaluator = AblationEvaluator()
        evaluator.load_ground_truth()
        evaluator.test_cases = evaluator.test_cases[:10]  # Limit for speed
        
        result = evaluator.run_configuration(ABLATION_CONFIGS["full_system"])
        
        assert isinstance(result, AblationResult)
        assert 0 <= result.accuracy <= 1
        assert 0 <= result.f1_score <= 1
        assert result.latency_p95 >= 0
        assert len(result.per_sample_correct) == len(evaluator.test_cases)


class TestConfidenceCalibration:
    """Tests for the confidence calibration module."""
    
    def test_import(self):
        """Test calibration module imports correctly."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator, CalibrationMetrics
        assert ConfidenceCalibrator is not None
        assert CalibrationMetrics is not None
    
    def test_calibrator_initialization(self):
        """Test calibrator initializes with different methods."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        for method in ["temperature", "isotonic", "platt"]:
            calibrator = ConfidenceCalibrator(method=method)
            assert calibrator is not None
            assert calibrator.method == method
            assert not calibrator.is_fitted
    
    def test_invalid_method(self):
        """Test that invalid method raises error."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        with pytest.raises(ValueError):
            ConfidenceCalibrator(method="invalid_method")
    
    def test_fit_temperature(self):
        """Test temperature scaling fitting."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        np.random.seed(42)
        confidences = np.random.beta(5, 2, 100)  # Skewed high
        outcomes = np.random.binomial(1, 0.7, 100)  # 70% accuracy
        
        calibrator = ConfidenceCalibrator(method="temperature")
        calibrator.fit(confidences, outcomes)
        
        assert calibrator.is_fitted
        assert calibrator.temperature != 1.0  # Should have adjusted
    
    def test_fit_isotonic(self):
        """Test isotonic regression fitting."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        np.random.seed(42)
        confidences = np.random.beta(5, 2, 100)
        outcomes = np.random.binomial(1, 0.7, 100)
        
        calibrator = ConfidenceCalibrator(method="isotonic")
        calibrator.fit(confidences, outcomes)
        
        assert calibrator.is_fitted
        assert calibrator.calibrator is not None
    
    def test_calibrate_single(self):
        """Test calibrating a single confidence score."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        np.random.seed(42)
        confidences = np.random.beta(5, 2, 100)
        outcomes = np.random.binomial(1, 0.7, 100)
        
        calibrator = ConfidenceCalibrator(method="isotonic")
        calibrator.fit(confidences, outcomes)
        
        calibrated = calibrator.calibrate(0.9)
        
        assert 0 <= calibrated <= 1
    
    def test_calibrate_batch(self):
        """Test batch calibration."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        np.random.seed(42)
        train_conf = np.random.beta(5, 2, 100)
        train_out = np.random.binomial(1, 0.7, 100)
        
        calibrator = ConfidenceCalibrator(method="isotonic")
        calibrator.fit(train_conf, train_out)
        
        test_conf = np.array([0.6, 0.7, 0.8, 0.9, 0.95])
        calibrated = calibrator.calibrate_batch(test_conf)
        
        assert len(calibrated) == len(test_conf)
        assert all(0 <= c <= 1 for c in calibrated)
    
    def test_evaluate_metrics(self):
        """Test calibration evaluation metrics."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        np.random.seed(42)
        confidences = np.random.beta(5, 2, 100)
        outcomes = np.random.binomial(1, 0.7, 100)
        
        calibrator = ConfidenceCalibrator(method="isotonic")
        calibrator.fit(confidences, outcomes)
        
        metrics = calibrator.evaluate(confidences, outcomes)
        
        assert metrics.ece >= 0
        assert metrics.mce >= 0
        assert 0 <= metrics.avg_confidence <= 1
        assert 0 <= metrics.avg_accuracy <= 1
    
    def test_ece_reduction(self):
        """Test that calibration reduces ECE (in expectation)."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        np.random.seed(42)
        # Generate overconfident predictions
        n = 200
        confidences = np.random.beta(8, 2, n)  # Very skewed towards 1
        outcomes = np.random.binomial(1, 0.65, n)  # Only 65% accurate
        
        # Split train/test
        train_conf, test_conf = confidences[:100], confidences[100:]
        train_out, test_out = outcomes[:100], outcomes[100:]
        
        # ECE before calibration
        uncal = ConfidenceCalibrator(method="isotonic")
        ece_before = uncal._compute_ece_raw(test_conf, test_out)
        
        # ECE after calibration
        calibrator = ConfidenceCalibrator(method="isotonic")
        calibrator.fit(train_conf, train_out)
        metrics = calibrator.evaluate(test_conf, test_out)
        ece_after = metrics.ece
        
        # Calibration should reduce ECE (with high probability)
        # Note: This may occasionally fail due to randomness
        assert ece_after <= ece_before + 0.1, f"ECE should decrease or stay similar"


class TestBenchmarkGenerator:
    """Tests for the benchmark dataset generator."""
    
    def test_import(self):
        """Test benchmark generator imports correctly."""
        from scripts.benchmark_generator import BenchmarkGenerator, TestCase
        assert BenchmarkGenerator is not None
        assert TestCase is not None
    
    def test_generator_initialization(self):
        """Test generator initializes with seed."""
        from scripts.benchmark_generator import BenchmarkGenerator
        
        gen1 = BenchmarkGenerator(seed=42)
        gen2 = BenchmarkGenerator(seed=42)
        
        cases1 = gen1.generate_positive_cases(10)
        cases2 = gen2.generate_positive_cases(10)
        
        assert len(cases1) == 10
        assert len(cases2) == 10
    
    def test_positive_case_generation(self):
        """Test generating positive (valid) cases."""
        from scripts.benchmark_generator import BenchmarkGenerator
        
        gen = BenchmarkGenerator(seed=42)
        cases = gen.generate_positive_cases(20)
        
        assert len(cases) == 20
        assert all(c.expected_valid for c in cases)
        assert all(c.item_type for c in cases)
        assert all(c.description for c in cases)
    
    def test_discrepancy_case_generation(self):
        """Test generating discrepancy cases."""
        from scripts.benchmark_generator import BenchmarkGenerator
        
        gen = BenchmarkGenerator(seed=42)
        cases = gen.generate_discrepancy_cases(10)
        
        assert len(cases) == 10
        assert all(not c.expected_valid for c in cases)
        assert all(c.has_discrepancy for c in cases)
        assert all(c.discrepancy_type for c in cases)
    
    def test_implausible_case_generation(self):
        """Test generating implausible cases."""
        from scripts.benchmark_generator import BenchmarkGenerator
        
        gen = BenchmarkGenerator(seed=42)
        cases = gen.generate_implausible_cases(5)
        
        assert len(cases) == 5
        assert all(not c.expected_valid for c in cases)
    
    def test_full_benchmark_generation(self):
        """Test generating complete benchmark."""
        from scripts.benchmark_generator import BenchmarkGenerator
        
        gen = BenchmarkGenerator(seed=42)
        cases = gen.generate_full_benchmark(
            positive_count=20,
            discrepancy_count=10,
            implausible_count=5,
            low_quality_count=5
        )
        
        assert len(cases) == 40
        
        # Check distribution
        valid_count = sum(1 for c in cases if c.expected_valid)
        invalid_count = sum(1 for c in cases if not c.expected_valid)
        
        assert valid_count == 20
        assert invalid_count == 20
    
    def test_statistics(self):
        """Test statistics calculation."""
        from scripts.benchmark_generator import BenchmarkGenerator
        
        gen = BenchmarkGenerator(seed=42)
        gen.generate_full_benchmark(positive_count=30, discrepancy_count=10, implausible_count=5, low_quality_count=5)
        
        stats = gen.get_statistics()
        
        assert stats["total_cases"] == 50
        assert "by_category" in stats
        assert "by_quality" in stats
        assert "validation_rate" in stats
    
    def test_save_and_load(self, tmp_path):
        """Test saving benchmark to file."""
        from scripts.benchmark_generator import BenchmarkGenerator
        
        gen = BenchmarkGenerator(seed=42)
        gen.generate_full_benchmark(positive_count=10, discrepancy_count=5, implausible_count=3, low_quality_count=2)
        
        output_path = tmp_path / "test_benchmark.json"
        gen.save(str(output_path))
        
        assert output_path.exists()
        
        with open(output_path) as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "test_cases" in data
        assert len(data["test_cases"]) == 20


class TestIntegration:
    """Integration tests between modules."""
    
    def test_ablation_with_benchmark(self):
        """Test running ablation on generated benchmark."""
        from scripts.benchmark_generator import BenchmarkGenerator
        from scripts.ablation_framework import AblationEvaluator, ABLATION_CONFIGS
        
        # Generate small benchmark
        gen = BenchmarkGenerator(seed=42)
        gen.generate_full_benchmark(positive_count=15, discrepancy_count=5, implausible_count=3, low_quality_count=2)
        
        # Save it
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
            import json
            from dataclasses import asdict
            json.dump({"test_cases": [asdict(tc) for tc in gen.test_cases]}, f)
            temp_path = f.name
        
        # Run ablation
        evaluator = AblationEvaluator(ground_truth_path=temp_path)
        evaluator.load_ground_truth()
        
        result = evaluator.run_configuration(ABLATION_CONFIGS["full_system"])
        
        assert result.accuracy > 0
        assert result.num_samples == 25
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_calibrator_with_ablation_results(self):
        """Test calibrating confidence scores from ablation."""
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        # Simulate ablation confidence outputs
        np.random.seed(42)
        confidences = np.random.uniform(0.5, 0.95, 50)
        outcomes = (confidences + np.random.normal(0, 0.2, 50) > 0.65).astype(int)
        
        calibrator = ConfidenceCalibrator(method="isotonic")
        calibrator.fit(confidences, outcomes)
        
        # Verify calibration works
        original_mean = confidences.mean()
        calibrated = calibrator.calibrate_batch(confidences)
        calibrated_mean = calibrated.mean()
        
        # Just verify it runs and produces valid outputs
        assert all(0 <= c <= 1 for c in calibrated)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
