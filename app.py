{\rtf1\ansi\ansicpg936\cocoartf2818
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
\
st.set_page_config(page_title="Y Square Studio \uc0\u31649 \u29702 \u31995 \u32479 ", layout="wide")\
\
# \uc0\u21021 \u22987 \u21270 \u20869 \u23384 \u25968 \u25454 \u24211 \
if 'scripts_db' not in st.session_state:\
    st.session_state['scripts_db'] = pd.DataFrame(columns=['\uc0\u21095 \u26412 \u21517 \u31216 ', '\u20154 \u25968 \u37197 \u32622 ', '\u21333 \u20154 \u20215 \u26684 ($)', '\u20027 \u24320 DM', '\u26085 \u26399 '])\
if 'employee_db' not in st.session_state:\
    st.session_state['employee_db'] = pd.DataFrame(columns=['\uc0\u21592 \u24037 \u22995 \u21517 ', '\u26102 \u34218 ($)'])\
if 'attendance_db' not in st.session_state:\
    st.session_state['attendance_db'] = pd.DataFrame(columns=['\uc0\u25171 \u21345 \u26085 \u26399 ', '\u21592 \u24037 \u22995 \u21517 ', '\u24037 \u20316 \u26102 \u38271 (\u23567 \u26102 )', '\u24403 \u26085 \u34218 \u36164 ($)'])\
\
st.title("Y Square Studio \uc0\u38376 \u24215 \u31649 \u29702 \u31995 \u32479 ")\
\
tab1, tab2 = st.tabs(["\uc0\u55357 \u56538  \u21095 \u26412 \u21015 \u34920 \u31649 \u29702 ", "\u9200  \u21592 \u24037 \u32771 \u21220 \u19982 \u34218 \u36164 "])\
\
with tab1:\
    col1, col2 = st.columns([1, 2])\
    with col1:\
        st.subheader("\uc0\u28155 \u21152 \u26032 \u21095 \u26412  / \u22330 \u27425 ")\
        with st.form("add_script_form"):\
            script_name = st.text_input("\uc0\u21095 \u26412 \u21517 \u31216 ")\
            player_count = st.number_input("\uc0\u20154 \u25968 \u37197 \u32622 ", min_value=1, step=1)\
            price = st.number_input("\uc0\u21333 \u20154 \u20215 \u26684  ($)", min_value=0.0, step=1.0)\
            dm_name = st.text_input("\uc0\u20027 \u24320  DM")\
            script_date = st.date_input("\uc0\u26085 \u26399 ")\
            if st.form_submit_button("\uc0\u28155 \u21152 \u35760 \u24405 "):\
                if script_name and dm_name:\
                    new_script = pd.DataFrame(\{'\uc0\u21095 \u26412 \u21517 \u31216 ': [script_name], '\u20154 \u25968 \u37197 \u32622 ': [player_count], '\u21333 \u20154 \u20215 \u26684 ($)': [price], '\u20027 \u24320 DM': [dm_name], '\u26085 \u26399 ': [script_date]\})\
                    st.session_state['scripts_db'] = pd.concat([st.session_state['scripts_db'], new_script], ignore_index=True)\
                    st.success("\uc0\u28155 \u21152 \u25104 \u21151 \u65281 ")\
                else:\
                    st.error("\uc0\u35831 \u36755 \u20837 \u21095 \u26412 \u21517 \u31216 \u21644  DM \u22995 \u21517 \u65281 ")\
    with col2:\
        st.subheader("\uc0\u24403 \u21069 \u21095 \u26412 \u21015 \u34920 ")\
        st.dataframe(st.session_state['scripts_db'], use_container_width=True)\
\
with tab2:\
    col3, col4 = st.columns([1, 2])\
    with col3:\
        st.subheader("1. \uc0\u21592 \u24037 \u30331 \u35760 ")\
        with st.form("add_employee_form"):\
            emp_name = st.text_input("\uc0\u21592 \u24037 /DM \u22995 \u21517 ")\
            hourly_rate = st.number_input("\uc0\u22522 \u30784 \u26102 \u34218  ($)", min_value=0.0, step=0.5, value=15.0)\
            if st.form_submit_button("\uc0\u24405 \u20837 \u21592 \u24037 "):\
                if emp_name and emp_name not in st.session_state['employee_db']['\uc0\u21592 \u24037 \u22995 \u21517 '].values:\
                    new_emp = pd.DataFrame(\{'\uc0\u21592 \u24037 \u22995 \u21517 ': [emp_name], '\u26102 \u34218 ($)': [hourly_rate]\})\
                    st.session_state['employee_db'] = pd.concat([st.session_state['employee_db'], new_emp], ignore_index=True)\
                    st.success(f"\uc0\u24405 \u20837 \u25104 \u21151 \u65281 ")\
        \
        st.subheader("2. \uc0\u32771 \u21220 \u25171 \u21345 ")\
        employee_list = st.session_state['employee_db']['\uc0\u21592 \u24037 \u22995 \u21517 '].tolist()\
        if employee_list:\
            with st.form("add_attendance_form"):\
                selected_emp = st.selectbox("\uc0\u36873 \u25321 \u21592 \u24037 ", employee_list)\
                work_date = st.date_input("\uc0\u24037 \u20316 \u26085 \u26399 ")\
                work_hours = st.number_input("\uc0\u24037 \u20316 \u26102 \u38271  (\u23567 \u26102 )", min_value=0.0, step=0.5)\
                if st.form_submit_button("\uc0\u35760 \u24405 \u32771 \u21220 "):\
                    rate = st.session_state['employee_db'][st.session_state['employee_db']['\uc0\u21592 \u24037 \u22995 \u21517 '] == selected_emp]['\u26102 \u34218 ($)'].values[0]\
                    daily_salary = work_hours * rate\
                    new_attendance = pd.DataFrame(\{'\uc0\u25171 \u21345 \u26085 \u26399 ': [work_date], '\u21592 \u24037 \u22995 \u21517 ': [selected_emp], '\u24037 \u20316 \u26102 \u38271 (\u23567 \u26102 )': [work_hours], '\u24403 \u26085 \u34218 \u36164 ($)': [daily_salary]\})\
                    st.session_state['attendance_db'] = pd.concat([st.session_state['attendance_db'], new_attendance], ignore_index=True)\
                    st.success(f"\uc0\u24050 \u35760 \u24405 \u34218 \u36164 : $\{daily_salary:.2f\}")\
\
    with col4:\
        st.subheader("\uc0\u32771 \u21220 \u19982 \u34218 \u36164 \u35760 \u24405 \u34920 ")\
        st.write("\uc0\u55357 \u56517  \u27599 \u26085 \u32771 \u21220 \u26126 \u32454 ")\
        st.dataframe(st.session_state['attendance_db'], use_container_width=True)\
        if not st.session_state['attendance_db'].empty:\
            st.write("\uc0\u55357 \u56496  \u34218 \u36164 \u24635 \u35745 ")\
            summary_df = st.session_state['attendance_db'].groupby('\uc0\u21592 \u24037 \u22995 \u21517 ').agg(\u24635 \u24037 \u20316 \u26102 \u38271 =('\u24037 \u20316 \u26102 \u38271 (\u23567 \u26102 )', 'sum'), \u24635 \u24212 \u20184 \u34218 \u36164 =('\u24403 \u26085 \u34218 \u36164 ($)', 'sum')).reset_index()\
            st.dataframe(summary_df, use_container_width=True)}