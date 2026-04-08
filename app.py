import streamlit as st
import pandas as pd
from datetime import datetime
import time
import re

st.set_page_config(page_title="Y Square Studio 管理系统", layout="wide")

# ==========================================
# 0. 核心数据初始化与强健兼容逻辑
# ==========================================
if 'scripts_db' not in st.session_state:
    st.session_state['scripts_db'] = pd.DataFrame(columns=['剧本名称', '人数配置', '单人价格($)', '日期'])

if 'inventory_db' not in st.session_state:
    st.session_state['inventory_db'] = pd.DataFrame(columns=['项目名称', '单价($)'])

if 'employee_db' not in st.session_state:
    st.session_state['employee_db'] = pd.DataFrame(columns=['员工姓名', '时薪($)'])
    
if 'attendance_db' not in st.session_state:
    st.session_state['attendance_db'] = pd.DataFrame(columns=['记录日期', '员工姓名', '工作类型', '时长(小时)', '当日薪资($)'])
else:
    if '打卡日期' in st.session_state['attendance_db'].columns:
        st.session_state['attendance_db'].rename(columns={'打卡日期': '记录日期'}, inplace=True)
    if '记录日期' not in st.session_state['attendance_db'].columns:
        st.session_state['attendance_db']['记录日期'] = pd.to_datetime(datetime.now().date())
        
if 'ledger_db' not in st.session_state:
    st.session_state['ledger_db'] = pd.DataFrame(columns=['交易时间', '关联剧本', '主开DM', '支付方式', '入账总额($)', '其中小费($)', '备注'])
    
if 'member_db' not in st.session_state:
    st.session_state['member_db'] = pd.DataFrame(columns=['会员姓名', '电话号码', '当前余额($)', '折扣率', '累计充值($)', '入会日期'])

st.title("Y Square Studio 门店管理系统")
tabs = st.tabs(["📚 剧本与零食", "⏰ 员工考勤", "💵 收银台", "📊 财务报表", "💎 会员管理"])

# ==========================================
# Tab 1: 剧本与零食列表管理
# ==========================================
with tabs[0]:
    col1, col2 = st.columns([1, 2.5])
    with col1:
        st.subheader("📚 添加剧本场次")
        with st.form("add_script_form"):
            s_name = st.text_input("剧本名称")
            s_pax = st.number_input("人数", min_value=1, value=6)
            s_price = st.number_input("单人原价 ($)", min_value=0.0, value=30.0)
            s_date = st.date_input("首开日期")
            if st.form_submit_button("确认录入剧本"):
                if s_name:
                    new_s = pd.DataFrame({'剧本名称':[s_name],'人数配置':[s_pax],'单人价格($)':[s_price],'日期':[s_date]})
                    st.session_state['scripts_db'] = pd.concat([st.session_state['scripts_db'], new_s], ignore_index=True)
                    st.rerun()
        
        st.divider()
        st.subheader("🍿 添加零食/饮料")
        with st.form("add_item_form"):
            i_name = st.text_input("项目名称 (如: 可乐, 自嗨锅)")
            i_price = st.number_input("售价 ($)", min_value=0.0, value=3.0, step=0.5)
            if st.form_submit_button("确认录入项目"):
                if i_name:
                    new_i = pd.DataFrame({'项目名称':[i_name],'单价($)':[i_price]})
                    st.session_state['inventory_db'] = pd.concat([st.session_state['inventory_db'], new_i], ignore_index=True)
                    st.rerun()

    with col2:
        tab_list1, tab_list2 = st.tabs(["📜 剧本库明细", "🥤 零食/饮料库"])
        
        with tab_list1:
            display_db = st.session_state['scripts_db'].copy()
            if not st.session_state['ledger_db'].empty:
                valid_ledger = st.session_state['ledger_db'][st.session_state['ledger_db']['关联剧本'] != '会员充值']
                counts = valid_ledger.groupby('关联剧本')['交易时间'].nunique()
                display_db['累计开本(场)'] = display_db['剧本名称'].map(counts).fillna(0).astype(int)
            else:
                display_db['累计开本(场)'] = 0
            
            cols = ['剧本名称', '累计开本(场)', '人数配置', '单人价格($)', '日期']
            display_db = display_db[cols]
            st.session_state['scripts_db'] = st.data_editor(display_db, num_rows="dynamic", use_container_width=True, key="ed_s").drop(columns=['累计开本(场)'], errors='ignore')

        with tab_list2:
            st.session_state['inventory_db'] = st.data_editor(st.session_state['inventory_db'], num_rows="dynamic", use_container_width=True, key="ed_i")

