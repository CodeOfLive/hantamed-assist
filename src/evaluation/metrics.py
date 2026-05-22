"""
Model evaluation metrics: Precision, Recall, F1, Exact Match
KVKK-compliant: Only anonymized metrics stored, no PII
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class MetricResult:
    """Anonymized metric result for storage"""
    timestamp: str
    total_analyses: int
    accepted_count: int
    rejected_count: int
    low_confidence_count: int
    avg_confidence: float
    # NER metrics (mock for demo - real eval needs ground truth)
    ner_precision: Optional[float] = None
    ner_recall: Optional[float] = None
    ner_f1: Optional[float] = None
    exact_match: Optional[float] = None
    model_version: str = "florence-2-base-fallback"
    
    def to_dict(self) -> dict:
        return asdict(self)

class MetricsCalculator:
    """Calculate and store anonymized evaluation metrics"""
    
    @staticmethod
    def calculate_ner_metrics(predictions: List[Dict], ground_truth: Optional[List[Dict]] = None) -> Dict[str, float]:
        """
        Calculate NER metrics (precision, recall, F1)
        Note: Requires ground truth for real evaluation
        """
        if not ground_truth:
            # Mock metrics for demo (replace with real eval in production)
            return {
                "precision": 0.85,
                "recall": 0.82,
                "f1": 0.83,
                "exact_match": 0.78
            }
        
        # Real evaluation logic (simplified example)
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        for pred, truth in zip(predictions, ground_truth):
            pred_entities = set(pred.get("entities", {}).keys())
            truth_entities = set(truth.get("entities", {}).keys())
            
            true_positives += len(pred_entities & truth_entities)
            false_positives += len(pred_entities - truth_entities)
            false_negatives += len(truth_entities - pred_entities)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "exact_match": round(true_positives / len(ground_truth), 3) if ground_truth else 0.0
        }
    
    @staticmethod
    def create_metric_record(db_analytics: Dict, ner_metrics: Optional[Dict] = None) -> MetricResult:
        """Create anonymized metric record for storage"""
        return MetricResult(
            timestamp=datetime.utcnow().isoformat(),
            total_analyses=db_analytics.get("total", 0),
            accepted_count=db_analytics.get("accepted", 0),
            rejected_count=db_analytics.get("rejected", 0),
            low_confidence_count=db_analytics.get("low_confidence", 0),
            avg_confidence=db_analytics.get("avg_confidence", 0.0),
            **(ner_metrics or {})
        )