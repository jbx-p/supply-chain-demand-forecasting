"""
inventory_optimizer.py

Translates demand forecasts into concrete inventory decisions: safety stock,
reorder point, and economic order quantity (EOQ). Also includes a simple
simulation to compare a naive inventory policy against an optimized one,
quantifying the cost impact of the difference.
"""

import numpy as np
from scipy.stats import norm


def calculate_safety_stock(demand_std, lead_time_days, service_level=0.95):
    """
    Safety Stock = Z(service_level) * demand_std * sqrt(lead_time)
    """
    z = norm.ppf(service_level)
    return z * demand_std * np.sqrt(lead_time_days)


def calculate_reorder_point(avg_daily_demand, lead_time_days, safety_stock):
    """
    Reorder Point = (avg daily demand * lead time) + safety stock
    """
    return (avg_daily_demand * lead_time_days) + safety_stock


def calculate_eoq(annual_demand, order_cost, holding_cost_per_unit):
    """
    Economic Order Quantity: the order size that minimizes total 
    ordering + holding cost.
    EOQ = sqrt( (2 * annual_demand * order_cost) / holding_cost_per_unit )
    """
    return np.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)

def simulate_inventory_policy(demand_series, reorder_point, order_qty, 
                                lead_time_days, starting_stock, unit_cost=1, 
                                stockout_cost_multiplier=3, holding_cost_rate=0.02):
    """
    Simulates day-by-day inventory levels under a given reorder policy.
    
    stockout_cost_multiplier: stockouts are assumed to cost more than the 
        unit cost itself (lost sale + potential rush-order premium + 
        customer dissatisfaction), so we multiply unit_cost by this factor.
    holding_cost_rate: daily holding cost as a fraction of unit_cost 
        (representing capital tied up, storage, etc.)
    """
    stock = starting_stock
    stockout_days = 0
    total_holding_cost = 0
    total_stockout_cost = 0
    pending_orders = []
    stock_history = []

    for day, demand in enumerate(demand_series):
        # Receive any orders arriving today
        arriving_today = [o for o in pending_orders if o == day]
        if arriving_today:
            stock += order_qty * len(arriving_today)
            pending_orders = [o for o in pending_orders if o != day]

        # Fulfill demand
        if demand > stock:
            shortfall = demand - stock
            stockout_days += 1
            total_stockout_cost += shortfall * unit_cost * stockout_cost_multiplier
            stock = 0
        else:
            stock -= demand

        # Holding cost on whatever remains
        total_holding_cost += stock * unit_cost * holding_cost_rate

        # Check if we need to trigger a reorder
        if stock <= reorder_point and (day + lead_time_days) not in pending_orders:
            pending_orders.append(day + lead_time_days)

        stock_history.append(stock)

    return {
        "stockout_days": stockout_days,
        "total_holding_cost": total_holding_cost,
        "total_stockout_cost": total_stockout_cost,
        "total_cost": total_holding_cost + total_stockout_cost,
        "stock_history": stock_history
    }