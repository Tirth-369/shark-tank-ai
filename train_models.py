
import os, json, joblib, warnings
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_absolute_error, r2_score, mean_squared_error
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data.csv")
MODEL_DIR = os.path.join(ROOT, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

SHARKS = ["Namita", "Vineeta", "Anupam", "Aman", "Peyush"]

# Only features that are available at pitch time.
BASE_NUMERIC = [
    "Season Number", "Episode Number", "Pitch Number", "Started in",
    "Number of Presenters", "Male Presenters", "Female Presenters",
    "Transgender Presenters", "Couple Presenters", "Pitchers Average Age",
    "Yearly Revenue", "Monthly Sales", "Gross Margin", "Net Margin",
    "EBITDA", "Cash Burn", "SKUs", "Has Patents", "Part of Match off",
    "Original Ask Amount", "Original Offered Equity", "Valuation Requested",
    "Namita Present", "Vineeta Present", "Anupam Present", "Aman Present",
    "Peyush Present", "Ritesh Present", "Amit Present", "Guest Present"
]

BASE_CATEGORICAL = ["Industry", "Pitchers State", "Bootstrapped"]

def clean(df):
    df = df.copy()

    # Known data correction from the project's preprocessing
    if "Pitchers State" in df:
        df["Pitchers State"] = df["Pitchers State"].replace("Vijayawada", "Andhra Pradesh")
        df["Pitchers State"] = df["Pitchers State"].fillna("Unknown").astype(str).str.split(",").str[0]

    # Date-derived feature
    if "Original Air Date" in df:
        d = pd.to_datetime(df["Original Air Date"], errors="coerce")
        season_start = pd.to_datetime(df["Season Start"], errors="coerce") if "Season Start" in df else pd.NaT
        df["days_into_season"] = (d - season_start).dt.days
        df["days_into_season"] = df["days_into_season"].fillna(30).clip(lower=0)

    # Feature engineering available before the outcome
    df["ask_log"] = np.log1p(pd.to_numeric(df["Original Ask Amount"], errors="coerce").clip(lower=0))
    df["valuation_requested_log"] = np.log1p(pd.to_numeric(df["Valuation Requested"], errors="coerce").clip(lower=0))
    df["ask_equity_ratio"] = (
        pd.to_numeric(df["Original Offered Equity"], errors="coerce") /
        (pd.to_numeric(df["Original Ask Amount"], errors="coerce").fillna(0) + 1)
    )
    df["valuation_ask_ratio"] = (
        pd.to_numeric(df["Valuation Requested"], errors="coerce") /
        (pd.to_numeric(df["Original Ask Amount"], errors="coerce").fillna(0) + 1)
    )
    df["sharks_present_count"] = df[[c for c in BASE_NUMERIC if c.endswith("Present")]].sum(axis=1)

    # Age group if source age is categorical
    if "Pitchers Average Age" in df:
        if df["Pitchers Average Age"].dtype == object:
            df["Pitchers Average Age"] = df["Pitchers Average Age"].map(
                {"Young": 0, "Middle": 1, "Old": 2}
            )

    # Ensure numeric columns are numeric
    for c in BASE_NUMERIC:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df

def make_preprocessor(X):
    numeric = [c for c in X.columns if c not in BASE_CATEGORICAL]
    categorical = [c for c in X.columns if c in BASE_CATEGORICAL]
    return ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]), numeric),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]), categorical)
    ])

def split_train_eval(X, y, classification=False):
    return train_test_split(
        X, y, test_size=0.20, random_state=42,
        stratify=y if classification else None
    )

def save_task(name, pipeline, metrics, features, target, target_type):
    joblib.dump(pipeline, os.path.join(MODEL_DIR, f"{name}.pkl"))
    return {
        "target": target, "target_type": target_type,
        "features": features, "metrics": metrics
    }

df = clean(pd.read_csv(DATA))

# Keep the same input features for all pitch-time predictions.
features = [c for c in BASE_NUMERIC + BASE_CATEGORICAL
            if c in df.columns] + [
    c for c in ["days_into_season", "ask_log", "valuation_requested_log",
                "ask_equity_ratio", "valuation_ask_ratio", "sharks_present_count"]
    if c in df.columns
]
# Remove accidental duplicate names
features = list(dict.fromkeys(features))
X_all = df[features].copy()

