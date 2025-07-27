import streamlit as st
from PIL import Image
import os
import pandas as pd
import psycopg2
from psycopg2 import sql
import plotly.express as px
from sqlalchemy import create_engine
import altair as alt
import pycountry
import plotly.graph_objects as go
from datetime import datetime

# Database connection parameters
db_params = {
    'dbname': 'secure_police_db',
    'user': 'postgres',
    'password': '10987654321',
    'host': 'localhost',
    'port': '5432'
}
# Function to create a connection to the PostgreSQL database
def create_connection():
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None
# Function to fetch data from the database
def fetch_data(query):
    conn = create_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(result, columns=column_names)
                df.columns= df.columns.str.strip()  # Strip whitespace from column names
                return df
        finally:
            conn.close()
    else:
        return pd.DataFrame()  # Return an empty DataFrame if connection fails
# Streamlit app layout
st.set_page_config(page_title="🚔 Patrol Ledger: SecureCheck Dashboard", layout="wide")
st.title("🚔 Patrol Ledger: SecureCheck Dashboard")
logo_path = os.path.join(os.path.expanduser("~"), "Downloads", "logo.png")
icon_path = os.path.join(os.path.expanduser("~"), "Downloads", "icon.png")
st.logo(
    image=logo_path,
    icon_image=icon_path # Optional second image (typically square icon)
)
with st.sidebar:
    st.title("A Digital Ledger for Police Post Logs")
    st.header("👮 Log Police Activity")
# Show full dataframe
query = "SELECT * FROM police_Logs"
df = fetch_data(query)
with st.expander("Patrol Logs", expanded=False):
    st.dataframe(df)
# Display Key Metrics
st.markdown("""
    <h1 style='color:#1F4E79; font-size: 32px;'>
        All-Time Statistics
    </h1>
""", unsafe_allow_html=True)
# Calculate metrics
total_stops = df.shape[0]
arrests = df[df['stop_outcome'].str.contains('Arrest', case=False, na=False)].shape[0]
warnings = df[df['stop_outcome'].str.contains('Warning', case=False, na=False)].shape[0]
drug_related = df[df['drugs_related_stop'] == 1].shape[0]
# Custom card template
def metric_card(title, value, color):
    st.markdown(f"""
        <div style="background-color:{color}; padding:1rem; border-radius:12px; text-align:center; color:white; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
            <h5 style="margin:0; font-size:1rem;">{title}</h5>
            <h2 style="margin:0; font-size:2rem;">{value}</h2>
        </div>
    """, unsafe_allow_html=True)
# Display in columns
col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Stops", total_stops, "#E57373") 
with col2:
    metric_card("Total Arrests", arrests, "#FFB74D")
with col3:
    metric_card("Total Warnings", warnings, "#BDBDBD")
with col4:
    metric_card("Drug Incidents", drug_related, "#B39DDB") 

#Key Ratios
def plot_gauge(indicator_number, indicator_color, indicator_suffix, indicator_title, max_bound):
    # Define darker and lighter variants for each color
    color_variants = {
        "red": ("#E74C3C", "#FADBD8"),
        "blue": ("#3498DB", "#D6EAF8"),
        "orange": ("#F39C12", "#FDEBD0"),
        "purple": ("#9B59B6", "#E8DAEF"),
        "green": ("#2ECC71", "#D5F5E3"),
        "teal": ("#1ABC9C", "#D1F2EB")
    }

    dark_color, light_color = color_variants.get(indicator_color, ("#999999", "#DDDDDD"))

    fig = go.Figure(
        go.Indicator(
            value=indicator_number,
            mode="gauge+number",
            domain={"x": [0, 1], "y": [0, 1]},
            number={"suffix": indicator_suffix, "font.size": 16},
            gauge={
                "axis": {"range": [0, max_bound]},
                "bar": {"color": dark_color},
                "steps": [
                    {"range": [0, indicator_number], "color": dark_color},
                    {"range": [indicator_number, max_bound], "color": light_color}
                ],
                "threshold": {
                    "line": {"color": dark_color, "width": 2},
                    "thickness": 0.75,
                    "value": indicator_number
                }
            },
            title={"text": f"<b>{indicator_title}</b>", "font": {"size": 12}}
        )
    )

    fig.update_layout(height=180, margin=dict(t=30, b=10, l=10, r=10))
    return fig
