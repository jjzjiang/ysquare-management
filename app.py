import streamlit as st
import pandas as pd
from datetime import datetime
import time

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
    # 彻底修复 KeyError，确保即使发生脏数据也能强行纠正结构
    if '打卡日期' in st.session_state['attendance_db'].columns:
        st.session_state['attendance_db'].rename(columns={'打卡日期': '记录日期'}, inplace=True)
    if '记录日期' not in st.session_state['attendance_db'].columns:
        st.session_state['attendance_db']['记录日期'] = pd.to_datetime(datetime.now().date())
        
if 'ledger_db' not in st.session_state:
    st.session_state['ledger_db'] = pd.DataFrame(columns=['交易时间', '关联剧本', '主开DM', '支付方式', '入账总额($)', '其中小费($)', '备注'])
if 'member_db' not in st.session_state:
    st.session_state['member_db'] = pd.DataFrame(columns=['会员姓名', '当前余额($)', '折扣率', '累计充值($)', '入会日期'])

st.title("Y Square Studio 门店管理系统")
tabs = st.tabs(["📚 剧本列表", "⏰ 员工考勤", "💵 收银台", "📊 财务报表", "💎 会员管理"])

# ==========================================
# Tab 1: 剧本列表管理
# ==========================================
with tabs[0]:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("添加剧本场次")
        with st.form("add_script_form"):
            s_name = st.text_input("剧本名称")
            s_pax = st.number_input("人数", min_value=1, value=6)
            s_price = st.number_input("单人原价 ($)", min_value=0.0, value=30.0)
            emp_list = st.session_state['employee_db']['员工姓名'].tolist()
            s_dm = st.selectbox("主开 DM", emp_list) if emp_list else st.text_input("主开 DM")
            s_date = st.date_input("开本日期")
            if st.form_submit_button("确认录入"):
                new_s = pd.DataFrame({'剧本名称':[s_name],'人数配置':[s_pax],'单人价格($)':[s_price],'主开DM':[s_dm],'日期':[s_date]})
                st.session_state['scripts_db'] = pd.concat([st.session_state['scripts_db'], new_s], ignore_index=True)
                st.rerun()
    with col2:
        st.subheader("剧本库明细")
        st.session_state['scripts_db'] = st.data_editor(st.session_state['scripts_db'], num_rows="dynamic", use_container_width=True, key="ed_s")

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
# Tab 3: 收银台 (重构：会员选择菜单合并为主干流程)
# ==========================================
with tabs[2]:
    c_p1, c_p2 = st.columns([1, 1.4])
    with c_p1:
        st.subheader("新建收银账单")
        s_opts = st.session_state['scripts_db']['剧本名称'].unique().tolist()
        
        if not s_opts:
            st.warning("请先在 Tab 1 录入剧本！")
        else:
            sel_s = st.selectbox("关联剧本场次", s_opts)
            s_data = st.session_state['scripts_db'][st.session_state['scripts_db']['剧本名称']==sel_s].iloc[-1]
            base_price = float(s_data['单人价格($)']) * int(s_data['人数配置'])
            h_dm = s_data['主开DM']
            
            st.info(f"💡 **本车应收标准票款**：${base_price:.2f} (主开DM: {h_dm})")
            st.divider()

            # 核心改动：把会员选择直接变成下拉菜单，如果不选就是常规组合支付
            m_list = st.session_state['member_db']['会员姓名'].tolist()
            m_options = ["-- 👤 常规组合支付 (不使用会员卡) --"] + m_list
            selected_member = st.selectbox("💳 支付方式 / 选择会员消费 (支持搜索)", m_options)

            if selected_member != "-- 👤 常规组合支付 (不使用会员卡) --":
                # --- 会员支付专属界面 ---
                m_info = st.session_state['member_db'][st.session_state['member_db']['会员姓名']==selected_member].iloc[-1]
                discount = float(m_info['折扣率'])
                final_price = base_price * discount
                
                st.success(f"💎 会员 **{selected_member}** 专属折扣: {discount*100:.0f}折 | 折后票款: **${final_price:.2f}**")
                st.caption(f"当前可用余额: ${m_info['当前余额($)']:,.2f}")
                
                # 小费比例选择器
                st.write("✨ **小费设置**")
                tip_pct = st.slider("选择小费比例 (%)", min_value=0, max_value=50, value=0, step=5)
                tip_amt = final_price * (tip_pct / 100)
                
                if tip_amt > 0:
                    st.write(f"小费金额: ${tip_amt:.2f}")
                    
                total_to_pay = final_price + tip_amt
                st.metric("本次总计扣除余额 (含小费)", f"${total_to_pay:.2f}")
                
                t_dms = st.multiselect("🧑‍🏫 平分小费给 DM", emp_list)
                note = st.text_input("备注", key="m_note")
                
                if st.button("🚀 确认会员余额扣款", type="primary", use_container_width=True):
                    if m_info['当前余额($)'] >= total_to_pay:
                        if tip_amt > 0 and not t_dms:
                            st.error("⚠️ 请选择分配小费的 DM！")
                            st.stop()
                        
                        # 扣除余额
                        st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==selected_member, '当前余额($)'] -= total_to_pay
                        
                        # 记录流水
                        final_note = f"会员:{selected_member} 消费 | {note}".strip()
                        new_log = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':[sel_s],'主开DM':[h_dm],'支付方式':['会员余额'],'入账总额($)':[total_to_pay],'其中小费($)':[tip_amt],'备注':[final_note]})
                        st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], new_log], ignore_index=True)
                        
                        # 记录DM小费工资
                        if tip_amt > 0 and t_dms:
                            t_recs = [{'记录日期':pd.to_datetime(datetime.now().date()),'员工姓名':e,'工作类型':'专属小费','时长(小时)':0.0,'当日薪资($)':tip_amt/len(t_dms)} for e in t_dms]
                            st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(t_recs)], ignore_index=True)
                            
                        st.toast(f"✅ 扣款成功！剩余余额: ${m_info['当前余额($)'] - total_to_pay:.2f}", icon="🎉")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"余额不足！当前余额仅剩 ${m_info['当前余额($)']:.2f}，请先在 Tab 5 充值。")
                        
            else:
                # --- 常规混合支付界面 ---
                st.write("💰 **拆分明细输入 (未付渠道留空即可)**")
                c1, c2 = st.columns(2)
                v_usd = c1.number_input("📱 Venmo", min_value=0.0, step=1.0)
                z_usd = c2.number_input("💸 Zelle", min_value=0.0, step=1.0)
                tr_usd = c1.number_input("🏦 转账", min_value=0.0, step=1.0)
                c_usd = c2.number_input("💵 现金", min_value=0.0, step=1.0)
                
                c3, c4 = st.columns(2)
                ex_rate = c3.number_input("汇率 (1 USD = ? RMB)", value=7.20, step=0.05)
                ali_rmb = c3.number_input("💙 支付宝(¥)", min_value=0.0, step=10.0)
                wx_rmb = c4.number_input("💚 微信(¥)", min_value=0.0, step=10.0)
                
                total_cash = v_usd + z_usd + c_usd + tr_usd + (ali_rmb/ex_rate if ex_rate > 0 else 0) + (wx_rmb/ex_rate if ex_rate > 0 else 0)
                
                st.write("✨ **对账与小费**")
                if base_price > 0 and total_cash > base_price:
                    tip_amount = total_cash - base_price
                    st.success(f"实收 **${total_cash:.2f}**，溢出 **${tip_amount:.2f}** 自动记为小费")
                else:
                    tip_amount = 0.0
                    st.caption(f"当前实收 **${total_cash:.2f}**")
                    
                if st.checkbox("手动覆写小费金额"):
                    tip_amount = st.number_input("输入小费", value=float(tip_amount), min_value=0.0)
                    
                t_dms = st.multiselect("🧑‍🏫 选择DM平分小费", emp_list)
                note = st.text_input("账单备注")
                
                if st.button("🚀 确认收账入库", type="primary", use_container_width=True):
                    if total_cash > 0:
                        if tip_amount > 0 and not t_dms:
                            st.error("⚠️ 请选择分配小费的 DM！")
                            st.stop()

                        def save_l(m, a, r=None):
                            method_tip = a * (tip_amount / total_cash) if total_cash > 0 else 0
                            f_note = f"{note} [{m}收 ¥{r:.2f}]".strip() if r else note
                            new_log = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':[sel_s],'主开DM':[h_dm],'支付方式':[m],'入账总额($)':[a],'其中小费($)':[method_tip],'备注':[f_note]})
                            st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], new_log], ignore_index=True)
                            
                        if v_usd > 0: save_l("Venmo", v_usd)
                        if z_usd > 0: save_l("Zelle", z_usd)
                        if c_usd > 0: save_l("现金", c_usd)
                        if tr_usd > 0: save_l("转账", tr_usd)
                        if ali_rmb > 0: save_l("支付宝", ali_rmb/ex_rate, ali_rmb)
                        if wx_rmb > 0: save_l("微信", wx_rmb/ex_rate, wx_rmb)
                        
                        if tip_amount > 0 and t_dms:
                            t_recs = [{'记录日期':pd.to_datetime(datetime.now().date()),'员工姓名':e,'工作类型':'专属小费','时长(小时)':0.0,'当日薪资($)':tip_amount/len(t_dms)} for e in t_dms]
                            st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(t_recs)], ignore_index=True)
                            
                        st.toast("✅ 入库成功！", icon="🎉")
                        time.sleep(0.5)
                        st.rerun()

    with c_p2:
        st.subheader("流水记录")
        st.session_state['ledger_db'] = st.data_editor(st.session_state['ledger_db'], num_rows="dynamic", use_container_width=True, height=550, key="ed_l")

