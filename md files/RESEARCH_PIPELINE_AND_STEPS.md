# Smishing ML project — step-by-step guide (for you + Cursor)

Use this file as the **single source of truth** for what to build and in what order. **Paste sections into Cursor chat** (or say *“follow RESEARCH_PIPELINE_AND_STEPS.md Phase B”*) so the assistant knows exactly what you want without redoing planning.

**Scope of this document:** instructions and checklists only — no dataset downloads, no trained model files, and no code *implementation* here. You (with Cursor) execute each step in your repo.

---

## How to use this with Cursor

1. **Open this file** in the editor alongside chat.
2. For each phase, use a prompt like:  
   *“Read `RESEARCH_PIPELINE_AND_STEPS.md`. Complete Phase B only: add a script that loads UCI SMS Spam Collection from `data/raw/`, outputs `data/splits/train.csv`, `val.csv`, `test.csv` with stratified split and random_state=42. Do not touch the mobile app yet.”*
3. After each phase, **tick the checklist** in your own notes (or duplicate the checklist into a `PROGRESS.md` if you like).
4. **Never fit** the vectoriser or model on the **test** set — only train (and optionally validation) for fitting; test is for **final numbers** only.

---

## Part A — Your research objectives (what “done” looks like)

You must be able to **show evidence** for each objective. Below: objective → what you deliver → how you know it’s met.

| # | Research objective | What you deliver | “Done” checklist |
|---|-------------------|------------------|------------------|
| **1** | Evaluate limitations and **false negative** rates of rule-based SMS filtering on **obfuscated** malicious texts | A **fixed** rule baseline (keywords + patterns); a list of **obfuscated** malicious test messages; metrics on that subset | You report **FN rate** (or recall on malicious class for rules) on obfuscated set; you show **concrete examples** where rules fail |
| **2** | Extract and identify **critical** linguistic, structural, behavioural features | Written feature definition + **numbers** (feature importances, top TF‑IDF terms, or coefficient tables) | You can name **which features** matter most and show **evidence** (tables/plots) tied to ham vs spam |
| **3** | Design, train, validate a **supervised** ML model (binary: benign vs malicious); **simulated real-time** | Train/val/test split; saved trained **Pipeline**; script that scores **one** or **many** new SMS strings | Model trains without errors; **held-out test** metrics exist; optional: you note **inference time** per message or per batch |
| **4** | **Compare** ML vs traditional (rule/keyword) using **accuracy, precision, recall, F1** | Same test messages scored by **both** systems; comparison table + optional **McNemar** + optional **bootstrap CIs** | Side-by-side metrics on **identical** test set; hypothesis (H₀/H₁) addressed with your chosen statistical test |

**Research questions (RQ1–RQ4)** are answered by the same work: Obj 1 → RQ1; Obj 2 → RQ2; Obj 3 → RQ3; Obj 4 → RQ4 + hypotheses.

---

## Part B — What “the system works” means (acceptance test)

Treat the project as **working** when all of the following are true:

1. **Data:** You have one labelled dataset (at minimum UCI ham/spam) in CSV form with columns for text and binary (or ham/spam) label.
2. **Splits:** `train` / `val` / `test` files exist; test was **not** used for any fitting or hyperparameter choice.
3. **ML pipeline:** One saved object (e.g. sklearn `Pipeline`: vectoriser → classifier) loads with joblib and `predict`s on new strings.
4. **Metrics:** On the **test** set you print (or save) at least **accuracy, precision, recall, F1** for the malicious class (and optionally macro/weighted).
5. **Baseline:** Rule-based detector runs on the **same** test messages; you can compare columns of predictions.
6. **Thesis link:** One short document or appendix section maps **each objective** to a **figure or table** in your dissertation.

Optional for “strong” demo: mobile app or API calls the saved pipeline — not required for objectives if your write-up focuses on Python evaluation.

---

## Part C — End-to-end pipeline (one sentence per stage)

```
Labelled SMS → clean/tokenise (preprocessing) → numeric features (e.g. TF-IDF)
    → train classifier on TRAIN features only
    → tune using VAL (or CV on train)
    → final numbers on TEST only
    → run same TEST SMS through rules
    → compare + (optional) McNemar / bootstrap
```

**NLP and ML are not two separate mystery systems:** NLP here means **featurisation** of the **same** SMS you already labelled. The classifier learns from those features.