query_gauges = """
SELECT
  ROUND(100.0 * COUNT(CASE WHEN stop_outcome = 'Arrest' THEN 1 END) / COUNT(*), 2) AS arrest_ratio,
  ROUND(100.0 * COUNT(CASE WHEN driver_gender = 'F' THEN 1 END) / COUNT(*), 2) AS female_ratio,
  ROUND(100.0 * COUNT(CASE WHEN drugs_related_stop = TRUE THEN 1 END) / COUNT(*), 2) AS drug_ratio,
  ROUND(100.0 * COUNT(CASE WHEN driver_age < 18 THEN 1 END) / COUNT(*), 2) AS juvenile_ratio,
  ROUND(100.0 * COUNT(CASE WHEN stop_outcome = 'Warning' THEN 1 END) / COUNT(*), 2) AS verbal_warning_ratio,
  ROUND(100.0 * COUNT(CASE WHEN stop_duration = '0-15 Min' THEN 1 END) / COUNT(*), 2) AS short_stop_ratio
FROM police_logs;
"""
df_gauges = fetch_data(query_gauges)
st.markdown("""
    <h1 style='color:#1F4E79; font-size: 32px;'>
         Key Ratios
    </h1>
""", unsafe_allow_html=True)
gauge_row = st.columns(6)
if not df_gauges.empty:
    # Extract ratios
    arrest_ratio = df_gauges['arrest_ratio'].iloc[0]
    female_ratio = df_gauges['female_ratio'].iloc[0]
    drug_ratio = df_gauges['drug_ratio'].iloc[0]
    juvenile_ratio = df_gauges['juvenile_ratio'].iloc[0]
    verbal_warning_ratio = df_gauges['verbal_warning_ratio'].iloc[0]
    short_stop_ratio = df_gauges['short_stop_ratio'].iloc[0]

    with gauge_row[0]:
        st.plotly_chart(plot_gauge(arrest_ratio, "red", "%", "Arrest Ratio", 100), use_container_width=True)
    with gauge_row[1]:
        st.plotly_chart(plot_gauge(female_ratio, "blue", "%", "Female Drivers", 100), use_container_width=True)
    with gauge_row[2]:
        st.plotly_chart(plot_gauge(drug_ratio, "orange", "%", "Drug Stops", 100), use_container_width=True)
    with gauge_row[3]:
        st.plotly_chart(plot_gauge(juvenile_ratio, "purple", "%", "Juvenile Drivers", 100), use_container_width=True)
    with gauge_row[4]:
        st.plotly_chart(plot_gauge(verbal_warning_ratio, "green", "%", "Verbal Warnings", 100), use_container_width=True)
    with gauge_row[5]:
        st.plotly_chart(plot_gauge(short_stop_ratio, "teal", "%", "Short Stops", 100), use_container_width=True)
 