# ==========================================
# Tab 4: 经营报表
# ==========================================
with tabs[3]:
    st.header("📊 财务损益分析")
    rent = st.number_input("月房租设置 ($)", value=7000.0)
    st.divider()
    l_df = st.session_state['ledger_db'].copy()
    a_df = st.session_state['attendance_db'].copy()
    if not l_df.empty:
        l_df['交易时间'] = pd.to_datetime(l_df['交易时间'])
        l_df['月'] = l_df['交易时间'].dt.strftime('%Y-%m')
        rev = l_df.groupby('月')['入账总额($)'].sum()
        if not a_df.empty and '记录日期' in a_df.columns:
            a_df['记录日期'] = pd.to_datetime(a_df['记录日期'])
            a_df['月'] = a_df['记录日期'].dt.strftime('%Y-%m')
            tips = a_df[a_df['工作类型']=='专属小费'].groupby('月')['当日薪资($)'].sum()
            wages = a_df[a_df['工作类型']!='专属小费'].groupby('月')['当日薪资($)'].sum()
            
            report = pd.DataFrame({'营收':rev, '员工工资':wages, '小费支出':tips}).fillna(0)
            report['房租'] = rent
            report['净利润'] = report['营收'] - report['员工工资'] - report['小费支出'] - report['房租']
            st.table(report.sort_index(ascending=False).style.format("${:,.2f}"))
            
            if not report.empty:
                last = report.iloc[-1]
                cols = st.columns(4)
                cols[0].metric("最新月营收", f"${last['营收']:,.2f}")
                cols[1].metric("工资占比", f"{ (last['员工工资']/last['营收']*100 if last['营收']>0 else 0):.1f}%")
                cols[2].metric("小费占比", f"{ (last['小费支出']/last['营收']*100 if last['营收']>0 else 0):.1f}%")
                cols[3].metric("月净利润", f"${last['净利润']:,.2f}")

