import streamlit as st
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Y Square Studio 管理系统", layout="wide")

# --- 数据初始化 ---
if 'scripts_db' not in st.session_state:
    st.session_state['scripts_db'] = pd.DataFrame(columns=['剧本名称', '人数配置', '单人价格($)', '主开DM', '日期'])
if 'employee_db' not in st.session_state:
    st.session_state['employee_db'] = pd.DataFrame(columns=['员工姓名', '时薪($)'])
if 'attendance_db' not in st.session_state:
    st.session_state['attendance_db'] = pd.DataFrame(columns=['记录日期', '员工姓名', '工作类型', '时长(小时)', '当日薪资($)'])
if 'ledger_db' not in st.session_state:
    st.session_state['ledger_db'] = pd.DataFrame(columns=['交易时间', '关联剧本', '支付方式', '入账总额($)', '其中小费($)', '备注'])

st.title("Y Square Studio 门店管理系统")
tab1, tab2, tab3 = st.tabs(["📚 剧本列表管理", "⏰ 员工考勤与薪资", "💵 收银与流水记录"])

# ==========================================
# Tab 1: 剧本管理 (保持不变，省略展开代码)
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
        display_scripts = st.session_state['scripts_db'].copy()
        if search_script:
            mask = display_scripts['剧本名称'].str.contains(search_script, case=False, na=False) | display_scripts['主开DM'].str.contains(search_script, case=False, na=False)
            st.dataframe(display_scripts[mask], use_container_width=True)
        else:
            st.session_state['scripts_db'] = st.data_editor(st.session_state['scripts_db'], num_rows="dynamic", use_container_width=True, key="edit_scripts")
        
        with st.expander("🗑️ 快速删除剧本"):
            if not display_scripts.empty:
                del_options = display_scripts.apply(lambda row: f"{row['日期']} | {row['剧本名称']}", axis=1)
                if st.button("🚨 确认删除选中项", key="del_s"):
                    del_idx = st.selectbox("选择", display_scripts.index, format_func=lambda x: del_options[x], label_visibility="collapsed")
                    st.session_state['scripts_db'] = st.session_state['scripts_db'].drop(del_idx).reset_index(drop=True)
                    st.rerun()

# ==========================================
# Tab 2: 考勤与月度结算 (保持紧凑版)
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
                st.rerun()
        
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
                    st.rerun()
            else:
                selected_emps = st.multiselect("选择参与演绎的 DM", employee_list)
                act_fee = st.number_input("每人演绎费 ($)", min_value=0.0, step=5.0)
                if st.button("批量提交演绎记录") and selected_emps:
                    batch_data = [{'记录日期': pd.to_datetime(work_date), '员工姓名': emp, '工作类型': "演绎NPC", '时长(小时)': 0.0, '当日薪资($)': act_fee} for emp in selected_emps]
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(batch_data)], ignore_index=True)
                    st.rerun()

    with col_right:
        st.subheader("💰 财务月结看板")
        if not st.session_state['attendance_db'].empty:
            df = st.session_state['attendance_db'].copy()
            df['记录日期'] = pd.to_datetime(df['记录日期'])
            target_month = st.selectbox("选择月份", sorted(df['记录日期'].dt.strftime('%Y-%m').unique().tolist(), reverse=True))
            month_df = df[df['记录日期'].dt.strftime('%Y-%m') == target_month]
            
            edited_month_df = st.data_editor(month_df, use_container_width=True, key="edit_att")
            if not edited_month_df.equals(month_df):
                 for col in edited_month_df.columns: st.session_state['attendance_db'].loc[edited_month_df.index, col] = edited_month_df[col]
            
            if not month_df.empty:
                summary = month_df.groupby('员工姓名').agg(总工时=('时长(小时)', 'sum'), 本月薪资=('当日薪资($)', 'sum')).reset_index()
                st.dataframe(summary, use_container_width=True)