#Advanced Analysis
st.markdown("""
    <h1 style='color:#1F4E79; font-size: 32px;'>
         Advanced Analysis
    </h1>
""", unsafe_allow_html=True)
selected_query = st.selectbox("Select Query", [
    # 🚗 Vehicle-Based
    "1.Top 10 vehicle numbers involved in drug-related stops",
    "2.Vehicles most frequently searched",

    # 🧍 Demographic-Based
    "3.Driver age group with the highest arrest rate",
    "4.Gender distribution of drivers stopped in each country",
    "5.Race and gender combination with highest search rate",

    # 🕒 Time & Duration-Based
    "6.Time of day with most traffic stops",
    "7.Average stop duration for different violations",
    "8.Are nighttime stops more likely to lead to arrests",

    # ⚖️ Violation-Based
    "9.Violations most associated with searches or arrests",
    "10.Most common violations among younger drivers (<25)",
    "11.Violations rarely resulting in search or arrest",

    # 🌍 Location-Based
    "12.Countries with highest rate of drug-related stops",
    "13.Arrest rate by country and violation",
    "14.Country with most stops where a search was conducted"
])
query_map = {
     # 🚗 Vehicle-Based
    "1.Top 10 vehicle numbers involved in drug-related stops": """
        SELECT vehicle_number
        FROM police_logs
        WHERE drugs_related_stop = TRUE
        GROUP BY vehicle_number
        ORDER BY COUNT(*) DESC
        LIMIT 10;
    """,
    "2.Vehicles most frequently searched": """
        SELECT vehicle_number
        FROM police_logs
        WHERE search_conducted = TRUE
        GROUP BY vehicle_number
        ORDER BY COUNT(*) DESC
        LIMIT 10;
    """,
    # Demographic-Based
    "3.Driver age group with the highest arrest rate": """
        SELECT 
        CASE 
            WHEN driver_age < 18 THEN 'Under 18'
            WHEN driver_age BETWEEN 18 AND 25 THEN '18 to 25'
            WHEN driver_age BETWEEN 26 AND 40 THEN '26 to 40'
            WHEN driver_age BETWEEN 41 AND 60 THEN '41 to 60'
            ELSE '60+' 
        END AS driver_age_group,
        AVG(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END) AS arrest_rate
        FROM police_logs
        WHERE driver_age IS NOT NULL
        GROUP BY driver_age_group
        ORDER BY arrest_rate DESC;
        """,
    "4.Gender distribution of drivers stopped in each country": """
        SELECT country_name, driver_gender,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY country_name) AS gender_ratio
        FROM police_logs
        GROUP BY country_name, driver_gender
        ORDER BY country_name, gender_ratio DESC;
    """,
    "5.Race and gender combination with highest search rate": """
        SELECT driver_race, driver_gender,
        AVG(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS search_rate
        FROM police_logs
        GROUP BY driver_race, driver_gender
        ORDER BY search_rate DESC
        LIMIT 1;
    """,
    # Time & Duration-Based
    "6.Time of day with most traffic stops": """
    SELECT 
    CASE 
        WHEN EXTRACT(HOUR FROM stop_time) BETWEEN 0 AND 5 THEN 'Late Night (12AM–5AM)'
        WHEN EXTRACT(HOUR FROM stop_time) BETWEEN 6 AND 11 THEN 'Morning (6AM–11AM)'
        WHEN EXTRACT(HOUR FROM stop_time) BETWEEN 12 AND 17 THEN 'Afternoon (12PM–5PM)'
        WHEN EXTRACT(HOUR FROM stop_time) BETWEEN 18 AND 21 THEN 'Evening (6PM–9PM)'
        ELSE 'Night (10PM–11PM)'
    END AS time_block,
    COUNT(*) AS stop_count
    FROM police_logs
    WHERE stop_time IS NOT NULL
    GROUP BY time_block
    ORDER BY stop_count DESC;
    """,
    "7.Average stop duration for different violations": """
   SELECT 
    violation,
    ROUND(AVG(
        CASE 
            WHEN stop_duration = '0-15 Min' THEN 10
            WHEN stop_duration = '16-30 Min' THEN 20
            WHEN stop_duration = '30+ Min' THEN 35
            ELSE NULL
        END
    ), 2) AS avg_duration_minutes
    FROM police_logs
    WHERE stop_duration IS NOT NULL
    GROUP BY violation
    ORDER BY avg_duration_minutes DESC;
    """,
    "8.Are nighttime stops more likely to lead to arrests": """
    SELECT 
    CASE 
        WHEN EXTRACT(HOUR FROM stop_time) BETWEEN 20 AND 23 
             OR EXTRACT(HOUR FROM stop_time) BETWEEN 0 AND 5 THEN 'Night'
        ELSE 'Day'
    END AS time_period,
    ROUND(AVG(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END), 4) AS arrest_rate
    FROM police_logs
    WHERE stop_time IS NOT NULL
    GROUP BY time_period
    ORDER BY arrest_rate DESC;
    """,
    # Violation-Based
    "9.Violations most associated with searches or arrests": """
    SELECT 
    violation,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches,
    SUM(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(AVG(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END), 4) AS search_rate,
    ROUND(AVG(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END), 4) AS arrest_rate
    FROM police_logs
    GROUP BY violation
    HAVING COUNT(*) > 10  -- Optional: filter out low-frequency violations
    ORDER BY search_rate DESC, arrest_rate DESC;
    """,
    "10.Most common violations among younger drivers (<25)": """
    SELECT violation, COUNT(*) AS count
    FROM police_logs
    WHERE driver_age < 25
    GROUP BY violation
    ORDER BY count DESC;
    """,
    "11.Violations rarely resulting in search or arrest": """
    SELECT 
    violation,
    ROUND(AVG(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END), 4) AS search_rate,
    ROUND(AVG(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END), 4) AS arrest_rate
    FROM police_logs
    GROUP BY violation
    ORDER BY search_rate ASC, arrest_rate ASC
    LIMIT 1;
    """,
    #Location-Based
    "12.Countries with highest rate of drug-related stops": """
    SELECT 
    country_name,
    COUNT(*) AS total_drug_stops,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage_of_all_drug_stops
    FROM police_logs
    WHERE drugs_related_stop = TRUE
    GROUP BY country_name
    ORDER BY total_drug_stops DESC;
    """,
    "13.Arrest rate by country and violation": """
    SELECT 
    country_name,
    violation,
    ROUND(AVG(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END), 4) AS arrest_rate
    FROM police_logs
    GROUP BY country_name, violation
    ORDER BY arrest_rate DESC;
    """,
    "14.Country with most stops where a search was conducted": """
    SELECT 
    country_name,
    COUNT(*) AS total_searches
    FROM police_logs
    WHERE search_conducted = TRUE
    GROUP BY country_name
    ORDER BY total_searches DESC
    LIMIT 1;
  """
}
query_highlights = {
    # 🚗 Vehicle-Based
    "1.Top 10 vehicle numbers involved in drug-related stops": lambda df: (
        f"🚓 Most frequent vehicle in drug stops: **{df.iloc[0]['vehicle_number']}**"
    ),
    "2.Vehicles most frequently searched": lambda df: (
        f"🔍 Most searched vehicle: **{df.iloc[0]['vehicle_number']}**"
    ),
    # 👤 Demographic-Based
    "3.Driver age group with the highest arrest rate": lambda df: (
        f"👤 Highest arrest rate: **{df.iloc[0]['driver_age_group']}**"
    ),
    "4.Gender distribution of drivers stopped in each country": lambda df: (
        f"📊 Gender with highest ratio in top country: **{df.iloc[0]['driver_gender']} ({df.iloc[0]['gender_ratio']:.1f}%)**"
    ),
    "5.Race and gender combination with highest search rate": lambda df: (
        f"👥 Highest search rate among: **{df.iloc[0]['driver_race']} - {df.iloc[0]['driver_gender']}**"
    ),
    # ⏰ Time & Duration-Based
    "6.Time of day with most traffic stops": lambda df: (
        f"⏰ Most traffic stops occur during: **{df.iloc[0]['time_block']}**"
    ),
    "7.Average stop duration for different violations": lambda df: (
    f"⏱️ Longest average stop duration is for **{df.iloc[0]['violation']}** "
    f"with **{df.iloc[0]['avg_duration_minutes']} mins**"
    ),
    "8.Are nighttime stops more likely to lead to arrests": lambda df: (
        f"🌙 Higher arrest rate during: **{df.iloc[0]['time_period']} ({df.iloc[0]['arrest_rate']:.2%})**"
    ),
    # ⚠️ Violation-Based
    "9.Violations most associated with searches or arrests": lambda df: (
        f"🚨 Violation most associated with search/arrest: **{df.iloc[0]['violation']}**"
    ),
    "10.Most common violations among younger drivers (<25)": lambda df: (
        f"🧒 Most common violation (<25): **{df.iloc[0]['violation']} ({df.iloc[0]['count']})**"
    ),
    "11.Violations rarely resulting in search or arrest": lambda df: (
        f"⚠️ Least actionable violation: **{df.iloc[0]['violation']}**"
    ),
    # 🌍 Location-Based
    "12.Countries with highest rate of drug-related stops": lambda df: (
        f"🌍 Most drug-related stops: **{df.iloc[0]['country_name']} ({df.iloc[0]['total_drug_stops']} stops)**"
    ),
    "13.Arrest rate by country and violation": lambda df: (
        f"🚔 Highest arrest rate for violation: **{df.iloc[0]['violation']} in {df.iloc[0]['country_name']}**"
    ),
    "14.Country with most stops where a search was conducted": lambda df: (
        f"🔍 Country with most searches: **{df.iloc[0]['country_name']} ({df.iloc[0]['total_searches']} searches)**"
    ),
}
if st.button("Let’s Analyse"):
    if selected_query in query_map:
        selected_sql = query_map[selected_query]
        highlight_fn = query_highlights.get(selected_query)

        try:
            conn = psycopg2.connect(**db_params)
            result_df = pd.read_sql(selected_sql, conn)
            conn.close()

            if not result_df.empty:
                # ✅ Optional highlight
                if highlight_fn:
                    try:
                        st.success(highlight_fn(result_df))
                    except Exception as e:
                        st.info("ℹ️ Highlight skipped due to formatting issue.")

                st.badge("Aggregated View")
                st.dataframe(result_df, use_container_width=True)
            else:
                st.warning("⚠️ No data returned for the selected query.")

        except Exception as e:
            st.error(f"🚨 Error executing query: {e}")

    else:
        st.error("❌ Invalid query selection.")                 
