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
    st.session_state['ledger_db'] = pd.DataFrame(columns=['交易时间', '关联剧本', '主开DM', '支付方式', '入账总额($)', '其中小费($)', '备注'])

st.title("Y Square Studio 门店管理系统")
tabs = st.tabs(["📚 剧本列表管理", "⏰ 员工考勤与薪资", "💵 收银与流水记录", "📊 经营营收报表"])

# ==========================================
# Tab 1-3 逻辑保持一致 (为节省篇幅，此处省略，请确保保留你之前运行正常的代码)
# ==========================================
# (注：生产环境中请将此处替换为之前完整的 Tab 1, 2, 3 代码内容)

# ==========================================
# Tab 4: 经营营收报表 (New!)
# ==========================================
with tabs[3]:
    st.header("📈 门店经营损益分析")
    st.caption("数据基于流水记录与员工薪资自动汇总")

    # 1. 准备数据源
    df_ledger = st.session_state['ledger_db'].copy()
    df_attendance = st.session_state['attendance_db'].copy()
    
    if not df_ledger.empty or not df_attendance.empty:
        # 处理时间格式
        if not df_ledger.empty:
            df_ledger['交易时间'] = pd.to_datetime(df_ledger['交易时间'])
            df_ledger['月份'] = df_ledger['交易时间'].dt.strftime('%Y-%m')
        
        if not df_attendance.empty:
            df_attendance['记录日期'] = pd.to_datetime(df_attendance['记录日期'])
            df_attendance['月份'] = df_attendance['记录日期'].dt.strftime('%Y-%m')

        # 2. 计算各月营收
        revenue_monthly = pd.DataFrame()
        if not df_ledger.empty:
            revenue_monthly = df_ledger.groupby('月份')['入账总额($)'].sum().reset_index()
            revenue_monthly.columns = ['月份', '剧本总营收($)']

        # 3. 计算各月支出 (区分工资和小费)
        expense_monthly = pd.DataFrame()
        if not df_attendance.empty:
            # 提取小费支出
            tips_cost = df_attendance[df_attendance['工作类型'] == "专属小费"].groupby('月份')['当日薪资($)'].sum().reset_index()
            tips_cost.columns = ['月份', '小费支出($)']
            
            # 提取工资支出 (带本 + 演绎)
            wages_cost = df_attendance[df_attendance['工作类型'] != "专属小费"].groupby('月份')['当日薪资($)'].sum().reset_index()
            wages_cost.columns = ['月份', '员工工资($)']
            
            expense_monthly = pd.merge(wages_cost, tips_cost, on='月份', how='outer').fillna(0)

        # 4. 合并报表
        if not revenue_monthly.empty or not expense_monthly.empty:
            report_df = pd.merge(revenue_monthly, expense_monthly, on='月份', how='outer').fillna(0)
            
            # 添加固定成本：房租
            report_df['房租支出($)'] = 7000.0
            
            # 计算总支出与净利润
            report_df['总支出($)'] = report_df['员工工资($)'] + report_df['小费支出($)'] + report_df['房租支出($)']
            report_df['净利润($)'] = report_df['剧本总营收($)'] - report_df['总支出($)']

            # 5. UI 展示
            # 汇总指标卡
            latest_month = report_df.sort_values('月份', ascending=False).iloc[0]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"{latest_month['月份']} 总营收", f"${latest_month['剧本总营收($)']:,.2f}")
            m2.metric(f"{latest_month['月份']} 人工成本", f"${(latest_month['员工工资($)'] + latest_month['小费支出($)']):,.2f}")
            
            # 利润指标着色
            profit_val = latest_month['净利润($)']
            m3.metric(f"{latest_month['月份']} 净利润", f"${profit_val:,.2f}", delta=f"{profit_val:,.2f}", delta_color="normal")
            m4.metric("固定房租", "$7,000.00")

            st.divider()
            st.subheader("🗓️ 历史月度损益明细")
            
            # 格式化表格显示
            styled_report = report_df.sort_values('月份', ascending=False).style.format({
                '剧本总营收($)': '{:,.2f}',
                '员工工资($)': '{:,.2f}',
                '小费支出($)': '{:,.2f}',
                '房租支出($)': '{:,.2f}',
                '总支出($)': '{:,.2f}',
                '净利润($)': '{:,.2f}'
            })
            st.table(styled_report)

            # 可视化趋势 (可选)
            st.subheader("📈 营收与利润趋势")
            chart_data = report_df.set_index('月份')[['剧本总营收($)', '总支出($)', '净利润($)']]
            st.line_chart(chart_data)

        else:
            st.info("数据不足，无法生成报表。请确保已录入流水和考勤信息。")
    else:
        st.info("暂无财务数据，请先录入收银记录和考勤。")

# ==========================================
# 以下是之前的 Tab 1, 2, 3 完整逻辑 (请确保合并时不要覆盖)
# ==========================================
# ... [此处粘贴你之前版本中所有的 Tab 1, 2, 3 代码内容] ...
