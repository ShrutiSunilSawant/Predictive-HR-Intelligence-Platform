import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

# THEME COLORS

COLORS = {
    'background': '#243447',
    'paper_bgcolor': '#2c3e50',
    'grid': '#2f3d52',
    'text': '#e2e8f0',
    'subtext': '#94a3b8',

    # Muted *non-pop* accent palette
    'blue': '#5FA8F5',      
    'green': '#78D39E',     
    'red': '#F28B82',       
    'yellow': '#F7C66F',    
    'purple': '#B39DDB',    

    # Department palette 
    'departments': [
        '#4f6fa9',  
        '#5a8f6f',  
        '#b76e79',  
        '#c9a96a',  
        '#7f6fa3',  
        '#5e8c99',  
        '#8c736a',  
    ],

    # Risk levels (muted shades)
    'risk_levels': {
        'Low': '#5a8f6f',      
        'Medium': '#c9a96a',   
        'High': '#b76e79'      
    }
}

# BASE LAYOUT

def create_base_layout():
    """Shared dark theme layout for all charts (no legend positioning here)."""
    return go.Layout(
        paper_bgcolor=COLORS["paper_bgcolor"],
        plot_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"]),
        margin=dict(l=40, r=40, t=80, b=90),  
        xaxis=dict(
            gridcolor=COLORS["grid"],
            linecolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
        ),
        yaxis=dict(
            gridcolor=COLORS["grid"],
            linecolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
        ),
        
    )


# EXISTING CHART FUNCTIONS 

def create_productivity_chart(time_series_data):
    """
    Smooth, expressive productivity chart.
    Shows visible up/down trends + spacing.
    """

    df = time_series_data.copy()
    df["week_year"] = df["year"].astype(str) + "-W" + df["week"].astype(str)

    # USE MEAN instead of MEDIAN → restores real variation
    weekly = df.groupby("week_year").agg({
        "productivity_ratio": "mean",
        "activity_percentage": "mean",
    }).reset_index()

    weekly["activity_norm"] = weekly["activity_percentage"] / 100

    # Compute a zoomed-in y-axis range
    y_min = min(weekly["productivity_ratio"].min(), weekly["activity_norm"].min())
    y_max = max(weekly["productivity_ratio"].max(), weekly["activity_norm"].max())

    padding = 0.05  # adds space above/below the lines
    y_min -= padding
    y_max += padding

    layout = create_base_layout()
    layout.update(
        title=None,
        xaxis_title="Week",
        yaxis_title="Values",
        height=420,
        margin=dict(l=50, r=40, t=20, b=120),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
        ),
    )

    fig = go.Figure(layout=layout)

    # Productivity line
    fig.add_trace(go.Scatter(
        x=weekly["week_year"],
        y=weekly["productivity_ratio"],
        mode="lines",
        name="Mean Productivity",
        line=dict(
            width=4,
            color=COLORS["blue"],
            shape="spline",
            smoothing=1.1,
        ),
    ))

    # Activity line
    fig.add_trace(go.Scatter(
        x=weekly["week_year"],
        y=weekly["activity_norm"],
        mode="lines",
        name="Mean Activity %",
        line=dict(
            width=4,
            color=COLORS["green"],
            shape="spline",
            smoothing=1.1,
        ),
    ))

    fig.update_xaxes(
        tickangle=-40,
        tickfont=dict(size=11),
        nticks=10,
        automargin=True,
    )

    fig.update_yaxes(
        tickfont=dict(size=11),
        range=[y_min, y_max],  
    )

    return plot(
        fig,
        output_type="div",
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )


def create_department_risk_chart(dept_risk_data):
    """Bar chart: Attrition risk by department."""
    layout = create_base_layout()
    layout.update(
        title=dict(text="Attrition Risk by Department", font=dict(size=18)),
        xaxis_title="Department",
        yaxis_title="Attrition Probability"
    )

    max_risk = dept_risk_data['Average Risk'].max()
    colors = [
        COLORS['green'] if x < 0.3 else
        COLORS['yellow'] if x < 0.6 else
        COLORS['red']
        for x in dept_risk_data['Average Risk']
    ]

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Bar(
        x=dept_risk_data['Department'],
        y=dept_risk_data['Average Risk'],
        marker_color=colors,
        text=dept_risk_data['Count'],
        textposition='auto'
    ))

    return plot(fig, output_type='div', include_plotlyjs=False)


