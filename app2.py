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

# HELPER FUNCTION TO ENCODE IMAGES (Required for this method)
@st.cache_data
def image_to_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# --- Placeholder Functions ---
# NOTE: Replace these with your actual function definitions for the app to work correctly.
def _ta_save_journal(user, data):
    st.toast(f"Placeholder: Saving journal for {user}...")
    return True

def ta_update_xp(user, amount, reason):
    st.toast(f"Placeholder: Awarding {amount} XP to {user} for {reason}.")

def ta_update_streak(user):
    st.toast(f"Placeholder: Updating streak for {user}.")

def check_and_award_trade_milestones(user):
    pass

def check_and_award_performance_milestones(user):
    pass

def award_xp_for_notes_added_if_changed(user, trade_id, notes):
    st.toast(f"Placeholder: Awarding XP for notes on trade {trade_id}.")

def save_user_data(user):
    st.toast(f"Placeholder: Saving all data for {user}.")

# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================
# This block runs only once when the app starts.
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'trading_journal'
    st.session_state.logged_in_user = None # Starts as logged out
    # Initialize trade_journal as an empty DataFrame with expected columns
    st.session_state.trade_journal = pd.DataFrame(columns=[
        "TradeID", "Date", "Symbol", "Direction", "Outcome", "Lots", 
        "EntryPrice", "StopLoss", "FinalExit", "PnL", "RR", "Tags", 
        "EntryRationale", "Strategy", "TradeJournalNotes", 
        "EntryScreenshot", "ExitScreenshot"
    ])
    st.session_state.gamification_flags = {}


