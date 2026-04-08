import streamlit as st
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Y Square Studio 管理系统", layout="wide")

# --- 数据初始化与向下兼容 ---
if 'scripts_db' not in st.session_state:
    st.session_state['scripts_db'] = pd.DataFrame(columns=['剧本名称', '人数配置', '单人价格($)', '主开DM', '日期'])
    
if 'employee_db' not in st.session_state:
    st.session_state['employee_db'] = pd.DataFrame(columns=['员工姓名', '时薪($)'])
    
if 'attendance_db' not in st.session_state:
    st.session_state['attendance_db'] = pd.DataFrame(columns=['记录日期', '员工姓名', '工作类型', '时长(小时)', '当日薪资($)'])
else:
    if '打卡日期' in st.session_state['attendance_db'].columns:
        st.session_state['attendance_db'].rename(columns={'打卡日期': '记录日期'}, inplace=True)
        
if 'ledger_db' not in st.session_state:
    st.session_state['ledger_db'] = pd.DataFrame(columns=['交易时间', '关联剧本', '主开DM', '支付方式', '入账总额($)', '其中小费($)', '备注'])
else:
    if '主开DM' not in st.session_state['ledger_db'].columns:
        st.session_state['ledger_db'].insert(2, '主开DM', "")

st.title("Y Square Studio 门店管理系统")
tab1, tab2, tab3, tab4 = st.tabs(["📚 剧本列表管理", "⏰ 员工考勤与薪资", "💵 收银与流水记录", "📊 经营营收报表"])

# ==========================================
# Tab 1: 剧本管理
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("添加新剧本 / 场次")
        with st.form("add_script_form"):
            script_name = st.text_input("剧本名称")
            player_count = st.number_input("人数配置", min_value=1, step=1, value=6)
            price = st.number_input("单人价格 ($)", min_value=0.0, step=1.0, value=30.0)
            
            employee_list = st.session_state['employee_db']['员工姓名'].tolist()
            dm_name = st.selectbox("主开 DM", employee_list) if employee_list else st.text_input("主开 DM")
            script_date = st.date_input("开本日期")
            if st.form_submit_button("添加记录") and script_name and dm_name:
                new_script = pd.DataFrame({'剧本名称': [script_name], '人数配置': [player_count], '单人价格($)': [price], '主开DM': [dm_name], '日期': [script_date]})
                st.session_state['scripts_db'] = pd.concat([st.session_state['scripts_db'], new_script], ignore_index=True)
                st.toast("剧本已录入！", icon="✅")
                time.sleep(0.5)
                st.rerun()

    with col2:
        st.subheader("当前剧本库")
        search_script = st.text_input("🔍 搜索剧本名称或主开 DM", "", key="search_s")
        if search_script:
            display_scripts = st.session_state['scripts_db']
            mask = display_scripts['剧本名称'].str.contains(search_script, case=False, na=False) | display_scripts['主开DM'].str.contains(search_script, case=False, na=False)
            st.dataframe(display_scripts[mask], use_container_width=True)
            st.info("💡 清空搜索框即可进入修改/删除模式。")
        else:
            st.caption("✨ **直接编辑模式**：双击单元格修改，勾选最左侧方框可删除整行。")
            st.session_state['scripts_db'] = st.data_editor(st.session_state['scripts_db'], num_rows="dynamic", use_container_width=True, key="edit_scripts")

