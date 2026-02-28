"""
Real Validation Pipeline Evaluator
Connects ablation framework to actual CLIP, YOLO, and validation components.

This module provides the bridge between the synthetic evaluation framework
and the real multimodal validation system for production-grade metrics.

Features:
- Uses actual CLIPValidator for image-text similarity
- Uses real SpatialTemporalValidator for plausibility
- Collects ground truth from validated items in database
- Saves calibration training data for future model improvement
"""

import json
import time
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

logger = logging.getLogger(__name__)

# Import real validators lazily
_clip_validator = None
_spatial_temporal_validator = None
_consistency_engine = None
_image_validator = None


def get_clip_validator():
    """Lazy-load CLIP validator."""
    global _clip_validator
    if _clip_validator is None:
        try:
            from src.cross_modal.clip_validator import CLIPValidator
            _clip_validator = CLIPValidator()
            logger.info("CLIPValidator loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIPValidator: {e}")
    return _clip_validator


def get_spatial_temporal_validator():
    """Lazy-load spatial-temporal validator."""
    global _spatial_temporal_validator
    if _spatial_temporal_validator is None:
        try:
            from src.intelligence.spatial_temporal_validator import get_spatial_temporal_validator as get_stv
            _spatial_temporal_validator = get_stv()
            logger.info("SpatialTemporalValidator loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SpatialTemporalValidator: {e}")
    return _spatial_temporal_validator


def get_consistency_engine():
    """Lazy-load consistency engine."""
    global _consistency_engine
    if _consistency_engine is None:
        try:
            from src.cross_modal.consistency_engine import ConsistencyEngine
            _consistency_engine = ConsistencyEngine()
            logger.info("ConsistencyEngine loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ConsistencyEngine: {e}")
    return _consistency_engine


def get_image_validator():
    """Lazy-load image validator."""
    global _image_validator
    if _image_validator is None:
        try:
            from src.image.validator import ImageValidator
            _image_validator = ImageValidator()
            logger.info("ImageValidator loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ImageValidator: {e}")
    return _image_validator


@dataclass
class RealValidationResult:
    """Result from evaluating a real item through the pipeline."""
    test_case_id: str
    image_path: Optional[str]
    text_description: str
    
    # Component scores
    clip_similarity: float
    spatial_temporal_score: float
    image_quality_score: float
    text_completeness_score: float
    
    # Overall validation
    overall_confidence: float
    predicted_valid: bool
    
    # Ground truth (if available)
    ground_truth_valid: Optional[bool]
    
    # Metadata
    latency_seconds: float
    component_latencies: Dict[str, float]
    timestamp: str


