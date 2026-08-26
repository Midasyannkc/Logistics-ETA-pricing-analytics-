"""
Runnable local counterpart to the Databricks gold feature table.

1. Loads the synthetic trip events (data/trip_events.csv).
2. Computes baseline ETA error (predicted vs. actual) as if serving the
   raw prediction, then trains a small linear correction model on
   demand_index / distance_km / hour_of_day to show the error reduction
   a lightweight Databricks-trained model buys in production.
3. Computes pricing elasticity (conversion rate vs. surge multiplier)
   and driver utilization by region.

Run: python eta_model_and_kpis.py
Reads:  ../data/trip_events.csv
Writes: ../data/eta_metrics.csv, ../data/pricing_elasticity.csv,
        ../data/utilization_by_region.csv
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

df = pd.read_csv("../data/trip_events.csv", parse_dates=["requested_at"])
df["hour_of_day"] = df["requested_at"].dt.hour

# ---- 1. Baseline ETA error (the raw predicted_eta_minutes column) ----
baseline_mae = mean_absolute_error(df["actual_eta_minutes"], df["predicted_eta_minutes"])
baseline_rmse = mean_squared_error(df["actual_eta_minutes"], df["predicted_eta_minutes"]) ** 0.5

# ---- 2. Correction model: predict the residual using demand + context ----
df["baseline_error"] = df["actual_eta_minutes"] - df["predicted_eta_minutes"]
features = ["distance_km", "demand_index", "hour_of_day", "predicted_eta_minutes"]
X = df[features]
y = df["actual_eta_minutes"]

X_train, X_test, y_train, y_test, pred_train, pred_test = train_test_split(
    X, y, df["predicted_eta_minutes"], test_size=0.25, random_state=13
)

model = LinearRegression()
model.fit(X_train, y_train)
corrected_pred = model.predict(X_test)

corrected_mae = mean_absolute_error(y_test, corrected_pred)
corrected_rmse = mean_squared_error(y_test, corrected_pred) ** 0.5
raw_mae_on_test = mean_absolute_error(y_test, pred_test)
raw_rmse_on_test = mean_squared_error(y_test, pred_test) ** 0.5

eta_metrics = pd.DataFrame([
    {"metric": "MAE_minutes", "raw_model": round(raw_mae_on_test, 2), "corrected_model": round(corrected_mae, 2)},
    {"metric": "RMSE_minutes", "raw_model": round(raw_rmse_on_test, 2), "corrected_model": round(corrected_rmse, 2)},
])
eta_metrics.to_csv("../data/eta_metrics.csv", index=False)

# ---- 3. Pricing elasticity: conversion rate by surge multiplier bin ----
df["surge_bin"] = pd.cut(
    df["surge_multiplier"],
    bins=[0.99, 1.1, 1.3, 1.5, 1.75, 2.0, 2.5],
    labels=["1.0-1.1", "1.1-1.3", "1.3-1.5", "1.5-1.75", "1.75-2.0", "2.0-2.5"],
)
elasticity = (
    df.groupby("surge_bin", observed=True)
    .agg(trips=("trip_id", "count"), conversion_rate=("converted", "mean"))
    .reset_index()
)
elasticity["conversion_rate"] = (elasticity["conversion_rate"] * 100).round(1)
elasticity.to_csv("../data/pricing_elasticity.csv", index=False)

# ---- 4. Driver/dasher utilization by region ----
util = (
    df.groupby("region")
    .agg(
        trips=("trip_id", "count"),
        driver_availability_rate=("driver_available", "mean"),
        conversion_rate=("converted", "mean"),
    )
    .reset_index()
)
util["driver_availability_rate"] = (util["driver_availability_rate"] * 100).round(1)
util["conversion_rate"] = (util["conversion_rate"] * 100).round(1)
util.to_csv("../data/utilization_by_region.csv", index=False)

print(f"Baseline MAE (full data): {baseline_mae:.2f} min, RMSE: {baseline_rmse:.2f} min")
print(f"Test-set raw MAE: {raw_mae_on_test:.2f} min -> corrected MAE: {corrected_mae:.2f} min")
print("Wrote eta_metrics.csv, pricing_elasticity.csv, utilization_by_region.csv")
