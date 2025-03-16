import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Temperature Log Dashboard",
    page_icon="🌡️",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Function to create database connection
def get_db_connection():
    try:
        # Try using the complete DATABASE_URL if available
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return create_engine(db_url)
        
        # If no DATABASE_URL, construct from individual parameters
        user = os.getenv("PGUSER")
        password = os.getenv("PGPASSWORD")
        host = os.getenv("PGHOST", "localhost")
        port = os.getenv("PGPORT", "5432")
        database = os.getenv("PGDATABASE")
        
        conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return create_engine(conn_string)
    except Exception as e:
        st.error(f"Failed to connect to the database: {e}")
        return None

# Function to create table in PostgreSQL
def create_table(engine, df):
    try:
        df.to_sql('temperature_logs', engine, if_exists='replace', index=False)
        return True
    except Exception as e:
        st.error(f"Failed to create table: {e}")
        return False

# Function to clean and process the data
def process_data(df):
    # Make a copy to avoid SettingWithCopyWarning
    df_processed = df.copy()
    
    # Convert date string to datetime format
    try:
        df_processed['noted_date'] = pd.to_datetime(df_processed['noted_date'], format='%d-%m-%Y %H:%M')
    except Exception as e:
        st.warning(f"Date format conversion warning: {e}. Trying alternative formats...")
        try:
            df_processed['noted_date'] = pd.to_datetime(df_processed['noted_date'])
        except:
            st.error("Could not convert date format. Please check your data.")
            return None
    
    # Ensure columns have the right data types
    if 'temp' in df_processed.columns:
        df_processed['temp'] = pd.to_numeric(df_processed['temp'], errors='coerce')
    
    # Ensure out/in column is properly formatted
    if 'out/in' in df_processed.columns:
        df_processed['out/in'] = df_processed['out/in'].astype(str)
    
    return df_processed

# Function to check if table exists in database
def table_exists(engine):
    try:
        query = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'temperature_logs')")
        result = engine.connect().execute(query).scalar()
        return result
    except Exception as e:
        st.error(f"Failed to check if table exists: {e}")
        return False

# Function to get data from database
def get_data_from_db(engine):
    try:
        query = "SELECT * FROM temperature_logs"
        data = pd.read_sql(query, engine)
        
        # Convert datetime format if needed
        if 'noted_date' in data.columns:
            data['noted_date'] = pd.to_datetime(data['noted_date'])
            
        return data
    except Exception as e:
        st.error(f"Failed to retrieve data from database: {e}")
        return None

# Function to calculate basic statistics
def calculate_statistics(df):
    if df is None or df.empty:
        return None
    
    stats = {}
    
    # Overall statistics
    stats['total_records'] = len(df)
    stats['avg_temp'] = df['temp'].mean()
    stats['min_temp'] = df['temp'].min()
    stats['max_temp'] = df['temp'].max()
    
    # Indoor/outdoor statistics
    if 'out/in' in df.columns:
        indoor_data = df[df['out/in'] == 'In']
        outdoor_data = df[df['out/in'] == 'Out']
        
        stats['indoor_records'] = len(indoor_data)
        stats['outdoor_records'] = len(outdoor_data)
        
        stats['avg_indoor_temp'] = indoor_data['temp'].mean() if not indoor_data.empty else None
        stats['avg_outdoor_temp'] = outdoor_data['temp'].mean() if not outdoor_data.empty else None
        
        stats['min_indoor_temp'] = indoor_data['temp'].min() if not indoor_data.empty else None
        stats['min_outdoor_temp'] = outdoor_data['temp'].min() if not outdoor_data.empty else None
        
        stats['max_indoor_temp'] = indoor_data['temp'].max() if not indoor_data.empty else None
        stats['max_outdoor_temp'] = outdoor_data['temp'].max() if not outdoor_data.empty else None
    
    return stats