class RealValidationEvaluator:
    """
    Evaluates the multimodal validation system using real components.
    
    This connects the ablation framework to actual CLIP, YOLO, and
    Bayesian validators for production-grade evaluation.
    """
    
    def __init__(self, 
                 image_dataset_dir: str = "data/image_dataset",
                 output_dir: str = "paper/real_results"):
        """
        Initialize the real validation evaluator.
        
        Args:
            image_dataset_dir: Directory containing test images
            output_dir: Directory to save evaluation results
        """
        self.image_dataset_dir = Path(image_dataset_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[RealValidationResult] = []
        self.calibration_data: List[Dict] = []
        
        # Component availability tracking
        self.available_components = {
            "clip": False,
            "spatial_temporal": False,
            "image": False,
            "consistency_engine": False,
        }
    
    def initialize_components(self) -> Dict[str, bool]:
        """Initialize all validation components and check availability."""
        logger.info("Initializing validation components...")
        
        if get_clip_validator():
            self.available_components["clip"] = True
        
        if get_spatial_temporal_validator():
            self.available_components["spatial_temporal"] = True
        
        if get_image_validator():
            self.available_components["image"] = True
        
        if get_consistency_engine():
            self.available_components["consistency_engine"] = True
        
        available = sum(self.available_components.values())
        total = len(self.available_components)
        logger.info(f"Components initialized: {available}/{total} available")
        
        return self.available_components
    
    def evaluate_single_item(self,
                            image_path: Optional[str],
                            text_description: str,
                            item_type: str = "default",
                            location: Optional[str] = None,
                            time_period: Optional[str] = None,
                            ground_truth: Optional[bool] = None,
                            ablation_config: Optional[Dict] = None) -> RealValidationResult:
        """
        Evaluate a single item through the real validation pipeline.
        
        Args:
            image_path: Path to item image (optional)
            text_description: Text description of the item
            item_type: Category of item (phone, wallet, etc.)
            location: Where item was found/lost
            time_period: When item was found/lost
            ground_truth: Known validation outcome (for calibration)
            ablation_config: Component enable/disable flags for ablation
        
        Returns:
            RealValidationResult with all component scores
        """
        start_time = time.time()
        component_latencies = {}
        ablation_config = ablation_config or {}
        
        # Default all components enabled
        use_clip = ablation_config.get("use_clip", True)
        use_spatial_temporal = ablation_config.get("use_spatial_temporal", True)
        use_image = ablation_config.get("use_image", True)
        
        # Initialize scores
        clip_similarity = 0.0
        spatial_temporal_score = 0.0
        image_quality_score = 0.0
        text_completeness_score = 0.5  # Default
        
        # 1. CLIP Cross-Modal Alignment
        if use_clip and image_path and self.available_components["clip"]:
            clip_start = time.time()
            try:
                clip_validator = get_clip_validator()
                result = clip_validator.validate_image_text_alignment(image_path, text_description)
                clip_similarity = result.get("similarity", 0.0)
            except Exception as e:
                logger.warning(f"CLIP validation failed: {e}")
            component_latencies["clip"] = time.time() - clip_start
        
        # 2. Spatial-Temporal Plausibility
        if use_spatial_temporal and location and self.available_components["spatial_temporal"]:
            st_start = time.time()
            try:
                st_validator = get_spatial_temporal_validator()
                result = st_validator.calculate_plausibility(
                    item=item_type,
                    location=location,
                    time=time_period
                )
                spatial_temporal_score = result.get("plausibility_score", 0.0)
            except Exception as e:
                logger.warning(f"Spatial-temporal validation failed: {e}")
            component_latencies["spatial_temporal"] = time.time() - st_start
        
        # 3. Image Quality Assessment
        if use_image and image_path and self.available_components["image"]:
            img_start = time.time()
            try:
                image_validator = get_image_validator()
                result = image_validator.validate(image_path)
                image_quality_score = result.get("overall_score", 0.0) / 100.0  # Normalize
            except Exception as e:
                logger.warning(f"Image validation failed: {e}")
            component_latencies["image"] = time.time() - img_start
        
        # 4. Calculate Overall Confidence
        # Weighted combination based on available modalities
        weights = {"clip": 0.35, "spatial_temporal": 0.25, "image": 0.25, "text": 0.15}
        
        total_weight = 0.0
        weighted_score = 0.0
        
        if use_clip and image_path:
            weighted_score += weights["clip"] * clip_similarity
            total_weight += weights["clip"]
        
        if use_spatial_temporal and location:
            weighted_score += weights["spatial_temporal"] * spatial_temporal_score
            total_weight += weights["spatial_temporal"]
        
        if use_image and image_path:
            weighted_score += weights["image"] * image_quality_score
            total_weight += weights["image"]
        
        # Text is always available
        weighted_score += weights["text"] * text_completeness_score
        total_weight += weights["text"]
        
        # Normalize by total weight
        overall_confidence = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Make validation decision
        threshold = 0.65
        predicted_valid = overall_confidence >= threshold
        
        latency = time.time() - start_time
        
        result = RealValidationResult(
            test_case_id=f"real_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            image_path=image_path,
            text_description=text_description[:100] + "..." if len(text_description) > 100 else text_description,
            clip_similarity=round(clip_similarity, 4),
            spatial_temporal_score=round(spatial_temporal_score, 4),
            image_quality_score=round(image_quality_score, 4),
            text_completeness_score=round(text_completeness_score, 4),
            overall_confidence=round(overall_confidence, 4),
            predicted_valid=predicted_valid,
            ground_truth_valid=ground_truth,
            latency_seconds=round(latency, 4),
            component_latencies={k: round(v, 4) for k, v in component_latencies.items()},
            timestamp=datetime.now().isoformat(),
        )
        
        self.results.append(result)
        
        # Save calibration data if ground truth available
        if ground_truth is not None:
            self.calibration_data.append({
                "confidence": overall_confidence,
                "outcome": 1 if (predicted_valid == ground_truth) else 0,
                "ground_truth": ground_truth,
                "predicted": predicted_valid,
            })
        
        return result
    
    def evaluate_dataset(self, 
                        test_cases: List[Dict],
                        ablation_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Evaluate multiple test cases.
        
        Args:
            test_cases: List of test case dictionaries with keys:
                - image_path (optional)
                - text_description
                - item_type
                - location (optional)
                - time_period (optional)
                - expected_valid (optional, ground truth)
            ablation_config: Component enable/disable flags
        
        Returns:
            Aggregate metrics and per-case results
        """
        self.initialize_components()
        
        logger.info(f"Evaluating {len(test_cases)} test cases...")
        
        for i, case in enumerate(test_cases):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(test_cases)}")
            
            self.evaluate_single_item(
                image_path=case.get("image_path"),
                text_description=case.get("text_description", case.get("description", "")),
                item_type=case.get("item_type", "default"),
                location=case.get("location"),
                time_period=case.get("time_period"),
                ground_truth=case.get("expected_valid"),
                ablation_config=ablation_config,
            )
        
        # Calculate aggregate metrics
        metrics = self._compute_metrics()
        
        return metrics
    
    def _compute_metrics(self) -> Dict[str, Any]:
        """Compute aggregate evaluation metrics."""
        if not self.results:
            return {"error": "No results to compute metrics"}
        
        # Filter to results with ground truth
        results_with_gt = [r for r in self.results if r.ground_truth_valid is not None]
        
        if results_with_gt:
            correct = sum(1 for r in results_with_gt if r.predicted_valid == r.ground_truth_valid)
            accuracy = correct / len(results_with_gt)
            
            # Precision, Recall, F1
            tp = sum(1 for r in results_with_gt if r.predicted_valid and r.ground_truth_valid)
            fp = sum(1 for r in results_with_gt if r.predicted_valid and not r.ground_truth_valid)
            fn = sum(1 for r in results_with_gt if not r.predicted_valid and r.ground_truth_valid)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        else:
            accuracy = precision = recall = f1 = None
        
        # Latency statistics
        latencies = [r.latency_seconds for r in self.results]
        
        # Component score distributions
        clip_scores = [r.clip_similarity for r in self.results if r.clip_similarity > 0]
        st_scores = [r.spatial_temporal_score for r in self.results if r.spatial_temporal_score > 0]
        img_scores = [r.image_quality_score for r in self.results if r.image_quality_score > 0]
        
        metrics = {
            "total_cases": len(self.results),
            "cases_with_ground_truth": len(results_with_gt),
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "latency": {
                "mean": np.mean(latencies),
                "p50": np.percentile(latencies, 50),
                "p95": np.percentile(latencies, 95),
                "p99": np.percentile(latencies, 99),
            },
            "component_scores": {
                "clip_similarity_mean": np.mean(clip_scores) if clip_scores else None,
                "spatial_temporal_mean": np.mean(st_scores) if st_scores else None,
                "image_quality_mean": np.mean(img_scores) if img_scores else None,
            },
            "confidence_distribution": {
                "mean": np.mean([r.overall_confidence for r in self.results]),
                "std": np.std([r.overall_confidence for r in self.results]),
                "min": min(r.overall_confidence for r in self.results),
                "max": max(r.overall_confidence for r in self.results),
            },
        }
        
        return metrics
    
    def save_calibration_data(self, output_path: str = "data/calibration_training_data.json"):
        """Save collected calibration data for training the calibrator."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        output = {
            "generated_at": datetime.now().isoformat(),
            "num_samples": len(self.calibration_data),
            "data": self.calibration_data,
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Calibration data saved to: {output_path}")
        return output_path
    
    def save_results(self, output_path: Optional[str] = None):
        """Save evaluation results to JSON."""
        output_path = output_path or str(self.output_dir / "real_evaluation_results.json")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        output = {
            "generated_at": datetime.now().isoformat(),
            "available_components": self.available_components,
            "metrics": self._compute_metrics(),
            "results": [asdict(r) for r in self.results],
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_path}")
        return output_path
    
    def run_real_ablation_study(self, test_cases: List[Dict]) -> Dict[str, Dict]:
        """
        Run ablation study using real validation components.
        
        Tests different component configurations on the same test cases.
        """
        from scripts.ablation_framework import ABLATION_CONFIGS
        
        results = {}
        
        for config_name, config in ABLATION_CONFIGS.items():
            logger.info(f"\n{'='*40}")
            logger.info(f"Ablation: {config_name}")
            logger.info(f"{'='*40}")
            
            # Reset results for this configuration
            self.results = []
            self.calibration_data = []
            
            # Create ablation config dict
            ablation_config = {
                "use_clip": config.use_clip,
                "use_spatial_temporal": config.use_spatial_temporal,
                "use_image": config.use_image,
            }
            
            # Run evaluation
            metrics = self.evaluate_dataset(test_cases, ablation_config)
            
            results[config_name] = {
                "config": asdict(config),
                "metrics": metrics,
            }
            
            logger.info(f"Accuracy: {metrics.get('accuracy')}")
        
        # Save ablation results
        output_path = self.output_dir / "real_ablation_results.json"
        with open(output_path, 'w') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "configurations": results,
            }, f, indent=2, default=str)
        
        logger.info(f"\nAblation results saved to: {output_path}")
        return results


