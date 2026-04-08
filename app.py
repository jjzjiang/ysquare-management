import streamlit as st
import pandas as pd
from datetime import datetime
import time
import re  # 核心修复：用于安全处理搜索匹配

st.set_page_config(page_title="Y Square Studio 管理系统", layout="wide")

# ==========================================
# 0. 核心数据初始化与强健兼容逻辑
# ==========================================
if 'scripts_db' not in st.session_state:
    st.session_state['scripts_db'] = pd.DataFrame(columns=['剧本名称', '人数配置', '单人价格($)', '主开DM', '日期'])
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
else:
    if '电话号码' not in st.session_state['member_db'].columns:
        st.session_state['member_db'].insert(1, '电话号码', "")

st.title("Y Square Studio 门店管理系统")
tabs = st.tabs(["📚 剧本列表", "⏰ 员工考勤", "💵 收银台", "📊 财务报表", "💎 会员管理"])

# ==========================================
# Tab 1: 剧本列表管理
# ==========================================
with tabs[0]:
    col1, col2 = st.columns([1, 2.5])
    with col1:
        st.subheader("添加剧本场次")
        with st.form("add_script_form"):
            s_name = st.text_input("剧本名称")
            s_pax = st.number_input("人数", min_value=1, value=6)
            s_price = st.number_input("单人原价 ($)", min_value=0.0, value=30.0)
            emp_list = st.session_state['employee_db']['员工姓名'].tolist()
            s_dm = st.selectbox("主开 DM", emp_list) if emp_list else st.text_input("主开 DM")
            s_date = st.date_input("首开日期")
            if st.form_submit_button("确认录入"):
                new_s = pd.DataFrame({'剧本名称':[s_name],'人数配置':[s_pax],'单人价格($)':[s_price],'主开DM':[s_dm],'日期':[s_date]})
                st.session_state['scripts_db'] = pd.concat([st.session_state['scripts_db'], new_s], ignore_index=True)
                st.rerun()
    with col2:
        st.subheader("剧本库明细 (关联流水数据)")
        display_db = st.session_state['scripts_db'].copy()
        if not st.session_state['ledger_db'].empty:
            valid_ledger = st.session_state['ledger_db'][st.session_state['ledger_db']['关联剧本'] != '会员充值']
            counts = valid_ledger.groupby('关联剧本')['交易时间'].nunique()
            display_db['累计开本(场)'] = display_db['剧本名称'].map(counts).fillna(0).astype(int)
        else:
            display_db['累计开本(场)'] = 0
            
        cols = ['剧本名称', '累计开本(场)', '人数配置', '单人价格($)', '主开DM', '日期']
        display_db = display_db[cols]
        
        search_script = st.text_input("🔍 搜索剧本名称或主开 DM", "", key="search_s")
        if search_script:
            mask = display_db['剧本名称'].str.contains(search_script, case=False, na=False) | display_db['主开DM'].str.contains(search_script, case=False, na=False)
            st.dataframe(display_db[mask], use_container_width=True)
            st.info("💡 清空搜索框即可进入修改模式。")
        else:
            st.caption("✨ **直接编辑模式**：双击单元格修改。`累计开本(场)` 由系统自动关联计算。")
            edited_db = st.data_editor(
                display_db, 
                num_rows="dynamic", 
                use_container_width=True, 
                key="ed_s",
                column_config={"累计开本(场)": st.column_config.NumberColumn(disabled=True)}
            )
            st.session_state['scripts_db'] = edited_db.drop(columns=['累计开本(场)'], errors='ignore')