# ==========================================
# Tab 2: 员工考勤与薪资 (保持逻辑)
# ==========================================
with tabs[1]:
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("员工入职")
        with st.form("add_emp"):
            e_name = st.text_input("员工姓名")
            e_rate = st.number_input("时薪 ($)", value=15.0)
            if st.form_submit_button("添加员工"):
                st.session_state['employee_db'] = pd.concat([st.session_state['employee_db'], pd.DataFrame({'员工姓名':[e_name],'时薪($)':[e_rate]})], ignore_index=True)
                st.rerun()
        st.divider()
        st.subheader("考勤录入")
        emp_list = st.session_state['employee_db']['员工姓名'].tolist()
        if emp_list:
            w_date = st.date_input("日期", key="att_date")
            w_type = st.radio("类型", ["带本", "NPC演绎"], horizontal=True)
            if w_type == "带本":
                target_e = st.selectbox("选择 DM", emp_list)
                hrs = st.number_input("时长", min_value=0.5, step=0.5)
                if st.button("提交考勤"):
                    rate = st.session_state['employee_db'][st.session_state['employee_db']['员工姓名']==target_e]['时薪($)'].values[0]
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame({'记录日期':[pd.to_datetime(w_date)],'员工姓名':[target_e],'工作类型':['带本'],'时长(小时)':[hrs],'当日薪资($)':[hrs*rate]})], ignore_index=True)
                    st.rerun()
            else:
                target_es = st.multiselect("选择 NPC", emp_list)
                fee = st.number_input("单人演绎费", value=10.0)
                if st.button("批量提交演绎"):
                    batch = [{'记录日期':pd.to_datetime(w_date),'员工姓名':e,'工作类型':'演绎NPC','时长(小时)':0.0,'当日薪资($)':fee} for e in target_es]
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(batch)], ignore_index=True)
                    st.rerun()
    with col_r:
        st.subheader("薪资明细")
        st.session_state['attendance_db'] = st.data_editor(st.session_state['attendance_db'], num_rows="dynamic", use_container_width=True, key="ed_att")