def create_risk_distribution_chart(risk_distribution):
    """Pie chart: overall attrition risk distribution."""
    colors = [COLORS['risk_levels'][level] for level in risk_distribution['Risk Level']]

    layout = create_base_layout()
    layout.update(title=dict(text="Attrition Risk Distribution", font=dict(size=18)))

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Pie(
        labels=risk_distribution['Risk Level'],
        values=risk_distribution['Count'],
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textfont=dict(color=COLORS['text'])
    ))

    return plot(fig, output_type='div', include_plotlyjs=False)


def create_survey_breakdown_chart(question_scores):
    """Horizontal bar chart for survey question scores."""
    layout = create_base_layout()
    layout.update(
        title=dict(text="Survey Question Breakdown", font=dict(size=18)),
        xaxis_title="Average Score",
        height=600,
        yaxis=dict(categoryorder='total ascending')
    )

    colors = [
        COLORS['red'] if x < 3 else
        COLORS['yellow'] if x < 4 else
        COLORS['green']
        for x in question_scores['numeric_response']
    ]

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Bar(
        y=question_scores['question'],
        x=question_scores['numeric_response'],
        orientation='h',
        marker_color=colors
    ))

    # Reference line at score 3
    fig.add_shape(
        type="line",
        x0=3, y0=-0.5,
        x1=3, y1=len(question_scores) - 0.5,
        line=dict(color=COLORS['grid'], width=2, dash="dash")
    )

    return plot(fig, output_type='div', include_plotlyjs=False)


def create_employee_time_chart(employee_time):
    """Individual employee time tracking chart."""
    layout = create_base_layout()
    layout.update(
        title=dict(text="Employee Time Tracking History", font=dict(size=18)),
        xaxis_title="Date",
        yaxis_title="Hours"
    )

    fig = go.Figure(layout=layout)

    # Hours logged
    fig.add_trace(go.Scatter(
        x=employee_time['date'],
        y=employee_time['hours_logged'],
        mode='lines+markers',
        name='Hours Logged',
        line=dict(width=3, color=COLORS['blue'])
    ))

    # Billable hours
    fig.add_trace(go.Scatter(
        x=employee_time['date'],
        y=employee_time['billable_hours'],
        mode='lines+markers',
        name='Billable Hours',
        line=dict(width=3, color=COLORS['green'])
    ))

    # Meeting hours (optional)
    if 'meeting_hours' in employee_time.columns:
        fig.add_trace(go.Scatter(
            x=employee_time['date'],
            y=employee_time['meeting_hours'],
            mode='lines+markers',
            name='Meeting Hours',
            line=dict(width=3, color=COLORS['yellow'])
        ))

    return plot(fig, output_type='div', include_plotlyjs=False)


# NEW CHARTS ADDED FOR FULL DASHBOARD SUPPORT

def create_department_productivity_chart(dept_df):
    """
    Bar chart: average productivity ratio by department.
    Matches the same height/margins as the trend chart.
    Card h5 supplies the title.
    """

    layout = create_base_layout()
    layout.update(
        title=None,                          
        xaxis_title="Department",
        yaxis_title="Avg Productivity Ratio",
        height=380,                          
        margin=dict(
            l=40,
            r=40,
            t=40,
            b=80,                            
        ),
    )

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Bar(
        x=dept_df["department"],
        y=dept_df["productivity_ratio"],
        marker_color=COLORS["blue"],
        hovertemplate="<b>%{x}</b><br>Avg productivity: %{y:.2f}<extra></extra>",
    ))

    fig.update_xaxes(
        tickangle=-35,
        tickfont=dict(size=11),
    )
    fig.update_yaxes(
        tickfont=dict(size=11),
        range=[0, 1.0],
    )

    return plot(
        fig,
        output_type="div",
        include_plotlyjs=False,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


def create_hours_heatmap(df):
    pivot = df.pivot_table(
        index="employee_id",
        columns="week",
        values="hours_logged",
        aggfunc="mean"
    )

    layout = create_base_layout()
    layout.update(
        title="Weekly Hours Heatmap",
        xaxis_title="Week Number",
        yaxis_title="Employee ID",
        height=450
    )

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale="Blues"
    ))

    return plot(fig, output_type="div", include_plotlyjs=False)


def create_department_satisfaction_chart(dept_df):
    layout = create_base_layout()
    layout.update(
        title="Average Satisfaction by Department",
        xaxis_title="Department",
        yaxis_title="Avg Satisfaction"
    )

    fig = go.Figure(layout=layout)

    fig.add_trace(go.Bar(
        x=dept_df["department"],
        y=dept_df["avg_satisfaction"],
        marker_color=COLORS["green"]
    ))

    return plot(fig, output_type="div", include_plotlyjs=False)
