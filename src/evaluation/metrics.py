import json
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
import numpy as np

def evaluate_predictions(pred_file: str, gt_file: str) -> dict:
    try:
        with open(pred_file) as f: preds = json.load(f)
        with open(gt_file) as f: gt = json.load(f)
        
        p, r, f, _ = precision_recall_fscore_support(
            [1]*len(preds), [1 if len(v)>0 else 0 for v in preds.values()], average='binary'
        )
        exact_match = sum(1 for p, g in zip(preds, gt) if str(preds[p]) == str(gt[g])) / max(len(gt), 1)
        return {"Precision": p, "Recall": r, "F1": f, "ExactMatch": exact_match}
    except Exception as e:
        return {"error": str(e)}