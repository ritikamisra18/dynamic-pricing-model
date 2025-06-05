import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta

st.set_page_config(layout="wide")

st.title("Ad Exchange Performance Dashboard")

# Upload section
uploaded_file = st.file_uploader("Upload your GAM report (CSV or XLSX)", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, sheet_name='Report data')

    # Remove totals row (assumes it's the last row and contains 'Total' or similar in any column)
    if df.apply(lambda row: row.astype(str).str.contains('total', case=False).any(), axis=1).iloc[-1]:
        df = df.iloc[:-1]

    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Aggregate by hour
    df_hourly = df.groupby(['Date', 'Hour']).agg({
        'Ad Exchange revenue (US$)': 'sum',
        'Ad Exchange average eCPM (US$)': 'mean',
        'Ad Exchange ad requests': 'sum',
        'Ad Exchange impressions': 'sum',
        'Ad Exchange match rate': 'mean'
    }).reset_index()

    df_hourly['Timestamp'] = df_hourly['Date'].astype(str) + ' ' + df_hourly['Hour'].astype(str) + ':00'
    df_hourly['Timestamp'] = pd.to_datetime(df_hourly['Timestamp'])

    st.subheader("Trend Graphs")
    col1, col2 = st.columns(2)

    with col1:
        st.line_chart(df_hourly.set_index('Timestamp')['Ad Exchange average eCPM (US$)'], use_container_width=True)
        st.caption("Ad Exchange eCPM over time")

    with col2:
        st.line_chart(df_hourly.set_index('Timestamp')['Ad Exchange revenue (US$)'], use_container_width=True)
        st.caption("Ad Exchange Revenue over time")

    st.line_chart(df_hourly.set_index('Timestamp')['Ad Exchange ad requests'], use_container_width=True)
    st.caption("Ad Requests over time")

    st.subheader("Smart Recommendations Table")

    # Recommendation logic
    def recommend(row):
        if row['Ad Exchange average eCPM (US$)'] > 0.5 and row['Ad Exchange match rate'] < 0.3:
            return "Use Floor Pricing"
        elif row['Ad Exchange match rate'] > 0.8 and row['Ad Exchange average eCPM (US$)'] < 0.2:
            return "Use Target CPM"
        elif row['Ad Exchange revenue (US$)'] < 0.01:
            return "Use Google Optimized"
        else:
            return "No Change"

    df_hourly['Recommendation'] = df_hourly.apply(recommend, axis=1)

    st.dataframe(df_hourly[['Timestamp',
                            'Ad Exchange average eCPM (US$)',
                            'Ad Exchange match rate',
                            'Ad Exchange revenue (US$)',
                            'Recommendation']].sort_values(by='Timestamp'))

    # Predict recommendations for the next day hourly
    st.subheader("Next Day Hourly Recommendation Prediction")
    last_date = df_hourly['Date'].max()
    next_day = last_date + timedelta(days=1)
    next_day_hours = pd.DataFrame({'Date': [next_day]*24, 'Hour': list(range(24))})

    # Use rolling hourly average of the last day for prediction
    last_day_data = df_hourly[df_hourly['Date'] == last_date].set_index('Hour')
    next_day_hours = next_day_hours.join(last_day_data[['Ad Exchange revenue (US$)',
                                                         'Ad Exchange average eCPM (US$)',
                                                         'Ad Exchange match rate',
                                                         'Ad Exchange ad requests']], on='Hour')
    next_day_hours.dropna(inplace=True)

    next_day_hours['Timestamp'] = pd.to_datetime(next_day_hours['Date'].astype(str) + ' ' + next_day_hours['Hour'].astype(str) + ':00')
    next_day_hours['Recommendation'] = next_day_hours.apply(recommend, axis=1)

    st.dataframe(next_day_hours[['Timestamp',
                                 'Ad Exchange average eCPM (US$)',
                                 'Ad Exchange match rate',
                                 'Ad Exchange revenue (US$)',
                                 'Ad Exchange ad requests',
                                 'Recommendation']])

    # Trend Graphs for Next Day Prediction
    st.subheader("Predicted Trend Graphs for Next Day")
    col3, col4 = st.columns(2)

    with col3:
        st.line_chart(next_day_hours.set_index('Timestamp')['Ad Exchange average eCPM (US$)'], use_container_width=True)
        st.caption("Predicted eCPM for Next Day")

    with col4:
        st.line_chart(next_day_hours.set_index('Timestamp')['Ad Exchange ad requests'], use_container_width=True)
        st.caption("Predicted Ad Requests for Next Day")

else:
    st.info("Upload a report to begin analysis.")