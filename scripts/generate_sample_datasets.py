"""
Sample Dataset Generator for Multi-Agent AI Business Analyst.

Generates diverse benchmark datasets spanning multiple business verticals:
1. SaaS Subscription & Recurring Revenue (MRR, Churn, LTV, CAC)
2. Healthcare & Hospital Operations (Costs, Length of Stay, Patient Satisfaction)
3. Global Supply Chain & Logistics (Transit Times, Shipping Costs, Delivery Delays)
"""

import random
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_datasets"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# 1. SaaS Subscription Metrics Dataset
# -------------------------------------------------------------
def generate_saas_dataset(num_records: int = 150):
    plans = ["Starter", "Professional", "Enterprise", "Custom"]
    plan_prices = {"Starter": 49.0, "Professional": 199.0, "Enterprise": 799.0, "Custom": 1499.0}
    industries = ["Fintech", "HealthTech", "E-Commerce", "EdTech", "Logistics", "Marketing"]

    start_date = datetime(2024, 1, 1)
    rows = []

    for i in range(1, num_records + 1):
        signup = start_date + timedelta(days=random.randint(0, 300))
        plan = random.choices(plans, weights=[0.4, 0.35, 0.2, 0.05])[0]
        mrr = plan_prices[plan]
        arr = mrr * 12
        cac = round(random.uniform(150.0, 950.0), 2)
        ltv = round(mrr * random.uniform(8.0, 36.0), 2)
        churned = random.choices([0, 1], weights=[0.85, 0.15])[0]
        support_tickets = random.randint(0, 12)
        nps_score = random.randint(4, 10)

        rows.append({
            "Customer_ID": f"CUST-SAAS-{i:04d}",
            "Subscription_Date": signup.strftime("%Y-%m-%d"),
            "Industry": random.choice(industries),
            "Plan_Tier": plan,
            "Monthly_Recurring_Revenue": mrr,
            "Annual_Recurring_Revenue": arr,
            "Customer_Acquisition_Cost": cac,
            "Customer_Lifetime_Value": ltv,
            "Support_Tickets_Logged": support_tickets,
            "NPS_Satisfaction_Score": nps_score,
            "Is_Churned": churned,
        })

    df = pd.DataFrame(rows)
    output_path = OUTPUT_DIR / "saas_subscription_metrics.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated SaaS dataset: {output_path} ({len(df)} rows)")


# -------------------------------------------------------------
# 2. Healthcare & Hospital Operations Dataset
# -------------------------------------------------------------
def generate_healthcare_dataset(num_records: int = 120):
    departments = ["Cardiology", "Orthopedics", "Neurology", "Pediatrics", "Oncology", "General Surgery"]
    insurances = ["Medicare", "Private Insurance", "Medicaid", "Self-Pay"]
    start_date = datetime(2024, 1, 1)
    rows = []

    for i in range(1, num_records + 1):
        admit_date = start_date + timedelta(days=random.randint(0, 320))
        dept = random.choice(departments)
        bed_days = random.randint(1, 14)
        base_cost = random.uniform(2500.0, 18000.0)
        treatment_cost = round(base_cost + (bed_days * 850.0), 2)
        patient_age = random.randint(18, 88)
        satisfaction = round(random.uniform(6.5, 10.0), 1)
        readmitted = 1 if (bed_days > 8 and random.random() < 0.25) else 0

        rows.append({
            "Patient_ID": f"PAT-MED-{i:04d}",
            "Admission_Date": admit_date.strftime("%Y-%m-%d"),
            "Department": dept,
            "Patient_Age": patient_age,
            "Length_Of_Stay_Days": bed_days,
            "Treatment_Cost": treatment_cost,
            "Insurance_Provider": random.choice(insurances),
            "Readmitted_Within_30_Days": readmitted,
            "Patient_Satisfaction_Rating": satisfaction,
        })

    df = pd.DataFrame(rows)
    output_path = OUTPUT_DIR / "healthcare_clinic_operations.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated Healthcare dataset: {output_path} ({len(df)} rows)")


# -------------------------------------------------------------
# 3. Global Supply Chain Logistics Dataset
# -------------------------------------------------------------
def generate_supply_chain_dataset(num_records: int = 140):
    origins = ["Shanghai", "Rotterdam", "Singapore", "Los Angeles", "Hamburg", "Dubai"]
    destinations = ["New York", "Chicago", "Frankfurt", "Tokyo", "London", "Sydney"]
    shipping_modes = ["Ocean Freight", "Air Cargo", "Road Freight", "Rail Express"]
    start_date = datetime(2024, 1, 1)
    rows = []

    for i in range(1, num_records + 1):
        ship_date = start_date + timedelta(days=random.randint(0, 310))
        mode = random.choice(shipping_modes)
        distance_km = random.randint(800, 14000)
        cargo_weight_kg = random.randint(150, 25000)
        base_rate = 1.2 if mode == "Ocean Freight" else (4.5 if mode == "Air Cargo" else 2.0)
        shipping_cost = round((cargo_weight_kg * 0.15) + (distance_km * base_rate * 0.05), 2)
        expected_days = max(2, int(distance_km / 800) + (10 if mode == "Ocean Freight" else 1))
        actual_days = expected_days + random.choice([0, 0, 0, 1, 2, -1, 4])
        is_delayed = 1 if actual_days > expected_days else 0
        damage_claimed = 1 if (is_delayed and random.random() < 0.08) else 0

        rows.append({
            "Shipment_ID": f"SHIP-LOG-{i:04d}",
            "Shipment_Date": ship_date.strftime("%Y-%m-%d"),
            "Origin_Hub": random.choice(origins),
            "Destination_Hub": random.choice(destinations),
            "Transport_Mode": mode,
            "Distance_Kilometers": distance_km,
            "Cargo_Weight_KG": cargo_weight_kg,
            "Shipping_Cost_USD": shipping_cost,
            "Transit_Days": actual_days,
            "Is_Delayed": is_delayed,
            "Damage_Claim_Filed": damage_claimed,
        })

    df = pd.DataFrame(rows)
    output_path = OUTPUT_DIR / "supply_chain_logistics.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated Supply Chain dataset: {output_path} ({len(df)} rows)")


if __name__ == "__main__":
    generate_saas_dataset()
    generate_healthcare_dataset()
    generate_supply_chain_dataset()
    print("All multi-domain benchmark datasets generated successfully!")