# ==========================================
# Tab 2: 员工考勤与薪资
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
# Tab 3: 收银台
# ==========================================
with tabs[2]:
    st.subheader("📈 门店现金流监控大盘")
    display_ledger = st.session_state['ledger_db']
    
    if not display_ledger.empty:
        actual_cash_in = display_ledger[display_ledger['支付方式'] != '会员余额']['入账总额($)'].sum()
        total_tips = display_ledger['其中小费($)'].sum()
        net_cash = actual_cash_in - total_tips
        
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 门店实际现金流入 (含充值)", f"${actual_cash_in:,.2f}")
        m2.metric("📊 剥离小费后净现金", f"${net_cash:,.2f}")
        m3.metric("✨ 待发小费池", f"${total_tips:,.2f}")
    else:
        st.info("今日暂无进账记录。")
    
    st.divider()

    c_p1, c_p2 = st.columns([1, 1.4])
    with c_p1:
        st.subheader("新建收银账单")
        s_opts = st.session_state['scripts_db']['剧本名称'].unique().tolist()
        
        if not s_opts:
            st.warning("请先在 Tab 1 录入剧本！")
        else:
            sel_s = st.selectbox("关联剧本场次", s_opts)
            s_data = st.session_state['scripts_db'][st.session_state['scripts_db']['剧本名称']==sel_s].iloc[-1]
            single_price = float(s_data['单人价格($)'])
            pax = int(s_data['人数配置'])
            base_price = single_price * pax
            h_dm = s_data['主开DM']
            
            st.info(f"💡 **剧本标准价**：单人 ${single_price:.2f} × {pax}人 = 满编标准总价 **${base_price:.2f}**")
            st.divider()

            st.write("💰 **外部拆分支付输入 (未付渠道留空)**")
            col_u1, col_u2 = st.columns(2)
            v_usd = col_u1.number_input("📱 Venmo ($)", min_value=0.0, step=1.0)
            z_usd = col_u2.number_input("💸 Zelle ($)", min_value=0.0, step=1.0)
            tr_usd = col_u1.number_input("🏦 转账 ($)", min_value=0.0, step=1.0)
            c_usd = col_u2.number_input("💵 现金 ($)", min_value=0.0, step=1.0)
            
            col_u3, col_u4 = st.columns(2)
            ex_rate = col_u3.number_input("汇率 (1 USD = ? RMB)", value=7.20, step=0.05)
            ali_rmb = col_u3.number_input("💙 支付宝 (¥)", min_value=0.0, step=10.0)
            wx_rmb = col_u4.number_input("💚 微信 (¥)", min_value=0.0, step=10.0)
            
            external_total = v_usd + z_usd + c_usd + tr_usd + (ali_rmb/ex_rate if ex_rate > 0 else 0) + (wx_rmb/ex_rate if ex_rate > 0 else 0)

            st.divider()
            st.write("💎 **选择会员消费 (自动打折与防超扣)**")
            m_list = st.session_state['member_db']['会员姓名'].tolist()
            selected_members = st.multiselect("🔍 本车有哪些会员？(支持多选)", m_list)
            
            member_deductions = {}
            member_total = 0.0
            expected_member_revenue = 0.0 
            total_explicit_member_tip = 0.0 
            
            if selected_members:
                for idx, m in enumerate(selected_members):
                    st.markdown(f"**👤 会员：{m}**")
                    m_info = st.session_state['member_db'][st.session_state['member_db']['会员姓名']==m].iloc[-1]
                    discount = float(m_info['折扣率'])
                    balance = float(m_info['当前余额($)'])
                    discounted_single = single_price * discount
                    expected_member_revenue += discounted_single
                    
                    st.caption(f"当前余额: ${balance:.2f} | 专属折扣: {discount*100:.0f}折 | **折后应付票价: ${discounted_single:.2f}**")
                    
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        tip_mode = st.radio("添加小费", ["无", "固定金额 ($)", "百分比 (%)"], horizontal=True, key=f"tmode_{m}")
                    with col_t2:
                        m_tip = 0.0
                        if tip_mode == "固定金额 ($)":
                            m_tip = st.number_input("金额 ($)", min_value=0.0, step=1.0, value=5.0, key=f"tval_{m}")
                        elif tip_mode == "百分比 (%)":
                            m_pct = st.slider("比例 (%)", 0, 50, 15, 5, key=f"tpct_{m}")
                            m_tip = discounted_single * (m_pct / 100)
                            st.write(f"小费计算得: ${m_tip:.2f}")
                            
                    total_explicit_member_tip += m_tip
                    target_deduct = discounted_single + m_tip
                    
                    st.markdown(f"👉 **该会员本次消费总计 (票价 + 小费): ${target_deduct:.2f}**")
                    deduct_amt = st.number_input(f"💳 实际从 {m} 余额扣除", min_value=0.0, max_value=max(balance, 0.0), value=float(min(target_deduct, balance)), step=1.0, key=f"deduct_{m}_{target_deduct}")
                    
                    if deduct_amt > 0:
                        member_deductions[m] = deduct_amt
                        member_total += deduct_amt
                    
                    if idx < len(selected_members) - 1:
                        st.write("---")
                        
            st.divider()
            st.write("✨ **财务对账与结算**")
            
            external_pax = max(0, pax - len(selected_members))
            expected_external_revenue = external_pax * single_price
            actual_expected_total = expected_external_revenue + expected_member_revenue
            
            total_collected = external_total + member_total
            
            extra_overflow = total_collected - actual_expected_total - total_explicit_member_tip
            extra_overflow_tip = max(0, extra_overflow)
            system_calculated_tip = total_explicit_member_tip + extra_overflow_tip
            
            st.caption(f"📊 本车包含 {len(selected_members)} 位会员，动态折后应收总款应为：**${actual_expected_total:.2f}**")
            
            if system_calculated_tip > 0:
                st.success(f"🧾 最终实收 **${total_collected:.2f}**。包含系统计算总小费: **${system_calculated_tip:.2f}**")
            else:
                st.info(f"🧾 最终实收 **${total_collected:.2f}**")
                
            if total_collected < actual_expected_total:
                st.warning(f"⚠️ 实收金额低于本车应收标准！(若是打折券/免单/未付款情况请忽略此提示)。")
                    
            if st.checkbox("手动覆写系统计算的总小费金额"):
                final_tip_amount = st.number_input("输入最终总小费 ($)", value=float(system_calculated_tip), min_value=0.0)
            else:
                final_tip_amount = system_calculated_tip
                
            t_dms = st.multiselect("🧑‍🏫 选择分配小费的 DM", emp_list, default=[h_dm] if h_dm in emp_list else [])
            note = st.text_input("账单备注", key="m_note")
            
            if st.button("🚀 确认收账入库", type="primary", use_container_width=True):
                if total_collected > 0:
                    if final_tip_amount > 0 and not t_dms:
                        st.error("⚠️ 产生了小费，请在上方选择【分配小费的 DM】！")
                        st.stop()
                    
                    for m, amt in member_deductions.items():
                        st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==m, '当前余额($)'] -= amt
                        m_tip = amt * (final_tip_amount / total_collected) if total_collected > 0 else 0
                        m_log = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':[sel_s],'主开DM':[h_dm],'支付方式':['会员余额'],'入账总额($)':[amt],'其中小费($)':[m_tip],'备注':[f"会员 [{m}] 扣款 | {note}"]})
                        st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], m_log], ignore_index=True)

                    def save_ext(method, amt, r=None):
                        method_tip = amt * (final_tip_amount / total_collected) if total_collected > 0 else 0
                        f_note = f"{note} [{method}收 ¥{r:.2f}]".strip() if r else note
                        ext_log = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':[sel_s],'主开DM':[h_dm],'支付方式':[method],'入账总额($)':[amt],'其中小费($)':[method_tip],'备注':[f_note]})
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
                        
                    st.toast("✅ 结算成功！账款及小费已同步。", icon="🎉")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("入账总额不能为 0！")

    with c_p2:
        st.subheader("流水明细与修改")
        search_ledger = st.text_input("🔍 搜索查账 (清空搜索框以进入编辑模式)", "", key="search_l")
        
        if search_ledger:
            mask = st.session_state['ledger_db']['关联剧本'].str.contains(search_ledger, case=False, na=False) | st.session_state['ledger_db']['备注'].str.contains(search_ledger, case=False, na=False) | st.session_state['ledger_db']['主开DM'].str.contains(search_ledger, case=False, na=False)
            st.dataframe(st.session_state['ledger_db'][mask], use_container_width=True, height=550)
        else:
            st.session_state['ledger_db'] = st.data_editor(st.session_state['ledger_db'], num_rows="dynamic", use_container_width=True, height=550, key="ed_l")