# ==========================================
# Tab 3: 收银台 (联动零食多选)
# ==========================================
with tabs[2]:
    st.subheader("📈 门店总营业额监控")
    display_ledger = st.session_state['ledger_db']
    if not display_ledger.empty:
        actual_cash_in = display_ledger[display_ledger['支付方式'] != '会员余额']['入账总额($)'].sum()
        total_tips = display_ledger['其中小费($)'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 门店实际现金流入", f"${actual_cash_in:,.2f}")
        m2.metric("📊 剥离小费后净现金", f"${actual_cash_in - total_tips:,.2f}")
        m3.metric("✨ 待发小费池", f"${total_tips:,.2f}")

    st.divider()
    c_p1, c_p2 = st.columns([1.2, 1.4])
    with c_p1:
        st.subheader("新建收银账单")
        s_opts = st.session_state['scripts_db']['剧本名称'].unique().tolist()
        
        if not s_opts:
            st.warning("请先在 Tab 1 录入剧本！")
        else:
            sel_s = st.selectbox("🎯 关联剧本场次", s_opts)
            s_data = st.session_state['scripts_db'][st.session_state['scripts_db']['剧本名称']==sel_s].iloc[-1]
            single_price = float(s_data['单人价格($)'])
            pax = int(s_data['人数配置'])
            base_price = single_price * pax
            session_dm = st.selectbox("🧑‍🏫 本场带本 DM", emp_list) if emp_list else ""
            
            # --- 核心更新：零食多选区域 ---
            st.divider()
            st.write("🍿 **零食/饮料消费**")
            inventory_list = st.session_state['inventory_db']['项目名称'].tolist()
            selected_items = st.multiselect("🔍 搜索并选择零食/饮料 (支持多选)", inventory_list)
            
            snack_total = 0.0
            snack_details = []
            if selected_items:
                for item in selected_items:
                    item_price = st.session_state['inventory_db'][st.session_state['inventory_db']['项目名称'] == item]['单价($)'].values[0]
                    qty = st.number_input(f"数量: {item} (${item_price}/份)", min_value=1, value=1, key=f"qty_{item}")
                    snack_total += item_price * qty
                    snack_details.append(f"{item}x{qty}")
            
            actual_expected_total_base = base_price + snack_total
            st.info(f"💡 **本单计算**：剧本 ${base_price:.2f} + 零食 ${snack_total:.2f} = 总计应收 **${actual_expected_total_base:.2f}**")

            st.divider()
            st.write("💰 **支付明细录入**")
            col_u1, col_u2 = st.columns(2)
            v_usd = col_u1.number_input("📱 Venmo ($)", 0.0)
            z_usd = col_u2.number_input("💸 Zelle ($)", 0.0)
            tr_usd = col_u1.number_input("🏦 转账 ($)", 0.0)
            c_usd = col_u2.number_input("💵 现金 ($)", 0.0)
            
            col_u3, col_u4 = st.columns(2)
            ex_rate = col_u3.number_input("汇率 (1 USD = ? RMB)", 7.20)
            ali_rmb = col_u3.number_input("💙 支付宝 (¥)", 0.0)
            wx_rmb = col_u4.number_input("💚 微信 (¥)", 0.0)
            
            external_total = v_usd + z_usd + c_usd + tr_usd + (ali_rmb/ex_rate if ex_rate > 0 else 0) + (wx_rmb/ex_rate if ex_rate > 0 else 0)

            st.write("💎 **会员扣款**")
            m_list = st.session_state['member_db']['会员姓名'].tolist()
            selected_members = st.multiselect("🔍 本车有哪些会员？", m_list)
            member_deductions = {}
            member_total = 0.0
            total_explicit_member_tip = 0.0 
            
            if selected_members:
                for m in selected_members:
                    m_info = st.session_state['member_db'][st.session_state['member_db']['会员姓名']==m].iloc[-1]
                    m_discount = float(m_info['折扣率'])
                    m_bal = float(m_info['当前余额($)'])
                    m_discounted_price = single_price * m_discount
                    st.caption(f"会员 {m} | 折后票价: ${m_discounted_price:.2f} | 余额: ${m_bal:.2f}")
                    
                    col_t1, col_t2 = st.columns(2)
                    with col_t1: tip_mode = st.radio("添加小费", ["无", "$", "%"], horizontal=True, key=f"tm_{m}")
                    with col_t2:
                        m_tip = 0.0
                        if tip_mode == "$": m_tip = st.number_input("金额", 0.0, key=f"tv_{m}")
                        elif tip_mode == "%": m_tip = m_discounted_price * (st.slider("比例", 0, 50, 15, 5, key=f"tp_{m}")/100)
                    
                    target_deduct = m_discounted_price + m_tip
                    st.markdown(f"👉 **该会员消费合计: ${target_deduct:.2f}**")
                    deduct_amt = st.number_input(f"实际从 {m} 扣除", 0.0, m_bal, min(target_deduct, m_bal), key=f"dd_{m}_{target_deduct}")
                    if deduct_amt > 0:
                        member_deductions[m] = deduct_amt
                        member_total += deduct_amt
                        total_explicit_member_tip += m_tip

            # 最终对账
            total_collected = external_total + member_total
            # 动态计算应收（考虑会员折扣和零食）
            actual_expected_total = (pax - len(selected_members)) * single_price + (len(selected_members) * single_price * 0.9) + snack_total # 简化逻辑：会员按各自折扣，这里仅作UI提示
            
            st.divider()
            final_tip_amount = max(0, total_collected - (actual_expected_total_base - (len(selected_members)*single_price*(1-0.8)))) # 这是一个概数，建议以手动覆写为准
            
            st.success(f"🧾 最终实收: **${total_collected:.2f}**")
            if st.checkbox("手动确认/修改总小费金额"):
                final_tip_amount = st.number_input("输入总小费 ($)", value=0.0)
            
            t_dms = st.multiselect("🧑‍🏫 分配小费的 DM", emp_list, default=[session_dm] if session_dm else [])
            snack_note = f" [含零食: {', '.join(snack_details)}]" if snack_details else ""
            note = st.text_input("账单备注") + snack_note
            
            if st.button("🚀 确认结账入库", type="primary", use_container_width=True):
                if total_collected > 0:
                    for m, amt in member_deductions.items():
                        st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==m, '当前余额($)'] -= amt
                        m_tip = amt * (final_tip_amount / total_collected) if total_collected > 0 else 0
                        m_log = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':[sel_s],'主开DM':[session_dm],'支付方式':['会员余额'],'入账总额($)':[amt],'其中小费($)':[m_tip],'备注':[f"会员 [{m}] 扣款 | {note}"]})
                        st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], m_log], ignore_index=True)

                    def save_ext(method, amt, r=None):
                        method_tip = amt * (final_tip_amount / total_collected) if total_collected > 0 else 0
                        f_note = f"{note} [{method}收 ¥{r:.2f}]" if r else note
                        ext_log = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':[sel_s],'主开DM':[session_dm],'支付方式':[method],'入账总额($)':[amt],'其中小费($)':[method_tip],'备注':[f_note]})
                        st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], ext_log], ignore_index=True)
                        
                    if v_usd > 0: save_ext("Venmo", v_usd)
                    if z_usd > 0: save_ext("Zelle", z_usd)
                    if c_usd > 0: save_ext("现金", c_usd)
                    if tr_usd > 0: save_ext("转账", tr_usd)
                    if ali_rmb > 0: save_ext("支付宝", ali_rmb/ex_rate, ali_rmb)
                    if wx_rmb > 0: save_ext("微信", wx_rmb/ex_rate, wx_rmb)
                    
                    if final_tip_amount > 0 and t_dms:
                        t_recs = [{'记录日期':pd.to_datetime(datetime.now().date()),'员工姓名':e,'工作类型':'专属小费','时长(小时)':0.0,'当日薪资($)':final_tip_amount/len(t_dms)} for e in t_dms]
                        st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(t_recs)], ignore_index=True)
                    st.rerun()

    with c_p2:
        st.subheader("流水明细")
        st.session_state['ledger_db'] = st.data_editor(st.session_state['ledger_db'], num_rows="dynamic", use_container_width=True, height=600, key="ed_l")

