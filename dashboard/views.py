import os

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render

# ETL
from analytics.etl import run_etl_pipeline
# Plotly utilities
from analytics.plotly_utils import (create_department_productivity_chart,
                                    create_department_risk_chart,
                                    create_department_satisfaction_chart,
                                    create_employee_time_chart,
                                    create_hours_heatmap,
                                    create_productivity_chart,
                                    create_risk_distribution_chart,
                                    create_survey_breakdown_chart)

# Helper - Load processed CSVs

def get_data(name):
    """
    Load a processed CSV from data/processed using an absolute path
    so it matches analytics.etl.run_etl_pipeline.
    """
    base_dir = settings.BASE_DIR  
    processed_dir = os.path.join(base_dir, "data", "processed")
    path = os.path.join(processed_dir, f"{name}.csv")

    if not os.path.exists(path):
        return None

    return pd.read_csv(path)


# Signup

def signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        pw1 = request.POST["password1"]
        pw2 = request.POST["password2"]

        if pw1 != pw2:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")

        User.objects.create_user(username=username, email=email, password=pw1)
        return redirect("login")

    return render(request, "signup.html")

def logout_view(request):
    logout(request)
    return redirect("login")



# HOME DASHBOARD

@login_required
def dashboard_home(request):

    employees = get_data("employees")
    projects = get_data("project_data")
    satisfaction = get_data("employee_satisfaction")

    context = {
        "employee_count": len(employees) if employees is not None else 0,
        "departments": employees["department"].nunique() if employees is not None else 0,
        "avg_satisfaction": round(satisfaction["avg_satisfaction"].mean(), 2)
        if satisfaction is not None else 0,
        "active_projects": projects[projects["is_completed"] == 0]["project_id"].nunique()
        if projects is not None else 0,
    }

    if employees is not None:
        context["departments_list"] = employees["department"].unique().tolist()

    return render(request, "dashboard/home.html", context)



# PRODUCTIVITY DASHBOARD

@login_required
def productivity_dashboard(request):

    employees = get_data("employees")
    weekly = get_data("weekly_time")
    projects = get_data("project_data")

    department = request.GET.get("department")

    # Filter by department
    if department and employees is not None:
        emp_ids = employees[employees["department"] == department]["employee_id"].tolist()
        weekly = weekly[weekly["employee_id"].isin(emp_ids)]
        projects = projects[projects["employee_id"].isin(emp_ids)]

    # KPIs
    avg_productivity = round(weekly["productivity_ratio"].mean() * 100, 1) if weekly is not None else 0
    avg_hours = round(weekly["hours_logged"].mean(), 1) if weekly is not None else 0
    project_completion = round(projects["is_completed"].mean() * 100, 1) if projects is not None else 0
    on_time_rate = round(projects["on_time"].mean() * 100, 1) if projects is not None else 0

    # Charts
    productivity_trend = None
    productivity_by_dept = None
    heatmap_html = None

    if weekly is not None and not weekly.empty:

        df = weekly.copy()
        df["week_year"] = df["year"].astype(str) + "-W" + df["week"].astype(str)

        # Trend
        productivity_trend = create_productivity_chart(df)

        # Productivity by department
        merged = weekly.merge(employees[["employee_id", "department"]], on="employee_id")
        dept_df = merged.groupby("department")["productivity_ratio"].mean().reset_index()
        productivity_by_dept = create_department_productivity_chart(dept_df)

        # Heatmap
        heatmap_html = create_hours_heatmap(weekly)

    context = {
        "avg_productivity": avg_productivity,
        "avg_hours": avg_hours,
        "project_completion": project_completion,
        "on_time_rate": on_time_rate,

        # charts
        "productivity_trend": productivity_trend,
        "productivity_by_department": productivity_by_dept,
        "heatmap_plot": heatmap_html,

        # filters
        "departments_list": employees["department"].unique().tolist() if employees is not None else [],
        "selected_department": department,
    }

    return render(request, "dashboard/productivity.html", context)



# ENGAGEMENT DASHBOARD

