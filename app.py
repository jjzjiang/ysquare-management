import streamlit as st
import pandas as pd
from datetime import datetime
import time
import re

st.set_page_config(page_title="Y Square Studio 管理系统 (V5.01)", layout="wide")

# ==========================================
# 0. 核心数据初始化 (V5.01 稳定版)
# ==========================================
if 'scripts_db' not in st.session_state:
    st.session_state['scripts_db'] = pd.DataFrame(columns=['剧本名称', '人数配置', '单人价格($)', '日期'])
else:
    if '主开DM' in st.session_state['scripts_db'].columns:
        st.session_state['scripts_db'] = st.session_state['scripts_db'].drop(columns=['主开DM'])

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
else:
    if '电话号码' not in st.session_state['member_db'].columns:
        st.session_state['member_db'].insert(1, '电话号码', "")

st.title("Y Square Studio 门店管理系统 [V5.01]")
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
                    st.toast("剧本已录入！", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
        
        st.divider()
        st.subheader("🍿 添加零食/饮料")
        with st.form("add_item_form"):
            i_name = st.text_input("项目名称 (如: 可乐, 薯片)")
            i_price = st.number_input("售价 ($)", min_value=0.0, value=3.0, step=0.5)
            if st.form_submit_button("确认录入项目"):
                if i_name:
                    new_i = pd.DataFrame({'项目名称':[i_name],'单价($)':[i_price]})
                    st.session_state['inventory_db'] = pd.concat([st.session_state['inventory_db'], new_i], ignore_index=True)
                    st.toast("零食已录入！", icon="🍿")
                    time.sleep(0.5)
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
            
            search_script = st.text_input("🔍 搜索剧本名称 (清空进入编辑模式)", "", key="search_s")
            if search_script:
                mask = display_db['剧本名称'].str.contains(search_script, case=False, na=False)
                st.dataframe(display_db[mask], use_container_width=True)
            else:
                st.caption("✨ **直接编辑模式**：双击单元格修改。")
                edited_db = st.data_editor(display_db, num_rows="dynamic", use_container_width=True, key="ed_s", column_config={"累计开本(场)": st.column_config.NumberColumn(disabled=True)})
                st.session_state['scripts_db'] = edited_db.drop(columns=['累计开本(场)'], errors='ignore')

        with tab_list2:
            st.session_state['inventory_db'] = st.data_editor(st.session_state['inventory_db'], num_rows="dynamic", use_container_width=True, key="ed_i")

# ==========================================
# Tab 2: 员工考勤与薪资
# ==========================================
with tabs[1]:
    col_l, col_r = st.columns([1, 2.5])
    with col_l:
        st.subheader("员工入职")
        with st.form("add_emp"):
            e_name = st.text_input("员工姓名")
            e_rate = st.number_input("时薪 ($)", value=15.0)
            if st.form_submit_button("添加员工"):
                if e_name and e_name not in st.session_state['employee_db']['员工姓名'].values:
                    st.session_state['employee_db'] = pd.concat([st.session_state['employee_db'], pd.DataFrame({'员工姓名':[e_name],'时薪($)':[e_rate]})], ignore_index=True)
                    st.toast(f"已录入 {e_name}", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
        
        with st.expander("⚙️ 修改或删除员工资料 (点此展开)"):
            st.session_state['employee_db'] = st.data_editor(st.session_state['employee_db'], num_rows="dynamic", use_container_width=True, key="ed_emp")

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
                    st.toast("考勤已记录", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
            else:
                target_es = st.multiselect("选择 NPC", emp_list)
                fee = st.number_input("单人演绎费", value=10.0)
                if st.button("批量提交演绎"):
                    if target_es:
                        batch = [{'记录日期':pd.to_datetime(w_date),'员工姓名':e,'工作类型':'演绎NPC','时长(小时)':0.0,'当日薪资($)':fee} for e in target_es]
                        st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(batch)], ignore_index=True)
                        st.toast("演绎考勤已记录", icon="✅")
                        time.sleep(0.5)
                        st.rerun()
                        
    with col_r:
        st.subheader("💰 财务月结看板")
        search_emp = st.text_input("🔍 搜索员工姓名单独查账", "", key="search_e")
        
        if not st.session_state['attendance_db'].empty:
            df_att = st.session_state['attendance_db'].copy()
            df_att['记录日期'] = pd.to_datetime(df_att['记录日期'])
            all_months = df_att['记录日期'].dt.strftime('%Y-%m').unique().tolist()
            target_month = st.selectbox("📅 选择统计月份", sorted(all_months, reverse=True))
            
            month_df = df_att[df_att['记录日期'].dt.strftime('%Y-%m') == target_month]
            
            if search_emp:
                st.dataframe(month_df[month_df['员工姓名'].str.contains(search_emp, case=False, na=False)], use_container_width=True)
            else:
                st.caption("✨ 双击下方表格即可修改考勤记录。")
                edited_month_df = st.data_editor(month_df, use_container_width=True, key="edit_att_monthly")
                if not edited_month_df.equals(month_df):
                     for col in edited_month_df.columns: 
                         st.session_state['attendance_db'].loc[edited_month_df.index, col] = edited_month_df[col]
                     st.toast("考勤修改已保存！", icon="💾")
            
            if not month_df.empty:
                st.write(f"**{target_month} 员工总薪资汇总**")
                summary = month_df.groupby('员工姓名').agg(总工时=('时长(小时)', 'sum'), 本月应付=('当日薪资($)', 'sum')).reset_index()
                st.dataframe(summary, use_container_width=True)
                
            with st.expander("🗑️ 录错了想删除记录？点此展开"):
                if not month_df.empty:
                    att_del_options = month_df.apply(lambda row: f"{row['记录日期'].strftime('%m-%d')} | {row['员工姓名']} | {row['工作类型']} | ${row['当日薪资($)']}", axis=1)
                    att_del_idx = st.selectbox("选择要删除的记录", month_df.index, format_func=lambda x: att_del_options[x], label_visibility="collapsed")
                    if st.button("🚨 确认删除这笔记录"):
                        st.session_state['attendance_db'] = st.session_state['attendance_db'].drop(att_del_idx).reset_index(drop=True)
                        st.toast("已删除", icon="🗑️")
                        time.sleep(0.5)
                        st.rerun()

# ==========================================
# Tab 3: 收银台 (V5.01 修复显示视觉误差，明确隔离会员扣款)
# ==========================================
with tabs[2]:
    st.subheader("📈 门店总营业额监控")
    display_ledger = st.session_state['ledger_db']
    if not display_ledger.empty:
        # V5.01: 营业额严格排除了 '会员余额'
        actual_cash_in = display_ledger[display_ledger['支付方式'] != '会员余额']['入账总额($)'].sum()
        member_consumed = display_ledger[display_ledger['支付方式'] == '会员余额']['入账总额($)'].sum()
        total_tips = display_ledger['其中小费($)'].sum()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💰 门店总营业额", f"${actual_cash_in:,.2f}", "真实进账 (不含余额抵扣)")
        m2.metric("💎 会员余额消耗", f"${member_consumed:,.2f}", "内部账单 (不计入营业额)", delta_color="off")
        m3.metric("✨ 待发小费池", f"${total_tips:,.2f}")
        m4.metric("📊 剥离小费后净现金", f"${actual_cash_in - total_tips:,.2f}")

    st.divider()
    c_p1, c_p2 = st.columns([1.2, 1.4])
    with c_p1:
        st.subheader("新建收银账单")
        s_opts = st.session_state['scripts_db']['剧本名称'].unique().tolist()
        emp_list = st.session_state['employee_db']['员工姓名'].tolist()
        inventory_list = st.session_state['inventory_db']['项目名称'].tolist()
        
        if not s_opts:
            st.warning("请先在 Tab 1 录入剧本！")
        else:
            sel_s = st.selectbox("🎯 关联剧本场次", s_opts)
            s_data = st.session_state['scripts_db'][st.session_state['scripts_db']['剧本名称']==sel_s].iloc[-1]
            single_price = float(s_data['单人价格($)'])
            pax = int(s_data['人数配置'])
            base_price = single_price * pax
            session_dm = st.selectbox("🧑‍🏫 本场带本 DM (记录流水用)", emp_list) if emp_list else ""
            
            st.divider()
            st.write("🍿 **非会员/整车 零食与饮料 (由外部渠道支付)**")
            selected_global_items = st.multiselect("🔍 选择零食/饮料 (支持多选)", inventory_list, key="global_snacks")
            
            global_snack_total = 0.0
            global_snack_details = []
            if selected_global_items:
                cols_g = st.columns(len(selected_global_items))
                for i, item in enumerate(selected_global_items):
                    item_price = st.session_state['inventory_db'][st.session_state['inventory_db']['项目名称'] == item]['单价($)'].values[0]
                    qty = cols_g[i % len(cols_g)].number_input(f"{item} (${item_price})", min_value=1, value=1, key=f"gqty_{item}")
                    global_snack_total += item_price * qty
                    global_snack_details.append(f"{item}x{qty}")

            st.divider()
            st.write("💰 **外部拆分支付输入 (未付渠道留空)**")
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

            st.divider()
            st.write("💎 **选择会员消费 (独立计费与专属零食)**")
            m_list = st.session_state['member_db']['会员姓名'].unique().tolist()
            selected_members = st.multiselect("🔍 本车有哪些会员？(支持多选)", m_list, key="member_selector")
            
            member_deductions = {}
            member_snack_notes = {}
            member_total = 0.0
            expected_member_revenue = 0.0 
            total_explicit_member_tip = 0.0 
            
            if selected_members:
                for idx, m in enumerate(selected_members):
                    st.markdown(f"**👤 会员：{m}**")
                    m_info = st.session_state['member_db'][st.session_state['member_db']['会员姓名']==m].iloc[-1]
                    m_discount = float(m_info['折扣率'])
                    m_bal = float(m_info['当前余额($)'])
                    m_discounted_price = single_price * m_discount
                    
                    st.caption(f"当前余额: ${m_bal:.2f} | 折后票价: ${m_discounted_price:.2f}")
                    
                    m_snack_items = st.multiselect(f"🍿 {m} 独立购买的零食/饮料", inventory_list, key=f"msnack_{m}")
                    m_snack_total = 0.0
                    m_snack_details = []
                    if m_snack_items:
                        cols_sq = st.columns(len(m_snack_items))
                        for i, item in enumerate(m_snack_items):
                            item_price = st.session_state['inventory_db'][st.session_state['inventory_db']['项目名称'] == item]['单价($)'].values[0]
                            qty = cols_sq[i % len(cols_sq)].number_input(f"{item} (${item_price})", min_value=1, value=1, key=f"mqty_{m}_{item}")
                            m_snack_total += item_price * qty
                            m_snack_details.append(f"{item}x{qty}")
                    
                    expected_member_revenue += (m_discounted_price + m_snack_total)
                    member_snack_notes[m] = f" [含零食: {', '.join(m_snack_details)}]" if m_snack_details else ""
                    
                    col_t1, col_t2 = st.columns(2)
                    with col_t1: tip_mode = st.radio("添加小费", ["无", "固定金额 ($)", "百分比 (%)"], horizontal=True, key=f"tm_{m}")
                    with col_t2:
                        m_tip = 0.0
                        if tip_mode == "固定金额 ($)": m_tip = st.number_input("金额", 0.0, key=f"tv_{m}")
                        elif tip_mode == "百分比 (%)": m_tip = m_discounted_price * (st.slider("比例", 0, 50, 15, 5, key=f"tp_{m}")/100)
                    
                    total_explicit_member_tip += m_tip
                    target_deduct = m_discounted_price + m_snack_total + m_tip
                    
                    st.markdown(f"👉 **该会员本次消费合计: ${target_deduct:.2f}**")
                    deduct_amt = st.number_input(f"💳 实际从 {m} 余额扣除", min_value=0.0, max_value=max(m_bal, 0.0), value=float(min(target_deduct, m_bal)), step=1.0, key=f"deduct_stable_{m}")
                    
                    if deduct_amt > 0:
                        member_deductions[m] = deduct_amt
                        member_total += deduct_amt
                    
                    if idx < len(selected_members) - 1:
                        st.write("---")

            st.divider()
            # V5.01: 核心优化！拆分显示账单，彻底解决“重复计算”视觉误导
            st.markdown("### 🧾 账单结算汇总")
            
            external_pax = max(0, pax - len(selected_members))
            expected_external_revenue = (external_pax * single_price) + global_snack_total
            actual_expected_total = expected_external_revenue + expected_member_revenue
            
            total_collected = external_total + member_total
            
            extra_overflow = total_collected - actual_expected_total - total_explicit_member_tip
            extra_overflow_tip = max(0, extra_overflow)
            system_calculated_tip = total_explicit_member_tip + extra_overflow_tip
            
            # 采用直观的面板分别显示“进账”和“抵扣”
            col_sum1, col_sum2, col_sum3 = st.columns(3)
            col_sum1.metric("📌 本单总流水 (含抵扣)", f"${total_collected:.2f}")
            col_sum2.metric("💰 实际新增营业额 (外部支付)", f"${external_total:.2f}")
            col_sum3.metric("💎 会员余额内部抵扣", f"${member_total:.2f}")
            
            st.caption(f"*(本车满编系统折后标准应收款为: **${actual_expected_total:.2f}**)*")
            
            if system_calculated_tip > 0:
                st.success(f"🎉 账单金额充裕！本单共产生总小费: **${system_calculated_tip:.2f}** (包含会员自选小费与外部溢出款)")
            else:
                st.info("✅ 账单已配平。")
                
            if total_collected < actual_expected_total:
                st.warning(f"⚠️ 本单各项支付与抵扣金额加总，低于本单应收标准！请确认是否存在漏付款。")
            
            if st.checkbox("手动确认/修改总小费金额"):
                final_tip_amount = st.number_input("输入总小费 ($)", value=float(system_calculated_tip), min_value=0.0)
            else:
                final_tip_amount = system_calculated_tip
            
            t_dms = st.multiselect("🧑‍🏫 分配小费的 DM", emp_list, default=[session_dm] if session_dm else [])
            snack_note = f" [全局含零食: {', '.join(global_snack_details)}]" if global_snack_details else ""
            note = st.text_input("账单全局备注") + snack_note
            
            if st.button("🚀 确认结账入库", type="primary", use_container_width=True):
                if total_collected > 0:
                    if final_tip_amount > 0 and not t_dms:
                        st.error("⚠️ 产生了小费，请在上方选择【分配小费的 DM】！")
                        st.stop()
                    
                    for m, amt in member_deductions.items():
                        st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==m, '当前余额($)'] -= amt
                        m_tip = amt * (final_tip_amount / total_collected) if total_collected > 0 else 0
                        m_s_note = member_snack_notes.get(m, "")
                        f_m_note = f"会员 [{m}] 扣款{m_s_note} | {note}".strip() if note else f"会员 [{m}] 扣款{m_s_note}".strip()
                        m_log = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':[sel_s],'主开DM':[session_dm],'支付方式':['会员余额'],'入账总额($)':[amt],'其中小费($)':[m_tip],'备注':[f_m_note]})
                        st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], m_log], ignore_index=True)

                    def save_ext(method, amt, r=None):
                        method_tip = amt * (final_tip_amount / total_collected) if total_collected > 0 else 0
                        f_note = f"{note} [{method}收 ¥{r:.2f}]".strip() if r else note
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
                    
                    st.toast("✅ 结算成功！账单已按分类入库。", icon="🎉")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("入账总额不能为 0！")

    with c_p2:
        st.subheader("流水明细与修改")
        search_ledger = st.text_input("🔍 搜索查账 (清空以进入编辑模式)", "", key="search_l")
        if search_ledger:
            mask = st.session_state['ledger_db']['关联剧本'].str.contains(search_ledger, case=False, na=False) | st.session_state['ledger_db']['备注'].str.contains(search_ledger, case=False, na=False) | st.session_state['ledger_db']['主开DM'].str.contains(search_ledger, case=False, na=False)
            st.dataframe(st.session_state['ledger_db'][mask], use_container_width=True, height=600)
        else:
            st.session_state['ledger_db'] = st.data_editor(st.session_state['ledger_db'], num_rows="dynamic", use_container_width=True, height=600, key="ed_l")

