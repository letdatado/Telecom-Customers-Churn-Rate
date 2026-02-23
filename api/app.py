from __future__ import annotations

import uuid
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional, Dict, Any

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field


# ------------------------
# Paths / Config
# ------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "telco_churn.db"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

PREPROCESSOR_PATH = ARTIFACTS_DIR / "preprocessor.joblib"
MODEL_PATH = ARTIFACTS_DIR / "churn_model_rf.joblib"

DEFAULT_THRESHOLD = 0.48
AGGRESSIVE_THRESHOLD = 0.28


# ------------------------
# Load artifacts once
# ------------------------
preprocessor = joblib.load(PREPROCESSOR_PATH)
model = joblib.load(MODEL_PATH)


# ------------------------
# API schema
# ------------------------
class PredictRequest(BaseModel):
    # Core customer attributes (from vw_churn_training_dataset)
    gender: str
    senior_citizen: int = Field(..., ge=0, le=1)
    partner: str
    dependents: str
    country: str
    state: str

    contract_type: str
    paperless_billing: str
    payment_method: str

    phone_service: str
    multiple_lines: str
    internet_service: str
    online_security: str
    online_backup: str
    device_protection: str
    tech_support: str
    streaming_tv: str
    streaming_movies: str

    tenure_months: int = Field(..., ge=0)
    monthly_charges: float = Field(..., ge=0)
    total_charges: Optional[float] = None
    cltv: float = Field(..., ge=0)

    # Decisioning mode
    mode: Literal["default", "aggressive"] = "default"


class PredictResponse(BaseModel):
    request_id: str
    mode: str
    threshold: float
    churn_probability: float
    churn_flag: int


# ------------------------
# Utilities
# ------------------------
def _threshold_for_mode(mode: str) -> float:
    return AGGRESSIVE_THRESHOLD if mode == "aggressive" else DEFAULT_THRESHOLD


def _log_prediction(
    request_id: str,
    mode: str,
    threshold: float,
    churn_probability: float,
    churn_flag: int
) -> None:
    ts_utc = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO prediction_log (ts_utc, request_id, mode, threshold, churn_probability, churn_flag)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (ts_utc, request_id, mode, threshold, float(churn_probability), int(churn_flag)),
    )
    conn.commit()
    conn.close()


def _payload_to_dataframe(payload: PredictRequest) -> pd.DataFrame:
    # Build a 1-row DataFrame matching vw_churn_training_dataset column names used in preprocessing
    row: Dict[str, Any] = payload.model_dump()
    row.pop("mode", None)  # not a model feature
    return pd.DataFrame([row])


# ------------------------
# FastAPI
# ------------------------
app = FastAPI(title="Telco Churn Scoring API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    request_id = str(uuid.uuid4())
    threshold = _threshold_for_mode(req.mode)

    X_raw = _payload_to_dataframe(req)
    X_transformed = preprocessor.transform(X_raw)

    churn_probability = float(model.predict_proba(X_transformed)[0, 1])
    churn_flag = int(churn_probability >= threshold)

    _log_prediction(
        request_id=request_id,
        mode=req.mode,
        threshold=threshold,
        churn_probability=churn_probability,
        churn_flag=churn_flag,
    )

    return PredictResponse(
        request_id=request_id,
        mode=req.mode,
        threshold=threshold,
        churn_probability=churn_probability,
        churn_flag=churn_flag,
    )

@app.get("/")
def root():
    return {"message": "Telco Churn API is running. Visit /docs to test /predict."}

@app.get("/monitoring/summary")
def monitoring_summary(limit: int = 1000):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT churn_flag, AVG(churn_probability) AS avg_prob, COUNT(*) AS n
        FROM (SELECT * FROM prediction_log ORDER BY id DESC LIMIT ?)
        GROUP BY churn_flag
        """,
        (limit,),
    ).fetchall()
    conn.close()

    return {
        "window_size": limit,
        "by_flag": [
            {"churn_flag": int(r[0]), "avg_probability": float(r[1]), "count": int(r[2])}
            for r in rows
        ]
    }
