import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Page config
st.set_page_config(
    page_title="DataPlatform Dashboard",
    page_icon="📊",
    layout="wide"
)

# Database connection
@st.cache_resource
def get_db_connection():
    # Detect if running locally (not in Docker) and adjust host
    db_host = os.getenv('DB_HOST', 'localhost')
    # If host is 'postgres' (Docker hostname) and we're running locally, use localhost
    if db_host == 'postgres' and not os.path.exists('/.dockerenv'):
        db_host = 'localhost'
        # Also adjust port for local connection (Docker exposes on 5434)
        db_port = os.getenv('DB_PORT', '5434')
    else:
        db_port = os.getenv('DB_PORT', '5432')
    
    # Build connection string with SSL support
    base_conn = f"postgresql://{os.getenv('DB_USER', 'datauser')}:{os.getenv('DB_PASSWORD', 'mypassword')}@{db_host}:{db_port}/{os.getenv('DB_NAME', 'dataplatform')}"
    
    # Add SSL parameters if configured
    ssl_mode = os.getenv('DB_SSL_MODE', 'prefer')
    ssl_params = [f"sslmode={ssl_mode}"]
    
    ssl_ca_path = os.getenv('DB_SSL_CA_PATH')
    if ssl_ca_path:
        ssl_params.append(f"sslrootcert={ssl_ca_path}")
    
    if ssl_params:
        conn_string = f"{base_conn}?{'&'.join(ssl_params)}"
    else:
        conn_string = base_conn
    
    return create_engine(conn_string)

engine = get_db_connection()

# Title
st.title("📊 DataPlatform Analytics Dashboard")
st.markdown("---")

# Sidebar - Filters and Controls
st.sidebar.header("🎛️ Filters & Controls")

# Date Range Filter
st.sidebar.subheader("📅 Date Range")
default_end = datetime.now()
default_start = default_end - timedelta(days=30)
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(default_start.date(), default_end.date()),
    max_value=datetime.now().date()
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = default_end.date()

