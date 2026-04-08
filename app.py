import streamlit as st
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Y Square Studio 管理系统", layout="wide")

# --- 数据初始化与缓存兼容 ---
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
    st.session_state['ledger_db'] = pd.DataFrame(columns=['交易时间', '关联剧本', '支付方式', '入账总额($)', '其中小费($)', '备注'])

st.title("Y Square Studio 门店管理系统")

tab1, tab2, tab3 = st.tabs(["📚 剧本列表管理", "⏰ 员工考勤与薪资", "💵 收银与流水记录"])

# ==========================================
# Tab 1: 剧本管理
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("添加新剧本 / 场次")
        with st.form("add_script_form"):
            script_name = st.text_input("剧本名称")
            player_count = st.number_input("人数配置 (例如: 6)", min_value=1, step=1, value=6)
            price = st.number_input("单人价格 ($)", min_value=0.0, step=1.0, value=30.0)
            
            employee_list = st.session_state['employee_db']['员工姓名'].tolist()
            if not employee_list:
                dm_name = st.text_input("主开 DM (⚠️ 请先去 Tab 2 录入员工名单)")
            else:
                dm_name = st.selectbox("主开 DM", employee_list)
                
            script_date = st.date_input("开本日期")
            if st.form_submit_button("添加记录"):
                if script_name and dm_name:
                    new_script = pd.DataFrame({'剧本名称': [script_name], '人数配置': [player_count], '单人价格($)': [price], '主开DM': [dm_name], '日期': [script_date]})
                    st.session_state['scripts_db'] = pd.concat([st.session_state['scripts_db'], new_script], ignore_index=True)
                    st.toast("剧本信息已录入！", icon="✅")
                    time.sleep(0.5)
                    st.rerun()

    with col2:
        st.subheader("当前剧本库")
        search_script = st.text_input("🔍 搜索剧本名称或主开 DM", "", key="search_s")
        
        display_scripts = st.session_state['scripts_db'].copy()
        if search_script:
            mask = display_scripts['剧本名称'].str.contains(search_script, case=False, na=False) | \
                   display_scripts['主开DM'].str.contains(search_script, case=False, na=False)
            display_scripts = display_scripts[mask]
        
        st.dataframe(display_scripts, use_container_width=True)
        
        with st.expander("🗑️ 删除错误剧本记录"):
            if not display_scripts.empty:
                del_options = display_scripts.apply(lambda row: f"{row['日期']} | {row['剧本名称']} | DM: {row['主开DM']}", axis=1)
                del_idx = st.selectbox("选择要删除的剧本", display_scripts.index, format_func=lambda x: del_options[x], key="del_script")
                if st.button("🚨 确认删除此剧本"):
                    st.session_state['scripts_db'] = st.session_state['scripts_db'].drop(del_idx).reset_index(drop=True)
                    st.toast("删除成功！", icon="🗑️")
                    time.sleep(0.5)
                    st.rerun()

