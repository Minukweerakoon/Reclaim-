"""
Calibration API Endpoint
Enables confidence calibration data collection and model training.

Part of Research Enhancement for Publication-Grade Metrics.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calibration", tags=["calibration"])


class CalibrationOutcomeRequest(BaseModel):
    """Request to record a validation outcome for calibration."""
    request_id: str
    predicted_valid: bool
    actual_valid: bool
    confidence: float
    component_scores: Optional[Dict] = None


class CalibrationTrainRequest(BaseModel):
    """Request to trigger calibrator training."""
    method: str = "isotonic"  # temperature, isotonic, or platt
    min_samples: int = 30


@router.post("/outcome")
async def record_calibration_outcome(request: CalibrationOutcomeRequest):
    """
    Record a validation outcome for calibrator training.
    
    Call this when you learn the true outcome of a validation decision,
    e.g., when an item is successfully matched or user confirms mismatch.
    
    This data trains the confidence calibrator for better routing decisions.
    
    Args:
        request_id: Unique identifier for the validation request
        predicted_valid: What the system predicted
        actual_valid: What actually happened (ground truth)
        confidence: The confidence score that was output
        component_scores: Optional breakdown of component scores
    """
    try:
        from scripts.real_validation_evaluator import CalibrationDataCollector
        
        collector = CalibrationDataCollector()
        
        # Record the prediction
        entry = collector.record_prediction(
            request_id=request.request_id,
            confidence=request.confidence,
            predicted_valid=request.predicted_valid,
            component_scores=request.component_scores,
        )
        
        # Record the outcome
        collector.record_outcome(request.request_id, request.actual_valid)
        
        return {
            "status": "recorded",
            "request_id": request.request_id,
            "outcome_correct": request.predicted_valid == request.actual_valid,
            "total_samples": len(collector.data),
            "samples_with_outcome": len([d for d in collector.data if d.get("outcome") is not None])
        }
        
    except ImportError:
        logger.warning("CalibrationDataCollector not available")
        return {
            "status": "unavailable",
            "message": "Calibration module not installed. Run: pip install scikit-learn"
        }
    except Exception as e:
        logger.error(f"Error recording calibration outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_calibrator(request: CalibrationTrainRequest):
    """
    Train the confidence calibrator on collected data.
    
    Call this after collecting sufficient validation outcomes (30+ recommended).
    The trained calibrator will be saved and used for future confidence calculations.
    
    Methods:
        - isotonic: Non-parametric, works well with small datasets
        - temperature: Single parameter scaling, simplest
        - platt: Logistic regression based
    """
    try:
        from scripts.real_validation_evaluator import CalibrationDataCollector
        
        collector = CalibrationDataCollector()
        
        # Check data availability
        data_with_outcomes = [d for d in collector.data if d.get("outcome") is not None]
        
        if len(data_with_outcomes) < request.min_samples:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {request.min_samples} samples with outcomes",
                "current_samples": len(data_with_outcomes),
                "hint": "Keep recording outcomes via /api/calibration/outcome"
            }
        
        calibrator = collector.train_calibrator(method=request.method)
        
        if calibrator is None:
            return {
                "status": "training_failed",
                "message": "Calibrator training failed. Check logs for details."
            }
        
        # Get calibration metrics
        import numpy as np
        confs = np.array([d["confidence"] for d in data_with_outcomes])
        outs = np.array([d["outcome"] for d in data_with_outcomes])
        metrics = calibrator.evaluate(confs, outs)
        
        return {
            "status": "trained",
            "method": request.method,
            "samples_used": len(data_with_outcomes),
            "ece": round(metrics.ece, 4),
            "avg_confidence": round(metrics.avg_confidence, 4),
            "model_path": f"models/calibrator_{request.method}.pkl",
            "message": "Calibrator trained successfully. Restart server to apply to live predictions."
        }
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return {
            "status": "error",
            "message": "Required modules not available. Install scikit-learn."
        }
    except Exception as e:
        logger.error(f"Error training calibrator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_calibration_stats():
    """
    Get calibration statistics and status.
    
    Returns information about:
    - Whether calibration is active
    - How much training data has been collected
    - Calibration method in use
    """
    try:
        result = {
            "calibrated": False,
            "data_collected": 0,
            "data_with_outcomes": 0,
        }
        
        # Check data collector
        try:
            from scripts.real_validation_evaluator import CalibrationDataCollector
            collector = CalibrationDataCollector()
            result["data_collected"] = len(collector.data)
            result["data_with_outcomes"] = len([d for d in collector.data if d.get("outcome") is not None])
        except ImportError:
            pass
        
        # Check if calibrator is loaded in consistency engine
        try:
            from src.cross_modal.consistency_engine import ConsistencyEngine
            engine = ConsistencyEngine()
            stats = engine.get_calibration_stats()
            result.update(stats)
        except Exception as e:
            result["engine_error"] = str(e)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting calibration stats: {e}")
        return {
            "calibrated": False,
            "error": str(e)
        }


@router.get("/training-data")
async def get_training_data_summary():
    """Get summary of collected calibration training data."""
    try:
        from scripts.real_validation_evaluator import CalibrationDataCollector
        import numpy as np
        
        collector = CalibrationDataCollector()
        
        if not collector.data:
            return {
                "total_samples": 0,
                "message": "No data collected yet. Use /api/calibration/outcome to record outcomes."
            }
        
        confs, outs = collector.get_training_data()
        
        if len(confs) == 0:
            return {
                "total_samples": len(collector.data),
                "samples_with_outcome": 0,
                "message": "Data collected but no outcomes recorded yet."
            }
        
        return {
            "total_samples": len(collector.data),
            "samples_with_outcome": len(confs),
            "confidence_stats": {
                "mean": float(np.mean(confs)),
                "std": float(np.std(confs)),
                "min": float(np.min(confs)),
                "max": float(np.max(confs)),
            },
            "accuracy_rate": float(np.mean(outs)),
            "ready_for_training": len(confs) >= 30,
        }
        
    except ImportError:
        return {"status": "unavailable", "message": "Required modules not installed"}
    except Exception as e:
        logger.error(f"Error getting training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
