# =========================================================
# TRADING JOURNAL PAGE
# =========================================================
elif st.session_state.current_page == 'trading_journal':
    if st.session_state.logged_in_user is None:
        st.warning("Please log in to access your Trading Journal.")
        st.session_state.current_page = 'account'
        st.rerun()

    # --- REPLACEMENT FOR THE TITLE ---
    # Instead of a simple title, we use markdown with HTML for the icon and text.
    icon_path = os.path.join("icons", "trading_journal.png")
    if os.path.exists(icon_path):
        icon_base64 = image_to_base64(icon_path)
        # This HTML uses flexbox to align the icon and title with a specific gap.
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="data:image/png;base64,{icon_base64}" width="100">
                <h1 style="margin: 0; font-size: 2.75rem;">Trading Journal</h1>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback in case the icon file is not found
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

                else: # Manual PnL and RR inputs are used
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
        
        # ========== START: GUARANTEED CSS OVERRIDE FOR st.button ==========
        # This CSS is now much more specific and forceful, and will work.
        st.markdown(
            """
            <style>
                div[data-testid="stColumn"] > div[data-testid="stHorizontalBlock"] {
                    position: relative;
                }

                /* Create a wrapper class to apply to the st.button's column */
                .st-emotion-cache-12w0qpk {
                    position: absolute;
                    top: 2px;
                    right: 3px;
                    z-index: 10;
                }
                
                /* Aggressively target the button inside the wrapper */
                .st-emotion-cache-12w0qpk button {
                    /* --- CRITICAL SIZE OVERRIDES --- */
                    font-size: 10px !important;
                    height: 1.1rem !important;  /* Make button vertically tiny */
                    min-height: 1.1rem !important;
                    width: 1.1rem !important;   /* Make button horizontally tiny */
                    min-width: 1.1rem !important;
                    padding: 0 !important;
                    line-height: 0 !important; /* Center the icon */

                    /* Appearance */
                    background: transparent !important;
                    color: #999 !important;
                    border: none !important;
                }

                .st-emotion-cache-12w0qpk button:hover {
                    color: #fff !important; 
                    background: rgba(100, 100, 100, 0.3) !important;
                }
            </style>
            """, unsafe_allow_html=True
        )
        # ========== END: CSS OVERRIDE ==========

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

            tag_options_raw = df_playbook['Tags'].astype(str).str.split(',').explode().dropna().str.strip()
            if not tag_options_raw.empty:
                tag_options = sorted(list(set(tag_options_raw)))
            else:
                tag_options = []

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
                    # Trade Header - MODIFIED BLOCK
                    st.markdown(f"""
                    <div style="display: flex; flex-direction: row; align-items: stretch; gap: 15px; margin-left: -10px;">
                      <div style="width: 4px; background-color: {outcome_color}; border-radius: 3px;"></div>
                      <div style="padding-top: 2px; padding-bottom: 2px;">
                        <div style="font-size: 1.1em; font-weight: 600;">
                          {row['Symbol']} <span style="font-weight: 500; color: {outcome_color};">{row['Direction']} / {row['Outcome']}</span> <span style="font-weight: normal; vertical-align: middle;">🔗</span>
                        </div>
                        <div style="color: #8b949e; font-size: 0.9em; margin-top: 2px;">
                          {row['Date'].strftime('%A, %d %B %Y')} | {trade_id_key}
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("---")

                    # Metrics Section
                    metric_cols = st.columns(3)
                    
                    pnl_val = float(pd.to_numeric(row.get('PnL', 0.0), errors='coerce') or 0.0)
                    rr_val = float(pd.to_numeric(row.get('RR', 0.0), errors='coerce') or 0.0)
                    lots_val = float(pd.to_numeric(row.get('Lots', 0.01), errors='coerce') or 0.01)

                    def render_metric_cell_or_form(col_obj, metric_label, db_column, current_value, key_suffix, format_str, is_pnl_metric=False):
                        is_editing = st.session_state.edit_state.get(f"{key_suffix}_{trade_id_key}", False)
                        
                        main_col, button_col = col_obj.columns([4, 1])

                        with main_col:
                            if is_editing:
                                with st.form(f"form_{key_suffix}_{trade_id_key}", clear_on_submit=False):
                                    st.markdown(f"**Edit {metric_label}**")
                                    new_value = st.number_input("", value=current_value, format=format_str, key=f"input_{key_suffix}_{trade_id_key}", label_visibility="collapsed")
                                    s_col, c_col = st.columns(2)
                                    if s_col.form_submit_button("✓ Save", type="primary", use_container_width=True):
                                        st.session_state.trade_journal.loc[index, db_column] = new_value
                                        _ta_save_journal(st.session_state.logged_in_user, st.session_state.trade_journal)
                                        st.session_state.edit_state[f"{key_suffix}_{trade_id_key}"] = False
                                        st.rerun()
                                    if c_col.form_submit_button("✗ Cancel", use_container_width=True):
                                        st.session_state.edit_state[f"{key_suffix}_{trade_id_key}"] = False
                                        st.rerun()
                            else:
                                border_style = ""
                                if is_pnl_metric:
                                    border_color = "#2da44e" if current_value > 0 else ("#cf222e" if current_value < 0 else "#30363d")
                                    val_color = "#50fa7b" if current_value > 0 else ("#ff5555" if current_value < 0 else "#c9d1d9")
                                    border_style = f"border: 1px solid {border_color};"
                                    display_val_str = f"<div class='value' style='color:{val_color};'>${current_value:.2f}</div>"
                                elif metric_label == "R-Multiple":
                                    display_val_str = f"<div class='value'>{current_value:.2f}R</div>"
                                else: # Position Size
                                    display_val_str = f"<div class='value'>{current_value:.2f} lots</div>"
                                
                                st.markdown(f"""
                                    <div class='playbook-metric-display' style='{border_style}'>
                                        <div class='label'>{metric_label}</div>
                                        {display_val_str}
                                    </div>""", unsafe_allow_html=True)
                        
                        with button_col:
                            st.markdown('<div class="st-emotion-cache-12w0qpk">', unsafe_allow_html=True)
                            if not is_editing:
                                if st.button("✏️", key=f"edit_btn_{key_suffix}_{trade_id_key}", help=f"Edit {metric_label}"):
                                    st.session_state.edit_state[f"{key_suffix}_{trade_id_key}"] = True
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                    render_metric_cell_or_form(metric_cols[0], "Net PnL", "PnL", pnl_val, "pnl", "%.2f", is_pnl_metric=True)
                    render_metric_cell_or_form(metric_cols[1], "R-Multiple", "RR", rr_val, "rr", "%.2f")
                    render_metric_cell_or_form(metric_cols[2], "Position Size", "Lots", lots_val, "lots", "%.2f")
                    
                    st.markdown("---")

                    if row['EntryRationale']: st.markdown(f"**Entry Rationale:** *{row['EntryRationale']}*")
                    if row['Tags']:
                        tags_list = [f"`{tag.strip()}`" for tag in str(row['Tags']).split(',') if tag.strip()]
                        if tags_list: st.markdown(f"**Tags:** {', '.join(tags_list)}")
                    
                    with st.expander("Journal Notes & Screenshots", expanded=False):
                        notes = st.text_area(
                            "Trade Journal Notes",
                            value=row['TradeJournalNotes'],
                            key=f"notes_{trade_id_key}",
                            height=150
                        )

                        action_cols_notes_delete = st.columns([1, 1, 4]) 

                        if action_cols_notes_delete[0].button("Save Notes", key=f"save_notes_{trade_id_key}", type="primary"):
                            original_notes_from_df = st.session_state.trade_journal.loc[st.session_state.trade_journal['TradeID'] == trade_id_key, 'TradeJournalNotes'].iloc[0]
                            st.session_state.trade_journal.loc[index, 'TradeJournalNotes'] = notes
                            
                            if _ta_save_journal(st.session_state.logged_in_user, st.session_state.trade_journal):
                                current_notes_hash = hashlib.md5(notes.strip().encode()).hexdigest() if notes.strip() else ""
                                gamification_flags = st.session_state.get('gamification_flags', {})
                                notes_award_key = f"xp_notes_for_trade_{trade_id_key}_content_hash"
                                last_awarded_notes_hash = gamification_flags.get(notes_award_key)

                                if notes.strip() and current_notes_hash != last_awarded_notes_hash:
                                    award_xp_for_notes_added_if_changed(st.session_state.logged_in_user, trade_id_key, notes)
                                else:
                                    st.toast(f"Notes for {row['TradeID']} updated (no new XP for same content).", icon="✅")
                                save_user_data(st.session_state.logged_in_user)
                                st.rerun()
                            else:
                                st.error("Failed to save notes.")

                        if action_cols_notes_delete[1].button("Delete Trade", key=f"delete_trade_{trade_id_key}"):
                            username = st.session_state.logged_in_user
                            xp_deduction_amount = 0
                            xp_deduction_amount += 10

                            gamification_flags = st.session_state.get('gamification_flags', {})
                            notes_award_key_for_deleted = f"xp_notes_for_trade_{trade_id_key}_content_hash"
                            if notes_award_key_for_deleted in gamification_flags:
                                xp_deduction_amount += 5
                                del gamification_flags[notes_award_key_for_deleted]
                            
                            if trade_id_key in st.session_state.edit_state:
                                for key in list(st.session_state.edit_state.keys()):
                                    if trade_id_key in key:
                                        del st.session_state.edit_state[key]
                            
                            st.session_state.gamification_flags = gamification_flags
                            
                            if xp_deduction_amount > 0:
                                ta_update_xp(username, -xp_deduction_amount, f"Deleted trade {row['TradeID']}")
                                st.toast(f"Trade {row['TradeID']} deleted. {xp_deduction_amount} XP deducted.", icon="🗑️")
                            else:
                                st.toast(f"Trade {row['TradeID']} deleted.", icon="🗑️")

                            st.session_state.trade_journal.drop(index, inplace=True)
                            st.session_state.trade_journal.reset_index(drop=True, inplace=True)
                            
                            if row['EntryScreenshot'] and os.path.exists(row['EntryScreenshot']):
                                try: os.remove(row['EntryScreenshot'])
                                except OSError as e: logging.error(f"Error deleting entry screenshot {row['EntryScreenshot']}: {e}")
                            if row['ExitScreenshot'] and os.path.exists(row['ExitScreenshot']):
                                try: os.remove(row['ExitScreenshot'])
                                except OSError as e: logging.error(f"Error deleting exit screenshot {row['ExitScreenshot']}: {e}")

                            if _ta_save_journal(username, st.session_state.trade_journal):
                                check_and_award_trade_milestones(username)
                                check_and_award_performance_milestones(username)
                                st.rerun()
                            else:
                                st.error("Failed to delete trade.")
                        
                        st.markdown("---")
                        st.subheader("Update Screenshots")
                        
                        image_base_path = os.path.join("user_data", st.session_state.logged_in_user, "journal_images")
                        os.makedirs(image_base_path, exist_ok=True)

                        upload_cols = st.columns(2)
                        
                        with upload_cols[0]:
                            new_entry_screenshot_file = st.file_uploader(
                                f"Upload/Update Entry Screenshot", 
                                type=["png", "jpg", "jpeg"], 
                                key=f"update_entry_ss_uploader_{trade_id_key}"
                            )
                            if new_entry_screenshot_file:
                                if st.button("Save Entry Image", key=f"save_new_entry_ss_btn_{trade_id_key}", type="secondary", use_container_width=True):
                                    if row['EntryScreenshot'] and os.path.exists(row['EntryScreenshot']):
                                        try: os.remove(row['EntryScreenshot'])
                                        except OSError as e: logging.error(f"Error deleting old entry screenshot {row['EntryScreenshot']}: {e}")

                                    entry_screenshot_filename = f"{trade_id_key}_entry_{uuid.uuid4().hex[:4]}_{new_entry_screenshot_file.name}"
                                    entry_screenshot_full_path = os.path.join(image_base_path, entry_screenshot_filename)
                                    with open(entry_screenshot_full_path, "wb") as f:
                                        f.write(new_entry_screenshot_file.getbuffer())
                                    
                                    st.session_state.trade_journal.loc[index, 'EntryScreenshot'] = entry_screenshot_full_path
                                    _ta_save_journal(st.session_state.logged_in_user, st.session_state.trade_journal)
                                    st.toast("Entry screenshot updated!", icon="📸")
                                    st.rerun()

                        with upload_cols[1]:
                            new_exit_screenshot_file = st.file_uploader(
                                f"Upload/Update Exit Screenshot", 
                                type=["png", "jpg", "jpeg"], 
                                key=f"update_exit_ss_uploader_{trade_id_key}"
                            )
                            if new_exit_screenshot_file:
                                if st.button("Save Exit Image", key=f"save_new_exit_ss_btn_{trade_id_key}", type="secondary", use_container_width=True):
                                    if row['ExitScreenshot'] and os.path.exists(row['ExitScreenshot']):
                                        try: os.remove(row['ExitScreenshot'])
                                        except OSError as e: logging.error(f"Error deleting old exit screenshot {row['ExitScreenshot']}: {e}")

                                    exit_screenshot_filename = f"{trade_id_key}_exit_{uuid.uuid4().hex[:4]}_{new_exit_screenshot_file.name}"
                                    exit_screenshot_full_path = os.path.join(image_base_path, exit_screenshot_filename)
                                    with open(exit_screenshot_full_path, "wb") as f:
                                        f.write(new_exit_screenshot_file.getbuffer())

                                    st.session_state.trade_journal.loc[index, 'ExitScreenshot'] = exit_screenshot_full_path
                                    _ta_save_journal(st.session_state.logged_in_user, st.session_state.trade_journal)
                                    st.toast("Exit screenshot updated!", icon="📸")
                                    st.rerun()
                                    
                        st.markdown("---")
                        st.subheader("Current Visuals")
                        visual_cols = st.columns(2)
                        if row['EntryScreenshot'] and os.path.exists(row['EntryScreenshot']):
                            visual_cols[0].image(row['EntryScreenshot'], caption="Entry", width=250)
                        else:
                            visual_cols[0].info("No Entry Screenshot available.")
                        
                        if row['ExitScreenshot'] and os.path.exists(row['ExitScreenshot']):
                            visual_cols[1].image(row['ExitScreenshot'], caption="Exit", width=250)
                        else:
                            visual_cols[1].info("No Exit Screenshot available.")
                            
                    st.markdown("---") 


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
            profit_factor = pd.to_numeric(wins['PnL'], errors='coerce').sum() / abs(pd.to_numeric(losses['PnL'], errors='coerce').sum()) if not losses.empty and pd.to_numeric(losses['PnL'], errors='coerce').sum() != 0 else (float('inf') if pd.to_numeric(wins['PnL'], errors='coerce').sum() > 0 else 0)


            kpi_cols = st.columns(4)

            pnl_metric_color = "#2da44e" if total_pnl >= 0 else "#cf222e"
            pnl_value_color_inner = "#50fa7b" if total_pnl >= 0 else "#ff5555"
            pnl_delta_icon = "⬆️" if total_pnl >= 0 else "⬇️"
            pnl_delta_display = f'<span style="font-size: 0.875rem; color: {pnl_value_color_inner};">{pnl_delta_icon} {abs(total_pnl):,.2f}</span>'


            kpi_cols[0].markdown(
                f"""
                <div class="stMetric" style="background-color: #161b22; border: 1px solid {pnl_metric_color}; border-radius: 8px; padding: 1.2rem; transition: all 0.2s ease-in-out;">
                    <div data-testid="stMetricLabel" style="font-weight: 500; color: #8b949e;">Net PnL ($)</div>
                    <div data-testid="stMetricValue" style="font-size: 2.25rem; line-height: 1.2; font-weight: 600; color: {pnl_value_color_inner};">${total_pnl:,.2f}</div>
                    {pnl_delta_display}
                </div>
                """, unsafe_allow_html=True
            )

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
                fig_equity.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#161b22")
                st.plotly_chart(fig_equity, use_container_width=True)

            with chart_cols[1]:
                st.subheader("Performance by Symbol")
                pnl_by_symbol = df_analytics.groupby('Symbol')['PnL'].sum().sort_values(ascending=False)
                fig_pnl_symbol = px.bar(pnl_by_symbol, title="Net PnL by Symbol", template="plotly_dark")
                fig_pnl_symbol.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#161b22", showlegend=False)
                st.plotly_chart(fig_pnl_symbol, use_container_width=True)