# Main application
def main():
    st.title("Temperature Log Dashboard 🌡️")
    
    # Sidebar
    st.sidebar.title("Controls")
    
    # Database connection status
    engine = get_db_connection()
    if engine:
        st.sidebar.success("Connected to database ✅")
    else:
        st.sidebar.error("Database connection failed ❌")
        st.stop()
    
    # Upload file section
    st.sidebar.header("Upload Temperature Data")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["Data Upload & Preview", "Visualizations", "Statistics"])
    
    with tab1:
        if uploaded_file is not None:
            # Read the file
            with st.spinner("Reading CSV file..."):
                df = pd.read_csv(uploaded_file)
            
            st.subheader("Raw Data Preview")
            st.write(df.head())
            
            st.subheader("Data Information")
            buffer = pd.io.StringIO()
            df.info(buf=buffer)
            s = buffer.getvalue()
            st.text(s)
            
            # Process the data
            with st.spinner("Processing data..."):
                processed_df = process_data(df)
            
            if processed_df is None:
                st.error("Failed to process data. Please check the file format.")
                st.stop()
            
            st.subheader("Processed Data Preview")
            st.write(processed_df.head())
            
            # Upload to database
            if st.button("Upload to Database"):
                with st.spinner("Uploading to database..."):
                    success = create_table(engine, processed_df)
                
                if success:
                    st.success("Data successfully uploaded to the database!")
                else:
                    st.error("Failed to upload data to the database.")
        else:
            # Check if data exists in database
            if table_exists(engine):
                st.info("Data already exists in the database. You can view visualizations and statistics in the other tabs.")
            else:
                st.info("Please upload a CSV file with temperature log data.")
    
    # Data retrieval for visualizations and statistics
    data = None
    if table_exists(engine):
        with st.spinner("Loading data from database..."):
            data = get_data_from_db(engine)
    
    with tab2:
        if data is not None and not data.empty:
            st.subheader("Temperature Visualizations")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Option to filter by indoor/outdoor
                location_filter = st.selectbox(
                    "Filter by location:",
                    ["All", "Indoor Only", "Outdoor Only"]
                )
            
            with col2:
                # Date range filter
                min_date = data['noted_date'].min().date()
                max_date = data['noted_date'].max().date()
                
                date_range = st.date_input(
                    "Select date range:",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            
            with col3:
                # Option to resample data for smoother visualization
                resample_options = {
                    "None": None,
                    "Hourly Average": "H",
                    "Daily Average": "D"
                }
                resample = st.selectbox(
                    "Resample data:",
                    list(resample_options.keys())
                )
            
            # Apply filters
            filtered_data = data.copy()
            
            # Location filter
            if location_filter == "Indoor Only":
                filtered_data = filtered_data[filtered_data['out/in'] == 'In']
            elif location_filter == "Outdoor Only":
                filtered_data = filtered_data[filtered_data['out/in'] == 'Out']
            
            # Date range filter
            if len(date_range) == 2:
                start_date, end_date = date_range
                start_date = pd.Timestamp(start_date)
                end_date = pd.Timestamp(end_date)
                filtered_data = filtered_data[
                    (filtered_data['noted_date'] >= start_date) & 
                    (filtered_data['noted_date'] <= end_date)
                ]
            
            # Resample if selected
            if resample_options[resample]:
                # We need to group by out/in if we want to maintain that distinction
                if location_filter == "All":
                    # Create separate dataframes for indoor and outdoor
                    indoor_data = filtered_data[filtered_data['out/in'] == 'In']
                    outdoor_data = filtered_data[filtered_data['out/in'] == 'Out']
                    
                    # Resample each
                    indoor_resampled = indoor_data.set_index('noted_date')['temp'].resample(resample_options[resample]).mean().reset_index()
                    indoor_resampled['out/in'] = 'In'
                    
                    outdoor_resampled = outdoor_data.set_index('noted_date')['temp'].resample(resample_options[resample]).mean().reset_index()
                    outdoor_resampled['out/in'] = 'Out'
                    
                    # Combine back
                    filtered_data = pd.concat([indoor_resampled, outdoor_resampled])
                else:
                    # Just resample the filtered data
                    filtered_data = filtered_data.set_index('noted_date')['temp'].resample(resample_options[resample]).mean().reset_index()
                    filtered_data['out/in'] = location_filter.replace(" Only", "")
            
            # Check if we have data after filtering
            if filtered_data.empty:
                st.warning("No data available for the selected filters.")
            else:
                # Time series plot
                st.subheader("Temperature Over Time")
                
                if location_filter == "All":
                    # Create plot with color distinction
                    fig = px.line(
                        filtered_data, 
                        x='noted_date', 
                        y='temp',
                        color='out/in',
                        title='Temperature Time Series',
                        labels={
                            'noted_date': 'Date',
                            'temp': 'Temperature',
                            'out/in': 'Location'
                        }
                    )
                else:
                    # Single color plot
                    fig = px.line(
                        filtered_data, 
                        x='noted_date', 
                        y='temp',
                        title='Temperature Time Series',
                        labels={
                            'noted_date': 'Date',
                            'temp': 'Temperature'
                        }
                    )
                
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Temperature",
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Distribution plot
                st.subheader("Temperature Distribution")
                
                if location_filter == "All":
                    # Create histogram with color distinction
                    fig = px.histogram(
                        filtered_data,
                        x='temp',
                        color='out/in',
                        marginal='box',
                        title='Temperature Distribution',
                        labels={
                            'temp': 'Temperature',
                            'out/in': 'Location'
                        }
                    )
                else:
                    # Single color histogram
                    fig = px.histogram(
                        filtered_data,
                        x='temp',
                        marginal='box',
                        title='Temperature Distribution',
                        labels={
                            'temp': 'Temperature'
                        }
                    )
                
                fig.update_layout(
                    xaxis_title="Temperature",
                    yaxis_title="Count"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for visualization. Please upload data in the 'Data Upload & Preview' tab.")
    
    with tab3:
        if data is not None and not data.empty:
            st.subheader("Temperature Statistics")
            
            # Calculate statistics
            stats = calculate_statistics(data)
            
            if stats:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Overall Statistics")
                    st.metric("Total Records", f"{stats['total_records']:,}")
                    st.metric("Average Temperature", f"{stats['avg_temp']:.2f}°")
                    st.metric("Minimum Temperature", f"{stats['min_temp']:.2f}°")
                    st.metric("Maximum Temperature", f"{stats['max_temp']:.2f}°")
                
                with col2:
                    st.subheader("Indoor vs Outdoor")
                    st.metric("Indoor Records", f"{stats['indoor_records']:,}")
                    st.metric("Outdoor Records", f"{stats['outdoor_records']:,}")
                    
                    # Create comparison chart
                    comparison_data = {
                        'Location': ['Indoor', 'Outdoor'],
                        'Average': [stats['avg_indoor_temp'], stats['avg_outdoor_temp']],
                        'Minimum': [stats['min_indoor_temp'], stats['min_outdoor_temp']],
                        'Maximum': [stats['max_indoor_temp'], stats['max_outdoor_temp']]
                    }
                    
                    comparison_df = pd.DataFrame(comparison_data)
                    
                    # Melting the dataframe for easier plotting
                    melted_df = pd.melt(
                        comparison_df,
                        id_vars=['Location'],
                        value_vars=['Average', 'Minimum', 'Maximum'],
                        var_name='Statistic',
                        value_name='Temperature'
                    )
                    
                    fig = px.bar(
                        melted_df,
                        x='Statistic',
                        y='Temperature',
                        color='Location',
                        barmode='group',
                        title='Indoor vs Outdoor Temperature Comparison'
                    )
                    
                    fig.update_layout(
                        xaxis_title="Statistic",
                        yaxis_title="Temperature"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display daily statistics
                st.subheader("Daily Temperature Statistics")
                
                # Group by date and calculate statistics
                data['date'] = data['noted_date'].dt.date
                daily_stats = data.groupby(['date', 'out/in'])['temp'].agg(['mean', 'min', 'max']).reset_index()
                daily_stats.columns = ['Date', 'Location', 'Average', 'Minimum', 'Maximum']
                
                # Format the dataframe for display
                daily_stats['Date'] = pd.to_datetime(daily_stats['Date'])
                daily_stats = daily_stats.sort_values(by='Date', ascending=False)
                
                st.dataframe(daily_stats.style.format({
                    'Date': lambda x: x.strftime('%Y-%m-%d'),
                    'Average': '{:.2f}°',
                    'Minimum': '{:.2f}°',
                    'Maximum': '{:.2f}°'
                }))
            else:
                st.warning("Could not calculate statistics from the available data.")
        else:
            st.info("No data available for statistics. Please upload data in the 'Data Upload & Preview' tab.")

if __name__ == "__main__":
    main()
