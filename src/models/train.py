import os
import json
import torch
from transformers import AutoProcessor, AutoModelForCausalLM, Trainer, TrainingArguments, EarlyStoppingCallback
from sklearn.model_selection import train_test_split
from src.data.synthetic_generator import generate_synthetic_data
from loguru import logger
import warnings
warnings.filterwarnings("ignore")

def train_lightweight():
    logger.info("Starting lightweight fine-tuning on synthetic data...")
    
    data_dir = "data/raw"
    if not os.path.exists(data_dir):
        generate_synthetic_data(count=1300)
    
    gt_path = os.path.join(data_dir, "ground_truth.json")
    if not os.path.exists(gt_path):
        logger.warning(f"Ground truth not found at {gt_path}, generating...")
        generate_synthetic_data(count=1300)
    
    with open(gt_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    
    # Split: 70/15/15
    train_data, temp = train_test_split(dataset, test_size=0.30, random_state=42)
    val_data, test_data = train_test_split(temp, test_size=0.50, random_state=42)
    
    logger.info(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")
    
    processor = AutoProcessor.from_pretrained("microsoft/Florence-2-base", trust_remote_code=True)
    
    # CPU fallback: float32, no device_map
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Florence-2-base",
        torch_dtype=torch.float32,
        trust_remote_code=True,
        attn_implementation="eager"  # CPU-compatible
    )
    
    # Simplified dataset wrapper
    class MedDataset(torch.utils.data.Dataset):
        def __init__(self, data, processor):
            self.data = data
            self.processor = processor
        def __len__(self): return len(self.data)
        def __getitem__(self, i):
            prompt = f"<OCR> {self.data[i].get('prompt', '')}"
            enc = self.processor.tokenizer.encode(prompt, return_tensors="pt")
            return {"input_ids": enc[0], "labels": enc[0]}
    
    training_args = TrainingArguments(
        output_dir="logs/training",
        per_device_train_batch_size=1,  # CPU için küçük batch
        gradient_accumulation_steps=4,
        learning_rate=2e-5,
        num_train_epochs=2,  # Test için 2 epoch (production'da 5)
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        report_to="none",
        logging_dir="logs/training",
        fp16=False,  # CPU'da float32
        remove_unused_columns=False
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=MedDataset(train_data, processor),
        eval_dataset=MedDataset(val_data, processor),
        callbacks=[EarlyStoppingCallback(early_stopping_patience=1)]
    )
    
    trainer.train()
    trainer.save_model("models/fine_tuned")
    logger.info("✅ Training completed. Model saved to models/fine_tuned")
    
    # Basit evaluation
    metrics = trainer.evaluate()
    logger.info(f"✅ Evaluation metrics: {metrics}")
    
    return metrics

if __name__ == "__main__":
    train_lightweight()