# ==========================================
# Tab 4: 经营报表
# ==========================================
with tabs[3]:
    st.header("📊 财务损益动态分析")
    
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        rent = st.number_input("🏠 设定此筛选期间的房租/固定支出 ($)", value=7000.0, step=100.0)
    with col_d2:
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        date_range = st.date_input("📅 选择财务统计范围 (开始与结束日期)", value=(start_of_month, today))
        
    st.divider()

    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        st.stop()

    l_df = st.session_state['ledger_db'].copy()
    a_df = st.session_state['attendance_db'].copy()
    
    cash_rev = 0.0
    service_rev = 0.0
    tips = 0.0
    wages = 0.0

    if not l_df.empty:
        l_df['交易时间_dt'] = pd.to_datetime(l_df['交易时间']).dt.date
        mask_l = (l_df['交易时间_dt'] >= start_date) & (l_df['交易时间_dt'] <= end_date)
        filtered_l = l_df[mask_l]
        
        cash_rev = filtered_l[filtered_l['支付方式'] != '会员余额']['入账总额($)'].sum()
        service_rev = filtered_l[filtered_l['关联剧本'] != '会员充值']['入账总额($)'].sum()
        
    if not a_df.empty and '记录日期' in a_df.columns:
        a_df['记录日期_dt'] = pd.to_datetime(a_df['记录日期']).dt.date
        mask_a = (a_df['记录日期_dt'] >= start_date) & (a_df['记录日期_dt'] <= end_date)
        filtered_a = a_df[mask_a]
        tips = filtered_a[filtered_a['工作类型'] == '专属小费']['当日薪资($)'].sum()
        wages = filtered_a[filtered_a['工作类型'] != '专属小费']['当日薪资($)'].sum()

    profit = cash_rev - wages - tips - rent

    if cash_rev > 0:
        wages_pct = (wages / cash_rev) * 100
        tips_pct = (tips / cash_rev) * 100
        rent_pct = (rent / cash_rev) * 100
        profit_pct = (profit / cash_rev) * 100
    else:
        wages_pct = tips_pct = rent_pct = profit_pct = 0.0

    st.subheader(f"📊 {start_date} 至 {end_date} 核心财务指标")
    st.info("💡 财务引擎已启动【防重复计算】：会员充值款将直接计入现金流，后续会员打本扣除余额的交易将被视为内部抵扣，不重复计算现金营收，确保报表与实际账户入账 100% 匹配。")
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("区间实际现金流入", f"${cash_rev:,.2f}", "包含充值 / 剔除余额抵扣", delta_color="off")
    m2.metric("员工时薪支出", f"${wages:,.2f}", f"占现金流: {wages_pct:.1f}%", delta_color="inverse")
    m3.metric("DM专属小费支出", f"${tips:,.2f}", f"占现金流: {tips_pct:.1f}%", delta_color="inverse")
    m4.metric("固定房租成本", f"${rent:,.2f}", f"占现金流: {rent_pct:.1f}%", delta_color="inverse")
    m5.metric("区间净利润", f"${profit:,.2f}", f"净利润率: {profit_pct:.1f}%")

    st.caption(f"*(补充参考：此区间内门店纯剧本打本产值为 **${service_rev:,.2f}**，不含充值，包含会员余额抵扣)*")

    st.divider()
    st.write("📝 **期间明细参考**")
    c_sub1, c_sub2 = st.columns(2)
    with c_sub1:
        st.caption("🧾 流水入账记录")
        if not l_df.empty and not filtered_l.empty:
            st.dataframe(filtered_l[['交易时间', '关联剧本', '支付方式', '入账总额($)']], use_container_width=True)
        else:
            st.info("期间无入账记录。")
    with c_sub2:
        st.caption("🧑‍🏫 员工薪资产生")
        if not a_df.empty and not filtered_a.empty:
            st.dataframe(filtered_a[['记录日期', '员工姓名', '工作类型', '当日薪资($)']], use_container_width=True)
        else:
            st.info("期间无人工支出记录。")