# ==========================================
# Tab 2: 考勤与月度结算
# ==========================================
with tab2:
    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.subheader("1. 员工名册管理")
        with st.form("add_employee_form"):
            emp_name = st.text_input("员工姓名")
            hourly_rate = st.number_input("基础时薪 ($)", min_value=0.0, step=0.5, value=15.0)
            if st.form_submit_button("新员工入职") and emp_name not in st.session_state['employee_db']['员工姓名'].values:
                st.session_state['employee_db'] = pd.concat([st.session_state['employee_db'], pd.DataFrame({'员工姓名': [emp_name], '时薪($)': [hourly_rate]})], ignore_index=True)
                st.toast(f"已录入 {emp_name}", icon="✅")
                time.sleep(0.5)
                st.rerun()
        
        with st.expander("⚙️ 修改或删除员工 (点此展开)"):
            st.session_state['employee_db'] = st.data_editor(st.session_state['employee_db'], num_rows="dynamic", use_container_width=True, key="edit_emp")
        
        st.divider()
        st.subheader("2. 快速录入考勤")
        employee_list = st.session_state['employee_db']['员工姓名'].tolist()
        if employee_list:
            work_date = st.date_input("日期", value=datetime.now(), key="work_d")
            work_type = st.radio("工作内容", ["日常带本", "NPC演绎"], horizontal=True)
            if work_type == "日常带本":
                selected_emp = st.selectbox("选择 DM", employee_list)
                hours = st.number_input("带本时长 (小时)", min_value=0.0, step=0.5)
                if st.button("提交带本记录"):
                    rate = st.session_state['employee_db'][st.session_state['employee_db']['员工姓名'] == selected_emp]['时薪($)'].values[0]
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame({'记录日期': [pd.to_datetime(work_date)], '员工姓名': [selected_emp], '工作类型': ["带本"], '时长(小时)': [hours], '当日薪资($)': [hours * rate]})], ignore_index=True)
                    st.toast("记录成功", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
            else:
                selected_emps = st.multiselect("选择参与演绎的 DM", employee_list)
                act_fee = st.number_input("每人演绎费 ($)", min_value=0.0, step=5.0)
                if st.button("批量提交演绎记录") and selected_emps:
                    batch_data = [{'记录日期': pd.to_datetime(work_date), '员工姓名': emp, '工作类型': "演绎NPC", '时长(小时)': 0.0, '当日薪资($)': act_fee} for emp in selected_emps]
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(batch_data)], ignore_index=True)
                    st.toast("记录成功", icon="✅")
                    time.sleep(0.5)
                    st.rerun()

    with col_right:
        st.subheader("💰 财务月结看板")
        if not st.session_state['attendance_db'].empty:
            df = st.session_state['attendance_db'].copy()
            df['记录日期'] = pd.to_datetime(df['记录日期'])
            target_month = st.selectbox("选择月份", sorted(df['记录日期'].dt.strftime('%Y-%m').unique().tolist(), reverse=True))
            month_df = df[df['记录日期'].dt.strftime('%Y-%m') == target_month]
            
            st.caption("✨ 双击下方表格即可修改考勤记录，修改会自动保存。")
            edited_month_df = st.data_editor(month_df, use_container_width=True, key="edit_att")
            if not edited_month_df.equals(month_df):
                 for col in edited_month_df.columns: 
                     st.session_state['attendance_db'].loc[edited_month_df.index, col] = edited_month_df[col]
                 st.toast("考勤修改已保存！", icon="💾")
            
            with st.expander("🗑️ 录错了想删除？点此选择并删除记录"):
                if not month_df.empty:
                    att_del_options = month_df.apply(lambda row: f"{row['记录日期'].strftime('%m-%d')} | {row['员工姓名']} | {row['工作类型']} | ${row['当日薪资($)']}", axis=1)
                    att_del_idx = st.selectbox("选择", month_df.index, format_func=lambda x: att_del_options[x], label_visibility="collapsed")
                    if st.button("🚨 确认删除这笔薪资记录"):
                        st.session_state['attendance_db'] = st.session_state['attendance_db'].drop(att_del_idx).reset_index(drop=True)
                        st.toast("已删除", icon="🗑️")
                        time.sleep(0.5)
                        st.rerun()

            if not month_df.empty:
                summary = month_df.groupby('员工姓名').agg(总工时=('时长(小时)', 'sum'), 本月应付=('当日薪资($)', 'sum')).reset_index()
                st.dataframe(summary, use_container_width=True)

