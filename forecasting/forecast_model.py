"""
forecast_model.py

Core forecasting functions using Prophet. Given a demand series for a 
specific product/warehouse combination, trains a model and produces a 
forecast with confidence intervals.
"""

import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error


def prepare_series(demand_df, product_id, warehouse_id):
    series = demand_df[
        (demand_df.product_id == product_id) & (demand_df.warehouse_id == warehouse_id)
    ][["date", "units_sold"]].rename(columns={"date": "ds", "units_sold": "y"})
    return series.sort_values("ds").reset_index(drop=True)


def train_test_split_series(series, test_frac=0.2):
    split_point = int(len(series) * (1 - test_frac))
    return series.iloc[:split_point], series.iloc[split_point:]


def fit_prophet_model(train_df):
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
    model.fit(train_df)
    return model


def forecast_future(model, periods):
    future = model.make_future_dataframe(periods=periods)
    return model.predict(future)


def evaluate_forecast(actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    mape = mean_absolute_percentage_error(actual, predicted) * 100
    return {"mae": mae, "mape": mape}


def run_full_forecast(demand_df, product_id, warehouse_id, periods=90):
    """
    Convenience function: trains on ALL available data (no held-out test set)
    and forecasts `periods` days into the future. Used for live forecasts
    (e.g., in the Streamlit app), as opposed to evaluation.
    """
    series = prepare_series(demand_df, product_id, warehouse_id)
    model = fit_prophet_model(series)
    forecast = forecast_future(model, periods)
    return forecast, model