# Complex Analysis
st.markdown("""
    <h1 style='color:#1F4E79; font-size: 32px;'>
         Complex Analysis
    </h1>
""", unsafe_allow_html=True)
analysis_cards = [
    "1. Yearly Breakdown of Stops and Arrests by Country",
    "2. Driver Violation Trends Based on Age and Race",
    "3. Time Period Analysis of Stops",
    "4. Violations with High Search and Arrest Rates",
    "5. Driver Demographics by Country",
    "6. Top 5 Violations with Highest Arrest Rates"
]
query_map = {
    analysis_cards[0]: """SELECT 
    country_name,
    stop_year,
    total_stops,
    total_arrests,
    ROUND(CAST(total_arrests AS numeric) * 100.0 / total_stops, 2) AS arrest_rate,
    RANK() OVER (PARTITION BY stop_year ORDER BY total_arrests DESC) AS arrest_rank_in_year
    FROM (
    SELECT 
        country_name,
        EXTRACT(YEAR FROM stop_date) AS stop_year,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END) AS total_arrests
    FROM police_logs
    WHERE stop_date IS NOT NULL
    GROUP BY country_name, stop_year
    ) AS yearly_data
    ORDER BY country_name, stop_year;
    """,

    analysis_cards[1]: """
WITH age_groups AS (
    SELECT 
        id,
        CASE 
            WHEN driver_age < 18 THEN 'Under 18'
            WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
            WHEN driver_age BETWEEN 26 AND 35 THEN '26-35'
            WHEN driver_age BETWEEN 36 AND 45 THEN '36-45'
            WHEN driver_age BETWEEN 46 AND 60 THEN '46-60'
            ELSE '60+' 
            END AS age_group
        FROM police_logs
        WHERE driver_age IS NOT NULL
    )
    -- Join with main logs table
    SELECT 
    ag.age_group,
    INITCAP(pl.driver_race) AS driver_race,
    INITCAP(pl.violation) AS violation,
    COUNT(*) AS violation_count
    FROM police_logs pl
    JOIN age_groups ag ON pl.id = ag.id
    WHERE pl.driver_race IS NOT NULL AND pl.violation IS NOT NULL
    GROUP BY ag.age_group, pl.driver_race, pl.violation
    ORDER BY ag.age_group, violation_count DESC;
    """,

    analysis_cards[2]: """SELECT
    EXTRACT(YEAR FROM stop_date) AS stop_year,
    TO_CHAR(stop_date, 'Month') AS stop_month,
    EXTRACT(MONTH FROM stop_date) AS month_number,
    EXTRACT(HOUR FROM stop_time) AS stop_hour,
    COUNT(*) AS total_stops
    FROM police_logs
    WHERE stop_date IS NOT NULL
    AND stop_time IS NOT NULL
    GROUP BY stop_year, stop_month, month_number, stop_hour
    ORDER BY stop_year, month_number, stop_hour;""",

    analysis_cards[3]: """-- Violations with High Search and Arrest Rates (Using Window Function)
    SELECT 
    violation,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS searches,
    SUM(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END) AS arrests,
    ROUND(SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 3) AS search_rate,
    ROUND(SUM(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 3) AS arrest_rate,
    RANK() OVER (ORDER BY SUM(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) DESC) AS arrest_rank
    FROM police_logs
    WHERE violation IS NOT NULL
    GROUP BY violation
    ORDER BY arrest_rate DESC
    LIMIT 10;""",

    analysis_cards[4]: """-- 5. Driver Demographics by Country (Age, Gender, and Race)
SELECT
    country_name,
    CASE
        WHEN driver_age < 18 THEN 'Under 18'
        WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
        WHEN driver_age BETWEEN 26 AND 35 THEN '26-35'
        WHEN driver_age BETWEEN 36 AND 50 THEN '36-50'
        WHEN driver_age BETWEEN 51 AND 65 THEN '51-65'
        ELSE '65+'
    END AS age_group,
    driver_gender,
    driver_race,
    COUNT(*) AS total_stops
FROM police_logs
WHERE 
    country_name IN ('Canada', 'India', 'USA') AND
    driver_age IS NOT NULL AND
    driver_gender IS NOT NULL AND
    driver_race IS NOT NULL
GROUP BY
    country_name,
    age_group,
    driver_gender,
    driver_race
ORDER BY
    country_name,
    age_group,
    driver_gender,
    driver_race;

""",

    analysis_cards[5]: """
SELECT 
    violation,
    total_stops,
    total_arrests,
    arrest_rate,
    RANK() OVER (ORDER BY arrest_rate DESC) AS arrest_rank
FROM (
    SELECT 
        violation,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END) AS total_arrests,
        ROUND(SUM(CASE WHEN stop_outcome ILIKE '%arrest%' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate
    FROM police_logs
    WHERE violation IS NOT NULL
    GROUP BY violation
) AS violation_stats
ORDER BY arrest_rank
LIMIT 5;

"""
}

