import streamlit as st
import pandas as pd
import plotly.express as px
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.policies import DCAwareRoundRobinPolicy
from datetime import datetime, timedelta
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit page configuration
st.set_page_config(page_title="FinStream Real-Time Dashboard", layout="centered")

# Initialize Cassandra connection
@st.cache_resource
def init_cassandra():
    try:
        cluster = Cluster(
            ['cassandra'],
            port=9042,
            load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
            protocol_version=4
        )
        session = cluster.connect('fintech')
        logger.info("Connected to Cassandra")
        return session
    except Exception as e:
        logger.error(f"Cassandra connection failed: {str(e)}")
        st.error(f"Cannot connect to Cassandra: {str(e)}")
        return None

# Pie Chart: Trade Count Proportion (fintech.trade_aggregations)
def fetch_trade_count(session, time_window_minutes=10):
    try:
        query = """
        SELECT symbol, trade_count
        FROM trade_aggregations
        WHERE window_start > %s AND window_start < %s
        ALLOW FILTERING
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        statement = SimpleStatement(query)
        rows = session.execute(statement, [start_time, end_time])
        
        df = pd.DataFrame(rows, columns=['symbol', 'trade_count'])
        df = df.groupby('symbol')['trade_count'].sum().reset_index()
        df.columns = ['Symbol', 'Total Trades']
        return df
    except Exception as e:
        logger.error(f"Error fetching trade count: {str(e)}")
        st.error(f"Error fetching trade count: {str(e)}")
        return pd.DataFrame()

# Stat Chart: Latest Trade Price (fintech.trades)
def fetch_latest_price(session, time_window_minutes=5):
    try:
        query = """
        SELECT symbol, price
        FROM trades
        WHERE ingestion_time >= %s
        ALLOW FILTERING
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        statement = SimpleStatement(query)
        rows = session.execute(statement, [start_time])
        
        df = pd.DataFrame(rows, columns=['symbol', 'price'])
        df = df.groupby('symbol')['price'].last().reset_index()
        df.columns = ['Symbol', 'Latest Price']
        return df
    except Exception as e:
        logger.error(f"Error fetching latest price: {str(e)}")
        st.error(f"Error fetching latest price: {str(e)}")
        return pd.DataFrame()

# Line Chart: Trade Count Trend (fintech.trades)
def fetch_trade_count_trend(session, time_window_minutes=15):
    try:
        query = """
        SELECT ingestion_time, symbol
        FROM trades
        WHERE ingestion_time > %s AND ingestion_time < %s
        ALLOW FILTERING
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        statement = SimpleStatement(query)
        rows = session.execute(statement, [start_time, end_time])
        
        df = pd.DataFrame(rows, columns=['ingestion_time', 'symbol'])
        df = df.groupby(['ingestion_time', 'symbol']).size().reset_index(name='Trade Count')
        df.columns = ['Time', 'Symbol', 'Trade Count']
        return df
    except Exception as e:
        logger.error(f"Error fetching trade count trend: {str(e)}")
        st.error(f"Error fetching trade count trend: {str(e)}")
        return pd.DataFrame()

# Area Chart: Total Volume Trend by Symbol (fintech.trades)
def fetch_volume_trend(session, time_window_minutes=15):
    try:
        query = """
        SELECT ingestion_time, symbol, volume
        FROM trades
        WHERE ingestion_time > %s AND ingestion_time < %s
        ALLOW FILTERING
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        statement = SimpleStatement(query)
        rows = session.execute(statement, [start_time, end_time])
        
        df = pd.DataFrame(rows, columns=['ingestion_time', 'symbol', 'volume'])
        df = df.groupby(['ingestion_time', 'symbol'])['volume'].sum().reset_index()
        df.columns = ['Time', 'Symbol', 'Total Volume']
        return df
    except Exception as e:
        logger.error(f"Error fetching volume trend: {str(e)}")
        st.error(f"Error fetching volume trend: {str(e)}")
        return pd.DataFrame()

