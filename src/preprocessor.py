from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer

from src.feature_engineering import TelecomFeatureEngineer


NUMERIC_FEATURES = [
    "tenure_months", "monthly_charges", "total_charges", "cltv",
    "avg_monthly_spend", "addon_count"
]

DEFAULT_CATEGORICAL_BASE = [
    # include ONLY the original categorical columns from the SQL view
    # (we'll add tenure_band inside build_preprocessor)
    "gender", "partner", "dependents", "country", "state",
    "contract_type", "paperless_billing", "payment_method",
    "phone_service", "multiple_lines", "internet_service",
    "online_security", "online_backup", "device_protection",
    "tech_support", "streaming_tv", "streaming_movies",
]


def build_preprocessor(categorical_features=None):
    """
    Returns an sklearn Pipeline that:
      1) adds engineered features (TelecomFeatureEngineer)
      2) imputes + one-hot encodes categoricals
      3) imputes numerics
    Import-safe: does NOT require X to exist.
    """
    if categorical_features is None:
        categorical_features = DEFAULT_CATEGORICAL_BASE

    # tenure_band is created by TelecomFeatureEngineer
    categorical_features = list(categorical_features) + ["tenure_band"]

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    ct = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop"
    )

    preprocessor = Pipeline(steps=[
        ("fe", TelecomFeatureEngineer()),
        ("ct", ct)
    ])

    return preprocessor