cols = st.columns(3)
clicked_card = None
for i, title in enumerate(analysis_cards):
    with cols[i % 3]:
        if st.button(title):
            clicked_card = title

if clicked_card:
    query = query_map.get(clicked_card)
    df = fetch_data(query)
    st.markdown(
    f"<h5 style='color:#3366cc; font-weight:600;'>📋 {clicked_card}</h5>",
    unsafe_allow_html=True
)

    if df.empty:
        st.warning(f"No data returned for: {clicked_card}")
    else:
        st.dataframe(df, use_container_width=True)


# Predictions
with st.sidebar.expander(" Add new police log entry & get predictions", expanded=False):
    
    with st.form("new_log_form"):
        stop_date = st.date_input("Stop Date")
        stop_time = st.time_input("Stop Time")
        country_name = st.text_input("Country Name")
        driver_gender = st.selectbox("Driver Gender", ["Male", "Female", "Other"])
        driver_age = st.number_input("Driver Age", min_value=0, max_value=120, value=27)
        driver_race = st.text_input("Driver Race")
        search_conducted = st.selectbox("Search Conducted", ["No", "Yes"])
        search_type = st.text_input("Search Type")
        drugs_related_stop = st.selectbox("Drugs Related Stop", ["No", "Yes"])
        stop_duration = st.selectbox("Stop Duration", [5, 10, 15])
        vehicle_number = st.text_input("Vehicle Number")
        timestamp = pd.Timestamp.now()
    
        submitted = st.form_submit_button("Submit Log Entry")

        if submitted:
    # Convert selectbox string inputs to numeric flags
            search_flag = int(search_conducted == "Yes")
            drugs_flag = int(drugs_related_stop == "Yes")

    # Confirm the column name matches actual DataFrame
            duration_col = 'stop_duration_minutes' if 'stop_duration_minutes' in df.columns else 'stop_duration'

    # Filter dataset for predictive comparison
            filtered_data = df[
            (df['driver_gender'] == driver_gender) &
            (df['driver_age'] == driver_age) &
            (df['search_conducted'] == search_flag) &
            (df[duration_col] == stop_duration) &
            (df['drugs_related_stop'] == drugs_flag)
        ]

    # Make predictions based on historical patterns
            if not filtered_data.empty:
                predicted_outcome = filtered_data['stop_outcome'].mode()[0]
                predicted_violation = filtered_data['violation'].mode()[0]
            else:
                predicted_outcome = "Warning"
                predicted_violation = "Speeding"

    # Compose narrative summary text
                search_text = "The search was conducted" if search_flag else "The search was not conducted"
                drug_text = "the stop was related to drugs" if drugs_flag else "the stop was not related to drugs"

    # Display prediction summary
                st.markdown(f"""
<div style="padding: 10px; border-radius: 8px; background-color: #f9f9f9; border: 1px solid #ccc; font-family: Arial; font-size: 13px;">

<b style="font-size:14px;">🔍 Prediction Summary</b>

<div style="margin: 8px 0;">
  <span style="background-color:#e0f7fa; color:#006064; padding:3px 8px; border-radius:8px; margin:2px; display:inline-block;">
    <b>Outcome:</b> {predicted_outcome}
  </span>
  <span style="background-color:#f1f8e9; color:#33691e; padding:3px 8px; border-radius:8px; margin:2px; display:inline-block;">
    <b>Violation:</b> {predicted_violation}
  </span>
  <span style="background-color:#e8eaf6; color:#1a237e; padding:3px 8px; border-radius:8px; margin:2px; display:inline-block;">
    <b>Search:</b> {search_text}
  </span>
  <span style="background-color:#fff3e0; color:#e65100; padding:3px 8px; border-radius:8px; margin:2px; display:inline-block;">
    <b>Drugs:</b> {drug_text}
  </span>
</div>

<p style="margin-top:6px; font-size:13px; line-height:1.4;">
🚗 A {driver_age}-year-old <b>{driver_gender}</b> driver was stopped for <b>{predicted_violation}</b> 
at <b>{stop_time.strftime("%I:%M %p")}</b> on <b>{stop_date.strftime('%Y-%m-%d')}</b> while driving vehicle <b>{vehicle_number}</b>.<br>
{search_text}, and they received a citation. The stop lasted <b>{stop_duration} minutes</b> and {drug_text.lower()}.
</p>
</div>
""", unsafe_allow_html=True)
                
