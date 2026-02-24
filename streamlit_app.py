# app.py - 保存到GitHub
import streamlit as st
import pandas as pd
import sqlite3

st.title("员工数据查询系统")

# 连接数据库（这里用SQLite示例，实际可换为MySQL/PostgreSQL）
conn = sqlite3.connect('example.db')

# 创建查询表单
with st.sidebar:
    st.header("查询条件")
    department = st.selectbox("选择部门", ["全部", "技术部", "市场部", "人事部"])
    min_salary = st.slider("最低薪资", 0, 100000, 30000)
    
# 构建查询
query = "SELECT * FROM employees WHERE salary >= ?"
params = [min_salary]

if department != "全部":
    query += " AND department = ?"
    params.append(department)

# 执行查询
if st.button("查询"):
    df = pd.read_sql_query(query, conn, params=params)
    st.dataframe(df)
    
    # 显示统计信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总人数", len(df))
    with col2:
        st.metric("平均薪资", f"¥{df['salary'].mean():.0f}")
    with col3:
        st.metric("最高薪资", f"¥{df['salary'].max():.0f}")
