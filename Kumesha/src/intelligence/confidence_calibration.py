"""
Confidence Calibration Module for Multimodal Validation System
Research-Grade Contribution: Calibrated Confidence Scores

This module addresses a critical research gap: ML models are often overconfident.
A model predicting 95% confidence might only be 70% accurate in practice.

Calibration Methods Implemented:
1. Temperature Scaling - Neural network calibration via single temperature parameter
2. Isotonic Regression - Non-parametric monotonic calibration
3. Platt Scaling - Logistic regression on logits

Metrics:
- Expected Calibration Error (ECE): Primary calibration metric
- Maximum Calibration Error (MCE): Worst-case calibration
- Reliability Diagrams: Visual calibration assessment

References:
- Guo et al. (2017) "On Calibration of Modern Neural Networks"
- Niculescu-Mizil & Caruana (2005) "Predicting Good Probabilities"
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CalibrationMetrics:
    """Calibration evaluation metrics."""
    ece: float  # Expected Calibration Error
    mce: float  # Maximum Calibration Error
    avg_confidence: float
    avg_accuracy: float
    overconfidence_gap: float  # avg_confidence - avg_accuracy
    num_samples: int
    bin_data: Dict[str, List[float]]


class ConfidenceCalibrator:
    """
    Calibrates model confidence scores to match empirical accuracy.
    
    Problem: Model predicts 90% confidence but only 70% are correct
    Solution: Learn calibration mapping: predicted → calibrated
    
    This is a key research contribution for routing decisions.
    """
    
    SUPPORTED_METHODS = ["temperature", "isotonic", "platt"]
    
    def __init__(self, method: str = "isotonic", n_bins: int = 15):
        """
        Initialize the confidence calibrator.
        
        Args:
            method: Calibration method ('temperature', 'isotonic', 'platt')
            n_bins: Number of bins for ECE calculation
        """
        if method not in self.SUPPORTED_METHODS:
            raise ValueError(f"Method must be one of {self.SUPPORTED_METHODS}")
        
        self.method = method
        self.n_bins = n_bins
        self.calibrator = None
        self.is_fitted = False
        
        # For temperature scaling
        self.temperature = 1.0
        
        # Calibration history for analysis
        self.calibration_history = []
    
    def fit(self, confidences: np.ndarray, outcomes: np.ndarray) -> "ConfidenceCalibrator":
        """
        Train calibrator on validation set.
        
        Args:
            confidences: Array of predicted confidence scores [0-1]
            outcomes: Array of binary outcomes (1=correct, 0=incorrect)
        
        Returns:
            self for chaining
        
        Example:
            confidences = np.array([0.95, 0.87, 0.62, 0.91])
            outcomes = np.array([1, 1, 0, 0])  # First two correct, last two wrong
            calibrator.fit(confidences, outcomes)
        """
        confidences = np.asarray(confidences).flatten()
        outcomes = np.asarray(outcomes).flatten()
        
        if len(confidences) != len(outcomes):
            raise ValueError("confidences and outcomes must have same length")
        
        if len(confidences) < 10:
            logger.warning(f"Only {len(confidences)} samples for calibration - results may be unreliable")
        
        logger.info(f"Fitting {self.method} calibrator with {len(confidences)} samples")
        
        if self.method == "temperature":
            self._fit_temperature(confidences, outcomes)
        elif self.method == "isotonic":
            self._fit_isotonic(confidences, outcomes)
        elif self.method == "platt":
            self._fit_platt(confidences, outcomes)
        
        self.is_fitted = True
        
        # Record calibration metrics
        metrics = self.evaluate(confidences, outcomes)
        self.calibration_history.append({
            "method": self.method,
            "num_samples": len(confidences),
            "ece_before": self._compute_ece_raw(confidences, outcomes),
            "ece_after": metrics.ece,
        })
        
        return self
    
    def _fit_temperature(self, confidences: np.ndarray, outcomes: np.ndarray):
        """Fit temperature scaling via grid search."""
        # Grid search for optimal temperature
        best_temp = 1.0
        best_ece = float('inf')
        
        for temp in np.linspace(0.1, 5.0, 100):
            calibrated = self._apply_temperature(confidences, temp)
            ece = self._compute_ece_raw(calibrated, outcomes)
            
            if ece < best_ece:
                best_ece = ece
                best_temp = temp
        
        self.temperature = best_temp
        logger.info(f"Optimal temperature: {best_temp:.3f} (ECE: {best_ece:.4f})")
    
    def _apply_temperature(self, confidences: np.ndarray, temperature: float) -> np.ndarray:
        """Apply temperature scaling to logits."""
        # Convert probabilities to logits, scale, convert back
        # Avoid log(0) and log(1)
        eps = 1e-7
        confidences_clipped = np.clip(confidences, eps, 1 - eps)
        logits = np.log(confidences_clipped / (1 - confidences_clipped))
        scaled_logits = logits / temperature
        return 1 / (1 + np.exp(-scaled_logits))
    
    def _fit_isotonic(self, confidences: np.ndarray, outcomes: np.ndarray):
        """Fit isotonic regression calibrator."""
        try:
            from sklearn.isotonic import IsotonicRegression
            self.calibrator = IsotonicRegression(
                y_min=0.0, y_max=1.0, out_of_bounds='clip'
            )
            self.calibrator.fit(confidences, outcomes)
        except ImportError:
            logger.error("sklearn not available for isotonic regression")
            raise
    
    def _fit_platt(self, confidences: np.ndarray, outcomes: np.ndarray):
        """Fit Platt scaling (logistic regression on confidences)."""
        try:
            from sklearn.linear_model import LogisticRegression
            self.calibrator = LogisticRegression(solver='lbfgs', max_iter=1000)
            self.calibrator.fit(confidences.reshape(-1, 1), outcomes)
        except ImportError:
            logger.error("sklearn not available for Platt scaling")
            raise
    
    def calibrate(self, confidence: float) -> float:
        """
        Calibrate a single confidence score.
        
        Args:
            confidence: Uncalibrated confidence score (0-1)
        
        Returns:
            Calibrated confidence score (0-1)
        
        Example:
            uncalibrated = 0.95  # Model says 95% confident
            calibrated = calibrator.calibrate(uncalibrated)
            # Returns 0.78 if model is overconfident
        """
        if not self.is_fitted:
            logger.warning("Calibrator not fitted, returning original confidence")
            return confidence
        
        confidence = np.clip(confidence, 0.0, 1.0)
        
        if self.method == "temperature":
            return float(self._apply_temperature(np.array([confidence]), self.temperature)[0])
        elif self.method == "isotonic":
            return float(self.calibrator.predict([confidence])[0])
        elif self.method == "platt":
            return float(self.calibrator.predict_proba([[confidence]])[0, 1])
        
        return confidence
    
    def calibrate_batch(self, confidences: np.ndarray) -> np.ndarray:
        """Calibrate a batch of confidence scores."""
        if not self.is_fitted:
            return confidences
        
        confidences = np.asarray(confidences).flatten()
        confidences = np.clip(confidences, 0.0, 1.0)
        
        if self.method == "temperature":
            return self._apply_temperature(confidences, self.temperature)
        elif self.method == "isotonic":
            return self.calibrator.predict(confidences)
        elif self.method == "platt":
            return self.calibrator.predict_proba(confidences.reshape(-1, 1))[:, 1]
        
        return confidences
    
    def _compute_ece_raw(self, confidences: np.ndarray, outcomes: np.ndarray) -> float:
        """Compute Expected Calibration Error without storing bin data."""
        bins = np.linspace(0, 1, self.n_bins + 1)
        ece = 0.0
        total = len(confidences)
        
        for i in range(self.n_bins):
            mask = (confidences >= bins[i]) & (confidences < bins[i + 1])
            if mask.sum() > 0:
                bin_conf = confidences[mask].mean()
                bin_acc = outcomes[mask].mean()
                bin_weight = mask.sum() / total
                ece += np.abs(bin_acc - bin_conf) * bin_weight
        
        return ece
    
    def evaluate(self, confidences: np.ndarray, outcomes: np.ndarray) -> CalibrationMetrics:
        """
        Evaluate calibration performance.
        
        Args:
            confidences: Predicted confidence scores (will be calibrated if fitted)
            outcomes: Binary outcomes (1=correct, 0=incorrect)
        
        Returns:
            CalibrationMetrics with ECE, MCE, and reliability diagram data
        """
        confidences = np.asarray(confidences).flatten()
        outcomes = np.asarray(outcomes).flatten()
        
        # Apply calibration if fitted
        if self.is_fitted:
            calibrated = self.calibrate_batch(confidences)
        else:
            calibrated = confidences
        
        bins = np.linspace(0, 1, self.n_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        ece = 0.0
        mce = 0.0
        total = len(calibrated)
        
        bin_accuracies = []
        bin_confidences = []
        bin_counts = []
        
        for i in range(self.n_bins):
            mask = (calibrated >= bins[i]) & (calibrated < bins[i + 1])
            count = mask.sum()
            
            if count > 0:
                bin_conf = calibrated[mask].mean()
                bin_acc = outcomes[mask].mean()
                bin_weight = count / total
                
                gap = np.abs(bin_acc - bin_conf)
                ece += gap * bin_weight
                mce = max(mce, gap)
                
                bin_accuracies.append(float(bin_acc))
                bin_confidences.append(float(bin_conf))
                bin_counts.append(int(count))
            else:
                bin_accuracies.append(None)
                bin_confidences.append(None)
                bin_counts.append(0)
        
        avg_confidence = float(calibrated.mean())
        avg_accuracy = float(outcomes.mean())
        
        return CalibrationMetrics(
            ece=float(ece),
            mce=float(mce),
            avg_confidence=avg_confidence,
            avg_accuracy=avg_accuracy,
            overconfidence_gap=avg_confidence - avg_accuracy,
            num_samples=len(outcomes),
            bin_data={
                "bin_centers": [float(x) for x in bin_centers],
                "accuracies": bin_accuracies,
                "confidences": bin_confidences,
                "counts": bin_counts,
            }
        )
    
    def generate_reliability_diagram(self, 
                                     confidences: np.ndarray, 
                                     outcomes: np.ndarray,
                                     output_path: str = "paper/figures/reliability_diagram.png",
                                     title: str = "Reliability Diagram") -> Optional[str]:
        """
        Generate a reliability diagram visualization.
        
        The diagram shows:
        - Bar chart of accuracy per confidence bin
        - Diagonal line representing perfect calibration
        - Gap between bars and diagonal shows calibration error
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
        except ImportError:
            logger.warning("matplotlib not available for visualization")
            return None
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        metrics = self.evaluate(confidences, outcomes)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Reliability diagram
        bin_centers = np.array(metrics.bin_data["bin_centers"])
        accuracies = metrics.bin_data["accuracies"]
        counts = metrics.bin_data["counts"]
        
        # Filter out empty bins
        valid_mask = [acc is not None for acc in accuracies]
        valid_centers = bin_centers[valid_mask]
        valid_accuracies = [acc for acc in accuracies if acc is not None]
        valid_counts = [c for c, acc in zip(counts, accuracies) if acc is not None]
        
        # Bar width
        width = 0.8 / self.n_bins
        
        # Accuracy bars
        bars = ax1.bar(valid_centers, valid_accuracies, width=width, 
                       color='#3498db', edgecolor='black', linewidth=0.5,
                       label='Accuracy', alpha=0.7)
        
        # Perfect calibration line
        ax1.plot([0, 1], [0, 1], 'k--', linewidth=2, label='Perfect Calibration')
        
        # Fill gap (calibration error visualization)
        for center, acc in zip(valid_centers, valid_accuracies):
            if acc < center:  # Overconfident
                ax1.fill_between([center - width/2, center + width/2], 
                                [acc, acc], [center, center],
                                color='red', alpha=0.3)
            else:  # Underconfident
                ax1.fill_between([center - width/2, center + width/2],
                                [center, center], [acc, acc],
                                color='green', alpha=0.3)
        
        ax1.set_xlabel('Confidence', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Accuracy', fontsize=12, fontweight='bold')
        ax1.set_title(f'{title}\nECE = {metrics.ece:.3f}, MCE = {metrics.mce:.3f}', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlim([0, 1])
        ax1.set_ylim([0, 1])
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Histogram of confidence distribution
        ax2.bar(valid_centers, valid_counts, width=width,
               color='#2ecc71', edgecolor='black', linewidth=0.5, alpha=0.7)
        ax2.set_xlabel('Confidence', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax2.set_title('Confidence Distribution', fontsize=14, fontweight='bold')
        ax2.set_xlim([0, 1])
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Reliability diagram saved to: {output_path}")
        return output_path
    
    def save(self, path: str):
        """Save calibrator to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "method": self.method,
            "n_bins": self.n_bins,
            "temperature": self.temperature,
            "is_fitted": self.is_fitted,
            "calibration_history": self.calibration_history,
        }
        
        if self.method in ["isotonic", "platt"] and self.calibrator is not None:
            state["calibrator"] = self.calibrator
        
        with open(path, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"Calibrator saved to: {path}")
    
    @classmethod
    def load(cls, path: str) -> "ConfidenceCalibrator":
        """Load calibrator from disk."""
        with open(path, 'rb') as f:
            state = pickle.load(f)
        
        calibrator = cls(method=state["method"], n_bins=state["n_bins"])
        calibrator.temperature = state["temperature"]
        calibrator.is_fitted = state["is_fitted"]
        calibrator.calibration_history = state.get("calibration_history", [])
        
        if "calibrator" in state:
            calibrator.calibrator = state["calibrator"]
        
        logger.info(f"Calibrator loaded from: {path}")
        return calibrator


class CalibrationEvaluator:
    """
    Evaluates and compares different calibration methods.
    """
    
    def __init__(self):
        self.methods = ["temperature", "isotonic", "platt"]
        self.results = {}
    
    def compare_methods(self, 
                       confidences: np.ndarray, 
                       outcomes: np.ndarray,
                       validation_split: float = 0.5) -> Dict[str, CalibrationMetrics]:
        """
        Compare all calibration methods on the same data.
        
        Args:
            confidences: All confidence scores
            outcomes: All outcomes
            validation_split: Fraction for calibration (rest for evaluation)
        
        Returns:
            Dictionary mapping method name to CalibrationMetrics
        """
        n = len(confidences)
        split_idx = int(n * validation_split)
        
        # Shuffle for random split
        indices = np.random.permutation(n)
        train_idx = indices[:split_idx]
        test_idx = indices[split_idx:]
        
        train_conf = confidences[train_idx]
        train_out = outcomes[train_idx]
        test_conf = confidences[test_idx]
        test_out = outcomes[test_idx]
        
        # Evaluate uncalibrated baseline
        uncalibrated = ConfidenceCalibrator(method="isotonic")  # Won't fit
        self.results["uncalibrated"] = CalibrationMetrics(
            ece=uncalibrated._compute_ece_raw(test_conf, test_out),
            mce=0.0,  # Not computed for baseline
            avg_confidence=float(test_conf.mean()),
            avg_accuracy=float(test_out.mean()),
            overconfidence_gap=float(test_conf.mean() - test_out.mean()),
            num_samples=len(test_out),
            bin_data={}
        )
        
        for method in self.methods:
            try:
                calibrator = ConfidenceCalibrator(method=method)
                calibrator.fit(train_conf, train_out)
                metrics = calibrator.evaluate(test_conf, test_out)
                self.results[method] = metrics
                logger.info(f"{method}: ECE = {metrics.ece:.4f}")
            except Exception as e:
                logger.error(f"Failed to evaluate {method}: {e}")
        
        return self.results
    
    def generate_comparison_table(self, output_path: str = "paper/tables/calibration_comparison.tex"):
        """Generate LaTeX table comparing calibration methods."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        latex = r"""\begin{table}[t]
\centering
\caption{Calibration Method Comparison. Lower ECE is better.}
\label{tab:calibration}
\begin{tabular}{lccc}
\toprule
\textbf{Method} & \textbf{ECE} & \textbf{Avg. Confidence} & \textbf{Overconf. Gap} \\
\midrule
"""
        
        for method in ["uncalibrated", "temperature", "isotonic", "platt"]:
            if method not in self.results:
                continue
            
            m = self.results[method]
            display_name = method.title()
            
            latex += f"{display_name} & {m.ece:.4f} & {m.avg_confidence:.2%} & {m.overconfidence_gap:+.2%} \\\\\n"
        
        latex += r"""\bottomrule
\end{tabular}
\end{table}
"""
        
        with open(output_path, 'w') as f:
            f.write(latex)
        
        logger.info(f"Comparison table saved to: {output_path}")
        return latex


# Standalone evaluation script
def main():
    """Demonstration of confidence calibration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate confidence calibration')
    parser.add_argument('--samples', type=int, default=500, help='Number of synthetic samples')
    parser.add_argument('--method', default='isotonic', choices=['temperature', 'isotonic', 'platt'])
    parser.add_argument('--output-dir', default='paper', help='Output directory')
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("CONFIDENCE CALIBRATION EVALUATION")
    print(f"{'='*60}")
    
    # Generate synthetic overconfident predictions
    np.random.seed(42)
    n = args.samples
    
    # Simulate overconfident model: predicts high confidence but accuracy is lower
    # True accuracy around 75%, but model says 85%
    true_accuracy = 0.75
    overconfidence = 0.15
    
    outcomes = np.random.binomial(1, true_accuracy, n)
    
    # Generate overconfident predictions
    base_conf = np.random.beta(8, 2, n)  # Skewed towards high confidence
    noise = np.random.normal(0, 0.05, n)
    confidences = np.clip(base_conf + noise, 0.01, 0.99)
    
    print(f"Samples: {n}")
    print(f"True accuracy: {outcomes.mean():.2%}")
    print(f"Avg. confidence (before): {confidences.mean():.2%}")
    print(f"Overconfidence gap: {confidences.mean() - outcomes.mean():+.2%}")
    
    # Compute ECE before calibration
    calibrator = ConfidenceCalibrator(method=args.method)
    ece_before = calibrator._compute_ece_raw(confidences, outcomes)
    print(f"ECE (before): {ece_before:.4f}")
    
    # Split into train/test
    split = int(0.6 * n)
    train_conf, test_conf = confidences[:split], confidences[split:]
    train_out, test_out = outcomes[:split], outcomes[split:]
    
    # Fit calibrator
    calibrator.fit(train_conf, train_out)
    
    # Evaluate on test set
    metrics = calibrator.evaluate(test_conf, test_out)
    print(f"\nAfter {args.method} calibration:")
    print(f"ECE (after): {metrics.ece:.4f}")
    print(f"Avg. confidence: {metrics.avg_confidence:.2%}")
    print(f"Overconfidence gap: {metrics.overconfidence_gap:+.2%}")
    
    # Generate reliability diagram
    diagram_path = f"{args.output_dir}/figures/reliability_diagram.png"
    calibrator.generate_reliability_diagram(test_conf, test_out, diagram_path)
    
    # Save calibrator
    calibrator.save(f"{args.output_dir}/models/calibrator_{args.method}.pkl")
    
    # Compare all methods
    print(f"\n{'='*60}")
    print("COMPARING ALL CALIBRATION METHODS")
    print(f"{'='*60}")
    
    evaluator = CalibrationEvaluator()
    results = evaluator.compare_methods(confidences, outcomes)
    
    for method, m in results.items():
        print(f"{method:15s}: ECE = {m.ece:.4f}, Gap = {m.overconfidence_gap:+.2%}")
    
    evaluator.generate_comparison_table(f"{args.output_dir}/tables/calibration_comparison.tex")
    
    print(f"\n✅ Calibration evaluation complete!")
    print(f"📈 Diagram: {diagram_path}")


if __name__ == "__main__":
    main()
