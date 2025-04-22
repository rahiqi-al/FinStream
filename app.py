import streamlit as st
import pandas as pd
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from datetime import datetime, timedelta
import plotly.express as px
import time

# Streamlit page config
st.set_page_config(page_title="FinStream Real-Time Dashboard", layout="centered")

# Cassandra connection
def get_cassandra_session():
    cluster = Cluster(['cassandra'], port=9042)
    session = cluster.connect('fintech')
    return session

# Bar Chart: Total Trade Volume by Symbol (fintech.trades)
def fetch_trade_volume(session):
    query = """
    SELECT symbol, volume
    FROM trades
    WHERE ingestion_time > %s AND ingestion_time < %s
    ALLOW FILTERING
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)
    
    statement = SimpleStatement(query)
    rows = session.execute(statement, (start_time, end_time))
    
    df = pd.DataFrame(rows, columns=['symbol', 'volume'])
    df = df.groupby('symbol')['volume'].sum().reset_index()
    df.columns = ['Symbol', 'Total Volume']
    
    return df

# Line Chart: Average Price Trend (fintech.trade_aggregations)
def fetch_avg_price(session):
    query = """
    SELECT window_start, symbol, avg_price
    FROM trade_aggregations
    WHERE window_start > %s AND window_start < %s
    ALLOW FILTERING
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    
    statement = SimpleStatement(query)
    rows = session.execute(statement, (start_time, end_time))
    
    df = pd.DataFrame(rows, columns=['window_start', 'symbol', 'avg_price'])
    df.columns = ['Time', 'Symbol', 'Average Price']
    
    return df

# Pie Chart: Trade Count Proportion (fintech.trade_aggregations)
def fetch_trade_count(session):
    query = """
    SELECT symbol, trade_count
    FROM trade_aggregations
    WHERE window_start > %s AND window_start < %s
    ALLOW FILTERING
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=10)
    
    statement = SimpleStatement(query)
    rows = session.execute(statement, (start_time, end_time))
    
    df = pd.DataFrame(rows, columns=['symbol', 'trade_count'])
    df = df.groupby('symbol')['trade_count'].sum().reset_index()
    df.columns = ['Symbol', 'Total Trades']
    
    return df

# Stat Chart: Latest Trade Price (fintech.trades)
def fetch_latest_price(session):
    query = """
    SELECT symbol, price
    FROM trades
    WHERE ingestion_time >= %s
    ALLOW FILTERING
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(seconds=5)
    
    statement = SimpleStatement(query)
    rows = session.execute(statement, (start_time,))
    
    df = pd.DataFrame(rows, columns=['symbol', 'price'])
    df = df.groupby('symbol')['price'].last().reset_index()
    df.columns = ['Symbol', 'Latest Price']
    
    return df

# Histogram: Volume Distribution by Symbol (fintech.trades)
def fetch_volume_distribution(session):
    query = """
    SELECT symbol, volume
    FROM trades
    WHERE ingestion_time > %s AND ingestion_time < %s
    ALLOW FILTERING
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)
    
    statement = SimpleStatement(query)
    rows = session.execute(statement, (start_time, end_time))
    
    df = pd.DataFrame(rows, columns=['symbol', 'volume'])
    df.columns = ['Symbol', 'Volume']
    
    return df

# Line Chart: Trade Count Trend (fintech.trades)
def fetch_trade_count_trend(session):
    query = """
    SELECT ingestion_time, symbol
    FROM trades
    WHERE ingestion_time > %s AND ingestion_time < %s
    ALLOW FILTERING
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    
    statement = SimpleStatement(query)
    rows = session.execute(statement, (start_time, end_time))
    
    df = pd.DataFrame(rows, columns=['ingestion_time', 'symbol'])
    df = df.groupby(['ingestion_time', 'symbol']).size().reset_index(name='Trade Count')
    df.columns = ['Time', 'Symbol', 'Trade Count']
    
    return df

# Line Chart: Historical Price Trend (fintech.trades)
def fetch_historical_price(session):
    query = """
    SELECT ingestion_time, symbol, price
    FROM trades
    WHERE ingestion_time > %s AND ingestion_time < %s
    ALLOW FILTERING
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=30)
    
    statement = SimpleStatement(query)
    rows = session.execute(statement, (start_time, end_time))
    
    df = pd.DataFrame(rows, columns=['ingestion_time', 'symbol', 'price'])
    df = df.groupby(['ingestion_time', 'symbol'])['price'].mean().reset_index()
    df.columns = ['Time', 'Symbol', 'Price']
    
    return df

# Area Chart: Total Volume Trend by Symbol (fintech.trades)
def fetch_volume_trend(session):
    query = """
    SELECT ingestion_time, symbol, volume
    FROM trades
    WHERE ingestion_time > %s AND ingestion_time < %s
    ALLOW FILTERING
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    
    statement = SimpleStatement(query)
    rows = session.execute(statement, (start_time, end_time))
    
    df = pd.DataFrame(rows, columns=['ingestion_time', 'symbol', 'volume'])
    df = df.groupby(['ingestion_time', 'symbol'])['volume'].sum().reset_index()
    df.columns = ['Time', 'Symbol', 'Total Volume']
    
    return df