---

## Part D — Step-by-step phases (do in order)

### Phase 0 — Machine and Python

1. Create a **virtual environment** (recommended).
2. Use **one** Python consistently (on Windows, `py -3` is often safer than `python` if the Store shim breaks).
3. Install dependencies: start from `ml-backend/requirements.txt`, then add whatever your scripts need (`pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `nltk`, …) and **pin versions** in that file when stable.
4. Set **global seeds** (`random_state=42`, NumPy, etc.) anywhere randomness affects splits or training.

**Cursor prompt example:** *“Add a `requirements-ml.txt` or extend `ml-backend/requirements.txt` with pinned pandas, numpy, scikit-learn for SMS classification. No application code yet.”*

---

### Phase 1 — Get data on disk

1. Download **UCI SMS Spam Collection** (official source: UCI Machine Learning Repository — SMS Spam Collection). File is typically tab-separated: `ham`/`spam` + message.
2. Save it under something like `data/raw/SMSSpamCollection` (no secrets; public data).
3. Optional: add your **synthetic Zimbabwe-style** CSV with the **same** column layout; merge with a `source` column so you can filter in analysis later.
4. **Deduplicate** exact duplicate lines; log how many rows removed.
5. Standardise labels to **binary**: e.g. `0` = benign (ham), `1` = malicious (spam) — pick one convention and **use it everywhere**.

**Cursor prompt example:** *“Add `data/raw/.gitkeep` and a README note that SMSSpamCollection must be placed manually. Add `scripts/load_uci_sms.py` that reads the file path as an argument and returns a pandas DataFrame with columns `label`, `message`.”*

---

### Phase 2 — Split data (train / validation / test)

1. From the full cleaned table, create **stratified** splits (preserve spam proportion in each split). Example ratio from your methodology: **70% / 15% / 15%** — adjust if your supervisor prefers another standard.
2. Save three CSVs, e.g. `data/splits/train.csv`, `val.csv`, `test.csv`.
3. **Lock** the test file: after this step, you only use test for **final** evaluation scripts, not for tuning.

**Cursor prompt example:** *“Create `scripts/make_splits.py` reading merged CSV, stratified 70/15/15, random_state=42, write to data/splits/. Print class counts per split.”*

---

### Phase 3 — Preprocessing (text → clean text)

1. Decide rules: lowercase, whitespace, URL handling (keep vs strip vs separate flag), digits/currency, encoding fixes.
2. Optional: NLTK tokeniser, stopword list, stemming/lemmatisation — **must be identical** in training pipeline and at inference.
3. Implement preprocessing either inside a sklearn `Pipeline` preprocessor or in a function the vectoriser calls — **consistency** matters more than fancy tricks for the MVP.

**Existing code to extend:** `ml-backend/preprocessing/clean_text.py`

**Cursor prompt example:** *“Align `clean_text.py` behaviour with the thesis preprocessing section: document each step in a docstring and ensure the same function is used by TfidfVectorizer’s preprocessor in training.”*

---

### Phase 4 — Feature extraction (RQ2 / Obj 2)

1. **Minimum:** `TfidfVectorizer` with chosen `max_features`, `ngram_range`, `min_df`, `max_df`. Fit on **train messages only**; `transform` val and test.
2. **Optional:** hand-crafted columns (length, URL flag, phone regex flag, …) merged with TF-IDF via sparse hstack + scaler (fit scaler on train only).
3. **Optional later:** GloVe averages, DistilBERT embeddings (heavier compute).

**Existing code to extend:** `ml-backend/feature-extraction/tfidf_features.py`, `ml-backend/models/train_model.py`

**Cursor prompt example:** *“Build a sklearn Pipeline: TF-IDF from Phase 4 settings + LogisticRegression(class_weight='balanced'). Fit on train.csv only; save with joblib to ml-backend/artifacts/. Use picklable preprocessor only.”*

---

### Phase 5 — Train and tune ML (RQ3 / Obj 3)

1. Fit pipeline on **training** rows.
2. Tune hyperparameters using **validation** set or **k-fold CV on train** — not using test scores for choices.
3. When hyperparameters are fixed, optionally refit on **train+val** once (document this); then produce **final** test metrics in a separate script run.
4. Save: fitted `Pipeline`, a small JSON/YAML of hyperparameters and training date, and path to data snapshot or checksum.

**Cursor prompt example:** *“Add `experiments/train.py` that reads train.csv, fits Pipeline, saves joblib + config JSON. Add `experiments/tune.py` or GridSearchCV block guarded so test.csv is never loaded during tuning.”*

---

### Phase 6 — Rule baseline + obfuscation (RQ1 / Obj 1)

1. Freeze a **rule configuration** (thresholds, keyword lists) — document it as your “traditional” baseline.
2. Apply `detect_smishing`-style logic (or extended rules) to every message in **test** set; store `y_pred_rules` (binary suspicious vs not — map clearly to ham/spam if your rules output score+threshold).
3. Build **obfuscated** malicious subset (manual list or script): substitutions, extra spaces, mixed case, shortened URL style strings, benign prefix + malicious tail.
4. Report rule **false negatives** on that subset (malicious labelled as benign by rules).

**Existing code:** `ml-backend/rule-engine/rules.py`

**Cursor prompt example:** *“Add `experiments/evaluate_rules.py` that loads test.csv, runs rules.py, outputs confusion matrix and recall for malicious class vs ground truth.”*

---

### Phase 7 — Compare ML vs rules (RQ4 / Obj 4 + hypotheses)

1. Load **same** `test.csv` true labels `y_true`.
2. Load ML `y_pred_ml` from saved pipeline `predict` (or `predict_proba` + threshold — if threshold, tune threshold on **val** only, not test).
3. Load `y_pred_rules`.
4. Build table: accuracy, precision, recall, F1 for **both** systems (define whether you report **per-class** for malicious vs **macro/weighted** — state it in the thesis).
5. Optional **McNemar:** paired test on ML vs rules disagreements with ground truth on the test set; report p-value vs 0.05.
6. Optional **bootstrap:** 1000 resamples of test rows to get 95% CI for F1 (or difference).

**Cursor prompt example:** *“Add `experiments/compare_ml_vs_rules.py` that loads test.csv, loads joblib pipeline, prints sklearn classification_report and confusion_matrix for ML and rules, then runs scipy.stats McNemar if both prediction arrays exist.”*

---

### Phase 8 — Figures and dissertation linkage

1. Confusion matrices (ML and rules) for **test**.
2. Bar chart: accuracy / precision / recall / F1 comparison.
3. For Obj 2: table of top positive coefficients (if logistic regression) or top TF‑IDF features for spam-like class.
4. Write one paragraph per **objective** pointing to figure/table numbers.

---

### Phase 9 — Optional “product” path

1. **Latency:** time `pipeline.predict` on N messages.
2. **API:** small FastAPI/Flask app loads joblib, accepts POST JSON `{ "message": "..." }`, returns label + probability.
3. **Mobile:** call API or bundle a tiny model — only after Python path is solid.

---

## Part E — ML metrics: what they are and how to test them on your trained model

### Labels convention (pick one and stick to it)

Assume **positive class = malicious (spam)** = `1`, **negative = ham** = `0`. All definitions below use that. If you swap labels, **precision/recall swap meaning** for “which class” — always say which class you care about.

### Core definitions (intuitive)

- **True Positive (TP):** model predicts malicious, truly malicious.  
- **False Positive (FP):** model predicts malicious, actually benign.  
- **True Negative (TN):** predicts benign, benign.  
- **False Negative (FN):** predicts benign, **actually malicious** (dangerous in security).

### Metrics you must report (thesis + Obj 4)

| Metric | Meaning (for malicious = positive) | Why it matters for smishing |
|--------|--------------------------------------|------------------------------|
| **Accuracy** | (TP + TN) / all | Easy but **misleading** if ham ≫ spam |
| **Precision** (malicious) | TP / (TP + FP) | Of all “malicious” alerts, how many were real? High FP → user ignores alerts |
| **Recall** (malicious) | TP / (TP + FN) | Of all real attacks, how many caught? **Missed attacks = FN** |
| **F1** (malicious) | Harmonic mean of precision and recall | Single score balancing both |
| **Specificity** (optional) | TN / (TN + FP) | How well benign is recognised |

**Security emphasis:** often **recall on malicious** and **false negative count** are highlighted because missing spam is costly.

### How you **compute** them in practice (after you have code)

1. Load **test** CSV: arrays `y_true`, `y_pred` (0/1 integers or same strings every time).
2. Use **scikit-learn**: `sklearn.metrics.classification_report(y_true, y_pred, digits=4)` for per-class precision/recall/F1; `confusion_matrix(y_true, y_pred)` for TN/FP/FN/TP.
3. Use **`recall_score`, `precision_score`, `f1_score`** with `pos_label=1` (if using 0/1) or `average='binary'` for the positive class.
4. For **probability threshold** models: get `predict_proba` on test, sweep thresholds using **only validation** data to pick threshold, then **once** apply on test and report metrics.

### How you **test** that your evaluation is correct (sanity checks)

1. **All-zero predictor:** if you predict all ham, recall for malicious should be **0** — confirms your positive label orientation.
2. **All-spam predictor:** recall malicious = **1**, precision likely low — confirms FP explosion.
3. **Subset size:** number of test rows matches `len(y_true) == len(y_pred)`.
4. **Stratification:** spam proportion in test ≈ proportion in full data (within sampling noise).
5. **Leakage check:** confirm training script never `fit`s on filenames containing `test`.

**Cursor prompt example:** *“Add `experiments/evaluate_ml.py` that loads test.csv, loads artifacts/pipeline.joblib, prints classification_report with labels 0/1 and confusion_matrix, and saves metrics to reports/metrics_test.json.”*

---

## Part F — Minimal viable path (short on time)

1. UCI only → splits → TF-IDF + Logistic Regression (balanced class weight).  
2. Save pipeline; evaluate on test → classification_report + confusion_matrix.  
3. Rules baseline on same test + small obfuscated malicious list for Obj 1.  
4. One comparison table + optional McNemar.  
5. Write-up tables for all four objectives.

Defer SMOTE, deep learning, BERT, until the MVP runs end-to-end.

---

## Part G — Suggested folders (so Cursor stays organised)

```text
data/raw/              # place SMSSpamCollection here (not committed if huge)
data/splits/           # train.csv, val.csv, test.csv
ml-backend/
  preprocessing/
  feature-extraction/
  models/
  rule-engine/
  artifacts/           # .joblib pipeline (gitignore if large)
experiments/           # train.py, evaluate_ml.py, evaluate_rules.py, compare_*.py
reports/               # metrics JSON, figures PNG
```

---

## Part H — Ethics (short)

Use **public** or **synthetic** SMS only unless you have operator permission and ethics clearance. Do not commit real user inboxes or PII.

---

## Part I — Map: existing repo files ↔ phases

| Phase | Existing starting point |
|-------|-------------------------|
| Preprocessing | `ml-backend/preprocessing/clean_text.py` |
| TF-IDF + LR | `ml-backend/feature-extraction/tfidf_features.py` |
| TF-IDF + NB | `ml-backend/models/train_model.py` |
| Rules | `ml-backend/rule-engine/rules.py` |
| UI demo (optional) | `mobile-app/react-native-app/app/index.tsx` (not wired to ML yet) |

---

## Appendix — Copy-paste Cursor prompts (one per milestone)

- **Milestone 1 — Data:** *“Follow RESEARCH_PIPELINE_AND_STEPS.md Phase 1–2. Add scripts under `experiments/` or `scripts/` to load UCI file from `data/raw/`, output stratified splits to `data/splits/`. No sklearn fit yet.”*
- **Milestone 2 — Train:** *“Follow Phase 4–5. Train TF-IDF + LogisticRegression Pipeline on train.csv only; save joblib under `ml-backend/artifacts/`. Never read test.csv during training.”*
- **Milestone 3 — ML metrics:** *“Follow Part E. Add evaluate script: classification_report, confusion_matrix, recall_score for positive class=1 on test.csv using saved pipeline.”*
- **Milestone 4 — Rules + obfuscation:** *“Follow Phase 6. Evaluate rules on test and on `data/obfuscated_malicious.csv` if present; report FN rate.”*
- **Milestone 5 — Compare:** *“Follow Phase 7. Same test set: ML vs rules metrics table + McNemar test.”*

---

*This guide aligns with your four research objectives and RQ1–RQ4 from Chapter 1, and the experimental pipeline described in Chapter 3. Adjust split ratios and optional statistics to match your supervisor’s requirements.*
