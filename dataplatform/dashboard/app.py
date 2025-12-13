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
    # Build connection string with SSL support
    base_conn = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
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

# Sidebar
st.sidebar.header("🎛️ Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh (every 30s)", value=False)

if auto_refresh:
    import time
    time.sleep(30)
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
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pipeline Execution History")
        query = """
            SELECT 
                DATE(created_at) as date,
                status,
                COUNT(*) as count
            FROM warehouse.pipeline_logs
            GROUP BY date, status
            ORDER BY date DESC
            LIMIT 30
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            fig = px.bar(df, x='date', y='count', color='status',
                         title="Daily Pipeline Executions",
                         color_discrete_map={'SUCCESS': 'green', 'FAILED': 'red'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pipeline history yet")
    
    with col2:
        st.subheader("Records Processed Over Time")
        query = """
            SELECT 
                DATE(created_at) as date,
                SUM(records_processed) as total_records
            FROM warehouse.pipeline_logs
            WHERE status='SUCCESS'
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            fig = px.line(df, x='date', y='total_records',
                          title="Daily Records Processed",
                          markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet")

with tab2:
    st.subheader("📦 Data Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Show staging table counts
        st.write("**Staging Tables**")
        query = """
            SELECT 
                table_name,
                (xpath('/row/cnt/text()', xml_count))[1]::text::int as row_count
            FROM (
                SELECT 
                    table_name,
                    table_schema,
                    query_to_xml(format('SELECT COUNT(*) as cnt FROM %I.%I', table_schema, table_name), false, true, '') as xml_count
                FROM information_schema.tables
                WHERE table_schema = 'staging'
            ) t
        """
        try:
            # Simpler query for counting
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'staging'
            """
            tables_df = pd.read_sql(tables_query, engine)
            
            table_counts = []
            for table in tables_df['table_name']:
                count_query = f"SELECT COUNT(*) as count FROM staging.{table}"
                count = pd.read_sql(count_query, engine)['count'].iloc[0]
                table_counts.append({'Table': table, 'Rows': count})
            
            if table_counts:
                df_counts = pd.DataFrame(table_counts)
                st.dataframe(df_counts, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading table counts: {e}")
    
    with col2:
        st.write("**Latest Data Sample**")
        try:
            # Show sample from sales_data
            query = "SELECT * FROM staging.sales_data ORDER BY processed_at DESC LIMIT 5"
            df = pd.read_sql(query, engine)
            st.dataframe(df, use_container_width=True)
        except:
            st.info("No data available yet")

with tab3:
    st.subheader("Recent Pipeline Executions")
    query = """
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
            END as error
        FROM warehouse.pipeline_logs
        ORDER BY created_at DESC
        LIMIT 10
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        # Color code by status
        def highlight_status(row):
            if row['status'] == 'SUCCESS':
                return ['background-color: #d4edda'] * len(row)
            elif row['status'] == 'FAILED':
                return ['background-color: #f8d7da'] * len(row)
            return [''] * len(row)
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No pipeline executions yet. Run your first pipeline!")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()