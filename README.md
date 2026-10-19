# Shark Tank AI — Sharkary-style interface

## Interface and main workflow

The frontend now follows the structure of the Sharkary reference site more closely: a compact top header, horizontal navigation, homepage hero, dataset statistic cards, shark cards, searchable popular-company cards, and dedicated Companies, Analytics, Pitch Analyzer, Compare Sharks, Scenario Simulator, and Model Card pages. The styling is a close adaptation for this project and uses the Indian Shark Tank dataset and existing models.

## Main improvement

This version is designed as an AI product rather than a dataset form.

### User flow

**Natural-language pitch → AI extraction → verification → ML predictions → scenario analysis**

The user can describe a startup in ordinary language. The app extracts business facts, shows what it understood, and allows corrections before prediction.

### Improved extraction

The extractor supports:
- Asking / seeking / raising amount
- Equity
- Requested valuation
- Annual revenue
- Monthly sales
- Gross/net margins
- EBITDA
- Business start year
- Customers/users
- Founders/presenters
- Industry
- State
- SKUs
- Patents/IP
- Bootstrapping
- Cash burn
- Business model signals
- Growth signals
- Distribution signals

### Important improvement

Missing numerical values are no longer silently replaced with arbitrary demo values.

The app uses:
1. Values explicitly detected in the pitch.
2. Logical derivations where appropriate (for example annual revenue → monthly sales).
3. Dataset-derived median/mode fallbacks only when the model requires a missing feature.

The UI identifies estimated fields.

### Scenario Simulator

After a prediction, the user can change:
- Ask amount
- Equity offered
- Requested valuation

and immediately see how the deal probability changes.

## Run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```