# ==========================================
# Tab 5: 会员记录 (智能模糊搜索修复版)
# ==========================================
with tabs[4]:
    m_col1, m_col2 = st.columns([1, 2])
    with m_col1:
        st.subheader("👤 会员业务")
        m_action = st.radio("选择业务类型", ["🔄 老会员充值 (续费)", "✨ 新会员开卡"], horizontal=True)
        
        if m_action == "🔄 老会员充值 (续费)":
            m_list = st.session_state['member_db']['会员姓名'].tolist()
            if m_list:
                r_name = st.selectbox("选择要续费的会员", m_list)
                r_recharge = st.number_input("续费金额 ($)", min_value=0.0, step=50.0, key="r_amt")
                r_pay = st.selectbox("支付方式", ["Venmo", "Zelle", "现金", "转账", "微信", "支付宝"], key="r_pay")
                
                if st.button("🚀 确认续费入账", type="primary"):
                    if r_recharge > 0:
                        st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==r_name, '当前余额($)'] += r_recharge
                        st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==r_name, '累计充值($)'] += r_recharge
                        new_r = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':['会员充值'],'主开DM':['-'],'支付方式':[r_pay],'入账总额($)':[r_recharge],'其中小费($)':[0.0],'备注':[f"老会员续费: {r_name}"]})
                        st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], new_r], ignore_index=True)
                        st.toast(f"{r_name} 续费成功！已自动计入总营收。", icon="💰")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("请输入有效金额")
            else:
                st.warning("暂无会员记录，请先使用新会员开卡功能。")
                
        else:
            m_name = st.text_input("新会员姓名")
            m_phone = st.text_input("联系电话 (选填)", placeholder="方便后续短信联系或防止重名")
            m_recharge = st.number_input("首充金额 ($)", min_value=0.0, step=50.0)
            m_discount = st.selectbox("会员折扣率", [1.0, 0.9, 0.88, 0.8, 0.75], format_func=lambda x: f"{x*100:.0f}折" if x<1 else "无折扣")
            m_pay = st.selectbox("支付方式", ["Venmo", "Zelle", "现金", "转账", "微信", "支付宝"], key="n_pay")
            
            if st.button("🚀 确认开卡入账", type="primary"):
                if m_name:
                    if m_name in st.session_state['member_db']['会员姓名'].values:
                        st.error("该会员姓名已存在！请切换到【老会员充值 (续费)】，或在姓名后添加字母以作区分。")
                    else:
                        new_m = pd.DataFrame({'会员姓名':[m_name], '电话号码':[m_phone], '当前余额($)':[m_recharge],'折扣率':[m_discount],'累计充值($)':[m_recharge],'入会日期':[datetime.now().strftime("%Y-%m-%d")]})
                        st.session_state['member_db'] = pd.concat([st.session_state['member_db'], new_m], ignore_index=True)
                        if m_recharge > 0:
                            new_r = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':['会员充值'],'主开DM':['-'],'支付方式':[m_pay],'入账总额($)':[m_recharge],'其中小费($)':[0.0],'备注':[f"新会员开卡: {m_name}"]})
                            st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], new_r], ignore_index=True)
                        st.toast(f"欢迎新会员: {m_name}！首充已计入营收。", icon="💎")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error("请输入会员姓名")

    with m_col2:
        st.subheader("📋 会员名册与消费记录")
        search_m = st.text_input("🔍 搜索会员 (支持姓名或电话搜索)", "")
        m_display = st.session_state['member_db'].copy()
        
        if search_m:
            mask = m_display['会员姓名'].str.contains(search_m, case=False, na=False) | m_display['电话号码'].str.contains(search_m, case=False, na=False)
            m_display = m_display[mask]
        
        st.caption("✨ 双击表格可直接修改会员资料 (包括补填老会员的电话号码)。")
        m_display = st.data_editor(m_display, use_container_width=True, key="ed_m")
        st.session_state['member_db'] = m_display
        
        st.divider()
        st.subheader("📖 会员历史消费明细")
        # 核心修复区：利用精准提取的名字列表，进行正则安全搜索
        if search_m and not m_display.empty and not st.session_state['ledger_db'].empty:
            matched_names = m_display['会员姓名'].tolist()
            # 无论他是开卡、续费还是打本，只要备注里带了他的名字，全部提取出来
            safe_pattern = "|".join([re.escape(name) for name in matched_names])
            m_logs = st.session_state['ledger_db'][st.session_state['ledger_db']['备注'].str.contains(safe_pattern, regex=True, na=False)]
            
            st.write("正在查看匹配会员的流水记录：")
            # 自动按时间倒序排列，最新交易在最上面
            st.dataframe(m_logs[['交易时间', '关联剧本', '支付方式', '入账总额($)', '备注']].sort_values('交易时间', ascending=False), use_container_width=True)
        elif search_m and m_display.empty:
            st.warning("未找到匹配的会员。")