#Country Map
st.markdown("""
    <h1 style='color:#1F4E79; font-size: 32px;'>
         Global Overview of Vehicle Stops: Geo Insights 📌
    </h1>
""", unsafe_allow_html=True)
col_map, col_stats = st.columns([3, 1])
with col_map:
    query_map = """
        SELECT country_name, COUNT(*) AS stop_count
        FROM police_logs
        GROUP BY country_name
        ORDER BY stop_count DESC;
    """
    df_map = fetch_data(query_map)
    df_map.rename(columns={"country_name": "country", "stop_count": "Stops"}, inplace=True)

    def get_iso3(country_name):
        try:
            return pycountry.countries.lookup(country_name).alpha_3
        except:
            return None

    df_map["iso_alpha"] = df_map["country"].apply(get_iso3)
    df_map = df_map.dropna(subset=["iso_alpha"])

    fig = px.choropleth(
        df_map,
        locations="iso_alpha",
        color="Stops",
        hover_name="country",
        color_continuous_scale="reds",
        projection="natural earth"
    )
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        template="plotly_dark",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    query_stats = """
        SELECT country_name, COUNT(*) AS stop_count
        FROM police_logs
        GROUP BY country_name
        ORDER BY stop_count DESC
;
    """
    df_countries = fetch_data(query_stats)

    if not df_countries.empty:
        st.dataframe(
            df_countries,
            use_container_width=True,
            hide_index=True,
            column_config={
                "country_name": st.column_config.TextColumn("Country"),
                "stop_count": st.column_config.ProgressColumn(
                    "Stop Count",
                    format="%d",
                    min_value=0,
                    max_value=int(df_countries["stop_count"].max())
                )
            }
        )

    with st.expander("ℹ️ About", expanded=True):
        st.write("""
        - Helps identify trends in **nationality-related driving patterns** recorded in the police logs.
        - Useful for **law enforcement analysis** and understanding **cross-border traffic behaviour**.
        """)

