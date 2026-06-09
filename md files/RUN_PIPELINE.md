## Run the research pipeline (defensive smishing detection)

This implements the phases in `RESEARCH_PIPELINE_AND_STEPS.md` as runnable scripts.

### 0) Create a venv and install dependencies

In PowerShell from the repo root:

```bash
py -3 -m venv .venv
.\.venv\Scripts\python -m ensurepip --upgrade
.\.venv\Scripts\python -m pip install -r "ml-backend\requirements.txt"
```

If downloads are slow, retry with higher timeouts:

```bash
.\.venv\Scripts\python -m pip install --default-timeout 120 --retries 10 -r "ml-backend\requirements.txt"
```

### 1) Put the UCI dataset on disk

Place the raw file at `data/raw/SMSSpamCollection` (see `data/README.md`).

### 2) Normalize and split the dataset

```bash
.\.venv\Scripts\python scripts\load_uci_sms.py
.\.venv\Scripts\python scripts\make_splits.py
```

Outputs:
- `data/processed/uci_sms.csv`
- `data/splits/train.csv`, `val.csv`, `test.csv`

### 3) Train ML (TF‑IDF + Logistic Regression)

```bash
.\.venv\Scripts\python experiments\train.py
```

Outputs:
- `ml-backend/artifacts/pipeline_lr_tfidf.joblib`
- `ml-backend/artifacts/pipeline_lr_tfidf.meta.json`

### 4) Evaluate ML and rules on the **test** split

```bash
.\.venv\Scripts\python experiments\evaluate_ml.py
.\.venv\Scripts\python experiments\evaluate_rules.py
```

Outputs:
- `reports/metrics_ml_test.json`, `reports/pred_ml_test.csv`
- `reports/metrics_rules_test.json`, `reports/pred_rules_test.csv`

### 5) Compare ML vs rules + McNemar test

```bash
.\.venv\Scripts\python experiments\compare_ml_vs_rules.py
```

Output:
- `reports/compare_ml_vs_rules.json`

