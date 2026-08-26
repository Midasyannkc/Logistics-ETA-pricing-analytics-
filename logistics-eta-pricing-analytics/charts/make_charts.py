import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.size"] = 11

eta = pd.read_csv("../data/eta_metrics.csv")
elasticity = pd.read_csv("../data/pricing_elasticity.csv")
util = pd.read_csv("../data/utilization_by_region.csv")

# 1. ETA MAE/RMSE: raw model vs corrected model
fig, ax = plt.subplots(figsize=(7, 5))
x = range(len(eta))
width = 0.35
ax.bar([i - width / 2 for i in x], eta["raw_model"], width, label="Raw prediction", color="#C0504D")
ax.bar([i + width / 2 for i in x], eta["corrected_model"], width, label="Databricks-corrected", color="#4F81BD")
ax.set_xticks(list(x))
ax.set_xticklabels(eta["metric"])
ax.set_ylabel("Minutes")
ax.set_title("ETA Prediction Error: Raw vs. Corrected Model")
ax.legend()
for i, (r, c) in enumerate(zip(eta["raw_model"], eta["corrected_model"])):
    ax.text(i - width / 2, r + 0.03, f"{r}", ha="center", fontsize=9)
    ax.text(i + width / 2, c + 0.03, f"{c}", ha="center", fontsize=9)
fig.tight_layout()
fig.savefig("eta_error_comparison.png", dpi=150)
plt.close(fig)

# 2. Pricing elasticity: conversion rate vs surge bin
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(elasticity["surge_bin"], elasticity["conversion_rate"], marker="o", color="#E4832A", linewidth=2)
ax.set_title("Conversion Rate vs. Surge Multiplier")
ax.set_ylabel("Conversion rate (%)")
ax.set_xlabel("Surge multiplier bin")
ax.grid(alpha=0.25)
for i, v in enumerate(elasticity["conversion_rate"]):
    ax.text(i, v + 1, f"{v}%", ha="center", fontsize=9)
fig.tight_layout()
fig.savefig("pricing_elasticity.png", dpi=150)
plt.close(fig)

# 3. Driver/dasher utilization by region
fig, ax = plt.subplots(figsize=(7, 5))
x = range(len(util))
width = 0.35
ax.bar([i - width / 2 for i in x], util["driver_availability_rate"], width, label="Driver availability %", color="#9BBB59")
ax.bar([i + width / 2 for i in x], util["conversion_rate"], width, label="Conversion rate %", color="#8064A2")
ax.set_xticks(list(x))
ax.set_xticklabels(util["region"])
ax.set_title("Driver Availability vs. Conversion by Region")
ax.set_ylabel("%")
ax.legend()
fig.tight_layout()
fig.savefig("utilization_by_region.png", dpi=150)
plt.close(fig)

print("Charts written: eta_error_comparison.png, pricing_elasticity.png, utilization_by_region.png")
