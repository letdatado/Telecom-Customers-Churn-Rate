import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

DB_PATH = Path("data/telco_churn.db")
XLSX_PATH = Path("data/raw/Telco_customer_churn.xlsx")

SNAPSHOT_DATE = "2026-01-28"  # constant snapshot date for this dataset


def clean_total_charges(x):
    """Excel sometimes stores blanks/spaces; coerce safely to float."""
    if pd.isna(x):
        return np.nan
    if isinstance(x, str) and x.strip() == "":
        return np.nan
    return pd.to_numeric(x, errors="coerce")


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found: {DB_PATH}")
    if not XLSX_PATH.exists():
        raise FileNotFoundError(f"XLSX not found: {XLSX_PATH}")

    df = pd.read_excel(XLSX_PATH)

    # Minimal cleaning + standardization 
    df = df.copy()

    # Ensure expected columns exist
    required_cols = [
        "CustomerID", "Gender", "Senior Citizen", "Partner", "Dependents",
        "Country", "State",
        "Contract", "Paperless Billing", "Payment Method",
        "Phone Service", "Multiple Lines", "Internet Service", "Online Security",
        "Online Backup", "Device Protection", "Tech Support",
        "Streaming TV", "Streaming Movies",
        "Tenure Months", "Monthly Charges", "Total Charges", "CLTV",
        "Churn Label"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # Coerce numeric fields
    df["Senior Citizen"] = pd.to_numeric(df["Senior Citizen"], errors="coerce").fillna(0).astype(int)
    df["Tenure Months"] = pd.to_numeric(df["Tenure Months"], errors="coerce").fillna(0).astype(int)
    df["Monthly Charges"] = pd.to_numeric(df["Monthly Charges"], errors="coerce")
    df["Total Charges"] = df["Total Charges"].apply(clean_total_charges)
    df["CLTV"] = pd.to_numeric(df["CLTV"], errors="coerce")

    # Keep only columns we need for star schema
    df = df[required_cols]

    # Connect DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Load dim_customer
    dim_customer = (
        df[["CustomerID", "Gender", "Senior Citizen", "Partner", "Dependents", "Country", "State"]]
        .drop_duplicates()
        .rename(columns={
            "CustomerID": "customer_id",
            "Gender": "gender",
            "Senior Citizen": "senior_citizen",
            "Partner": "partner",
            "Dependents": "dependents",
            "Country": "country",
            "State": "state",
        })
    )

    cur.executemany(
        """
        INSERT OR IGNORE INTO dim_customer
        (customer_id, gender, senior_citizen, partner, dependents, country, state)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        dim_customer.itertuples(index=False, name=None)
    )

    # Load dim_contract
    dim_contract = (
        df[["Contract", "Paperless Billing", "Payment Method"]]
        .drop_duplicates()
        .rename(columns={
            "Contract": "contract_type",
            "Paperless Billing": "paperless_billing",
            "Payment Method": "payment_method",
        })
    )

    cur.executemany(
        """
        INSERT INTO dim_contract (contract_type, paperless_billing, payment_method)
        VALUES (?, ?, ?)
        """,
        dim_contract.itertuples(index=False, name=None)
    )

    # Load dim_services
    dim_services = (
        df[[
            "Phone Service", "Multiple Lines", "Internet Service", "Online Security",
            "Online Backup", "Device Protection", "Tech Support",
            "Streaming TV", "Streaming Movies"
        ]]
        .drop_duplicates()
        .rename(columns={
            "Phone Service": "phone_service",
            "Multiple Lines": "multiple_lines",
            "Internet Service": "internet_service",
            "Online Security": "online_security",
            "Online Backup": "online_backup",
            "Device Protection": "device_protection",
            "Tech Support": "tech_support",
            "Streaming TV": "streaming_tv",
            "Streaming Movies": "streaming_movies",
        })
    )

    cur.executemany(
        """
        INSERT INTO dim_services
        (phone_service, multiple_lines, internet_service, online_security, online_backup,
         device_protection, tech_support, streaming_tv, streaming_movies)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        dim_services.itertuples(index=False, name=None)
    )

    conn.commit()

    # Populate fact_customer_snapshot
    # We create the fact rows by looking up surrogate keys from dims.
    # Use SQL joins to ensure consistency.

    # Create a temporary staging table for raw rows (fastest way to map keys)
    cur.execute("DROP TABLE IF EXISTS stg_raw;")
    cur.execute(
        """
        CREATE TABLE stg_raw (
            customer_id TEXT,
            gender TEXT,
            senior_citizen INTEGER,
            partner TEXT,
            dependents TEXT,
            country TEXT,
            state TEXT,

            contract_type TEXT,
            paperless_billing TEXT,
            payment_method TEXT,

            phone_service TEXT,
            multiple_lines TEXT,
            internet_service TEXT,
            online_security TEXT,
            online_backup TEXT,
            device_protection TEXT,
            tech_support TEXT,
            streaming_tv TEXT,
            streaming_movies TEXT,

            tenure_months INTEGER,
            monthly_charges REAL,
            total_charges REAL,
            cltv REAL,

            churn_label TEXT,
            snapshot_date TEXT
        );
        """
    )

    stg = df.rename(columns={
        "CustomerID": "customer_id",
        "Gender": "gender",
        "Senior Citizen": "senior_citizen",
        "Partner": "partner",
        "Dependents": "dependents",
        "Country": "country",
        "State": "state",

        "Contract": "contract_type",
        "Paperless Billing": "paperless_billing",
        "Payment Method": "payment_method",

        "Phone Service": "phone_service",
        "Multiple Lines": "multiple_lines",
        "Internet Service": "internet_service",
        "Online Security": "online_security",
        "Online Backup": "online_backup",
        "Device Protection": "device_protection",
        "Tech Support": "tech_support",
        "Streaming TV": "streaming_tv",
        "Streaming Movies": "streaming_movies",

        "Tenure Months": "tenure_months",
        "Monthly Charges": "monthly_charges",
        "Total Charges": "total_charges",
        "CLTV": "cltv",

        "Churn Label": "churn_label",
    }).copy()

    stg["snapshot_date"] = SNAPSHOT_DATE

    cur.executemany(
        """
        INSERT INTO stg_raw (
            customer_id, gender, senior_citizen, partner, dependents, country, state,
            contract_type, paperless_billing, payment_method,
            phone_service, multiple_lines, internet_service, online_security, online_backup,
            device_protection, tech_support, streaming_tv, streaming_movies,
            tenure_months, monthly_charges, total_charges, cltv,
            churn_label, snapshot_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?)
        """,
        stg.itertuples(index=False, name=None)
    )
    conn.commit()

    # Insert into fact using joins to get surrogate keys
    cur.execute("DELETE FROM fact_customer_snapshot;")  # idempotent for reruns

    cur.execute(
        """
        INSERT INTO fact_customer_snapshot (
            customer_key, contract_key, services_key,
            tenure_months, monthly_charges, total_charges, cltv,
            churn_label, snapshot_date
        )
        SELECT
            dc.customer_key,
            dcon.contract_key,
            ds.services_key,
            r.tenure_months,
            r.monthly_charges,
            r.total_charges,
            r.cltv,
            r.churn_label,
            r.snapshot_date
        FROM stg_raw r
        JOIN dim_customer dc
          ON dc.customer_id = r.customer_id
        JOIN dim_contract dcon
          ON dcon.contract_type = r.contract_type
         AND dcon.paperless_billing = r.paperless_billing
         AND dcon.payment_method = r.payment_method
        JOIN dim_services ds
          ON ds.phone_service = r.phone_service
         AND ds.multiple_lines = r.multiple_lines
         AND ds.internet_service = r.internet_service
         AND ds.online_security = r.online_security
         AND ds.online_backup = r.online_backup
         AND ds.device_protection = r.device_protection
         AND ds.tech_support = r.tech_support
         AND ds.streaming_tv = r.streaming_tv
         AND ds.streaming_movies = r.streaming_movies
        ;
        """
    )
    conn.commit()

    # Create indexes for performance (good SQL habit)
    cur.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_fact_customer_key ON fact_customer_snapshot(customer_key);
        CREATE INDEX IF NOT EXISTS idx_fact_contract_key ON fact_customer_snapshot(contract_key);
        CREATE INDEX IF NOT EXISTS idx_fact_services_key ON fact_customer_snapshot(services_key);
        CREATE INDEX IF NOT EXISTS idx_fact_churn ON fact_customer_snapshot(churn_label);
        """
    )
    conn.commit()

    # Basic validation
    fact_count = cur.execute("SELECT COUNT(*) FROM fact_customer_snapshot;").fetchone()[0]
    cust_count = cur.execute("SELECT COUNT(*) FROM dim_customer;").fetchone()[0]
    con_count = cur.execute("SELECT COUNT(*) FROM dim_contract;").fetchone()[0]
    svc_count = cur.execute("SELECT COUNT(*) FROM dim_services;").fetchone()[0]

    print("✅ Load complete.")
    print(f"dim_customer rows: {cust_count}")
    print(f"dim_contract rows: {con_count}")
    print(f"dim_services rows: {svc_count}")
    print(f"fact_customer_snapshot rows: {fact_count}")

    conn.close()


if __name__ == "__main__":
    main()