@login_required
def engagement_dashboard(request):

    employees = get_data("employees")
    satisfaction = get_data("employee_satisfaction")
    survey = get_data("survey_responses")

    department = request.GET.get("department")

    if department and employees is not None:
        emp_ids = employees[employees["department"] == department]["employee_id"].tolist()
        if satisfaction is not None:
            satisfaction = satisfaction[satisfaction["employee_id"].isin(emp_ids)]
        if survey is not None:
            survey = survey[survey["employee_id"].isin(emp_ids)]

    # --- KPI ---
    avg_satisfaction = 0
    if satisfaction is not None and not satisfaction.empty and "avg_satisfaction" in satisfaction.columns:
        avg_satisfaction = round(satisfaction["avg_satisfaction"].mean(), 2)

    # --- Department satisfaction chart ---
    dept_sat_chart = None
    if employees is not None and satisfaction is not None:
        
        dept_df = employees.merge(
            satisfaction[["employee_id", "avg_satisfaction"]],
            on="employee_id",
            how="left"
        )
        # group by department
        dept_df = (
            dept_df.groupby("department")["avg_satisfaction"]
            .mean()
            .reset_index()
            .dropna()
        )
        if not dept_df.empty:
            dept_sat_chart = create_department_satisfaction_chart(dept_df)

    # --- Survey breakdown chart ---
    survey_plot = None
    question_scores = None
    if survey is not None and not survey.empty:
        question_scores = (
            survey.groupby("question")["numeric_response"]
            .mean()
            .reset_index()
        )
        survey_plot = create_survey_breakdown_chart(question_scores)

    context = {
        "avg_satisfaction": avg_satisfaction,
        "survey_plot": survey_plot,
        "question_scores": question_scores.to_dict("records") if question_scores is not None else None,
        "department_chart": dept_sat_chart,
        "departments_list": employees["department"].unique().tolist() if employees is not None else [],
        "selected_department": department,
    }

    return render(request, "dashboard/engagement.html", context)



# ATTRITION DASHBOARD

@login_required
def attrition_dashboard(request):

    employees = get_data("employees")
    attrition = get_data("attrition_data")  

    if attrition is None or attrition.empty:
        return render(request, "dashboard/attrition.html", {"model_error": True})

    
    if "attrition_probability" in attrition.columns:
        probs = attrition["attrition_probability"].astype(float)

        
        low_q = probs.quantile(0.60)
        high_q = probs.quantile(0.90)

        def classify(p):
            if p >= high_q:
                return "High"
            elif p >= low_q:
                return "Medium"
            else:
                return "Low"

        attrition["risk_level"] = probs.apply(classify)

    department = request.GET.get("department")

    if department:
        attrition = attrition[attrition["department"] == department]

    # --- High-risk stats ---
    high_risk_count = (attrition["risk_level"] == "High").sum()
    total = len(attrition)
    high_risk_pct = (high_risk_count / total * 100) if total else 0

    # --- Risk distribution chart (donut) ---
    risk_dist = (
        attrition["risk_level"]
        .value_counts()
        .reindex(["Low", "Medium", "High"])
        .dropna()
        .reset_index()
    )
    risk_dist.columns = ["Risk Level", "Count"]
    risk_plot = create_risk_distribution_chart(risk_dist)

    # --- Risk by department chart (top section only when "All Departments") ---
    dept_risk_plot = None
    if not department:
        dept_df = (
            attrition.groupby("department")["attrition_probability"]
            .mean()
            .reset_index()
        )
        dept_df["Count"] = (
            attrition.groupby("department")["employee_id"]
            .count()
            .values
        )

        # Rename columns to what create_department_risk_chart expects
        dept_df = dept_df.rename(
            columns={
                "department": "Department",
                "attrition_probability": "Average Risk",
            }
        )

        dept_risk_plot = create_department_risk_chart(dept_df)

    # --- High risk employees table (sorted) ---
    high_risk_employees = (
        attrition[attrition["risk_level"] == "High"]
        .sort_values("attrition_probability", ascending=False)
    )

    context = {
        "high_risk_count": int(high_risk_count),
        "high_risk_pct": round(high_risk_pct, 1),
        "risk_plot": risk_plot,
        "dept_risk_plot": dept_risk_plot,
        "high_risk_employees": high_risk_employees.to_dict("records"),
        "departments_list": employees["department"].unique().tolist()
                            if employees is not None else [],
        "selected_department": department,
    }

    return render(request, "dashboard/attrition.html", context)



# EMPLOYEE DETAIL PAGE

@login_required
def employee_detail(request, employee_id):

    employees = get_data("employees")
    time = get_data("time_tracking")
    projects = get_data("project_data")
    attrition = get_data("attrition_data")

    if employees is None or employee_id not in employees["employee_id"].values:
        return render(request, "dashboard/employee_detail.html", {"not_found": True})

    employee = employees[employees["employee_id"] == employee_id].iloc[0].to_dict()

    emp_time = time[time["employee_id"] == employee_id] if time is not None else None
    time_plot = create_employee_time_chart(emp_time.sort_values("date")) \
        if emp_time is not None and not emp_time.empty else None

    emp_projects = projects[projects["employee_id"] == employee_id] if projects is not None else None

    emp_attr = None
    if attrition is not None:
        row = attrition[attrition["employee_id"] == employee_id]
        emp_attr = row.iloc[0].to_dict() if not row.empty else None

    context = {
        "employee": employee,
        "time_plot": time_plot,
        "projects": emp_projects.to_dict("records") if emp_projects is not None else None,
        "attrition_data": emp_attr,
    }

    return render(request, "dashboard/employee_detail.html", context)



# RUN ETL PAGE

@login_required
def run_etl(request):
    if request.method == "POST":
        try:
            run_etl_pipeline()
            return JsonResponse({"status": "success", "message": "ETL completed successfully"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return render(request, "dashboard/run_etl.html")
