## Run the research pipeline (defensive smishing detection)

Full system overview (data → NLP → ML → web UI + stack): [`docs/SYSTEM_AND_TECH_STACK.md`](docs/SYSTEM_AND_TECH_STACK.md).

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

### One-command retrain (recommended)

Pick a dataset preset; everything else runs automatically (normalize → splits → train → test metrics):

```bash
.\.venv\Scripts\python scripts\train_full_pipeline.py --dataset dataset1
.\.venv\Scripts\python scripts\train_full_pipeline.py --dataset uci
```

Optional: custom input path:

```bash
.\.venv\Scripts\python scripts\train_full_pipeline.py --dataset dataset1 --input path\to\your.csv
.\.venv\Scripts\python scripts\train_full_pipeline.py --dataset uci --input data\raw\SMSSpamCollection
```

Evaluation writes **new timestamped files** each run (`reports/metrics_ml_test_<UTC>.json`, `reports/pred_ml_test_<UTC>.csv`). To replace the fixed filenames instead:

```bash
.\.venv\Scripts\python experiments\evaluate_ml.py --overwrite
.\.venv\Scripts\python scripts\train_full_pipeline.py --dataset dataset1 --eval-overwrite
```

Skip evaluation only:

```bash
.\.venv\Scripts\python scripts\train_full_pipeline.py --dataset dataset1 --no-eval
```

---

### 1) Put Dataset1.csv on disk (recommended)

This repo already includes `ml-backend/dataset/Dataset1.csv`.

### 2) Normalize and split the dataset

```bash
.\.venv\Scripts\python scripts\load_dataset1.py
.\.venv\Scripts\python scripts\make_splits.py --in data/processed/dataset1.csv
```

Outputs:
- `data/processed/dataset1.csv`
- `data/splits/train.csv`, `val.csv`, `test.csv`

### 3) Train ML (TF‑IDF + Logistic Regression)

```bash
.\.venv\Scripts\python experiments\train.py
```

Outputs:
- `ml-backend/artifacts/pipeline_lr_tfidf.joblib`
- `ml-backend/artifacts/pipeline_lr_tfidf.meta.json`

### 4) Evaluate ML on the **test** split

```bash
.\.venv\Scripts\python experiments\evaluate_ml.py
```

Outputs (default: **new files each run**, UTC timestamp in the filename):

- `reports/metrics_ml_test_<YYYYMMDD_HHMMSS>.json`
- `reports/pred_ml_test_<YYYYMMDD_HHMMSS>.csv`

Overwrite the canonical names instead:

```bash
.\.venv\Scripts\python experiments\evaluate_ml.py --overwrite
```

### Optional: run the UCI dataset instead

If you want to run the UCI SMS Spam Collection pipeline instead, place the raw file at `data/raw/SMSSpamCollection` and run:

```bash
.\.venv\Scripts\python scripts\load_uci_sms.py
.\.venv\Scripts\python scripts\make_splits.py --in data/processed/uci_sms.csv
```



 .\.venv\Scripts\python scripts\train_full_pipeline.py --dataset dataset1