# Line Chart: Price Trend Over Time (fintech.trades)
def fetch_price_trend(session, time_window_minutes=15):
    try:
        query = """
        SELECT ingestion_time, symbol, price
        FROM trades
        WHERE ingestion_time > %s AND ingestion_time < %s
        ALLOW FILTERING
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        statement = SimpleStatement(query)
        rows = session.execute(statement, [start_time, end_time])
        
        df = pd.DataFrame(rows, columns=['ingestion_time', 'symbol', 'price'])
        df = df.groupby(['ingestion_time', 'symbol'])['price'].mean().reset_index()
        df.columns = ['Time', 'Symbol', 'Price']
        return df
    except Exception as e:
        logger.error(f"Error fetching price trend: {str(e)}")
        st.error(f"Error fetching price trend: {str(e)}")
        return pd.DataFrame()

# Main app
def main():
    session = init_cassandra()
    if session is None:
        st.stop()

    # Header
    st.markdown(
        "<h1 style='text-align: center; margin-bottom: 20px; font-size: 2.5em;'>FinStream Real-Time Dashboard</h1>",
        unsafe_allow_html=True
    )

    # Sidebar
    st.sidebar.markdown(
        "<h2 style='font-size: 1.5em; margin-bottom: 10px;'>Dashboard Controls</h2>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")
    time_window = st.sidebar.slider(
        "Time Window (minutes)",
        min_value=1,
        max_value=60,
        value=5,
        help="Set the time range for data displayed in charts."
    )
    refresh_interval = st.sidebar.slider(
        "Refresh Interval (seconds)",
        min_value=1,
        max_value=30,
        value=5,
        help="Set how often the dashboard refreshes with new data."
    )
    st.sidebar.markdown("### Visualization Settings")
    precision_toggle = st.sidebar.checkbox(
        "Round Price Metrics",
        value=True,
        help="Round prices to 2 decimal places or show full precision."
    )
    notify_toggle = st.sidebar.checkbox(
        "Refresh Notifications",
        value=False,
        help="Show a notification when the dashboard refreshes."
    )

    # Latest Trade Prices (always visible)
    st.markdown(
        "<h3 style='text-align: center; margin-bottom: 10px;'>Latest Trade Prices</h3>",
        unsafe_allow_html=True
    )
    prices_placeholder = st.empty()

    # Expanders for charts
    pie_expander = st.expander("Trade Count Proportion", expanded=False)
    count_expander = st.expander("Trade Count Trend", expanded=False)
    area_expander = st.expander("Volume Trend Over Time", expanded=False)
    price_trend_expander = st.expander("Price Trend Over Time", expanded=False)

    # Placeholders for charts
    with pie_expander:
        pie_placeholder = st.empty()
    with count_expander:
        count_placeholder = st.empty()
    with area_expander:
        area_placeholder = st.empty()
    with price_trend_expander:
        price_trend_placeholder = st.empty()

    # Update loop (friend's refresh logic)
    iteration = 0
    while True:
        key_suffix = f"{iteration}_{int(time.time())}"

        # Latest Trade Prices
        with prices_placeholder.container():
            df_stat = fetch_latest_price(session, time_window)
            if not df_stat.empty:
                cols = st.columns(len(df_stat))  # One column per symbol
                for idx, row in df_stat.iterrows():
                    with cols[idx]:
                        price = row['Latest Price']
                        display_price = f"${price:.2f}" if precision_toggle else f"${price}"
                        st.metric(
                            label=f"Latest Price for {row['Symbol']}",
                            value=display_price
                        )
            else:
                st.warning("No latest price data available.")

        # Pie Chart
        with pie_placeholder.container():
            df_pie = fetch_trade_count(session, time_window)
            if not df_pie.empty:
                fig_pie = px.pie(
                    df_pie,
                    names='Symbol',
                    values='Total Trades',
                    title='',
                    height=300
                )
                fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_chart_{key_suffix}")
            else:
                st.warning("No trade count data available.")

        # Line Chart (Trade Count)
        with count_placeholder.container():
            df_count = fetch_trade_count_trend(session, time_window)
            if not df_count.empty:
                fig_count = px.line(
                    df_count,
                    x='Time',
                    y='Trade Count',
                    color='Symbol',
                    title='',
                    labels={'Trade Count': 'Number of Trades', 'Time': 'Time'},
                    height=300
                )
                fig_count.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_count, use_container_width=True, key=f"count_chart_{key_suffix}")
            else:
                st.warning("No trade count trend data available.")

        # Area Chart
        with area_placeholder.container():
            df_area = fetch_volume_trend(session, time_window)
            if not df_area.empty:
                fig_area = px.area(
                    df_area,
                    x='Time',
                    y='Total Volume',
                    color='Symbol',
                    title='',
                    labels={'Total Volume': 'Volume (Shares)', 'Time': 'Time'},
                    height=300
                )
                fig_area.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_area, use_container_width=True, key=f"area_chart_{key_suffix}")
            else:
                st.warning("No volume trend data available.")

        # Line Chart (Price Trend)
        with price_trend_placeholder.container():
            df_price = fetch_price_trend(session, time_window)
            if not df_price.empty:
                fig_price = px.line(
                    df_price,
                    x='Time',
                    y='Price',
                    color='Symbol',
                    title='',
                    labels={'Price': 'Price ($)', 'Time': 'Time'},
                    height=300
                )
                fig_price.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_price, use_container_width=True, key=f"price_trend_chart_{key_suffix}")
            else:
                st.warning("No price trend data available.")

        # Show refresh notification if enabled
        if notify_toggle:
            st.toast(f"Dashboard refreshed at {datetime.now().strftime('%H:%M:%S')}", icon="🔄")

        # Increment iteration and wait
        iteration += 1
        time.sleep(refresh_interval)

main()