# ==========================================
# Tab 3: 收银记账
# ==========================================
with tab3:
    st.subheader("📈 门店营收大盘 (全折算为 USD)")
    display_ledger = st.session_state['ledger_db']
    
    if not display_ledger.empty:
        total_revenue = display_ledger['入账总额($)'].sum()
        total_tips = display_ledger['其中小费($)'].sum()
        pure_revenue = total_revenue - total_tips
        
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 门店总流水", f"${total_revenue:,.2f}")
        m2.metric("📊 净收(减去小费)", f"${pure_revenue:,.2f}")
        m3.metric("✨ 待发小费池", f"${total_tips:,.2f}")
    else:
        st.info("今日暂无进账记录。")
    
    st.divider()

    col_pay1, col_pay2 = st.columns([1, 1.4])
    
    with col_pay1:
        st.subheader("录入新账单")
        script_options = st.session_state['scripts_db']['剧本名称'].unique().tolist()
        expected_total = 0.0
        host_dm = ""
        
        if script_options:
            script_link = st.selectbox("🔍 搜索剧本场次", script_options)
            matched_script = st.session_state['scripts_db'][st.session_state['scripts_db']['剧本名称'] == script_link].iloc[-1]
            expected_total = float(matched_script['单人价格($)']) * int(matched_script['人数配置'])
            host_dm = matched_script['主开DM'] 
            
            st.info(f"💡 **应收票款**：${expected_total:.2f} (主开DM: {host_dm})")
        else:
            script_link = st.text_input("关联剧本名")
        
        st.write("💳 **拆分支付**")
        c1, c2 = st.columns(2)
        venmo_amt = c1.number_input("📱 Venmo", min_value=0.0, step=1.0)
        zelle_amt = c2.number_input("💸 Zelle", min_value=0.0, step=1.0)
        transfer_amt = c1.number_input("🏦 转账", min_value=0.0, step=1.0)
        cash_amt = c2.number_input("💵 现金", min_value=0.0, step=1.0)
        
        c3, c4 = st.columns(2)
        exchange_rate = c3.number_input("当前汇率 (USD=RMB)", value=7.20, step=0.05)
        alipay_rmb = c3.number_input("💙 支付宝(¥)", min_value=0.0, step=10.0)
        wechat_rmb = c4.number_input("💚 微信(¥)", min_value=0.0, step=10.0)
        
        alipay_usd = alipay_rmb / exchange_rate if exchange_rate > 0 else 0.0
        wechat_usd = wechat_rmb / exchange_rate if exchange_rate > 0 else 0.0

        total_collected = venmo_amt + zelle_amt + transfer_amt + cash_amt + alipay_usd + wechat_usd
        
        st.write("✨ **对账与小费**")
        if expected_total > 0 and total_collected > expected_total:
            tip_amount = total_collected - expected_total
            st.success(f"实收 **${total_collected:.2f}**，小费 **${tip_amount:.2f}**")
        else:
            tip_amount = 0.0
            st.caption(f"当前实收 **${total_collected:.2f}**")
            
        if st.checkbox("手动覆写小费金额"):
            tip_amount = st.number_input("输入小费", value=float(tip_amount))
            
        dm_list = st.session_state['employee_db']['员工姓名'].tolist()
        tipped_dms = st.multiselect("🧑‍🏫 选择DM平分小费", dm_list)
        pay_note = st.text_input("账单备注")
        
        if st.button("🚀 确认收账入库", type="primary", use_container_width=True):
            if total_collected > 0:
                if tip_amount > 0 and not tipped_dms:
                    st.error("⚠️ 请选择分配小费的 DM！")
                    st.stop()

                def save_record(method, amt, rmb_original=None):
                    method_tip = amt * (tip_amount / total_collected) if total_collected > 0 else 0
                    final_note = f"{pay_note} [{method}收 ¥{rmb_original:.2f}]".strip() if rmb_original else pay_note
                    st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], pd.DataFrame({
                        '交易时间': [datetime.now().strftime("%Y-%m-%d %H:%M")], 
                        '关联剧本': [script_link], 
                        '主开DM': [host_dm], 
                        '支付方式': [method], 
                        '入账总额($)': [amt], 
                        '其中小费($)': [method_tip], 
                        '备注': [final_note]
                    })], ignore_index=True)
                
                if venmo_amt > 0: save_record("Venmo", venmo_amt)
                if zelle_amt > 0: save_record("Zelle", zelle_amt)
                if transfer_amt > 0: save_record("转账", transfer_amt)
                if cash_amt > 0: save_record("现金", cash_amt)
                if alipay_usd > 0: save_record("支付宝", alipay_usd, alipay_rmb)
                if wechat_usd > 0: save_record("微信", wechat_usd, wechat_rmb)
                
                if tip_amount > 0 and tipped_dms:
                    tip_records = [{'记录日期': pd.to_datetime(datetime.now().date()), '员工姓名': dm, '工作类型': "专属小费", '时长(小时)': 0.0, '当日薪资($)': tip_amount / len(tipped_dms)} for dm in tipped_dms]
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(tip_records)], ignore_index=True)
                
                st.toast("✅ 入库成功！", icon="🎉")
                time.sleep(0.5)
                st.rerun()

    with col_pay2:
        st.subheader("流水明细与修改")
        search_ledger = st.text_input("🔍 搜索查账 (可搜剧本名或DM名)", "", key="search_l")
        
        if search_ledger:
            mask = st.session_state['ledger_db']['关联剧本'].str.contains(search_ledger, case=False, na=False) | \
                   st.session_state['ledger_db']['备注'].str.contains(search_ledger, case=False, na=False) | \
                   st.session_state['ledger_db']['主开DM'].str.contains(search_ledger, case=False, na=False)
            st.dataframe(st.session_state['ledger_db'][mask], use_container_width=True, height=450)
            st.info("💡 提示：搜索状态下不可修改。清空上方的搜索框，即可直接修改或删除流水。")
        else:
            st.caption("✨ **直接编辑模式**：双击单元格即可修改金额。勾选最左侧方框后按 Delete 可删除流水。")
            st.session_state['ledger_db'] = st.data_editor(st.session_state['ledger_db'], num_rows="dynamic", use_container_width=True, height=450, key="edit_ledger")

