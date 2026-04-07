import streamlit as st
import pandas as pd
from datetime import datetime

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

# --- Tab 1: 剧本管理 (关联 Tab 2) ---
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("添加新剧本 / 场次")
        with st.form("add_script_form"):
            script_name = st.text_input("剧本名称")
            player_count = st.number_input("人数配置 (例如: 6)", min_value=1, step=1, value=6)
            price = st.number_input("单人价格 ($)", min_value=0.0, step=1.0, value=30.0)
            
            # 核心升级 1：主开 DM 下拉菜单自动关联 Tab 2 的员工名单
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
                    st.success("剧本信息已录入！")
    with col2:
        st.subheader("当前剧本库")
        search_script = st.text_input("🔍 搜索剧本名称或主开 DM", "", key="search_s")
        display_scripts = st.session_state['scripts_db'].copy()
        if search_script:
            mask = display_scripts['剧本名称'].str.contains(search_script, case=False, na=False) | \
                   display_scripts['主开DM'].str.contains(search_script, case=False, na=False)
            display_scripts = display_scripts[mask]
        st.dataframe(display_scripts, use_container_width=True)

# --- Tab 2: 考勤与月度结算 ---
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
                    st.success(f"员工 {emp_name} 已录入系统")

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
                    st.success(f"{selected_emp} 记录成功")
            else:
                selected_emps = st.multiselect("选择参与演绎的所有 DM", employee_list)
                act_fee = st.number_input("每人演绎费 ($)", min_value=0.0, step=5.0)
                if st.button("批量提交演绎记录"):
                    if selected_emps:
                        batch_data = [{'记录日期': pd.to_datetime(work_date), '员工姓名': emp, '工作类型': "演绎NPC", '时长(小时)': 0.0, '当日薪资($)': act_fee} for emp in selected_emps]
                        st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(batch_data)], ignore_index=True)
                        st.success(f"已成功记录 {len(selected_emps)} 位 DM 的演绎工资")
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
            st.dataframe(month_df, use_container_width=True)
            if not month_df.empty:
                summary = month_df.groupby('员工姓名').agg(总工时=('时长(小时)', 'sum'), 本月总计薪资=('当日薪资($)', 'sum')).reset_index()
                st.dataframe(summary, use_container_width=True)
                st.download_button("下载本月工资单 (CSV)", summary.to_csv(index=False).encode('utf-8-sig'), f"salary_{target_month}.csv", "text/csv")

