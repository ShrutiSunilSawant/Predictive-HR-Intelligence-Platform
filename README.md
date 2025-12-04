# Predictive HR Intelligence Platform  
### By **Shruti Sunil Sawant**

A modern HR analytics platform that transforms raw workforce data into actionable insights.  
Built with a robust ETL pipeline, a clean modular Django architecture, and interactive Plotly dashboards, the platform empowers HR teams to analyze:

- Workforce productivity  
- Employee engagement  
- Attrition risk  
- Project performance  
- Individual employee history  

This system is designed for accuracy, interpretability, and real-time decision support.

---

## 🚀 Key Features

### **1. Automated ETL Pipeline**
- Cleans, validates, and processes multiple HR datasets  
- Generates standardized, analytics-ready tables  
- Automatically assigns attrition risk levels  
- Ensures consistent weekly and departmental aggregations  

---

### **2. Interactive Analytics Dashboards**
Built using Plotly for fully interactive data exploration:

#### **Productivity Insights**
- Weekly productivity trends  
- Department-level performance  
- Workload heatmaps  

#### **Engagement & Satisfaction**
- Average satisfaction KPI  
- Department satisfaction breakdowns  
- Survey question-level insights  

#### **Attrition Intelligence**
- Risk distribution across workforce  
- Departmental risk segmentation  
- High-risk employee identification  

#### **Employee Detail Views**
- Personal information  
- Productivity timeline  
- Satisfaction & performance metrics  
- Attrition scoring profile  
- Project history  

---

## 🏗️ System Architecture

HR_ANALYTICS/
│
├── analytics/
│   ├── etl.py                     # ETL pipeline
│   ├── plotly_utils.py            # All chart generation functions
│   └── __init__.py
│
├── dashboard/
│   ├── views.py                   # Dashboards + logic
│   ├── static/css/dashboard.css   # Modern dark theme UI
│   ├── templates/dashboard/*.html # Dashboard pages
│   └── __init__.py
│
├── data/
│   ├── raw/                       # Original CSVs
│   └── processed/                 # ETL output
│
├── templates/                     # Login, signup, base template
├── db.sqlite3                     # Local DB
├── urls.py
├── settings.py
└── manage.py

---

## Installation & Setup

### 1. Clone the Repository
git clone https://github.com/your-username/predictive-hr-intelligence.git
cd predictive-hr-intelligence

### 2. Create Virtual Environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Run Database Migrations
python manage.py migrate

### 5. Run ETL Pipeline
python manage.py shell
>>> from analytics.etl import run_etl_pipeline
>>> run_etl_pipeline()
>>> exit()

### 6. Start the Server
python manage.py runserver

---

## Datasets Used

Your platform is powered by four primary datasets:
| Dataset              | Purpose                                      |
| -------------------- | -------------------------------------------- |
| employees.csv        | Employee profiles, job info, managers        |
| time_tracking.csv    | Hours, billable/non-billable work, meetings  |
| project_data.csv     | Workload distribution, deadlines, priorities |
| survey_responses.csv | Engagement, satisfaction, sentiment          |
