# Telco Customer Churn — End-to-End ML System

An end-to-end machine learning system that predicts customer churn for a telecom company, covering data modeling, feature engineering, model training, explainability, API deployment, monitoring, and Dockerized orchestration.

## Problem Statement

Customer churn is one of the most expensive problems in the telecom industry. 
The goal of this project is to predict whether a customer is likely to churn, 
and expose that prediction via a production-style API and dashboard so that 
business teams can take timely retention actions.

## High-Level Architecture

The system is designed as a small production-style ML service:

- A FastAPI service performs model inference
- A Streamlit dashboard provides visualization and interaction
- A SQLite database stores analytics data and prediction logs
- Docker and docker-compose orchestrate the system

API  →  Model  →  Decision Threshold  →  Logging  
Dashboard  →  API  →  Monitoring

## Dataset

The project uses the **Telco Customer Churn** dataset (Kaggle), containing:

- ~7,000 customers
- Demographics (gender, senior citizen, dependents)
- Services (internet, security, streaming, support)
- Billing and contract information
- Churn labels and customer lifetime value (CLTV)


## Data Modeling

A dimensional **star schema** is used to simulate a real analytics warehouse.

### Dimensions
- `dim_customer`
- `dim_contract`
- `dim_services`

### Fact Table
- `fact_customer_snapshot`

A SQL view (`vw_churn_training_dataset`) is used as the stable source for
both analytics and machine learning training.


## Feature Engineering

Feature engineering is implemented using a scikit-learn pipeline to ensure
consistency between training and inference.

Key engineered features include:
- Average monthly spend
- Tenure bands
- Number of add-on services

Missing values are handled via imputation, and categorical features are
one-hot encoded.

## Model Training and Selection

Multiple models were evaluated:
- Logistic Regression
- Random Forest
- XGBoost

A **Random Forest** model was selected due to its strong recall, ability to
capture nonlinear interactions, and operational robustness.


## Business-Aware Thresholding

Instead of using a default 0.5 cutoff, decision thresholds were chosen using
precision–recall analysis.

Two operating modes are supported:

- **Default mode** (threshold = 0.48): balanced, always-on scoring
- **Aggressive mode** (threshold = 0.28): high-recall retention campaigns

This allows churn decisioning to be policy-driven rather than arbitrary.

## Explainability

SHAP (SHapley Additive exPlanations) is used to explain model predictions.

- Global explanations identify key churn drivers such as tenure and contract type
- Local explanations justify individual customer predictions

This ensures transparency and trust in model outputs.

## Model Serving (FastAPI)

The trained model is served via a FastAPI application.

### Key endpoints
- `GET /health`
- `POST /predict`
- `GET /monitoring/summary`

Each prediction returns a churn probability, a churn flag, and a request ID
for traceability.

## Monitoring

Each prediction is logged to a SQLite table containing:
- Timestamp
- Request ID
- Decision mode
- Threshold used
- Churn probability
- Churn flag

A monitoring endpoint provides aggregate summaries of recent predictions.

## Dashboard

A Streamlit dashboard allows users to:
- Score individual customers
- Compare default vs aggressive thresholds
- Visualize churn patterns
- Inspect monitoring summaries

The dashboard communicates with the API over HTTP.

## Docker and Orchestration

The system is fully containerized using Docker.

Key design choices:
- Stateless API container
- SQLite database mounted as a volume
- Orchestration via docker-compose

All services can be started with a single command:
```bash
docker compose up


---

## 🔹 Project Structure

```md
## Project Structure

.
├── api/                # FastAPI service
├── artifacts/          # Trained model and preprocessor
├── dashboard/          # Streamlit dashboard
├── data/               # SQLite database and raw data
├── notebooks/          # EDA, modeling, explainability
├── scripts/            # Client and utility scripts
├── sql/                # Schema and analytics SQL
├── Dockerfile
├── docker-compose.yml
└── README.md

## What This Project Demonstrates

- End-to-end machine learning engineering
- SQL-based data modeling
- Feature engineering pipelines
- Business-aware model evaluation
- Explainability and monitoring
- API and dashboard deployment
- Dockerized production workflows

```
