"""
generate_data.py

Generates synthetic daily demand data for multiple product/warehouse 
combinations, with realistic trend, weekly and yearly seasonality, 
random noise, and a few injected demand shocks.

This data is synthetic and generated purely for portfolio/demonstration 
purposes, as real operational demand data is proprietary.
"""

import numpy as np
import pandas as pd
from faker import Faker
import os

np.random.seed(42)  # ensures reproducible results every time you run this
fake = Faker()

# ---- Configuration ----
NUM_PRODUCTS = 10
NUM_WAREHOUSES = 5
START_DATE = "2024-01-01"
NUM_DAYS = 730  # 2 years of daily data

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_products(num_products):
    categories = ["Mining Equipment Parts", "Consumer Electronics", 
                  "Industrial Tools", "Packaged Goods", "Apparel"]
    products = []
    for pid in range(1, num_products + 1):
        products.append({
            "product_id": pid,
            "category": np.random.choice(categories),
            "unit_cost": round(np.random.uniform(15, 250), 2),
            "lead_time_days": int(np.random.choice([7, 10, 14, 21, 30]))
        })
    return pd.DataFrame(products)


def generate_warehouses(num_warehouses):
    locations = ["Kolwezi, DRC", "Guangzhou, China", "Lagos, Nigeria", 
                 "Kinshasa, DRC", "Shenzhen, China"]
    warehouses = []
    for wid in range(1, num_warehouses + 1):
        warehouses.append({
            "warehouse_id": wid,
            "location": locations[(wid - 1) % len(locations)],
            "capacity": int(np.random.choice([3000, 5000, 8000, 10000]))
        })
    return pd.DataFrame(warehouses)


def generate_demand_series(days, base, trend, weekly_amp, yearly_amp, noise_std):
    """
    Builds one time series combining trend, weekly seasonality, 
    yearly seasonality, and random noise.
    """
    t = np.arange(days)

    trend_component = base + trend * t
    weekly_component = weekly_amp * np.sin(2 * np.pi * t / 7)
    yearly_component = yearly_amp * np.sin(2 * np.pi * t / 365)
    noise = np.random.normal(0, noise_std, days)

    demand = trend_component + weekly_component + yearly_component + noise
    demand = np.clip(demand, 0, None)  # demand can't be negative
    return demand.round()


def inject_demand_shocks(demand, num_shocks=2):
    """
    Injects a small number of deliberate demand shocks (spikes or dips)
    to simulate real-world disruptions (e.g. supply issues, promotions).
    """
    days = len(demand)
    for _ in range(num_shocks):
        shock_day = np.random.randint(30, days - 30)
        shock_duration = np.random.randint(3, 10)
        shock_magnitude = np.random.choice([-1, 1]) * np.random.uniform(0.4, 0.8)
        for d in range(shock_day, min(shock_day + shock_duration, days)):
            demand[d] = max(0, demand[d] * (1 + shock_magnitude))
    return demand


def generate_all_demand_data(products_df, warehouses_df, days, start_date):
    dates = pd.date_range(start_date, periods=days)
    all_rows = []

    for _, product in products_df.iterrows():
        for _, warehouse in warehouses_df.iterrows():
            # Randomize parameters slightly per product/warehouse combo
            # so each of the 50 series looks distinct, not identical
            base = np.random.uniform(60, 150)
            trend = np.random.uniform(0.01, 0.08)
            weekly_amp = np.random.uniform(5, 20)
            yearly_amp = np.random.uniform(15, 50)
            noise_std = np.random.uniform(5, 12)

            demand = generate_demand_series(
                days, base, trend, weekly_amp, yearly_amp, noise_std
            )
            demand = inject_demand_shocks(demand, num_shocks=2)

            for i, date in enumerate(dates):
                all_rows.append({
                    "date": date,
                    "product_id": product["product_id"],
                    "warehouse_id": warehouse["warehouse_id"],
                    "units_sold": demand[i]
                })

    return pd.DataFrame(all_rows)


def main():
    print("Generating products...")
    products_df = generate_products(NUM_PRODUCTS)

    print("Generating warehouses...")
    warehouses_df = generate_warehouses(NUM_WAREHOUSES)

    print(f"Generating demand data for {NUM_PRODUCTS} products x "
          f"{NUM_WAREHOUSES} warehouses over {NUM_DAYS} days...")
    demand_df = generate_all_demand_data(products_df, warehouses_df, NUM_DAYS, START_DATE)

    products_df.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
    warehouses_df.to_csv(os.path.join(OUTPUT_DIR, "warehouses.csv"), index=False)
    demand_df.to_csv(os.path.join(OUTPUT_DIR, "daily_demand.csv"), index=False)

    print(f"Done. {len(demand_df)} demand rows saved to {OUTPUT_DIR}")
    print(f"  - products.csv: {len(products_df)} rows")
    print(f"  - warehouses.csv: {len(warehouses_df)} rows")
    print(f"  - daily_demand.csv: {len(demand_df)} rows")


if __name__ == "__main__":
    main()