# Shark Tank AI — Tkinter Desktop UI

The Streamlit frontend has been replaced with a native Python Tkinter desktop interface. The existing pitch extractor, dataset and model-training approach are retained.

## Included screens
- Home dashboard and Season 1 shark profiles
- Searchable Companies database
- Analytics
- Natural-language Pitch Analyzer with editable extracted fields
- Compare Sharks
- Scenario Simulator
- Dataset Insights
- Model Card

## Folder layout

Keep these files in one folder:

```text
project/
  tkinter_app.py
  pitch_extractor.py
  train_models(1).py
  data(2).csv          # or data.csv
  model_metrics.json
  requirements_tkinter.txt
  run_train_tkinter.bat
  run_app_tkinter.bat
  models/              # created by training
```

## Windows setup

Open Command Prompt or PowerShell in the project folder and run:

```powershell
py -3.11 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements_tkinter.txt
```

## Train the ML models

Double-click `run_train_tkinter.bat`.

The training script expects `data.csv`. The launcher automatically copies the supplied `data(2).csv` to `data.csv` if `data.csv` does not already exist. Training creates the `models/` folder and saves the prediction pipelines and metadata there.

## Launch the desktop application

Double-click `run_app_tkinter.bat`.

Or run:

```powershell
venv\Scripts\python.exe tkinter_app.py
```

No browser or Streamlit server is needed. Tkinter is included with most standard Windows Python installations.

## Notes
- Dataset browsing, analytics and model-metric screens can be opened even before training.
- Pitch prediction and scenario simulation require the trained files in `models/`.
- The app uses local initials placeholders for shark portraits. Optional downloaded portraits can be placed in `assets/sharks/`; portrait downloads are not required.
- Predictions are estimates based on historical dataset patterns, not guarantees of investment decisions.
