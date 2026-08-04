"""
streamlit_app.py

Interactive demand forecasting and inventory optimization simulator.
Lets a user select a product/warehouse, adjust service level and lead time,
and see live forecasted demand, recommended safety stock/reorder point,
and a cost comparison versus a naive policy.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

# --- Path setup so we can import from forecasting/ ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from forecasting.forecast_model import prepare_series, fit_prophet_model, forecast_future
from forecasting.inventory_optimizer import (
    calculate_safety_stock, calculate_reorder_point, simulate_inventory_policy
)

st.set_page_config(page_title="Demand Forecast & Inventory Optimizer", layout="wide")


@st.cache_data
def load_data():
    demand_df = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "raw", "daily_demand.csv"), parse_dates=["date"])
    products_df = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "raw", "products.csv"))
    warehouses_df = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "raw", "warehouses.csv"))
    return demand_df, products_df, warehouses_df

demand_df, products_df, warehouses_df = load_data()


st.title("📦 Demand Forecast & Inventory Optimizer")
st.markdown("Interactive tool for forecasting product demand and recommending inventory policy.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    product_id = st.selectbox("Product", sorted(products_df["product_id"].unique()))
with col2:
    warehouse_id = st.selectbox("Warehouse", sorted(warehouses_df["warehouse_id"].unique()))
with col3:
    service_level = st.slider("Target Service Level", min_value=0.80, max_value=0.99, value=0.95, step=0.01)
with col4:
    lead_time_override = st.number_input("Lead Time (days)", min_value=1, max_value=60, value=14)


series = prepare_series(demand_df, product_id, warehouse_id)
avg_daily_demand = series["y"].mean()
demand_std = series["y"].std()

with st.spinner("Training forecast model..."):
    model = fit_prophet_model(series)
    forecast = forecast_future(model, periods=90)


st.subheader(f"Demand Forecast — Product {product_id}, Warehouse {warehouse_id}")

chart_data = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(120).set_index("ds")
st.line_chart(chart_data[["yhat"]])

with st.expander("View forecast data table"):
    st.dataframe(chart_data.tail(30))


safety_stock = calculate_safety_stock(demand_std, lead_time_override, service_level)
reorder_point = calculate_reorder_point(avg_daily_demand, lead_time_override, safety_stock)

st.subheader("📋 Inventory Recommendation")

metric_col1, metric_col2, metric_col3 = st.columns(3)
with metric_col1:
    st.metric("Avg Daily Demand", f"{avg_daily_demand:.1f} units")
with metric_col2:
    st.metric("Recommended Safety Stock", f"{safety_stock:.0f} units")
with metric_col3:
    st.metric("Recommended Reorder Point", f"{reorder_point:.0f} units")


st.subheader("💰 Policy Cost Comparison")

unit_cost = products_df[products_df.product_id == product_id]["unit_cost"].values[0]
demand_values = series["y"].values

naive_reorder_point = avg_daily_demand * lead_time_override
naive_order_qty = avg_daily_demand * lead_time_override * 2
optimized_order_qty = naive_order_qty

naive_result = simulate_inventory_policy(
    demand_values, naive_reorder_point, naive_order_qty,
    lead_time_override, starting_stock=naive_reorder_point, unit_cost=unit_cost
)
optimized_result = simulate_inventory_policy(
    demand_values, reorder_point, optimized_order_qty,
    lead_time_override, starting_stock=naive_reorder_point, unit_cost=unit_cost
)

comp_col1, comp_col2 = st.columns(2)
with comp_col1:
    st.markdown("**Naive Policy** (no safety stock)")
    st.metric("Stockout Days", naive_result["stockout_days"])
    st.metric("Total Cost", f"${naive_result['total_cost']:.2f}")
with comp_col2:
    st.markdown("**Optimized Policy** (forecast-driven)")
    st.metric("Stockout Days", optimized_result["stockout_days"],
               delta=int(optimized_result["stockout_days"] - naive_result["stockout_days"]))
    st.metric("Total Cost", f"${optimized_result['total_cost']:.2f}",
               delta=f"${optimized_result['total_cost'] - naive_result['total_cost']:.2f}")


st.markdown("---")
st.caption(
    "Note: Demand data is synthetically generated for portfolio purposes. "
    "Safety stock assumes approximately normal demand distribution. "
    "Stockout cost is modeled as 3× unit cost; holding cost as 2% of unit cost per day."
)