# Bar Chart: Total Trade Count by Symbol (fintech.trades)
def fetch_trade_count_by_symbol(session):
    query = """
    SELECT symbol
    FROM trades
    WHERE ingestion_time > %s AND ingestion_time < %s
    ALLOW FILTERING
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)
    
    statement = SimpleStatement(query)
    rows = session.execute(statement, (start_time, end_time))
    
    df = pd.DataFrame(rows, columns=['symbol'])
    df = df.groupby('symbol').size().reset_index(name='Trade Count')
    df.columns = ['Symbol', 'Trade Count']
    
    return df

# Main app
def main():
    session = get_cassandra_session()
    
    # Header
    st.title("FinStream Real-Time Dashboard")
    
    # Expanders for charts
    bar_expander = st.expander("Total Trade Volume", expanded=True)
    pie_expander = st.expander("Trade Count Proportion", expanded=True)
    line_expander = st.expander("Average Price Trend", expanded=True)
    stat_expander = st.expander("Latest Trade Prices", expanded=True)
    hist_expander = st.expander("Volume Distribution", expanded=True)
    count_expander = st.expander("Trade Count Trend", expanded=True)
    hist_price_expander = st.expander("Historical Price Trend", expanded=True)
    area_expander = st.expander("Volume Trend Over Time", expanded=True)
    trade_count_expander = st.expander("Total Trade Count by Symbol", expanded=True)
    
    # Placeholders
    with bar_expander:
        bar_placeholder = st.empty()
    with pie_expander:
        pie_placeholder = st.empty()
    with line_expander:
        line_placeholder = st.empty()
    with stat_expander:
        stat_placeholder = st.empty()
    with hist_expander:
        hist_placeholder = st.empty()
    with count_expander:
        count_placeholder = st.empty()
    with hist_price_expander:
        hist_price_placeholder = st.empty()
    with area_expander:
        area_placeholder = st.empty()
    with trade_count_expander:
        trade_count_placeholder = st.empty()
    
    iteration = 0
    while True:
        # Unique key suffix
        key_suffix = f"{iteration}_{int(time.time())}"
        
        # Bar Chart
        df_bar = fetch_trade_volume(session)
        fig_bar = px.bar(
            df_bar,
            x='Symbol',
            y='Total Volume',
            title='',
            labels={'Total Volume': 'Volume (Shares)', 'Symbol': 'Symbol'},
            height=250
        )
        fig_bar.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
        bar_placeholder.plotly_chart(fig_bar, use_container_width=True, key=f"bar_chart_{key_suffix}")
        
        # Pie Chart
        df_pie = fetch_trade_count(session)
        fig_pie = px.pie(
            df_pie,
            names='Symbol',
            values='Total Trades',
            title='',
            height=250
        )
        fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        pie_placeholder.plotly_chart(fig_pie, use_container_width=True, key=f"pie_chart_{key_suffix}")
        
        # Line Chart (Avg Price)
        df_line = fetch_avg_price(session)
        fig_line = px.line(
            df_line,
            x='Time',
            y='Average Price',
            color='Symbol',
            title='',
            labels={'Average Price': 'Price (USD)', 'Time': 'Time'},
            height=250
        )
        fig_line.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        line_placeholder.plotly_chart(fig_line, use_container_width=True, key=f"line_chart_{key_suffix}")
        
        # Stat Chart (Table)
        df_stat = fetch_latest_price(session)
        stat_placeholder.table(df_stat.style.format({'Latest Price': '${:.2f}'}))
        
        # Histogram
        df_hist = fetch_volume_distribution(session)
        fig_hist = px.histogram(
            df_hist,
            x='Volume',
            color='Symbol',
            title='',
            labels={'Volume': 'Volume (Shares)', 'count': 'Trade Count'},
            height=250
        )
        fig_hist.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        hist_placeholder.plotly_chart(fig_hist, use_container_width=True, key=f"hist_chart_{key_suffix}")
        
        # Line Chart (Trade Count)
        df_count = fetch_trade_count_trend(session)
        fig_count = px.line(
            df_count,
            x='Time',
            y='Trade Count',
            color='Symbol',
            title='',
            labels={'Trade Count': 'Number of Trades', 'Time': 'Time'},
            height=250
        )
        fig_count.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        count_placeholder.plotly_chart(fig_count, use_container_width=True, key=f"count_chart_{key_suffix}")
        
        # Line Chart (Historical Price)
        df_hist_price = fetch_historical_price(session)
        fig_hist_price = px.line(
            df_hist_price,
            x='Time',
            y='Price',
            color='Symbol',
            title='',
            labels={'Price': 'Price (USD)', 'Time': 'Time'},
            height=250
        )
        fig_hist_price.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        hist_price_placeholder.plotly_chart(fig_hist_price, use_container_width=True, key=f"hist_price_chart_{key_suffix}")
        
        # Area Chart
        df_area = fetch_volume_trend(session)
        fig_area = px.area(
            df_area,
            x='Time',
            y='Total Volume',
            color='Symbol',
            title='',
            labels={'Total Volume': 'Volume (Shares)', 'Time': 'Time'},
            height=250
        )
        fig_area.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        area_placeholder.plotly_chart(fig_area, use_container_width=True, key=f"area_chart_{key_suffix}")
        
        # Bar Chart (Trade Count)
        df_trade_count = fetch_trade_count_by_symbol(session)
        fig_trade_count = px.bar(
            df_trade_count,
            x='Symbol',
            y='Trade Count',
            title='',
            labels={'Trade Count': 'Number of Trades', 'Symbol': 'Symbol'},
            height=250
        )
        fig_trade_count.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
        trade_count_placeholder.plotly_chart(fig_trade_count, use_container_width=True, key=f"trade_count_chart_{key_suffix}")
        
        # Increment iteration and wait
        iteration += 1
        time.sleep(5)

main()