# ==========================================
# Tab 4: 经营营收报表 (核心升级：可调房租 & 利润率分析)
# ==========================================
with tab4:
    st.header("📈 门店经营损益分析")
    st.caption("基于 Tab 2(考勤) 与 Tab 3(流水) 数据自动生成")

    # 1. 可自定义的固定房租成本
    col_rent1, col_rent2 = st.columns([1, 3])
    with col_rent1:
        current_rent = st.number_input("🏠 本月设定房租 ($)", min_value=0.0, step=100.0, value=7000.0)

    st.divider()

    df_ledger = st.session_state['ledger_db'].copy()
    df_attendance = st.session_state['attendance_db'].copy()
    
    if not df_ledger.empty or not df_attendance.empty:
        # 时间格式处理
        if not df_ledger.empty:
            df_ledger['交易时间'] = pd.to_datetime(df_ledger['交易时间'])
            df_ledger['月份'] = df_ledger['交易时间'].dt.strftime('%Y-%m')
        
        if not df_attendance.empty:
            df_attendance['记录日期'] = pd.to_datetime(df_attendance['记录日期'])
            df_attendance['月份'] = df_attendance['记录日期'].dt.strftime('%Y-%m')

        # 汇总收入
        revenue_monthly = pd.DataFrame()
        if not df_ledger.empty:
            revenue_monthly = df_ledger.groupby('月份')['入账总额($)'].sum().reset_index()
            revenue_monthly.columns = ['月份', '剧本总营收($)']

        # 汇总支出
        expense_monthly = pd.DataFrame()
        if not df_attendance.empty:
            tips_cost = df_attendance[df_attendance['工作类型'] == "专属小费"].groupby('月份')['当日薪资($)'].sum().reset_index()
            tips_cost.columns = ['月份', '小费总额($)']
            
            wages_cost = df_attendance[df_attendance['工作类型'] != "专属小费"].groupby('月份')['当日薪资($)'].sum().reset_index()
            wages_cost.columns = ['月份', '员工工资($)']
            
            expense_monthly = pd.merge(wages_cost, tips_cost, on='月份', how='outer').fillna(0)

        # 合并所有财务数据
        if not revenue_monthly.empty or not expense_monthly.empty:
            report_df = pd.merge(revenue_monthly, expense_monthly, on='月份', how='outer').fillna(0)
            
            # 补齐缺少的列
            for col in ['剧本总营收($)', '员工工资($)', '小费总额($)']:
                if col not in report_df.columns:
                    report_df[col] = 0.0
            
            # 引入动态房租并计算最终利润
            report_df['房租支出($)'] = current_rent
            report_df['净利润($)'] = report_df['剧本总营收($)'] - report_df['员工工资($)'] - report_df['小费总额($)'] - report_df['房租支出($)']

            # 提取最新月份的数据进行核心指标展示
            latest_month = report_df.sort_values('月份', ascending=False).iloc[0]
            
            rev = latest_month['剧本总营收($)']
            wages = latest_month['员工工资($)']
            tips = latest_month['小费总额($)']
            rent = latest_month['房租支出($)']
            profit = latest_month['净利润($)']

            # 计算各项占比 (如果当月营收为 0，则占比为 0 防止报错)
            if rev > 0:
                wages_pct = (wages / rev) * 100
                tips_pct = (tips / rev) * 100
                rent_pct = (rent / rev) * 100
                profit_pct = (profit / rev) * 100
            else:
                wages_pct = tips_pct = rent_pct = profit_pct = 0.0

            st.subheader(f"📊 {latest_month['月份']} 核心财务指标与占比")
            
            m1, m2, m3, m4, m5 = st.columns(5)
            
            m1.metric("总流水营收", f"${rev:,.2f}", "100% (计算基准)")
            # 员工工资
            m2.metric("员工时薪支出", f"${wages:,.2f}", f"占营收: {wages_pct:.1f}%", delta_color="inverse")
            # 小费 (100% 给 DM，计为成本)
            m3.metric("DM专属小费支出", f"${tips:,.2f}", f"占营收: {tips_pct:.1f}%", delta_color="inverse")
            # 房租
            m4.metric("房租固定支出", f"${rent:,.2f}", f"占营收: {rent_pct:.1f}%", delta_color="inverse")
            # 净利润
            m5.metric("最终净利润", f"${profit:,.2f}", f"净利润率: {profit_pct:.1f}%")

            st.divider()
            st.subheader("🗓️ 历史月度财务明细表")
            
            styled_report = report_df.sort_values('月份', ascending=False).style.format({
                '剧本总营收($)': '{:,.2f}',
                '员工工资($)': '{:,.2f}',
                '小费总额($)': '{:,.2f}',
                '房租支出($)': '{:,.2f}',
                '净利润($)': '{:,.2f}'
            })
            st.dataframe(styled_report, use_container_width=True)

        else:
            st.info("数据不足，无法生成报表。")
    else:
        st.info("暂无财务数据，请先在 Tab 2 和 Tab 3 中录入数据。")
