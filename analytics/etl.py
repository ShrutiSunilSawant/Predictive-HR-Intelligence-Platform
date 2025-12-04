import os
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"

# Helpers

def _load_csv(name: str, folder: Path = RAW_DIR) -> pd.DataFrame | None:
    """Load a CSV by basename (without .csv). Returns None if missing."""
    path = folder / f"{name}.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


def _save_csv(df: pd.DataFrame, name: str, folder: Path = PROC_DIR) -> None:
    """Save DF to processed folder, creating the folder if needed."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.csv"
    df.to_csv(path, index=False)

# Core ETL

def run_etl_pipeline() -> bool:
    
    # 1. Load RAW datasets
    
    employees = _load_csv("employees")
    projects = _load_csv("project_data")
    survey = _load_csv("survey_responses")
    time_tracking = _load_csv("time_tracking")

    
    if employees is None or projects is None or survey is None or time_tracking is None:
        raise FileNotFoundError(
            "One or more required raw CSVs are missing in data/raw "
            "(employees, project_data, survey_responses, time_tracking)."
        )

    # Copy raw → processed (so views always read from processed/)
    _save_csv(employees, "employees")
    _save_csv(projects, "project_data")
    _save_csv(survey, "survey_responses")
    _save_csv(time_tracking, "time_tracking")

    
    if "employee_id" not in employees.columns:
        raise KeyError("employees.csv must contain an 'employee_id' column")

    if "employee_id" not in projects.columns:
        raise KeyError("project_data.csv must contain an 'employee_id' column")

    if "employee_id" not in survey.columns:
        raise KeyError("survey_responses.csv must contain an 'employee_id' column")

    if "employee_id" not in time_tracking.columns:
        raise KeyError("time_tracking.csv must contain an 'employee_id' column")

    
    # 2. EMPLOYEE SATISFACTION (employee_satisfaction.csv)
    
    if "numeric_response" in survey.columns:
        score_col = "numeric_response"
    elif "score" in survey.columns:
        score_col = "score"
    else:
        
        survey["numeric_response"] = 3.5
        score_col = "numeric_response"

    emp_sat = (
        survey.groupby("employee_id")[score_col]
        .mean()
        .reset_index()
        .rename(columns={score_col: "avg_satisfaction"})
    )

    _save_csv(emp_sat, "employee_satisfaction")

    
    # 3. WEEKLY TIME AGGREGATION (weekly_time.csv)
    
    if "date" not in time_tracking.columns:
        raise KeyError("time_tracking.csv must contain a 'date' column")

    time_tracking["date"] = pd.to_datetime(time_tracking["date"])

    
    if "hours_logged" not in time_tracking.columns:
        raise KeyError("time_tracking.csv must contain a 'hours_logged' column")

    if "billable_hours" not in time_tracking.columns:
        time_tracking["billable_hours"] = time_tracking["hours_logged"]

    
    iso = time_tracking["date"].dt.isocalendar()
    time_tracking["year"] = iso["year"].astype(int)
    time_tracking["week"] = iso["week"].astype(int)

    weekly_agg = (
        time_tracking.groupby(["employee_id", "year", "week"])
        .agg(
            hours_logged=("hours_logged", "sum"),
            billable_hours=("billable_hours", "sum"),
        )
        .reset_index()
    )

    
    weekly_agg["productivity_ratio"] = (
        weekly_agg["billable_hours"] / weekly_agg["hours_logged"].replace(0, np.nan)
    ).fillna(0.0)

    
    weekly_agg["activity_percentage"] = (
        weekly_agg["hours_logged"] / 40.0 * 100.0
    ).clip(0, 300)

    _save_csv(weekly_agg, "weekly_time")


    # 4. HEURISTIC ATTRITION DATA (attrition_data.csv)
    
    # 4a. Merge satisfaction
    attr = employees.copy()
    attr = attr.merge(emp_sat, on="employee_id", how="left")

    # 4b. Avg weekly hours + productivity per employee
    emp_time_agg = (
        weekly_agg.groupby("employee_id")
        .agg(
            avg_hours=("hours_logged", "mean"),
            avg_productivity=("productivity_ratio", "mean"),
        )
        .reset_index()
    )
    attr = attr.merge(emp_time_agg, on="employee_id", how="left")

    # 4c. Project completion rate per employee
    
    if "project_id" not in projects.columns:
        raise KeyError("project_data.csv must contain a 'project_id' column")

    if "is_completed" not in projects.columns:
        # If missing, assume all are completed
        projects["is_completed"] = 1

    if "on_time" not in projects.columns:
        # If missing, assume all are on time
        projects["on_time"] = 1

    proj_agg = (
        projects.groupby("employee_id")
        .agg(
            total_projects=("project_id", "nunique"),
            completion_rate=("is_completed", "mean"),
            on_time_rate=("on_time", "mean"),
        )
        .reset_index()
    )
    attr = attr.merge(proj_agg, on="employee_id", how="left")

    # Fill NaNs with reasonable defaults
    attr["avg_satisfaction"] = attr["avg_satisfaction"].fillna(3.5)
    attr["avg_hours"] = attr["avg_hours"].fillna(40.0)
    attr["avg_productivity"] = attr["avg_productivity"].fillna(0.7)
    attr["completion_rate"] = attr["completion_rate"].fillna(0.8)
    attr["on_time_rate"] = attr["on_time_rate"].fillna(0.9)

    
    # 4d. Ensure 'name' and 'role' columns exist (avoid KeyError)
    
    if "name" not in attr.columns:
        if "employee_name" in attr.columns:
            attr["name"] = attr["employee_name"]
        elif "EmployeeName" in attr.columns:
            attr["name"] = attr["EmployeeName"]
        else:
            
            attr["name"] = "Employee"

    
    if "role" not in attr.columns:
        if "job_role" in attr.columns:
            attr["role"] = attr["job_role"]
        elif "JobRole" in attr.columns:
            attr["role"] = attr["JobRole"]
        elif "position" in attr.columns:
            attr["role"] = attr["position"]
        else:
            attr["role"] = "Role"

    
    # 4e. Heuristic attrition probability (0–1)
    
    
    sat_component = (5.0 - attr["avg_satisfaction"]) / 4.0  # 0–1

    
    hours_component = (attr["avg_hours"] - 45.0) / 20.0
    hours_component = hours_component.clip(0, 1)

    
    compl_component = (1.0 - attr["completion_rate"]).clip(0, 1)

    
    on_time_component = (1.0 - attr["on_time_rate"]).clip(0, 1)

    attrition_prob = (
        0.45 * sat_component
        + 0.25 * hours_component
        + 0.20 * compl_component
        + 0.10 * on_time_component
    ).clip(0, 1)

    attr["attrition_probability"] = attrition_prob.round(3)

    
    def _bucket(p: float) -> str:
        if p >= 0.7:
            return "High"
        if p >= 0.4:
            return "Medium"
        return "Low"

    attr["risk_level"] = attr["attrition_probability"].apply(_bucket)

    
    # 4f. Keep only relevant columns that actually exist
    
    desired_cols = [
        "employee_id",
        "name",
        "department",
        "role",
        "avg_satisfaction",
        "avg_hours",
        "avg_productivity",
        "total_projects",
        "completion_rate",
        "on_time_rate",
        "attrition_probability",
        "risk_level",
    ]
    keep_cols = [c for c in desired_cols if c in attr.columns]
    attr = attr[keep_cols]

    _save_csv(attr, "attrition_data")

    return True
