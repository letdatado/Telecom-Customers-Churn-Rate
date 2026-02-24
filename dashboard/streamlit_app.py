import os
import sqlite3
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Telco Churn Dashboard", layout="wide")

# ----------------------------
# Config
# ----------------------------
DEFAULT_API_URL = "http://api:8000"
API_URL = os.getenv("API_URL", DEFAULT_API_URL).rstrip("/")
DB_PATH = os.getenv("DB_PATH", "data/telco_churn.db")  # works locally; not on Streamlit Cloud unless you ship DB

st.title("Telco Churn — Dashboard")
st.caption(f"API_URL = {API_URL}")

tab1, tab2, tab3 = st.tabs(["Score a Customer", "Churn Insights (SQL View)", "Monitoring"])

# ----------------------------
# Helpers
# ----------------------------
def call_predict(payload: dict):
    r = requests.post(f"{API_URL}/predict", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()

def load_training_view_from_sqlite():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM vw_churn_training_dataset", conn)
    conn.close()
    return df

def safe_get_monitoring_summary():
    # Preferred: call API monitoring endpoint (works in cloud)
    try:
        r = requests.get(f"{API_URL}/monitoring/summary?limit=1000", timeout=20)
        if r.status_code == 200:
            return r.json(), "api"
    except Exception:
        pass

    # Fallback: local DB read (works locally only)
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            """
            SELECT churn_flag, AVG(churn_probability) AS avg_probability, COUNT(*) AS count
            FROM prediction_log
            GROUP BY churn_flag
            """,
            conn,
        )
        conn.close()
        return {"by_flag": df.to_dict(orient="records")}, "db"
    except Exception:
        return None, "none"


# ----------------------------
# Tab 1: Scoring
# ----------------------------
with tab1:
    st.subheader("Score a Customer")

    colA, colB, colC = st.columns(3)

    with colA:
        gender = st.selectbox("Gender", ["Male", "Female"])
        senior_citizen = st.selectbox("Senior Citizen", [0, 1])
        partner = st.selectbox("Partner", ["Yes", "No"])
        dependents = st.selectbox("Dependents", ["Yes", "No"])
        country = st.text_input("Country", "United States")
        state = st.text_input("State", "CA")

    with colB:
        contract_type = st.selectbox("Contract Type", ["Month-to-month", "One year", "Two year"])
        paperless_billing = st.selectbox("Paperless Billing", ["Yes", "No"])
        payment_method = st.selectbox(
            "Payment Method",
            ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
        )

        tenure_months = st.number_input("Tenure Months", min_value=0, max_value=120, value=5)
        monthly_charges = st.number_input("Monthly Charges", min_value=0.0, value=95.2)
        total_charges = st.number_input("Total Charges", min_value=0.0, value=450.0)
        cltv = st.number_input("CLTV", min_value=0.0, value=3500.0)

    with colC:
        phone_service = st.selectbox("Phone Service", ["Yes", "No"])
        multiple_lines = st.selectbox("Multiple Lines", ["Yes", "No", "No phone service"])
        internet_service = st.selectbox("Internet Service", ["Fiber optic", "DSL", "No"])

        online_security = st.selectbox("Online Security", ["Yes", "No", "No internet service"])
        online_backup = st.selectbox("Online Backup", ["Yes", "No", "No internet service"])
        device_protection = st.selectbox("Device Protection", ["Yes", "No", "No internet service"])
        tech_support = st.selectbox("Tech Support", ["Yes", "No", "No internet service"])
        streaming_tv = st.selectbox("Streaming TV", ["Yes", "No", "No internet service"])
        streaming_movies = st.selectbox("Streaming Movies", ["Yes", "No", "No internet service"])

        mode = st.radio("Decision Mode", ["default", "aggressive"], horizontal=True)
        st.write("Default threshold = 0.48, Aggressive = 0.28")

    payload = {
        "gender": gender,
        "senior_citizen": int(senior_citizen),
        "partner": partner,
        "dependents": dependents,
        "country": country,
        "state": state,
        "contract_type": contract_type,
        "paperless_billing": paperless_billing,
        "payment_method": payment_method,
        "phone_service": phone_service,
        "multiple_lines": multiple_lines,
        "internet_service": internet_service,
        "online_security": online_security,
        "online_backup": online_backup,
        "device_protection": device_protection,
        "tech_support": tech_support,
        "streaming_tv": streaming_tv,
        "streaming_movies": streaming_movies,
        "tenure_months": int(tenure_months),
        "monthly_charges": float(monthly_charges),
        "total_charges": float(total_charges),
        "cltv": float(cltv),
        "mode": mode,
    }

    if st.button("Predict Churn", type="primary"):
        try:
            out = call_predict(payload)
            st.success("Prediction success")
            st.json(out)

            prob = out["churn_probability"]
            flag = out["churn_flag"]
            st.metric("Churn Probability", f"{prob:.3f}")
            st.metric("Churn Flag", str(flag))
        except Exception as e:
            st.error(f"Prediction failed: {e}")


# ----------------------------
# Tab 2: Insights (from SQL view)
# ----------------------------
with tab2:
    st.subheader("Churn Insights (from vw_churn_training_dataset)")

    st.info(
        "Locally, this tab reads your SQLite database and plots key churn patterns. "
        "On Streamlit Cloud, you can keep this tab by switching it to call an API endpoint that returns aggregates."
    )

    try:
        df = load_training_view_from_sqlite()

        c1, c2 = st.columns(2)

        with c1:
            # churn rate by contract type
            grp = df.groupby("contract_type")["churn_target"].mean().reset_index()
            fig = px.bar(grp, x="contract_type", y="churn_target", title="Churn Rate by Contract Type")
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            # churn rate by tenure band
            tenure_band = pd.cut(
                df["tenure_months"], bins=[-1, 12, 24, 48, 1200], labels=["0-12", "13-24", "25-48", "49+"]
            )
            grp2 = df.assign(tenure_band=tenure_band).groupby("tenure_band")["churn_target"].mean().reset_index()
            fig2 = px.bar(grp2, x="tenure_band", y="churn_target", title="Churn Rate by Tenure Band")
            st.plotly_chart(fig2, use_container_width=True)

        # monthly charges distribution
        fig3 = px.box(df, x="churn_target", y="monthly_charges", title="Monthly Charges by Churn")
        st.plotly_chart(fig3, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load SQLite view locally: {e}")


# ----------------------------
# Tab 3: Monitoring
# ----------------------------
with tab3:
    st.subheader("Monitoring")

    summary, source = safe_get_monitoring_summary()
    if summary is None:
        st.warning("No monitoring data available yet. Make a few /predict calls first.")
    else:
        st.caption(f"Source: {source}")
        st.json(summary)

        by_flag = summary.get("by_flag", [])
        if by_flag:
            mdf = pd.DataFrame(by_flag)
            if "churn_flag" in mdf.columns:
                fig = px.bar(mdf, x="churn_flag", y="count", title="Predictions by churn_flag")
                st.plotly_chart(fig, use_container_width=True)
