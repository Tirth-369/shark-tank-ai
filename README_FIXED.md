# Shark Tank AI — Fixed Package

## What was fixed
- Removed the old trainer's incorrect `median()` behavior on categorical Age values.
- `Pitchers Average Age` is converted from Young/Middle/Old to 0/1/2 before numeric processing.
- Numeric and categorical missing values are handled separately with sklearn imputers.
- The trainer uses paths relative to the project folder, so `data.csv` is found correctly.
- The project uses one consistent model format for training and Streamlit inference.
- No repeated PowerShell `&` commands are required.

## Windows PowerShell setup
Open PowerShell in this folder:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, skip activation and use the venv Python directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Train models

```powershell
.\venv\Scripts\python.exe train_models.py
```

Successful training creates/updates files in `models/`.

## Start Streamlit

```powershell
.\venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open the Local URL shown by Streamlit, normally:

`http://localhost:8501`

## Important
Run each command separately. Do NOT write multiple commands joined with `&`.

The old error:
`ModuleNotFoundError: No module named 'joblib'`
means the package was installed in global Python while the script was being run by `venv`. Installing with `venv\\Scripts\\python.exe -m pip ...` fixes that mismatch.
