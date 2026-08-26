"""
Synthetic trip + dynamic pricing event generator.

Mimics the shape of a ride/delivery logistics platform's event stream:
trip requests, ETA predictions vs. actuals, and the surge multiplier
applied by the pricing engine at request time.

Run: python generate_synthetic_data.py
Output: data/trip_events.csv
"""
import csv
import random
from datetime import datetime, timedelta

random.seed(7)

REGIONS = ["North", "South", "East", "West", "Downtown"]
N_TRIPS = 20000
start_date = datetime(2026, 6, 1)


def random_timestamp():
    day_offset = random.randint(0, 59)
    hour_weights = [1] * 24
    for h in (7, 8, 9):
        hour_weights[h] = 5
    for h in (17, 18, 19):
        hour_weights[h] = 7
    hour = random.choices(range(24), weights=hour_weights)[0]
    minute = random.randint(0, 59)
    return start_date + timedelta(days=day_offset, hours=hour, minutes=minute)


def build_trip(trip_id):
    region = random.choice(REGIONS)
    requested_at = random_timestamp()
    is_peak = requested_at.hour in (7, 8, 9, 17, 18, 19)

    base_distance_km = max(0.8, random.gauss(6.5, 3.2))
    demand_index = random.uniform(1.4, 3.2) if is_peak else random.uniform(0.6, 1.6)
    surge_multiplier = round(min(2.5, max(1.0, 1 + (demand_index - 1) * 0.6)), 2)

    predicted_eta_minutes = round(max(2, base_distance_km * random.gauss(2.6, 0.3)), 1)
    # actual ETA has noise + a systematic bias at high demand (more traffic/congestion)
    congestion_bias = (demand_index - 1) * random.uniform(0.5, 2.0)
    actual_eta_minutes = round(max(2, predicted_eta_minutes + random.gauss(0, 2.0) + congestion_bias), 1)

    base_fare = 4.5 + base_distance_km * 1.35
    final_fare = round(base_fare * surge_multiplier, 2)

    driver_available = random.random() > (0.25 if is_peak else 0.08)
    converted = driver_available and random.random() > (0.05 + max(0, (surge_multiplier - 1.3) * 0.18))

    return {
        "trip_id": trip_id,
        "region": region,
        "requested_at": requested_at.isoformat(),
        "distance_km": round(base_distance_km, 2),
        "demand_index": round(demand_index, 2),
        "surge_multiplier": surge_multiplier,
        "predicted_eta_minutes": predicted_eta_minutes,
        "actual_eta_minutes": actual_eta_minutes,
        "base_fare_usd": round(base_fare, 2),
        "final_fare_usd": final_fare,
        "driver_available": int(driver_available),
        "converted": int(converted),
    }


def main():
    rows = [build_trip(i) for i in range(1, N_TRIPS + 1)]
    fieldnames = list(rows[0].keys())
    with open("trip_events.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic trip events to trip_events.csv")


if __name__ == "__main__":
    main()