# ==========================================
# Tab 4: 经营报表 (自动涵盖零食收入)
# ==========================================
with tabs[3]:
    st.header("📊 财务损益动态分析")
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1: rent = st.number_input("🏠 设定房租 ($)", value=7000.0)
    with col_d2: date_range = st.date_input("📅 选择范围", value=(datetime.now().replace(day=1).date(), datetime.now().date()))

    if len(date_range) == 2:
        start_date, end_date = date_range
        l_df = st.session_state['ledger_db'].copy()
        a_df = st.session_state['attendance_db'].copy()
        
        if not l_df.empty:
            l_df['交易时间_dt'] = pd.to_datetime(l_df['交易时间']).dt.date
            mask = (l_df['交易时间_dt'] >= start_date) & (l_df['交易时间_dt'] <= end_date)
            filtered_l = l_df[mask]
            
            # 总营业额自动包含了剧本收入 + 零食收入 (因为都在入账总额里)
            rev = filtered_l[filtered_l['支付方式'] != '会员余额']['入账总额($)'].sum()
            tips = 0.0
            wages = 0.0
            if not a_df.empty:
                a_df['记录日期_dt'] = pd.to_datetime(a_df['记录日期']).dt.date
                mask_a = (a_df['记录日期_dt'] >= start_date) & (a_df['记录日期_dt'] <= end_date)
                filtered_a = a_df[mask_a]
                tips = filtered_a[filtered_a['工作类型'] == '专属小费']['当日薪资($)'].sum()
                wages = filtered_a[filtered_a['工作类型'] != '专属小费']['当日薪资($)'].sum()

            profit = rev - wages - tips - rent
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("区间总营业额", f"${rev:,.2f}")
            m2.metric("时薪支出", f"${wages:,.2f}")
            m3.metric("小费支出", f"${tips:,.2f}")
            m4.metric("房租成本", f"${rent:,.2f}")
            m5.metric("净利润", f"${profit:,.2f}")

