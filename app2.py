import streamlit as st
import os
import io
import base64
import pandas as pd
import datetime as dt
import uuid
import hashlib
import logging
import plotly.express as px
from PIL import Image

# =========================================================
# HELPER & PLACEHOLDER FUNCTIONS
# =========================================================
@st.cache_data
def image_to_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Placeholder Functions (replace with your actual logic)
def _ta_save_journal(user, data): return True
def ta_update_xp(user, amount, reason): pass
def ta_update_streak(user): pass

# =========================================================
# SESSION STATE INITIALIZATION (SIMPLIFIED)
# This ensures the required keys exist on the very first run.
# =========================================================
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = "Test123"  # Simulate login for development
if 'trade_journal' not in st.session_state:
    st.session_state.trade_journal = pd.DataFrame(columns=[
        "TradeID", "Date", "Symbol", "Direction", "Outcome", "Lots", 
        "EntryPrice", "StopLoss", "FinalExit", "PnL", "RR", "Tags", 
        "EntryRationale", "Strategy", "TradeJournalNotes", 
        "EntryScreenshot", "ExitScreenshot"
    ])

# =========================================================
# PAGE RENDERING STARTS HERE (NO MORE 'if current_page' CHECK)
# =========================================================

# --- BULLETPROOF CUSTOM HEADER BLOCK ---
icon_path = "trading_journal.png"
if os.path.exists(icon_path):
    icon_base64 = image_to_base64(icon_path)
    # This .get() method is a failsafe. It will use the username if it exists,
    # or 'N/A' if it's somehow None, preventing the error.
    username = st.session_state.get('logged_in_user', 'N/A') 
    
    st.markdown(f"""
        <div style="
            background-color: #1F2937;
            padding: 20px 25px;
            border-radius: 10px;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            box-shadow: 0 0 15px #00FFFF60;
            border: 1px solid #00FFFF30;
        ">
            <!-- Icon -->
            <img src="data:image/png;base64,{icon_base64}" style="width: 80px; height: 80px; margin-right: 25px;">
            
            <!-- Title and Subtitle -->
            <div style="flex-grow: 1;">
                <h1 style="color: #00FFFF; margin: 0; font-size: 2.5em; font-weight: 600;">Trading Journal</h1>
                <p style="color: #9CA3AF; margin: 5px 0 0 0; font-size: 1em;">A streamlined interface for professional trade analysis.</p>
            </div>
            
            <!-- Logged In As Info -->
            <div style="text-align: right; color: #9CA3AF; font-size: 0.9em;">
                Logged in as:
                <div style="color: #FFFFFF; font-size: 1.2em; font-weight: bold;">{username}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    # Fallback if the icon is not found, now shows an error to help debug.
    st.error("Header icon 'trading_journal.png' not found. Please ensure it's in the same folder as the script.")
    st.title("Trading Journal")
    st.caption(f"Logged in as: **{st.session_state.get('logged_in_user', 'N/A')}**")


# --- TABS AND PAGE CONTENT ---
tab_entry, tab_playbook, tab_analytics = st.tabs(["**📝 Log New Trade**", "**📚 Trade Playbook**", "**📊 Analytics Dashboard**"])

with tab_entry:
    st.header("Log a New Trade")
    # ... (rest of your code for tab_entry is unchanged) ...
    with st.form("trade_entry_form", clear_on_submit=True):
        st.markdown("##### ⚡ Trade Entry Details")
        col1, col2, col3 = st.columns(3)
        pairs_map_for_selection = {"EUR/USD": "FX:EURUSD", "USD/JPY": "FX:USDJPY", "GBP/USD": "FX:GBPUSD"}
        with col1:
            date_val = st.date_input("Date", dt.date.today())
            symbol_options = list(pairs_map_for_selection.keys()) + ["Other"]
            symbol = st.selectbox("Symbol", symbol_options, index=0)
            if symbol == "Other": symbol = st.text_input("Custom Symbol")
        with col2:
            direction = st.radio("Direction", ["Long", "Short"], horizontal=True)
            lots = st.number_input("Size (Lots)", min_value=0.01, value=0.10, step=0.01, format="%.2f")
        with col3:
            entry_price = st.number_input("Entry Price", min_value=0.0, value=0.0, format="%.5f")
            stop_loss = st.number_input("Stop Loss", min_value=0.0, value=0.0, format="%.5f")
        
        submitted = st.form_submit_button("Save Trade", type="primary", use_container_width=True)
        if submitted:
            st.success("Trade logged successfully!")
            # Add your saving logic here
            st.rerun()

    # --- TAB 2: TRADE PLAYBOOK ---
    with tab_playbook:
        st.header("Your Trade Playbook")
        df_playbook = st.session_state.trade_journal
        
        if df_playbook.empty:
            st.info("Your logged trades will appear here. Log your first trade to get started!")
        else:
            # (Simplified playbook display for brevity)
            st.dataframe(df_playbook, use_container_width=True)

    # --- TAB 3: ANALYTICS DASHBOARD ---
    with tab_analytics:
        st.header("Your Performance Dashboard")
        df_analytics = st.session_state.trade_journal[st.session_state.trade_journal['Outcome'].isin(['Win', 'Loss'])].copy()

        if df_analytics.empty:
            st.info("Complete at least one winning or losing trade to view your performance analytics.")
        else:
            total_pnl = pd.to_numeric(df_analytics['PnL'], errors='coerce').fillna(0.0).sum()
            total_trades = len(df_analytics)
            wins = df_analytics[df_analytics['Outcome'] == 'Win']
            losses = df_analytics[df_analytics['Outcome'] == 'Loss']
            win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
            avg_win = pd.to_numeric(wins['PnL'], errors='coerce').mean() if not wins.empty else 0.0
            avg_loss = pd.to_numeric(losses['PnL'], errors='coerce').mean() if not losses.empty else 0.0
            profit_factor = pd.to_numeric(wins['PnL'], errors='coerce').sum() / abs(pd.to_numeric(losses['PnL'], errors='coerce').sum()) if not losses.empty and pd.to_numeric(losses['PnL'], errors='coerce').sum() != 0 else float('inf')

            kpi_cols = st.columns(4)
            kpi_cols[0].metric("Net PnL ($)", f"${total_pnl:,.2f}")
            kpi_cols[1].metric("Win Rate", f"{win_rate:.1f}%")
            kpi_cols[2].metric("Profit Factor", f"{profit_factor:.2f}")
            kpi_cols[3].metric("Avg. Win / Loss ($)", f"${avg_win:,.2f} / ${abs(avg_loss):,.2f}")

            st.markdown("---")
            chart_cols = st.columns(2)
            with chart_cols[0]:
                st.subheader("Cumulative PnL")
                df_analytics_sorted = df_analytics.sort_values(by='Date').copy()
                df_analytics_sorted['CumulativePnL'] = df_analytics_sorted['PnL'].cumsum()
                fig_equity = px.area(df_analytics_sorted, x='Date', y='CumulativePnL', title="Your Equity Curve", template="plotly_dark")
                st.plotly_chart(fig_equity, use_container_width=True)
            with chart_cols[1]:
                st.subheader("Performance by Symbol")
                pnl_by_symbol = df_analytics.groupby('Symbol')['PnL'].sum().sort_values(ascending=False)
                fig_pnl_symbol = px.bar(pnl_by_symbol, title="Net PnL by Symbol", template="plotly_dark")
                st.plotly_chart(fig_pnl_symbol, use_container_width=True)
