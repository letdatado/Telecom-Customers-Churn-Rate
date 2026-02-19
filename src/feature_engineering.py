import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class TelecomFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Custom feature engineering for telecom churn.
    Must live in a .py module (not a notebook) so joblib can reload it reliably.
    """

    def __init__(self):
        self.addon_cols = [
            "online_security", "online_backup", "device_protection",
            "tech_support", "streaming_tv", "streaming_movies"
        ]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        # Ensure numeric fields are numeric
        X["tenure_months"] = pd.to_numeric(X["tenure_months"], errors="coerce")
        X["total_charges"] = pd.to_numeric(X["total_charges"], errors="coerce")
        X["monthly_charges"] = pd.to_numeric(X["monthly_charges"], errors="coerce")
        X["cltv"] = pd.to_numeric(X["cltv"], errors="coerce")

        # Engineered features
        X["avg_monthly_spend"] = np.where(
            X["tenure_months"].fillna(0) > 0,
            X["total_charges"] / X["tenure_months"].replace({0: np.nan}),
            0.0
        )
        X["avg_monthly_spend"] = X["avg_monthly_spend"].replace([np.inf, -np.inf], np.nan)

        X["tenure_band"] = pd.cut(
            X["tenure_months"].fillna(0),
            bins=[-1, 12, 24, 48, 1200],
            labels=["0-12", "13-24", "25-48", "49+"]
        ).astype(str)

        X["addon_count"] = 0
        for c in self.addon_cols:
            if c in X.columns:
                X["addon_count"] += (X[c] == "Yes").astype(int)

        return X
