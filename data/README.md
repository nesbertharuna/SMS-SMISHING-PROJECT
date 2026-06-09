## Data folder

This repo expects the UCI SMS Spam Collection raw file to be placed manually:

- Input: `data/raw/SMSSpamCollection` (tab-separated, no header: `ham<TAB>message` or `spam<TAB>message`)
- Output (generated): `data/processed/uci_sms.csv`
- Output (generated splits): `data/splits/train.csv`, `data/splits/val.csv`, `data/splits/test.csv`

To generate the processed CSV + splits, run from the repo root:

```bash
py -3 scripts/load_uci_sms.py
py -3 scripts/make_splits.py
```

# Data folder

This repository expects **public or synthetic** SMS datasets only. Do not place real inbox exports or any PII here.

## UCI SMS Spam Collection (manual step)

1. Download the **SMS Spam Collection** dataset from the UCI Machine Learning Repository.
2. Place the raw file at:

`data/raw/SMSSpamCollection`

That file is typically tab-separated with **two columns** and **no header**:

- column 1: `ham` or `spam`
- column 2: message text

## Outputs produced by scripts

- `data/processed/uci_sms.csv`: normalized CSV with columns `label` (0/1) and `message`
- `data/splits/train.csv`, `val.csv`, `test.csv`: stratified splits

## Data collection (manual + public sources)

Collect your own labelled SMS samples (thesis / Zimbabwe-style smishing examples):

```bash
# Interactive: type label, message, feature_notes
python scripts/collect_sms.py add

# One-shot from command line
python scripts/collect_sms.py add --label smishing --message "Your OTP is required..." --feature-notes "urgency, credential_request"

# Import a batch CSV or JSONL (see data/raw/collected_sms_template.csv)
python scripts/collect_sms.py import data/raw/collected_sms_template.csv --dedupe

# Show counts
python scripts/collect_sms.py stats
```

Download public benchmark data (UCI SMS Spam Collection):

```bash
python scripts/download_datasets.py --uci --uci-to-collected
```

Merge collected + optional UCI into `ml-backend/dataset/Dataset1.csv`:

```bash
python scripts/merge_datasets.py --only-collected
python scripts/merge_datasets.py --include-existing --include-uci
```

Then train as usual:

```bash
python scripts/train_full_pipeline.py --dataset dataset1
```