# Fetch vehicle numbers
def fetch_vehicle_numbers():
    try:
        conn = psycopg2.connect(**db_params)
        df = pd.read_sql("SELECT DISTINCT vehicle_number FROM police_logs WHERE vehicle_number IS NOT NULL ORDER BY vehicle_number", conn)
        conn.close()
        return df["vehicle_number"].tolist()
    except Exception as e:
        st.sidebar.error(f"🚨 Error fetching vehicle list: {e}")
        return []

# Page Title
st.markdown("""
    <h1 style='color:#1F4E79; font-size: 32px;'>
        🛡️ Incident Report: Vehicle Stop Details
    </h1>
""", unsafe_allow_html=True)

# Sidebar selection
vehicle_list = fetch_vehicle_numbers()
with st.sidebar:
    st.header("🔎 Incident Report")
    selected_vehicle = st.selectbox("Search Vehicle Number", ["-- Select Vehicle --"] + vehicle_list)

# Main logic
if selected_vehicle and selected_vehicle != "-- Select Vehicle --":
    try:
        conn = psycopg2.connect(**db_params)
        query = """
            SELECT *
            FROM police_logs
            WHERE vehicle_number = %s
            ORDER BY stop_date DESC, stop_time DESC
            LIMIT 1
        """
        stop_df = pd.read_sql(query, conn, params=(selected_vehicle,))
        conn.close()

        if not stop_df.empty:
            row = stop_df.iloc[0]

            # Extract values
            driver_age = row.get("driver_age", "unknown")
            gender_raw = row.get("driver_gender", "").upper()
            driver_gender = "Female" if gender_raw == "F" else "Male" if gender_raw == "M" else "Unknown"
            predicted_violation = row.get("violation", "unknown violation").capitalize()
            stop_time = row.get("stop_time")
            stop_date = row.get("stop_date")
            vehicle_number = row.get("vehicle_number", "unknown")
            stop_duration = row.get("stop_duration", "N/A")
            drugs_related = row.get("drugs_related_stop", False)
            search_conducted = row.get("search_conducted", False)
            stop_outcome = row.get("stop_outcome", "no outcome")

            # Formatting
            time_fmt = datetime.strptime(str(stop_time), "%H:%M:%S").strftime("%I:%M %p") if stop_time else "unknown time"
            date_fmt = stop_date.strftime("%Y-%m-%d") if stop_date else "unknown date"
            search_text = "A search was conducted" if search_conducted else "No search was conducted"
            drug_text = "was drug-related" if drugs_related else "was not drug-related"

            # Summary display
            st.markdown(f"""
                <div style="background-color:#f7f9fa;padding:20px;border-radius:8px;border:1px solid #ccc;">
                🚗 <b>Vehicle {vehicle_number}</b> was involved in a traffic stop on <b>{date_fmt}</b> at <b>{time_fmt}</b> 
                for <b>{predicted_violation}</b>.<br>
                The driver, a <b>{driver_age}</b>-year-old <b>{driver_gender}</b>, was issued a <b>{stop_outcome}</b>.<br>
                {search_text}, the stop lasted <b>{stop_duration} minutes</b>, and it <b>{drug_text}</b>.
                </div>
            """, unsafe_allow_html=True)

        else:
            st.info("No stop data available for this vehicle.")

    except Exception as e:
        st.error(f"🚨 Error fetching stop summary: {e}")