# =========================================================
# TRADING JOURNAL PAGE
# =========================================================
# This check will now work because 'current_page' has been initialized.
if st.session_state.current_page == 'trading_journal':
    # You can set a default user for testing purposes, or leave it as None
    # For example: st.session_state.logged_in_user = "test_user"
    
    if st.session_state.logged_in_user is None:
        st.warning("Please log in to access your Trading Journal.")
        # In a real multi-page app, you would redirect. Here, we'll just show a message.
        st.info("Normally, you would be redirected to the account page to log in.")
        st.stop() # Stop the rest of the script from running if not logged in

    # --- REPLACEMENT FOR THE TITLE ---
    icon_path = os.path.join("icons", "trading_journal.png")
    if os.path.exists(icon_path):
        icon_base64 = image_to_base64(icon_path)
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="data:image/png;base64,{icon_base64}" width="100">
                <h1 style="margin: 0; font-size: 2.75rem;">Trading Journal</h1>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.title("Trading Journal")

    st.caption(f"A streamlined interface for professional trade analysis. | Logged in as: **{st.session_state.logged_in_user}**")
    st.markdown("---")

    tab_entry, tab_playbook, tab_analytics = st.tabs(["**📝 Log New Trade**", "**📚 Trade Playbook**", "**📊 Analytics Dashboard**"])

    # --- TAB 1: LOG NEW TRADE ---
    with tab_entry:
        st.header("Log a New Trade")
        st.caption("Focus on a quick, essential entry. You can add detailed notes and screenshots later in the Playbook.")

        with st.form("trade_entry_form", clear_on_submit=True):
            st.markdown("##### ⚡ Trade Entry Details")
            col1, col2, col3 = st.columns(3)

            pairs_map_for_selection = {
                "EUR/USD": "FX:EURUSD", "USD/JPY": "FX:USDJPY", "GBP/USD": "FX:GBPUSD", "USD/CHF": "OANDA:USDCHF",
                "AUD/USD": "FX:AUDUSD", "NZD/USD": "OANDA:NZDUSD", "USD/CAD": "FX:USDCAD"
            }

            with col1:
                date_val = st.date_input("Date", dt.date.today())
                symbol_options = list(pairs_map_for_selection.keys()) + ["Other"]
                symbol = st.selectbox("Symbol", symbol_options, index=0)
                if symbol == "Other": symbol = st.text_input("Custom Symbol")
            with col2:
                direction = st.radio("Direction", ["Long", "Short"], horizontal=True)
                lots = st.number_input("Size (Lots)", min_value=0.01, max_value=1000.0, value=0.10, step=0.01, format="%.2f")
            with col3:
                entry_price = st.number_input("Entry Price", min_value=0.0, value=0.0, step=0.00001, format="%.5f")
                stop_loss = st.number_input("Stop Loss", min_value=0.0, value=0.0, step=0.00001, format="%.5f")

            st.markdown("---")
            st.markdown("##### Trade Results & Metrics")
            res_col1, res_col2, res_col3 = st.columns(3)

            with res_col1:
                final_exit = st.number_input("Final Exit Price", min_value=0.0, value=0.0, step=0.00001, format="%.5f")
                outcome = st.selectbox("Outcome", ["Win", "Loss", "Breakeven", "No Trade/Study"])

            with res_col2:
                manual_pnl_input = st.number_input("Manual PnL ($)", value=0.0, format="%.2f", help="Enter the profit/loss amount manually.")

            with res_col3:
                manual_rr_input = st.number_input("Manual Risk:Reward (R)", value=0.0, format="%.2f", help="Enter the risk-to-reward ratio manually.")

            calculate_pnl_rr = st.checkbox("Calculate PnL/RR from Entry/Stop/Exit Prices", value=False,
                                           help="Check this to automatically calculate PnL and R:R based on prices entered above, overriding manual inputs.")
            st.markdown("---")
            
            st.markdown("##### Rationale & Tags")
            entry_rationale = st.text_area("Why did you enter this trade?", height=100)

            all_tags = sorted(list(set(st.session_state.trade_journal['Tags'].str.split(',').explode().dropna().str.strip().tolist()))) if not st.session_state.trade_journal.empty and 'Tags' in st.session_state.trade_journal.columns else []

            suggested_tags = ["Breakout", "Reversal", "Trend Follow", "Counter-Trend", "News Play", "FOMO", "Over-leveraged"]
            tags_selection = st.multiselect("Select Existing Tags", options=sorted(list(set(all_tags + suggested_tags))))

            new_tags_input = st.text_input("Add New Tags (comma-separated)", placeholder="e.g., strong momentum, poor entry, ...")

            submitted = st.form_submit_button("Save Trade", type="primary", use_container_width=True)
            if submitted:
                final_pnl, final_rr = 0.0, 0.0

                if calculate_pnl_rr:
                    if stop_loss == 0.0 or entry_price == 0.0:
                        st.error("Entry Price and Stop Loss must be greater than 0 to calculate PnL/RR automatically.")
                        st.stop()
                    
                    risk_per_unit = abs(entry_price - stop_loss)
                    pip_size_for_pair_calc = 0.0001
                    if "JPY" in symbol.upper():
                        pip_size_for_pair_calc = 0.01
                    
                    usd_per_pip_per_standard_lot = 10.0

                    price_change_raw = final_exit - entry_price
                    pips_moved = price_change_raw / pip_size_for_pair_calc
                    
                    if direction == "Long":
                        final_pnl = pips_moved * (lots * usd_per_pip_per_standard_lot) / 10 
                    else: # Short
                        final_pnl = -pips_moved * (lots * usd_per_pip_per_standard_lot) / 10
                    
                    if risk_per_unit > 0.0:
                        reward_per_unit = abs(final_exit - entry_price)
                        final_rr = reward_per_unit / risk_per_unit
                        
                        if (direction == "Long" and final_exit < entry_price) or (direction == "Short" and final_exit > entry_price):
                            final_rr *= -1

                        if final_exit == entry_price:
                            final_rr = 0.0
                    else:
                        final_rr = 0.0
                else: 
                    final_pnl = manual_pnl_input
                    final_rr = manual_rr_input

                newly_added_tags = [tag.strip() for tag in new_tags_input.split(',') if tag.strip()]
                final_tags_list = sorted(list(set(tags_selection + newly_added_tags)))
                trade_id_new = f"TRD-{uuid.uuid4().hex[:6].upper()}"
                entry_screenshot_path_saved = None
                exit_screenshot_path_saved = None

                new_trade_data = {
                    "TradeID": trade_id_new, "Date": pd.to_datetime(date_val),
                    "Symbol": symbol, "Direction": direction, "Outcome": outcome,
                    "Lots": lots, "EntryPrice": entry_price, "StopLoss": stop_loss, "FinalExit": final_exit,
                    "PnL": final_pnl, "RR": final_rr,
                    "Tags": ','.join(final_tags_list), "EntryRationale": entry_rationale,
                    "Strategy": '', "TradeJournalNotes": '', 
                    "EntryScreenshot": entry_screenshot_path_saved,
                    "ExitScreenshot": exit_screenshot_path_saved
                }
                new_df = pd.DataFrame([new_trade_data])
                st.session_state.trade_journal = pd.concat([st.session_state.trade_journal, new_df], ignore_index=True)

                if _ta_save_journal(st.session_state.logged_in_user, st.session_state.trade_journal):
                    ta_update_xp(st.session_state.logged_in_user, 10, "Logged a new trade")
                    ta_update_streak(st.session_state.logged_in_user)
                    st.success(f"Trade {new_trade_data['TradeID']} logged successfully!")
                    
                    check_and_award_trade_milestones(st.session_state.logged_in_user)
                    check_and_award_performance_milestones(st.session_state.logged_in_user)
                    
                    st.rerun()
                else:
                    st.error("Failed to save trade.")

    # --- TAB 2: TRADE PLAYBOOK ---
    with tab_playbook:
        st.header("Your Trade Playbook")
        df_playbook = st.session_state.trade_journal
        
        st.markdown(
            """
            <style>
                div[data-testid="stColumn"] > div[data-testid="stHorizontalBlock"] { position: relative; }
                .st-emotion-cache-12w0qpk { position: absolute; top: 2px; right: 3px; z-index: 10; }
                .st-emotion-cache-12w0qpk button {
                    font-size: 10px !important; height: 1.1rem !important; min-height: 1.1rem !important;
                    width: 1.1rem !important; min-width: 1.1rem !important; padding: 0 !important;
                    line-height: 0 !important; background: transparent !important; color: #999 !important; border: none !important;
                }
                .st-emotion-cache-12w0qpk button:hover { color: #fff !important; background: rgba(100, 100, 100, 0.3) !important; }
            </style>
            """, unsafe_allow_html=True
        )

        if df_playbook.empty:
            st.info("Your logged trades will appear here as playbook cards. Log your first trade to get started!")
        else:
            st.caption("Filter and review your past trades to refine your strategy and identify patterns.")
            
            if 'edit_state' not in st.session_state:
                st.session_state.edit_state = {}

            filter_cols = st.columns([1, 1, 1, 2])
            outcome_filter = filter_cols[0].multiselect("Filter Outcome", df_playbook['Outcome'].unique(), default=df_playbook['Outcome'].unique())
            symbol_filter = filter_cols[1].multiselect("Filter Symbol", df_playbook['Symbol'].unique(), default=df_playbook['Symbol'].unique())
            direction_filter = filter_cols[2].multiselect("Filter Direction", df_playbook['Direction'].unique(), default=df_playbook['Direction'].unique())

            tag_options = sorted(list(set(df_playbook['Tags'].astype(str).str.split(',').explode().dropna().str.strip()))) if not df_playbook.empty else []
            tag_filter = filter_cols[3].multiselect("Filter Tag", options=tag_options)
            
            filtered_df = df_playbook[
                (df_playbook['Outcome'].isin(outcome_filter)) &
                (df_playbook['Symbol'].isin(symbol_filter)) &
                (df_playbook['Direction'].isin(direction_filter))
            ]

            if tag_filter:
                filtered_df = filtered_df[filtered_df['Tags'].astype(str).apply(lambda x: any(tag in x.split(',') for tag in tag_filter))]

            for index, row in filtered_df.sort_values(by="Date", ascending=False).iterrows():
                trade_id_key = row['TradeID']
                outcome_color = {"Win": "#2da44e", "Loss": "#cf222e", "Breakeven": "#8b949e", "No Trade/Study": "#58a6ff"}.get(row['Outcome'], "#30363d")

                with st.container(border=True):
                    st.markdown(f"""
                    <div style="display: flex; align-items: stretch; gap: 15px; margin-left: -10px;">
                      <div style="width: 4px; background-color: {outcome_color}; border-radius: 3px;"></div>
                      <div>
                        <div style="font-size: 1.1em; font-weight: 600;">
                          {row['Symbol']} <span style="font-weight: 500; color: {outcome_color};">{row['Direction']} / {row['Outcome']}</span>
                        </div>
                        <div style="color: #8b949e; font-size: 0.9em; margin-top: 2px;">
                          {row['Date'].strftime('%A, %d %B %Y')} | {trade_id_key}
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("---")

                    # Metrics Section - Simplified for this example
                    metric_cols = st.columns(3)
                    metric_cols[0].metric("Net PnL", f"${row.get('PnL', 0.0):.2f}")
                    metric_cols[1].metric("R-Multiple", f"{row.get('RR', 0.0):.2f}R")
                    metric_cols[2].metric("Position Size", f"{row.get('Lots', 0.01):.2f} lots")
                    
                    st.markdown("---")
                    if row['EntryRationale']: st.markdown(f"**Entry Rationale:** *{row['EntryRationale']}*")
                    if row['Tags']:
                        tags_list = [f"`{tag.strip()}`" for tag in str(row['Tags']).split(',') if tag.strip()]
                        if tags_list: st.markdown(f"**Tags:** {', '.join(tags_list)}")
                    
                    with st.expander("Journal Notes & Screenshots", expanded=False):
                        # Simplified display for this example
                        st.text_area("Trade Journal Notes", value=row['TradeJournalNotes'], key=f"notes_{trade_id_key}", height=150)
                        st.button("Save Notes", key=f"save_notes_{trade_id_key}")
                        st.button("Delete Trade", key=f"delete_trade_{trade_id_key}")

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