# ==========================================
# Tab 2: 考勤与月度结算
# ==========================================
with tab2:
    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.subheader("1. 员工名册管理")
        with st.form("add_employee_form"):
            emp_name = st.text_input("员工/DM 姓名")
            hourly_rate = st.number_input("基础时薪 ($)", min_value=0.0, step=0.5, value=15.0)
            if st.form_submit_button("新员工入职"):
                if emp_name and emp_name not in st.session_state['employee_db']['员工姓名'].values:
                    new_emp = pd.DataFrame({'员工姓名': [emp_name], '时薪($)': [hourly_rate]})
                    st.session_state['employee_db'] = pd.concat([st.session_state['employee_db'], new_emp], ignore_index=True)
                    st.toast(f"员工 {emp_name} 已录入系统", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
        
        with st.expander("🗑️ 删除离职/输错的员工"):
            if not st.session_state['employee_db'].empty:
                emp_del_options = st.session_state['employee_db'].apply(lambda row: f"{row['员工姓名']} (时薪: ${row['时薪($)']})", axis=1)
                emp_del_idx = st.selectbox("选择要删除的员工", st.session_state['employee_db'].index, format_func=lambda x: emp_del_options[x], key="del_emp")
                if st.button("🚨 确认删除此员工"):
                    st.session_state['employee_db'] = st.session_state['employee_db'].drop(emp_del_idx).reset_index(drop=True)
                    st.toast("员工已删除！", icon="🗑️")
                    time.sleep(0.5)
                    st.rerun()

        st.divider()
        st.subheader("2. 快速录入考勤")
        employee_list = st.session_state['employee_db']['员工姓名'].tolist()
        if employee_list:
            work_date = st.date_input("日期", value=datetime.now(), key="work_d")
            work_type = st.radio("工作内容", ["日常带本 (个人)", "NPC演绎 (支持多人)"], horizontal=True)
            if work_type == "日常带本 (个人)":
                selected_emp = st.selectbox("选择 DM", employee_list)
                hours = st.number_input("带本时长 (小时)", min_value=0.0, step=0.5)
                if st.button("提交带本记录"):
                    rate = st.session_state['employee_db'][st.session_state['employee_db']['员工姓名'] == selected_emp]['时薪($)'].values[0]
                    salary = hours * rate
                    new_record = pd.DataFrame({'记录日期': [pd.to_datetime(work_date)], '员工姓名': [selected_emp], '工作类型': ["带本"], '时长(小时)': [hours], '当日薪资($)': [salary]})
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], new_record], ignore_index=True)
                    st.toast(f"{selected_emp} 记录成功", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
            else:
                selected_emps = st.multiselect("选择参与演绎的所有 DM", employee_list)
                act_fee = st.number_input("每人演绎费 ($)", min_value=0.0, step=5.0)
                if st.button("批量提交演绎记录"):
                    if selected_emps:
                        batch_data = [{'记录日期': pd.to_datetime(work_date), '员工姓名': emp, '工作类型': "演绎NPC", '时长(小时)': 0.0, '当日薪资($)': act_fee} for emp in selected_emps]
                        st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(batch_data)], ignore_index=True)
                        st.toast(f"已成功记录 {len(selected_emps)} 位 DM 的演绎工资", icon="✅")
                        time.sleep(0.5)
                        st.rerun()

    with col_right:
        st.subheader("💰 财务月结看板")
        search_emp = st.text_input("🔍 搜索员工姓名单独查账", "", key="search_e")
        if not st.session_state['attendance_db'].empty:
            df = st.session_state['attendance_db'].copy()
            df['记录日期'] = pd.to_datetime(df['记录日期'])
            all_months = df['记录日期'].dt.strftime('%Y-%m').unique().tolist()
            target_month = st.selectbox("选择统计月份", sorted(all_months, reverse=True))
            month_df = df[df['记录日期'].dt.strftime('%Y-%m') == target_month]
            
            if search_emp:
                month_df = month_df[month_df['员工姓名'].str.contains(search_emp, case=False, na=False)]
            
            st.write(f"📅 {target_month} 费用明细")
            
            # 安全更新逻辑：双击修改数字不污染数据库
            edited_month_df = st.data_editor(month_df, use_container_width=True, key="edit_att")
            if not edited_month_df.equals(month_df):
                 for col in edited_month_df.columns:
                     st.session_state['attendance_db'].loc[edited_month_df.index, col] = edited_month_df[col]
                 st.toast("已保存手动修改！", icon="💾")
            
            if not month_df.empty:
                summary = month_df.groupby('员工姓名').agg(总工时=('时长(小时)', 'sum'), 本月总计薪资=('当日薪资($)', 'sum')).reset_index()
                st.dataframe(summary, use_container_width=True)
                st.download_button("下载本月工资单 (CSV)", summary.to_csv(index=False).encode('utf-8-sig'), f"salary_{target_month}.csv", "text/csv")
            
            with st.expander("🗑️ 删除错误的考勤 / 演绎 / 小费记录"):
                if not month_df.empty:
                    att_del_options = month_df.apply(lambda row: f"{row['记录日期'].strftime('%Y-%m-%d')} | {row['员工姓名']} | {row['工作类型']} | 薪资: ${row['当日薪资($)']}", axis=1)
                    att_del_idx = st.selectbox("选择要删除的记录", month_df.index, format_func=lambda x: att_del_options[x], key="del_att")
                    if st.button("🚨 确认删除此记录"):
                        st.session_state['attendance_db'] = st.session_state['attendance_db'].drop(att_del_idx).reset_index(drop=True)
                        st.toast("记录已删除！", icon="🗑️")
                        time.sleep(0.5)
                        st.rerun()

# ==========================================
# Tab 3: 收银记账
# ==========================================
with tab3:
    col_pay1, col_pay2 = st.columns([1, 1.2])
    
    with col_pay1:
        st.subheader("录入新账单")
        
        script_options = st.session_state['scripts_db']['剧本名称'].unique().tolist()
        expected_total = 0.0
        
        if not script_options:
            st.warning("提示：请先在 Tab 1 录入剧本！")
            script_link = st.text_input("手动输入关联剧本名")
        else:
            script_link = st.selectbox("🔍 搜索/选择剧本场次", script_options)
            matched_script = st.session_state['scripts_db'][st.session_state['scripts_db']['剧本名称'] == script_link].iloc[-1]
            price_per_pax = float(matched_script['单人价格($)'])
            pax = int(matched_script['人数配置'])
            expected_total = price_per_pax * pax
            st.info(f"💡 **本车应收标准票款**：${expected_total:.2f}")
        
        st.divider()
        st.write("💳 **拆分支付输入** (未付渠道留空即可)")
        
        st.caption("🟢 **美元渠道 (USD $)**")
        c1, c2 = st.columns(2)
        venmo_amt = c1.number_input("📱 Venmo ($)", min_value=0.0, step=1.0)
        zelle_amt = c2.number_input("💸 Zelle ($)", min_value=0.0, step=1.0)
        transfer_amt = c1.number_input("🏦 银行转账 ($)", min_value=0.0, step=1.0)
        cash_amt = c2.number_input("💵 现金 ($)", min_value=0.0, step=1.0)
        
        st.write("")
        
        st.caption("🔴 **人民币渠道 (RMB ¥) - 自动折算美金**")
        exchange_rate = st.number_input("当前汇率设置 (1 USD = ? RMB)", value=7.20, step=0.05, format="%.2f")
        c3, c4 = st.columns(2)
        alipay_rmb = c3.number_input("💙 支付宝 (¥)", min_value=0.0, step=10.0)
        wechat_rmb = c4.number_input("💚 微信 (¥)", min_value=0.0, step=10.0)
        
        alipay_usd = alipay_rmb / exchange_rate if exchange_rate > 0 else 0.0
        wechat_usd = wechat_rmb / exchange_rate if exchange_rate > 0 else 0.0
        
        if alipay_rmb > 0 or wechat_rmb > 0:
            st.caption
