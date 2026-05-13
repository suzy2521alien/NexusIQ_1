#!/usr/bin/env python3
"""
Training script for Intent Detection Model
Run this in Google Colab for GPU training
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
import torch
from torch.utils.data import Dataset

# Scam categories
LABELS = [
    "investment_scam",
    "romance_scam",
    "phishing",
    "job_scam",
    "impersonation",
    "general_fraud"
]

class ScamDataset(Dataset):
    def __init__(self, texts, labels, tokenizer):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def train_intent_model():
    # Load sample training data (replace with your dataset)
    # Format: CSV with columns 'text' and 'label'
    data = {
        'text': [
            "Invest $5000 now and get $20000 back immediately",
            "I love you, send me money for my sick mother",
            "Click this link to verify your account",
            "Great job opportunity, send resume and fee",
            "I'm from the IRS, you owe taxes",
            "Your package is delayed, pay shipping fee"
        ],
        'label': [0, 1, 2, 3, 4, 5]  # Corresponding to LABELS
    }

    df = pd.DataFrame(data)

    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df['text'].tolist(), df['label'].tolist(), test_size=0.2
    )

    # Initialize tokenizer and model
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased',
        num_labels=len(LABELS)
    )

    # Create datasets
    train_dataset = ScamDataset(train_texts, train_labels, tokenizer)
    val_dataset = ScamDataset(val_texts, val_labels, tokenizer)

    # Training arguments
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )

    # Train
    trainer.train()

    # Save model
    model.save_pretrained('./intent_model')
    tokenizer.save_pretrained('./intent_model')

    print("Model trained and saved to ./intent_model")

if __name__ == "__main__":
    train_intent_model()