# Category/Source Filter
st.sidebar.subheader("📂 Category Filter")
try:
    # Get available sources/categories from staging tables
    tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'staging'
        ORDER BY table_name
    """
    tables_df = pd.read_sql(tables_query, engine)
    available_sources = ['All'] + tables_df['table_name'].tolist()
    
    selected_source = st.sidebar.selectbox(
        "Select Data Source",
        available_sources,
        index=0
    )
except:
    selected_source = 'All'
    available_sources = ['All']

# Auto-refresh settings
st.sidebar.subheader("🔄 Auto-Refresh")
auto_refresh_enabled = st.sidebar.checkbox("Enable Auto-refresh", value=False)
if auto_refresh_enabled:
    refresh_interval = st.sidebar.selectbox(
        "Refresh Interval",
        [10, 30, 60, 120],
        index=1,
        format_func=lambda x: f"{x} seconds"
    )
    
    # Check if new data has been processed (compare with last check)
    if 'last_pipeline_check' not in st.session_state:
        st.session_state.last_pipeline_check = None
    
    # Get latest pipeline execution time
    try:
        latest_query = "SELECT MAX(created_at) as latest FROM warehouse.pipeline_logs"
        latest_result = pd.read_sql(latest_query, engine)
        latest_time = latest_result['latest'].iloc[0] if not latest_result.empty else None
        
        if latest_time and (st.session_state.last_pipeline_check is None or 
                           latest_time > st.session_state.last_pipeline_check):
            st.session_state.last_pipeline_check = latest_time
            st.sidebar.success("🆕 New data detected! Refreshing...")
            st.rerun()
    except:
        pass
    
    # Auto-refresh timer
    import time
    time.sleep(refresh_interval)
    st.rerun()

# Metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Get total pipelines run
    query = "SELECT COUNT(*) as count FROM warehouse.pipeline_logs"
    result = pd.read_sql(query, engine)
    st.metric("Total Pipeline Runs", result['count'].iloc[0])

with col2:
    # Get successful runs
    query = "SELECT COUNT(*) as count FROM warehouse.pipeline_logs WHERE status='SUCCESS'"
    result = pd.read_sql(query, engine)
    success_count = result['count'].iloc[0]
    st.metric("Successful Runs", success_count, delta="Good", delta_color="normal")

with col3:
    # Get total records processed
    query = "SELECT COALESCE(SUM(records_processed), 0) as total FROM warehouse.pipeline_logs"
    result = pd.read_sql(query, engine)
    total = int(result['total'].iloc[0])
    st.metric("Records Processed", f"{total:,}")

with col4:
    # Get avg processing time
    query = """
        SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (end_time - start_time))), 0) as avg_time 
        FROM warehouse.pipeline_logs
        WHERE status='SUCCESS'
    """
    result = pd.read_sql(query, engine)
    avg_time = result['avg_time'].iloc[0]
    st.metric("Avg Processing Time", f"{avg_time:.1f}s")

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["📈 Pipeline Analytics", "📊 Data Overview", "📝 Logs"])

with tab1:
    # Apply date filter to queries
    date_filter = f"AND DATE(created_at) >= '{start_date}' AND DATE(created_at) <= '{end_date}'"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pipeline Execution History")
        query = f"""
            SELECT 
                DATE(created_at) as date,
                status,
                COUNT(*) as count
            FROM warehouse.pipeline_logs
            WHERE 1=1 {date_filter}
            GROUP BY date, status
            ORDER BY date DESC
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            fig = px.bar(df, x='date', y='count', color='status',
                         title=f"Pipeline Executions ({start_date} to {end_date})",
                         color_discrete_map={'SUCCESS': 'green', 'FAILED': 'red'},
                         labels={'date': 'Date', 'count': 'Number of Executions'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pipeline history for selected date range")
    
    with col2:
        st.subheader("Records Processed Over Time")
        query = f"""
            SELECT 
                DATE(created_at) as date,
                SUM(records_processed) as total_records
            FROM warehouse.pipeline_logs
            WHERE status='SUCCESS' {date_filter}
            GROUP BY date
            ORDER BY date DESC
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            fig = px.line(df, x='date', y='total_records',
                          title=f"Daily Records Processed ({start_date} to {end_date})",
                          markers=True,
                          labels={'date': 'Date', 'total_records': 'Records Processed'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for selected date range")
    
    # Additional trend visualizations
    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Processing Time Trends")
        query = f"""
            SELECT 
                DATE(created_at) as date,
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration
            FROM warehouse.pipeline_logs
            WHERE status='SUCCESS' {date_filter}
            GROUP BY date
            ORDER BY date DESC
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            fig = px.area(df, x='date', y='avg_duration',
                         title=f"Average Processing Time ({start_date} to {end_date})",
                         labels={'date': 'Date', 'avg_duration': 'Avg Duration (seconds)'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No processing time data available")
    
    with col4:
        st.subheader("Success Rate Over Time")
        query = f"""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) FILTER (WHERE status='SUCCESS') * 100.0 / COUNT(*) as success_rate
            FROM warehouse.pipeline_logs
            WHERE 1=1 {date_filter}
            GROUP BY date
            ORDER BY date DESC
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            fig = px.bar(df, x='date', y='success_rate',
                        title=f"Daily Success Rate ({start_date} to {end_date})",
                        labels={'date': 'Date', 'success_rate': 'Success Rate (%)'})
            fig.update_traces(marker_color='lightblue')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No success rate data available")

with tab2:
    st.subheader("📦 Data Overview")
    
    # Apply category filter
    if selected_source != 'All':
        st.info(f"📂 Filtering by: **{selected_source}**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Show staging table counts with category filter
        st.write("**Staging Tables**")
        try:
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'staging'
            """
            tables_df = pd.read_sql(tables_query, engine)
            
            # Filter by selected source if not 'All'
            if selected_source != 'All':
                tables_df = tables_df[tables_df['table_name'] == selected_source]
            
            table_counts = []
            for table in tables_df['table_name']:
                # Apply date filter if table has processed_at column
                try:
                    # Check if table has processed_at column
                    col_check = f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'staging' 
                        AND table_name = '{table}' 
                        AND column_name = 'processed_at'
                    """
                    has_date_col = pd.read_sql(col_check, engine)
                    
                    if not has_date_col.empty:
                        count_query = f"""
                            SELECT COUNT(*) as count 
                            FROM staging.{table}
                            WHERE DATE(processed_at) >= '{start_date}' 
                            AND DATE(processed_at) <= '{end_date}'
                        """
                    else:
                        count_query = f"SELECT COUNT(*) as count FROM staging.{table}"
                    
                    count = pd.read_sql(count_query, engine)['count'].iloc[0]
                    table_counts.append({'Table': table, 'Rows': count})
                except Exception as e:
                    # Fallback to simple count
                    count_query = f"SELECT COUNT(*) as count FROM staging.{table}"
                    count = pd.read_sql(count_query, engine)['count'].iloc[0]
                    table_counts.append({'Table': table, 'Rows': count})
            
            if table_counts:
                df_counts = pd.DataFrame(table_counts)
                # Create a bar chart for better visualization
                fig = px.bar(df_counts, x='Table', y='Rows',
                           title="Records by Data Source",
                           labels={'Table': 'Data Source', 'Rows': 'Number of Records'})
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_counts, use_container_width=True)
            else:
                st.info("No data available for selected filters")
        except Exception as e:
            st.error(f"Error loading table counts: {e}")
    
    with col2:
        st.write("**Latest Data Sample**")
        try:
            # Show sample from selected source or first available
            if selected_source != 'All':
                source_table = selected_source
            else:
                # Get first available table
                tables_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'staging'
                    LIMIT 1
                """
                tables_df = pd.read_sql(tables_query, engine)
                if tables_df.empty:
                    st.info("No data available yet")
                    source_table = None
                else:
                    source_table = tables_df['table_name'].iloc[0]
            
            if source_table:
                # Apply date filter if processed_at exists
                try:
                    query = f"""
                        SELECT * FROM staging.{source_table} 
                        WHERE DATE(processed_at) >= '{start_date}' 
                        AND DATE(processed_at) <= '{end_date}'
                        ORDER BY processed_at DESC LIMIT 10
                    """
                    df = pd.read_sql(query, engine)
                    if df.empty:
                        # Fallback without date filter
                        query = f"SELECT * FROM staging.{source_table} ORDER BY processed_at DESC LIMIT 10"
                        df = pd.read_sql(query, engine)
                except:
                    # Table might not have processed_at column
                    query = f"SELECT * FROM staging.{source_table} LIMIT 10"
                    df = pd.read_sql(query, engine)
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No data available for selected filters")
        except Exception as e:
            st.info(f"No data available: {e}")
    
    # Data trends by category
    st.markdown("---")
    st.subheader("📈 Data Trends by Category")
    
    try:
        # Get data trends for each source
        if selected_source == 'All':
            # Show trends for all sources
            trends_data = []
            for table in available_sources[1:]:  # Skip 'All'
                try:
                    query = f"""
                        SELECT 
                            DATE(processed_at) as date,
                            COUNT(*) as record_count
                        FROM staging.{table}
                        WHERE DATE(processed_at) >= '{start_date}' 
                        AND DATE(processed_at) <= '{end_date}'
                        GROUP BY date
                        ORDER BY date
                    """
                    df = pd.read_sql(query, engine)
                    if not df.empty:
                        df['source'] = table
                        trends_data.append(df)
                except:
                    continue
            
            if trends_data:
                combined_df = pd.concat(trends_data, ignore_index=True)
                fig = px.line(combined_df, x='date', y='record_count', color='source',
                             title=f"Data Trends by Source ({start_date} to {end_date})",
                             labels={'date': 'Date', 'record_count': 'Records', 'source': 'Data Source'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trend data available for selected date range")
        else:
            # Show trend for selected source only
            try:
                query = f"""
                    SELECT 
                        DATE(processed_at) as date,
                        COUNT(*) as record_count
                    FROM staging.{selected_source}
                    WHERE DATE(processed_at) >= '{start_date}' 
                    AND DATE(processed_at) <= '{end_date}'
                    GROUP BY date
                    ORDER BY date
                """
                df = pd.read_sql(query, engine)
                if not df.empty:
                    fig = px.line(df, x='date', y='record_count',
                                 title=f"{selected_source} Trend ({start_date} to {end_date})",
                                 labels={'date': 'Date', 'record_count': 'Records'})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No trend data available for selected source and date range")
            except Exception as e:
                st.info(f"Could not load trend data: {e}")
    except Exception as e:
        st.warning(f"Error loading trend data: {e}")

with tab3:
    st.subheader("Recent Pipeline Executions")
    
    # Apply date filter
    date_filter = f"AND DATE(created_at) >= '{start_date}' AND DATE(created_at) <= '{end_date}'"
    
    query = f"""
        SELECT 
            pipeline_name,
            status,
            records_processed,
            start_time,
            end_time,
            EXTRACT(EPOCH FROM (end_time - start_time)) as duration_seconds,
            CASE 
                WHEN error_message IS NOT NULL THEN LEFT(error_message, 100) || '...'
                ELSE 'N/A'
            END as error,
            created_at
        FROM warehouse.pipeline_logs
        WHERE 1=1 {date_filter}
        ORDER BY created_at DESC
        LIMIT 50
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        # Format the dataframe for better display
        display_df = df[['pipeline_name', 'status', 'records_processed', 
                         'start_time', 'end_time', 'duration_seconds', 'error']].copy()
        display_df['duration_seconds'] = display_df['duration_seconds'].round(2)
        
        # Color code by status using conditional formatting
        def highlight_status(val):
            if isinstance(val, str) and val == 'SUCCESS':
                return 'background-color: #d4edda'
            elif isinstance(val, str) and val == 'FAILED':
                return 'background-color: #f8d7da'
            return ''
        
        styled_df = display_df.style.applymap(highlight_status, subset=['status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Summary statistics
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Executions", len(df))
        with col2:
            success_count = len(df[df['status'] == 'SUCCESS'])
            st.metric("Successful", success_count, delta=f"{success_count/len(df)*100:.1f}%")
        with col3:
            avg_duration = df['duration_seconds'].mean()
            st.metric("Avg Duration", f"{avg_duration:.2f}s")
    else:
        st.info(f"No pipeline executions found for date range {start_date} to {end_date}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()