# --- Tab 3: 收银记账 (关联应收价格 & 智能小费) ---
with tab3:
    col_pay1, col_pay2 = st.columns([1, 1.2])
    
    with col_pay1:
        st.subheader("录入新账单")
        
        # 核心升级 2：自带搜索功能的下拉菜单 + 自动抓取价格
        script_options = st.session_state['scripts_db']['剧本名称'].unique().tolist()
        expected_total = 0.0
        
        if not script_options:
            st.warning("提示：请先在 Tab 1 录入剧本！")
            script_link = st.text_input("手动输入关联剧本名")
        else:
            # selectbox 原生支持键盘打字搜索
            script_link = st.selectbox("🔍 搜索/选择剧本场次 (点击后直接打字搜索)", script_options)
            
            # 从 Tab 1 的数据库中找到对应的剧本，计算应收总价
            matched_script = st.session_state['scripts_db'][st.session_state['scripts_db']['剧本名称'] == script_link].iloc[-1]
            price_per_pax = float(matched_script['单人价格($)'])
            pax = int(matched_script['人数配置'])
            expected_total = price_per_pax * pax
            
            st.info(f"💡 **系统联动**：此车单价 **${price_per_pax:.2f}** × **{pax}** 人 = 标准应收票款 **${expected_total:.2f}**")
        
        st.divider()
        st.write("💳 **拆分支付输入** (请输入实收金额，未付渠道留空为0)")
        
        c1, c2 = st.columns(2)
        venmo_amt = c1.number_input("📱 Venmo/Zelle ($)", min_value=0.0, step=1.0)
        cash_amt = c2.number_input("💵 现金 ($)", min_value=0.0, step=1.0)
        card_amt = c1.number_input("💳 刷卡 ($)", min_value=0.0, step=1.0)
        alipay_amt = c2.number_input("💙 支付宝 ($)", min_value=0.0, step=1.0)
        
        # 实时计算实收总额
        total_collected = venmo_amt + cash_amt + card_amt + alipay_amt
        
        st.divider()
        st.write("✨ **财务对账与小费**")
        
        # 核心升级 3：智能小费计算 (实收 - 应收)
        if expected_total > 0 and total_collected > expected_total:
            tip_amount = total_collected - expected_total
            st.success(f"🧾 **完美账单**：实收 **${total_collected:.2f}**。系统自动将溢出的 **${tip_amount:.2f}** 记为小费！")
        elif expected_total > 0 and 0 < total_collected < expected_total:
            tip_amount = 0.0
            st.warning(f"⚠️ **提醒**：实收 **${total_collected:.2f}**，低于应收票款，还差 **${(expected_total - total_collected):.2f}**。 (如为打折请忽略)")
        else:
            tip_amount = 0.0
            if total_collected > 0:
                st.success(f"🧾 实收 **${total_collected:.2f}**，金额与标准票款匹配。")
                
        # 允许手动覆写小费 (应对一些打折但又单独给了小费的复杂情况)
        override_tip = st.checkbox("手动修改小费金额 (如果有特殊情况)")
        if override_tip:
            tip_amount = st.number_input("手动输入小费($)", min_value=0.0, value=float(tip_amount))
            
        pay_note = st.text_input("备注 (如：张三等6人车，用了9折券)")
        
        if st.button("确认收账入库", type="primary"):
            if total_collected > 0:
                def save_record(method, amt):
                    # 将小费按金额比例分摊到对应的支付方式流水中
                    method_tip = amt * (tip_amount / total_collected) if total_collected > 0 else 0
                    new_ledger = pd.DataFrame({
                        '交易时间': [datetime.now().strftime("%Y-%m-%d %H:%M")],
                        '关联剧本': [script_link],
                        '支付方式': [method],
                        '入账总额($)': [amt],
                        '其中小费($)': [method_tip],
                        '备注': [pay_note]
                    })
                    st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], new_ledger], ignore_index=True)
                
                if venmo_amt > 0: save_record("Venmo/Zelle", venmo_amt)
                if cash_amt > 0: save_record("现金", cash_amt)
                if card_amt > 0: save_record("刷卡", card_amt)
                if alipay_amt > 0: save_record("支付宝", alipay_amt)
                
                st.success(f"✅ 账单已记录！共计 ${total_collected:.2f} 已按渠道拆分入库。")
            else:
                st.error("入账总额不能为 0，请检查上方填写的金额。")

    with col_pay2:
        st.subheader("流水记录与多维统计")
        if not st.session_state['ledger_db'].empty:
            search_ledger = st.text_input("🔍 搜索剧本名称或备注查账", "", key="search_l")
            display_ledger = st.session_state['ledger_db'].copy()
            
            if search_ledger:
                display_ledger = display_ledger[
                    display_ledger['关联剧本'].str.contains(search_ledger, case=False, na=False) | 
                    display_ledger['备注'].str.contains(search_ledger, case=False, na=False)
                ]
            
            st.dataframe(display_ledger, use_container_width=True)
            
            st.divider()
            st.write("📈 **财务维度汇总**")
            
            method_summary = display_ledger.groupby('支付方式').agg(
                渠道总入账=('入账总额($)', 'sum'),
                包含小费=('其中小费($)', 'sum')
            ).reset_index()
            
            total_revenue = method_summary['渠道总入账'].sum()
            total_tips = method_summary['包含小费'].sum()
            pure_revenue = total_revenue - total_tips
            
            m1, m2, m3 = st.columns(3)
            m1.metric("💰 门店总入账", f"${total_revenue:,.2f}")
            m2.metric("📊 剥离小费后净收", f"${pure_revenue:,.2f}")
            m3.metric("✨ 累计沉淀小费", f"${total_tips:,.2f}")
            
            st.dataframe(method_summary, use_container_width=True)
        else:
            st.info("暂无交易流水。")
