import streamlit as st
import pandas as pd

st.set_page_config(page_title="Y Square Studio 管理系统", layout="wide")

# 初始化内存数据库
if 'scripts_db' not in st.session_state:
    st.session_state['scripts_db'] = pd.DataFrame(columns=['剧本名称', '人数配置', '单人价格($)', '主开DM', '日期'])
if 'employee_db' not in st.session_state:
    st.session_state['employee_db'] = pd.DataFrame(columns=['员工姓名', '时薪($)'])
if 'attendance_db' not in st.session_state:
    st.session_state['attendance_db'] = pd.DataFrame(columns=['打卡日期', '员工姓名', '工作时长(小时)', '当日薪资($)'])

st.title("Y Square Studio 门店管理系统")

tab1, tab2 = st.tabs(["📚 剧本列表管理", "⏰ 员工考勤与薪资"])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("添加新剧本 / 场次")
        with st.form("add_script_form"):
            script_name = st.text_input("剧本名称")
            player_count = st.number_input("人数配置", min_value=1, step=1)
            price = st.number_input("单人价格 ($)", min_value=0.0, step=1.0)
            dm_name = st.text_input("主开 DM")
            script_date = st.date_input("日期")
            if st.form_submit_button("添加记录"):
                if script_name and dm_name:
                    new_script = pd.DataFrame({'剧本名称': [script_name], '人数配置': [player_count], '单人价格($)': [price], '主开DM': [dm_name], '日期': [script_date]})
                    st.session_state['scripts_db'] = pd.concat([st.session_state['scripts_db'], new_script], ignore_index=True)
                    st.success("添加成功！")
                else:
                    st.error("请输入剧本名称和 DM 姓名！")
    with col2:
        st.subheader("当前剧本列表")
        st.dataframe(st.session_state['scripts_db'], use_container_width=True)

with tab2:
    col3, col4 = st.columns([1, 2])
    with col3:
        st.subheader("1. 员工登记")
        with st.form("add_employee_form"):
            emp_name = st.text_input("员工/DM 姓名")
            hourly_rate = st.number_input("基础时薪 ($)", min_value=0.0, step=0.5, value=15.0)
            if st.form_submit_button("录入员工"):
                if emp_name and emp_name not in st.session_state['employee_db']['员工姓名'].values:
                    new_emp = pd.DataFrame({'员工姓名': [emp_name], '时薪($)': [hourly_rate]})
                    st.session_state['employee_db'] = pd.concat([st.session_state['employee_db'], new_emp], ignore_index=True)
                    st.success(f"录入成功！")
        
        st.subheader("2. 考勤打卡")
        employee_list = st.session_state['employee_db']['员工姓名'].tolist()
        if employee_list:
            with st.form("add_attendance_form"):
                selected_emp = st.selectbox("选择员工", employee_list)
                work_date = st.date_input("工作日期")
                work_hours = st.number_input("工作时长 (小时)", min_value=0.0, step=0.5)
                if st.form_submit_button("记录考勤"):
                    rate = st.session_state['employee_db'][st.session_state['employee_db']['员工姓名'] == selected_emp]['时薪($)'].values[0]
                    daily_salary = work_hours * rate
                    new_attendance = pd.DataFrame({'打卡日期': [work_date], '员工姓名': [selected_emp], '工作时长(小时)': [work_hours], '当日薪资($)': [daily_salary]})
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], new_attendance], ignore_index=True)
                    st.success(f"已记录薪资: ${daily_salary:.2f}")

    with col4:
        st.subheader("考勤与薪资记录表")
        st.write("📅 每日考勤明细")
        st.dataframe(st.session_state['attendance_db'], use_container_width=True)
        if not st.session_state['attendance_db'].empty:
            st.write("💰 薪资总计")
            summary_df = st.session_state['attendance_db'].groupby('员工姓名').agg(总工作时长=('工作时长(小时)', 'sum'), 总应付薪资=('当日薪资($)', 'sum')).reset_index()
            st.dataframe(summary_df, use_container_width=True)