results = {}

# ---------- 1. Deal prediction ----------
y = df["Accepted Offer"].fillna(0).astype(int)
Xtr, Xte, ytr, yte = split_train_eval(X_all, y, True)
deal = Pipeline([
    ("prep", make_preprocessor(Xtr)),
    ("model", ExtraTreesClassifier(
        n_estimators=350, min_samples_leaf=2, class_weight="balanced",
        random_state=42, n_jobs=-1
    ))
])
deal.fit(Xtr, ytr)
p = deal.predict_proba(Xte)[:,1]
pred = (p >= 0.5).astype(int)
results["deal"] = save_task(
    "deal_model", deal,
    {"accuracy": accuracy_score(yte,pred),
     "precision": precision_score(yte,pred,zero_division=0),
     "recall": recall_score(yte,pred,zero_division=0),
     "f1": f1_score(yte,pred,zero_division=0),
     "roc_auc": roc_auc_score(yte,p)},
    features, "Accepted Offer", "classification"
)

# ---------- 2. Offer likelihood ----------
# Received Offer is a separate upstream event and is more informative than
# treating Accepted Offer as the only outcome.
y = df["Received Offer"].fillna(0).astype(int)
Xtr, Xte, ytr, yte = split_train_eval(X_all, y, True)
offer = Pipeline([
    ("prep", make_preprocessor(Xtr)),
    ("model", ExtraTreesClassifier(
        n_estimators=350, min_samples_leaf=2, class_weight="balanced",
        random_state=43, n_jobs=-1
    ))
])
offer.fit(Xtr,ytr)
p = offer.predict_proba(Xte)[:,1]
pred = (p>=0.5).astype(int)
results["offer"] = save_task(
    "offer_model", offer,
    {"accuracy": accuracy_score(yte,pred),
     "precision": precision_score(yte,pred,zero_division=0),
     "recall": recall_score(yte,pred,zero_division=0),
     "f1": f1_score(yte,pred,zero_division=0),
     "roc_auc": roc_auc_score(yte,p)},
    features, "Received Offer", "classification"
)

# ---------- 3. Deal valuation ----------
# Successful deals only; do not use downstream deal/shark outcomes.
mask = df["Accepted Offer"].fillna(0).astype(int).eq(1) & df["Deal Valuation"].notna()
X = df.loc[mask, features]
y = np.log1p(pd.to_numeric(df.loc[mask,"Deal Valuation"], errors="coerce"))
Xtr, Xte, ytr, yte = train_test_split(X,y,test_size=.20,random_state=42)
valuation = Pipeline([
    ("prep", make_preprocessor(Xtr)),
    ("model", Ridge(alpha=10.0))
])
valuation.fit(Xtr,ytr)
lp = valuation.predict(Xte)
actual, predicted = np.expm1(yte), np.expm1(lp)
results["valuation"] = save_task(
    "valuation_model", valuation,
    {"r2": r2_score(yte,lp),
     "mae_lakh": mean_absolute_error(actual,predicted),
     "rmse_lakh": np.sqrt(mean_squared_error(actual,predicted))},
    features, "Deal Valuation", "regression_log_target"
)

# ---------- 4. Deal amount ----------
mask = df["Accepted Offer"].fillna(0).astype(int).eq(1) & df["Total Deal Amount"].notna()
X = df.loc[mask, features]
y = np.log1p(pd.to_numeric(df.loc[mask,"Total Deal Amount"], errors="coerce"))
Xtr, Xte, ytr, yte = train_test_split(X,y,test_size=.20,random_state=42)
amount = Pipeline([
    ("prep", make_preprocessor(Xtr)),
    ("model", Ridge(alpha=10.0))
])
amount.fit(Xtr,ytr)
lp = amount.predict(Xte)
actual, predicted = np.expm1(yte), np.expm1(lp)
results["deal_amount"] = save_task(
    "deal_amount_model", amount,
    {"r2": r2_score(yte,lp),
     "mae_lakh": mean_absolute_error(actual,predicted),
     "rmse_lakh": np.sqrt(mean_squared_error(actual,predicted))},
    features, "Total Deal Amount", "regression_log_target"
)