# ==========================================
# Tab 3: 收银记账 (✨ 核心排版优化版 ✨)
# ==========================================
with tab3:
    # 🌟 优化1：把总账单永远固定在最上面，再也不会看不到了！
    st.subheader("📈 门店营收大盘 (全折算为 USD)")
    display_ledger = st.session_state['ledger_db']
    
    if not display_ledger.empty:
        total_revenue = display_ledger['入账总额($)'].sum()
        total_tips = display_ledger['其中小费($)'].sum()
        pure_revenue = total_revenue - total_tips
        
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 门店总入账", f"${total_revenue:,.2f}")
        m2.metric("📊 剥离小费后净收", f"${pure_revenue:,.2f}")
        m3.metric("✨ 累计沉淀小费", f"${total_tips:,.2f}")
    else:
        st.info("今日暂无进账记录。")
    
    st.divider()

    # 🌟 优化2：左右分栏，右边留宽一点
    col_pay1, col_pay2 = st.columns([1, 1.4])
    
    with col_pay1:
        st.subheader("录入新账单")
        script_options = st.session_state['scripts_db']['剧本名称'].unique().tolist()
        expected_total = 0.0
        
        if script_options:
            script_link = st.selectbox("🔍 搜索剧本场次", script_options)
            matched_script = st.session_state['scripts_db'][st.session_state['scripts_db']['剧本名称'] == script_link].iloc[-1]
            expected_total = float(matched_script['单人价格($)']) * int(matched_script['人数配置'])
            st.info(f"💡 **应收票款**：${expected_total:.2f}")
        else:
            script_link = st.text_input("关联剧本名")
        
        st.write("💳 **拆分支付**")
        c1, c2 = st.columns(2)
        venmo_amt = c1.number_input("📱 Venmo", min_value=0.0, step=1.0)
        zelle_amt = c2.number_input("💸 Zelle", min_value=0.0, step=1.0)
        transfer_amt = c1.number_input("🏦 转账", min_value=0.0, step=1.0)
        cash_amt = c2.number_input("💵 现金", min_value=0.0, step=1.0)
        
        c3, c4 = st.columns(2)
        exchange_rate = c3.number_input("汇率 (USD=RMB)", value=7.20, step=0.05)
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
            
        if st.checkbox("手动覆写小费"):
            tip_amount = st.number_input("输入小费", value=float(tip_amount))
            
        dm_list = st.session_state['employee_db']['员工姓名'].tolist()
        tipped_dms = st.multiselect("🧑‍🏫 平分小费给DM", dm_list)
        pay_note = st.text_input("备注")
        
        if st.button("🚀 确认收账入库", type="primary", use_container_width=True):
            if total_collected > 0:
                if tip_amount > 0 and not tipped_dms:
                    st.error("⚠️ 请选择分配小费的 DM！")
                    st.stop()

                def save_record(method, amt, rmb_original=None):
                    method_tip = amt * (tip_amount / total_collected) if total_collected > 0 else 0
                    final_note = f"{pay_note} [{method}收 ¥{rmb_original:.2f}]".strip() if rmb_original else pay_note
                    st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], pd.DataFrame({'交易时间': [datetime.now().strftime("%Y-%m-%d %H:%M")], '关联剧本': [script_link], '支付方式': [method], '入账总额($)': [amt], '其中小费($)': [method_tip], '备注': [final_note]})], ignore_index=True)
                
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
        if not display_ledger.empty:
            search_ledger = st.text_input("🔍 搜索剧本名称查账", "", key="search_l")
            if search_ledger:
                display_ledger = display_ledger[display_ledger['关联剧本'].str.contains(search_ledger, case=False, na=False)]
            
            edited_ledger = st.data_editor(display_ledger, use_container_width=True, height=450, key="edit_ledger")
            if not edited_ledger.equals(display_ledger):
                 for col in edited_ledger.columns: st.session_state['ledger_db'].loc[edited_ledger.index, col] = edited_ledger[col]
                 st.toast("修改已保存！", icon="💾")
                 time.sleep(0.5)
                 st.rerun()