# ==========================================
# Tab 4: 经营报表
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
        
        rev = 0.0; tips = 0.0; wages = 0.0
        filtered_l = pd.DataFrame()
        filtered_a = pd.DataFrame()
        
        if not l_df.empty:
            l_df['交易时间_dt'] = pd.to_datetime(l_df['交易时间']).dt.date
            mask = (l_df['交易时间_dt'] >= start_date) & (l_df['交易时间_dt'] <= end_date)
            filtered_l = l_df[mask]
            
            # V5.01 严格排除会员余额，这是绝对不会错的
            rev = filtered_l[filtered_l['支付方式'] != '会员余额']['入账总额($)'].sum()
            
        if not a_df.empty and '记录日期' in a_df.columns:
            a_df['记录日期_dt'] = pd.to_datetime(a_df['记录日期']).dt.date
            mask_a = (a_df['记录日期_dt'] >= start_date) & (a_df['记录日期_dt'] <= end_date)
            filtered_a = a_df[mask_a]
            tips = filtered_a[filtered_a['工作类型'] == '专属小费']['当日薪资($)'].sum()
            wages = filtered_a[filtered_a['工作类型'] != '专属小费']['当日薪资($)'].sum()

        profit = rev - wages - tips - rent
        
        if rev > 0:
            wages_pct = (wages / rev) * 100
            tips_pct = (tips / rev) * 100
            rent_pct = (rent / rev) * 100
            profit_pct = (profit / rev) * 100
        else:
            wages_pct = tips_pct = rent_pct = profit_pct = 0.0

        st.info("💡 财务引擎已启动【防重复计算】：会员充值款直接计入现金流，后续会员打本扣除余额的交易视为内部抵扣，不重复计算营收，确保报表与账户 100% 匹配。")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("区间总营业额", f"${rev:,.2f}", "100% (真实新增款)", delta_color="off")
        m2.metric("时薪支出", f"${wages:,.2f}", f"占营业额: {wages_pct:.1f}%", delta_color="inverse")
        m3.metric("小费支出", f"${tips:,.2f}", f"占营业额: {tips_pct:.1f}%", delta_color="inverse")
        m4.metric("房租成本", f"${rent:,.2f}", f"占营业额: {rent_pct:.1f}%", delta_color="inverse")
        m5.metric("净利润", f"${profit:,.2f}", f"净利润率: {profit_pct:.1f}%")
        
        st.divider()
        st.write("📝 **期间明细参考**")
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1:
            st.caption("🧾 流水入账记录")
            if not filtered_l.empty:
                st.dataframe(filtered_l[['交易时间', '关联剧本', '主开DM', '支付方式', '入账总额($)', '备注']], use_container_width=True)
            else:
                st.info("期间无入账记录。")
        with c_sub2:
            st.caption("🧑‍🏫 员工薪资产生")
            if not filtered_a.empty:
                st.dataframe(filtered_a[['记录日期', '员工姓名', '工作类型', '当日薪资($)']], use_container_width=True)
            else:
                st.info("期间无人工支出记录。")

