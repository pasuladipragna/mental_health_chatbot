import pandas as pd
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding
)
from datasets import Dataset
from sklearn.model_selection import train_test_split

# Load dataset
df = pd.read_csv(r"C:\Users\Pasul\OneDrive\Documents\Desktop\mental_health_chatbot\mental_health_chatbot.csv")

# Correct formatting: combine input and response into one sequence
df["text"] = df.apply(
    lambda row: f"User: {row['Situation'].strip()}\nBot: {row['empathetic_dialogues'].strip()}",
    axis=1
)

# Split dataset
train_df, val_df = train_test_split(df[["text"]], test_size=0.2, random_state=42)
train_dataset = Dataset.from_pandas(train_df)
val_dataset = Dataset.from_pandas(val_df)

# Load tokenizer and model
model_name = "microsoft/DialoGPT-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = 'left'

model = AutoModelForCausalLM.from_pretrained(model_name)

# Tokenization function
def tokenize(example):
    result = tokenizer(
        example["text"],
        truncation=True,
        padding="max_length",
        max_length=64  # reduced from 128
    )
    result["labels"] = result["input_ids"].copy()
    return result

train_dataset = train_dataset.map(tokenize, batched=True)
val_dataset = val_dataset.map(tokenize, batched=True)

# Data collator
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# Training arguments
args = TrainingArguments(
    output_dir="./chatbot_model_small",
    num_train_epochs=4,  # start with 3, then increase if needed
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=2,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_dir="./logs",
    logging_steps=10,
    fp16=True,  # ⚡ faster if your GPU supports it
    report_to="none"
)

# Trainer
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator
)

# Train and save
trainer.train()
trainer.save_model("./chatbot_model_small")
tokenizer.save_pretrained("./chatbot_model_small")
print("✅ Model trained and saved to ./chatbot_model_small")