# ---------- 5. Equity prediction ----------
mask = df["Accepted Offer"].fillna(0).astype(int).eq(1) & df["Total Deal Equity"].notna()
X = df.loc[mask, features]
y = np.log1p(pd.to_numeric(df.loc[mask,"Total Deal Equity"], errors="coerce"))
Xtr, Xte, ytr, yte = train_test_split(X,y,test_size=.20,random_state=42)
equity = Pipeline([
    ("prep", make_preprocessor(Xtr)),
    ("model", Ridge(alpha=10.0))
])
equity.fit(Xtr,ytr)
lp = equity.predict(Xte)
actual, predicted = np.expm1(yte), np.expm1(lp)
results["equity"] = save_task(
    "equity_model", equity,
    {"r2": r2_score(yte,lp),
     "mae_percent_points": mean_absolute_error(actual,predicted),
     "rmse_percent_points": np.sqrt(mean_squared_error(actual,predicted))},
    features, "Total Deal Equity", "regression_log_target"
)

# ---------- 6. Number of sharks ----------
mask = df["Accepted Offer"].fillna(0).astype(int).eq(1) & df["Number of Sharks in Deal"].notna()
X = df.loc[mask, features]
y = pd.to_numeric(df.loc[mask,"Number of Sharks in Deal"], errors="coerce")
Xtr, Xte, ytr, yte = train_test_split(X,y,test_size=.20,random_state=42)
num_sharks = Pipeline([
    ("prep", make_preprocessor(Xtr)),
    ("model", ExtraTreesRegressor(
        n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1
    ))
])
num_sharks.fit(Xtr,ytr)
pred = np.clip(num_sharks.predict(Xte),0,5)
results["num_sharks"] = save_task(
    "num_sharks_model", num_sharks,
    {"r2": r2_score(yte,pred),
     "mae": mean_absolute_error(yte,pred),
     "rmse": np.sqrt(mean_squared_error(yte,pred))},
    features, "Number of Sharks in Deal", "regression"
)

# ---------- 7. Shark-specific probabilities ----------
# Train each shark independently on successful deals, using only pitch-time features.
shark_metrics = {}
for shark in SHARKS:
    target = df[shark + " Investment Amount"].notna().astype(int)
    mask = df["Accepted Offer"].fillna(0).astype(int).eq(1)
    X = df.loc[mask, features]
    yy = target.loc[mask]
    Xtr, Xte, ytr, yte = train_test_split(X,yy,test_size=.20,random_state=42,stratify=yy)
    pipe = Pipeline([
        ("prep", make_preprocessor(Xtr)),
        ("model", LogisticRegression(
            max_iter=1500, class_weight="balanced", random_state=42
        ))
    ])
    pipe.fit(Xtr,ytr)
    pp = pipe.predict_proba(Xte)[:,1]
    pr = (pp>=0.5).astype(int)
    shark_metrics[shark] = {
        "f1": f1_score(yte,pr,zero_division=0),
        "roc_auc": roc_auc_score(yte,pp) if yte.nunique()>1 else 0
    }
    joblib.dump(pipe, os.path.join(MODEL_DIR, f"shark_{shark.lower()}.pkl"))

results["sharks"] = {
    "target": "Individual shark investment",
    "target_type": "multi_binary",
    "metrics": shark_metrics,
    "features": features
}

metadata = {
    "features": features,
    "sharks": SHARKS,
    "results": results,
    "currency": "₹ lakh",
    "dataset_rows": int(len(df)),
    "dataset_columns": int(df.shape[1])
}
joblib.dump(metadata, os.path.join(MODEL_DIR,"metadata.pkl"))
with open(os.path.join(ROOT,"model_metrics.json"),"w") as f:
    json.dump(results,f,indent=2)

print("Training complete.")
for k,v in results.items():
    print(k, v["metrics"])