else:
    st.markdown("""
        <div style="padding: 20px; background-color: #f9f9f9; border-left: 6px solid #1F4E79; border-radius: 6px;">
        👈 Please select a vehicle number from the sidebar to view incident details.
        </div>
    """, unsafe_allow_html=True)

import streamlit as st

st.markdown("""
    <style>
        .news-title {
            color: #1F4E79;
            font-size: 32px;
            font-weight: bold;
            text-align: center;
        }
        .news-subtitle {
            color: #666666;
            font-size: 18px;
            font-style: italic;
            text-align: center;
            margin-bottom: 30px;
        }
        .news-body {
            font-size: 18px;
            line-height: 1.7;
            text-align: justify;
            color: #222;
            padding: 10px 30px;
        }
        .quote {
            font-style: italic;
            color: #444;
            background-color: #f2f2f2;
            padding: 12px;
            border-left: 4px solid #999;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
### 📎 Resources

🔗 [View Article](https://docs.google.com/document/d/1tSqqz7QRMaHM_0oBTCxOBcTZcLRSEKSswQqEAqVb7vk/edit?usp=sharing)

🔗 [Download Summary Report](https://docs.google.com/document/d/1uc1Yjh6BS0iMTChhsL87C8jF5Q0pdADZOB5MO5JgA2Q/edit?usp=sharing)
""")

with st.expander("📞 Important Helpline Numbers in India", expanded=True):
    st.markdown("""
    <style>
    .helpline-table {
        border-collapse: collapse;
        width: 100%;
    }
    .helpline-table th, .helpline-table td {
        border: 1px solid #ccc;
        padding: 8px 12px;
        text-align: left;
        font-size: 14px;
    }
    .helpline-table th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    </style>

    <table class="helpline-table">
        <thead>
            <tr>
                <th>🚨 Service</th>
                <th>☎️ Helpline Number</th>
                <th>📝 Purpose</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>National Emergency</td>
                <td><b>112</b></td>
                <td>Unified number for police, ambulance, and fire</td>
            </tr>
            <tr>
                <td>Police Control Room</td>
                <td><b>100</b></td>
                <td>To report crimes or seek help urgently</td>
            </tr>
            <tr>
                <td>Ambulance</td>
                <td><b>102 / 108</b></td>
                <td>For medical emergencies</td>
            </tr>
            <tr>
                <td>Traffic Helpline</td>
                <td><b>103</b> (or local control room)</td>
                <td>Report traffic violations or incidents</td>
            </tr>
            <tr>
                <td>Narcotics Bureau</td>
                <td><b>011-26761102</b><br>Email: <a href="mailto:ncb-nr@nic.in">ncb-nr@nic.in</a></td>
                <td>Report drug abuse or trafficking</td>
            </tr>
            <tr>
                <td>Mental Health (Kiran)</td>
                <td><b>9152987821</b></td>
                <td>Free support & counselling</td>
            </tr>
            <tr>
                <td>Childline India</td>
                <td><b>1098</b></td>
                <td>For children in distress or abuse cases</td>
            </tr>
            <tr>
                <td>Women’s Helpline</td>
                <td><b>1091</b></td>
                <td>Women safety and protection</td>
            </tr>
            <tr>
                <td>Cyber Crime Helpline</td>
                <td><b>1930</b></td>
                <td>Online fraud, scams, and abuse</td>
            </tr>
            <tr>
                <td>Anti-Terrorism</td>
                <td><b>1090</b></td>
                <td>Report suspicious activity</td>
            </tr>
        </tbody>
    </table>

    ---
    🔗 **Useful Links**  
    - [Narcotics Control Bureau](https://www.narcoticsindia.nic.in)  
    - [Ministry of Home Affairs](https://www.mha.gov.in)  
    - [Cyber Crime Portal](https://www.cybercrime.gov.in)
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; font-size: 13px; color: grey;'>
        <p><b>🚀 Project:</b> SecureCheck – Police Stop Analysis Dashboard</p>
        <p>📞 +91-9965088838 | 📧 priyahsekar@gmail.com</p>
        <p>🔗 <a href='https://www.linkedin.com/in/haripriya-gunasekar-27b25014a/' target='_blank'>LinkedIn</a> | 
        <a href='https://github.com/HaripriyaGunasekar' target='_blank'>GitHub</a></p>
        <p>🛠 Built with Python, Streamlit, Plotly | © 2025 Haripriya Gunasekar</p>
        <p style='font-size: 11px;'>Last updated: 27 July 2025</p>
    </div>
    """,
    unsafe_allow_html=True
)