class CalibrationDataCollector:
    """
    Collects validation outcomes over time for calibration training.
    
    This integrates with the FastAPI endpoints to record:
    - Predicted confidence scores
    - Actual validation outcomes (from user feedback or matching results)
    """
    
    def __init__(self, data_file: str = "data/calibration_training_data.json"):
        """Initialize the collector."""
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self.data: List[Dict] = []
        self._load()
    
    def _load(self):
        """Load existing calibration data."""
        if self.data_file.exists():
            try:
                with open(self.data_file) as f:
                    content = json.load(f)
                    self.data = content.get("data", [])
                logger.info(f"Loaded {len(self.data)} existing calibration samples")
            except Exception as e:
                logger.error(f"Failed to load calibration data: {e}")
    
    def _save(self):
        """Save calibration data."""
        output = {
            "last_updated": datetime.now().isoformat(),
            "num_samples": len(self.data),
            "data": self.data,
        }
        with open(self.data_file, 'w') as f:
            json.dump(output, f, indent=2)
    
    def record_prediction(self, 
                         request_id: str,
                         confidence: float,
                         predicted_valid: bool,
                         component_scores: Optional[Dict] = None):
        """
        Record a validation prediction for future calibration.
        
        Args:
            request_id: Unique request identifier
            confidence: Overall confidence score
            predicted_valid: Validation decision
            component_scores: Individual component scores
        """
        entry = {
            "request_id": request_id,
            "confidence": confidence,
            "predicted_valid": predicted_valid,
            "component_scores": component_scores or {},
            "timestamp": datetime.now().isoformat(),
            "outcome": None,  # To be filled later
        }
        self.data.append(entry)
        self._save()
        
        return entry
    
    def record_outcome(self, request_id: str, actual_valid: bool):
        """
        Record the actual validation outcome (ground truth).
        
        This is called when we receive feedback on whether the validation
        decision was correct (e.g., item was successfully matched).
        
        Args:
            request_id: Request to update
            actual_valid: Actual validation outcome
        """
        for entry in reversed(self.data):  # Search from end
            if entry.get("request_id") == request_id:
                entry["outcome"] = 1 if (entry["predicted_valid"] == actual_valid) else 0
                entry["ground_truth"] = actual_valid
                entry["outcome_timestamp"] = datetime.now().isoformat()
                self._save()
                logger.info(f"Recorded outcome for {request_id}")
                return True
        
        logger.warning(f"Request {request_id} not found")
        return False
    
    def get_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get calibration training data as numpy arrays.
        
        Returns:
            Tuple of (confidences, outcomes) for calibrator training
        """
        complete = [d for d in self.data if d.get("outcome") is not None]
        
        if not complete:
            return np.array([]), np.array([])
        
        confidences = np.array([d["confidence"] for d in complete])
        outcomes = np.array([d["outcome"] for d in complete])
        
        return confidences, outcomes
    
    def train_calibrator(self, method: str = "isotonic"):
        """
        Train a calibrator on collected data.
        
        Returns:
            Fitted ConfidenceCalibrator or None if insufficient data
        """
        from src.intelligence.confidence_calibration import ConfidenceCalibrator
        
        confidences, outcomes = self.get_training_data()
        
        if len(confidences) < 30:
            logger.warning(f"Only {len(confidences)} samples, need at least 30 for reliable calibration")
            return None
        
        calibrator = ConfidenceCalibrator(method=method)
        calibrator.fit(confidences, outcomes)
        
        # Save the trained calibrator
        calibrator.save(f"models/calibrator_{method}.pkl")
        
        logger.info(f"Trained {method} calibrator on {len(confidences)} samples")
        return calibrator


def main():
    """Demo: Run real validation evaluation on available images."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run real validation pipeline evaluation')
    parser.add_argument('--images-dir', default='data/image_dataset', help='Directory with test images')
    parser.add_argument('--output-dir', default='paper/real_results', help='Output directory')
    parser.add_argument('--max-images', type=int, default=50, help='Maximum images to evaluate')
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("REAL VALIDATION PIPELINE EVALUATOR")
    print(f"{'='*60}")
    
    evaluator = RealValidationEvaluator(
        image_dataset_dir=args.images_dir,
        output_dir=args.output_dir,
    )
    
    # Initialize components
    available = evaluator.initialize_components()
    print(f"\nAvailable components:")
    for name, status in available.items():
        print(f"  {name}: {'✅' if status else '❌'}")
    
    # Find test images
    image_dir = Path(args.images_dir)
    if image_dir.exists():
        images = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
        images = images[:args.max_images]
        
        print(f"\nFound {len(images)} test images")
        
        # Create test cases from images
        test_cases = []
        for img_path in images:
            test_cases.append({
                "image_path": str(img_path),
                "text_description": f"Found item: {img_path.stem}",
                "item_type": "default",
                "location": "library",
                "time_period": "afternoon",
            })
        
        if test_cases:
            metrics = evaluator.evaluate_dataset(test_cases)
            
            print(f"\n{'='*40}")
            print("EVALUATION METRICS")
            print(f"{'='*40}")
            print(f"Total cases: {metrics['total_cases']}")
            print(f"Latency (mean): {metrics['latency']['mean']:.3f}s")
            print(f"Latency (P95): {metrics['latency']['p95']:.3f}s")
            print(f"Confidence (mean): {metrics['confidence_distribution']['mean']:.2f}")
            
            if metrics.get('accuracy') is not None:
                print(f"Accuracy: {metrics['accuracy']:.2%}")
                print(f"F1 Score: {metrics['f1_score']:.2f}")
            
            # Save results
            evaluator.save_results()
            evaluator.save_calibration_data()
    else:
        print(f"\n⚠️ Image directory not found: {image_dir}")
        print("Creating sample evaluation with synthetic data...")
        
        # Demo with synthetic test cases
        from scripts.benchmark_generator import BenchmarkGenerator
        
        gen = BenchmarkGenerator(seed=42)
        gen.generate_full_benchmark(positive_count=20, discrepancy_count=5, implausible_count=3, low_quality_count=2)
        
        test_cases = [
            {
                "text_description": tc.description,
                "item_type": tc.item_type,
                "location": tc.location,
                "time_period": tc.time_period,
                "expected_valid": tc.expected_valid,
            }
            for tc in gen.test_cases[:30]
        ]
        
        metrics = evaluator.evaluate_dataset(test_cases)
        evaluator.save_results()
        
        print(f"\nMetrics: {json.dumps(metrics, indent=2, default=str)}")
    
    print(f"\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()