# ==========================================
# Tab 5: 会员记录
# ==========================================
with tabs[4]:
    m_col1, m_col2 = st.columns([1, 2])
    with m_col1:
        st.subheader("👤 新会员开卡/充值")
        m_name = st.text_input("会员姓名", key="m_input")
        m_recharge = st.number_input("充值金额 ($)", min_value=0.0, step=50.0)
        m_discount = st.selectbox("会员折扣率", [1.0, 0.9, 0.88, 0.8, 0.75], format_func=lambda x: f"{x*100:.0f}折" if x<1 else "无折扣")
        
        if st.button("确认充值/开卡"):
            if m_name:
                if m_name in st.session_state['member_db']['会员姓名'].values:
                    st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==m_name, '当前余额($)'] += m_recharge
                    st.session_state['member_db'].loc[st.session_state['member_db']['会员姓名']==m_name, '累计充值($)'] += m_recharge
                    new_r = pd.DataFrame({'交易时间':[datetime.now().strftime("%Y-%m-%d %H:%M")],'关联剧本':['会员充值'],'主开DM':['-'],'支付方式':['现金/转账'],'入账总额($)':[m_recharge],'其中小费($)':[0.0],'备注':[f"会员:{m_name} 充值"]})
                    st.session_state['ledger_db'] = pd.concat([st.session_state['ledger_db'], new_r], ignore_index=True)
                    st.toast(f"{m_name} 充值成功！", icon="💰")
                else:
                    new_m = pd.DataFrame({'会员姓名':[m_name],'当前余额($)':[m_recharge],'折扣率':[m_discount],'累计充值($)':[m_recharge],'入会日期':[datetime.now().strftime("%Y-%m-%d")]})
                    st.session_state['member_db'] = pd.concat([st.session_state['member_db'], new_m], ignore_index=True)
                    st.toast(f"欢迎新会员: {m_name}", icon="💎")
                time.sleep(0.5)
                st.rerun()

    with m_col2:
        st.subheader("📋 会员名册与消费记录")
        search_m = st.text_input("🔍 搜索会员", "")
        m_display = st.session_state['member_db'].copy()
        if search_m:
            m_display = m_display[m_display['会员姓名'].str.contains(search_m, case=False)]
        
        m_display = st.data_editor(m_display, use_container_width=True, key="ed_m")
        st.session_state['member_db'] = m_display
        
        st.divider()
        st.subheader("📖 会员历史消费明细")
        if search_m and not st.session_state['ledger_db'].empty:
            m_logs = st.session_state['ledger_db'][st.session_state['ledger_db']['备注'].str.contains(f"会员:{search_m}", na=False)]
            st.write(f"正在查看 {search_m} 的打本记录：")
            st.dataframe(m_logs[['交易时间', '关联剧本', '入账总额($)', '备注']], use_container_width=True)
