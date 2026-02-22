import requests

payload = {
  "gender": "Male",
  "senior_citizen": 0,
  "partner": "Yes",
  "dependents": "No",
  "country": "United States",
  "state": "CA",
  "contract_type": "Month-to-month",
  "paperless_billing": "Yes",
  "payment_method": "Electronic check",
  "phone_service": "Yes",
  "multiple_lines": "No",
  "internet_service": "Fiber optic",
  "online_security": "No",
  "online_backup": "No",
  "device_protection": "No",
  "tech_support": "No",
  "streaming_tv": "Yes",
  "streaming_movies": "Yes",
  "tenure_months": 5,
  "monthly_charges": 95.2,
  "total_charges": 450.0,
  "cltv": 3500,
  "mode": "default"
}

r = requests.post("http://127.0.0.1:8000/predict", json=payload, timeout=10)
print(r.status_code)
print(r.json())