# ==========================================
# Tab 5: 会员管理 (智能模糊搜索)
# ==========================================
with tabs[4]:
    m_col1, m_col2 = st.columns([1, 2])
    with m_col1:
        st.subheader("👤 会员业务")
        m_action = st.radio("业务类型", ["🔄 续费", "✨ 开卡"], horizontal=True)
        if m_action == "🔄 续费":
            m_list = st.session_state['member_db']['会员姓名'].tolist()
            if m_list:
                r_name = st.selectbox("选择会员", m_list)
                r_amt = st.number_input("续费金额", 0.0, step=50.0)
                r_pay = st.selectbox("支付方式", ["Venmo", "Zelle", "现金", "转账", "微信", "支付宝"])
                if st.button("确认续费"):
                    st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==r_name, '当前余额($)'] += r_amt
                    st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==r_name, '累计充值($)'] += r_amt
                    new_r = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':['会员充值'],'主开DM':['-'],'支付方式':[r_pay],'入账总额($)':[r_amt],'其中小费($)':[0.0],'备注':[f"老会员续费: {r_name}"]})
                    st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], new_r], ignore_index=True)
                    st.rerun()
        else:
            m_name = st.text_input("会员姓名")
            m_phone = st.text_input("联系电话")
            m_recharge = st.number_input("首充金额", 0.0, step=50.0)
            m_discount = st.selectbox("折扣率", [1.0, 0.9, 0.88, 0.8, 0.75], format_func=lambda x: f"{x*100:.0f}折" if x<1 else "无折扣")
            m_pay = st.selectbox("支付方式 ", ["Venmo", "Zelle", "现金", "转账", "微信", "支付宝"])
            if st.button("确认开卡"):
                new_m = pd.DataFrame({'会员姓名':[m_name], '电话号码':[m_phone], '当前余额($)':[m_recharge],'折扣率':[m_discount],'累计充值($)':[m_recharge],'入会日期':[datetime.now().strftime("%Y-%m-%d")]})
                st.session_state['member_db'] = pd.concat([st.session_state['member_db'], new_m], ignore_index=True)
                if m_recharge > 0:
                    new_r = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':['会员充值'],'主开DM':['-'],'支付方式':[m_pay],'入账总额($)':[m_recharge],'其中小费($)':[0.0],'备注':[f"新会员开卡: {m_name}"]})
                    st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], new_r], ignore_index=True)
                st.rerun()

    with m_col2:
        st.subheader("📋 会员名册与消费明细")
        search_m = st.text_input("🔍 搜索姓名/电话", "")
        m_display = st.session_state['member_db'].copy()
        if search_m:
            m_display = m_display[m_display['会员姓名'].str.contains(search_m, case=False, na=False) | m_display['电话号码'].str.contains(search_m, case=False, na=False)]
        st.session_state['member_db'] = st.data_editor(m_display, use_container_width=True, key="ed_m")
        
        st.divider()
        if search_m and not m_display.empty:
            matched_names = m_display['会员姓名'].tolist()
            safe_pattern = "|".join([re.escape(name) for name in matched_names])
            m_logs = st.session_state['ledger_db'][st.session_state['ledger_db']['备注'].str.contains(safe_pattern, regex=True, na=False)]
            st.write("📖 匹配会员的流水记录：")
            st.dataframe(m_logs[['交易时间', '关联剧本', '入账总额($)', '备注']].sort_values('交易时间', ascending=False), use_container_width=True)