# ==========================================
# Tab 5: 会员管理
# ==========================================
with tabs[4]:
    m_col1, m_col2 = st.columns([1, 2])
    with m_col1:
        st.subheader("👤 会员业务")
        m_action = st.radio("业务类型", ["🔄 续费", "✨ 开卡"], horizontal=True)
        if m_action == "🔄 续费":
            m_list = st.session_state['member_db']['会员姓名'].unique().tolist()
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
        search_m = st.text_input("🔍 搜索姓名/电话 (清空搜索框进入编辑模式)", "")
        
        if search_m:
            mask = st.session_state['member_db']['会员姓名'].str.contains(search_m, case=False, na=False) | st.session_state['member_db']['电话号码'].str.contains(search_m, case=False, na=False)
            m_display = st.session_state['member_db'][mask]
            st.dataframe(m_display, use_container_width=True)
            
            st.divider()
            if not m_display.empty:
                matched_names = m_display['会员姓名'].tolist()
                safe_pattern = "|".join([re.escape(name) for name in matched_names])
                m_logs = st.session_state['ledger_db'][st.session_state['ledger_db']['备注'].str.contains(safe_pattern, regex=True, na=False)]
                st.write("📖 匹配会员的流水记录：")
                st.dataframe(m_logs[['交易时间', '关联剧本', '支付方式', '入账总额($)', '备注']].sort_values('交易时间', ascending=False), use_container_width=True)
        else:
            st.caption("✨ 双击表格可直接修改会员资料。")
            st.session_state['member_db'] = st.data_editor(st.session_state['member_db'], use_container_width=True, key="ed_m")
