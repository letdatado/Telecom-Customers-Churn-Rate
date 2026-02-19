CREATE TABLE IF NOT EXISTS prediction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc TEXT NOT NULL,
    request_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    threshold REAL NOT NULL,
    churn_probability REAL NOT NULL,
    churn_flag INTEGER NOT NULL
);
