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

