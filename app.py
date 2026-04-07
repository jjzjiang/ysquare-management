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
    # 修复 KeyError：如果系统缓存了旧版本的'打卡日期'，自动重命名为新版的'记录日期'
    if '打卡日期' in st.session_state['attendance_db'].columns:
        st.session_state['attendance_db'].rename(columns={'打卡日期': '记录日期'}, inplace=True)

st.title("Y Square Studio 门店管理系统")

tab1, tab2 = st.tabs(["📚 剧本列表管理", "⏰ 员工考勤与薪资"])

# --- Tab 1: 剧本管理 ---
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("添加新剧本 / 场次")
        with st.form("add_script_form"):
            script_name = st.text_input("剧本名称")
            player_count = st.number_input("人数配置", min_value=1, step=1)
            price = st.number_input("单人价格 ($)", min_value=0.0, step=1.0)
            dm_name = st.text_input("主开 DM")
            script_date = st.date_input("开本日期")
            if st.form_submit_button("添加记录"):
                if script_name and dm_name:
                    new_script = pd.DataFrame({'剧本名称': [script_name], '人数配置': [player_count], '单人价格($)': [price], '主开DM': [dm_name], '日期': [script_date]})
                    st.session_state['scripts_db'] = pd.concat([st.session_state['scripts_db'], new_script], ignore_index=True)
                    st.success("剧本信息已录入！")
    with col2:
        st.subheader("当前剧本库")
        
        # 新增：剧本/DM 搜索栏
        search_script = st.text_input("🔍 搜索剧本名称或主开 DM", "")
        display_scripts = st.session_state['scripts_db'].copy()
        
        if search_script:
            # 实现模糊搜索过滤
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
            work_date = st.date_input("日期", value=datetime.now())
            work_type = st.radio("工作内容", ["日常带本 (个人)", "NPC演绎 (支持多人)"], horizontal=True)
            
            if work_type == "日常带本 (个人)":
                selected_emp = st.selectbox("选择 DM", employee_list)
                hours = st.number_input("带本时长 (小时)", min_value=0.0, step=0.5)
                if st.button("提交带本记录"):
                    rate = st.session_state['employee_db'][st.session_state['employee_db']['员工姓名'] == selected_emp]['时薪($)'].values[0]
                    salary = hours * rate
                    new_record = pd.DataFrame({
                        '记录日期': [pd.to_datetime(work_date)], '员工姓名': [selected_emp], 
                        '工作类型': ["带本"], '时长(小时)': [hours], '当日薪资($)': [salary]
                    })
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], new_record], ignore_index=True)
                    st.success(f"{selected_emp} 记录成功")
            
            else:
                selected_emps = st.multiselect("选择参与演绎的所有 DM", employee_list)
                act_fee = st.number_input("每人演绎费 ($)", min_value=0.0, step=5.0)
                if st.button("批量提交演绎记录"):
                    if selected_emps:
                        batch_data = []
                        for emp in selected_emps:
                            batch_data.append({
                                '记录日期': [pd.to_datetime(work_date)], '员工姓名': [emp], 
                                '工作类型': ["演绎NPC"], '时长(小时)': [0.0], '当日薪资($)': [act_fee]
                            })
                        for data in batch_data:
                            st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], pd.DataFrame(data)], ignore_index=True)
                        st.success(f"已成功记录 {len(selected_emps)} 位 DM 的演绎工资")
        else:
            st.warning("请先录入员工信息")

    with col_right:
        st.subheader("💰 财务月结看板")
        
        # 新增：员工薪资搜索栏
        search_emp = st.text_input("🔍 搜索员工姓名单独查账", "")
        
        if not st.session_state['attendance_db'].empty:
            df = st.session_state['attendance_db'].copy()
            df['记录日期'] = pd.to_datetime(df['记录日期'])
            
            all_months = df['记录日期'].dt.strftime('%Y-%m').unique().tolist()
            target_month = st.selectbox("选择统计月份", sorted(all_months, reverse=True))
            
            # 过滤1：按月份
            month_df = df[df['记录日期'].dt.strftime('%Y-%m') == target_month]
            
            # 过滤2：按搜索的员工姓名
            if search_emp:
                month_df = month_df[month_df['员工姓名'].str.contains(search_emp, case=False, na=False)]
            
            st.write(f"📅 {target_month} 费用明细")
            st.dataframe(month_df, use_container_width=True)
            
            st.write(f"📊 {target_month} 薪资汇总")
            if not month_df.empty:
                summary = month_df.groupby('员工姓名').agg(
                    总工时=('时长(小时)', 'sum'),
                    本月总计薪资=('当日薪资($)', 'sum')
                ).reset_index()
                st.dataframe(summary, use_container_width=True)
                
                st.download_button("下载本月工资单 (CSV)", summary.to_csv(index=False).encode('utf-8-sig'), f"salary_{target_month}.csv", "text/csv")
            else:
                st.info("未找到匹配的数据。")
        else:
            st.info("暂无考勤数据。")
