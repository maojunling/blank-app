import streamlit as st
import pandas as pd
from pyvis.network import Network
import networkx as nx
import tempfile
import os

st.title("微服务调用链拓扑分析系统")

# 1. 数据上传或连接APM系统
uploaded_file = st.file_uploader("上传调用链数据(CSV/JSON)", type=['csv', 'json'])
if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_json(uploaded_file)
    
    # 2. 构建拓扑图
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
    
    # 添加节点（微服务）
    services = df['service_name'].unique()
    for service in services:
        # 根据错误率设置节点颜色
        error_rate = df[df['service_name'] == service]['error_rate'].mean()
        color = "#ff6b6b" if error_rate > 0.1 else "#4ecdc4" if error_rate > 0.05 else "#45b7d1"
        
        net.add_node(
            service, 
            label=service,
            color=color,
            size=df[df['service_name'] == service]['qps'].mean() / 10,  # 节点大小反映流量
            title=f"""
            服务名: {service}
            平均响应时间: {df[df['service_name'] == service]['response_time'].mean():.2f}ms
            错误率: {error_rate:.2%}
            QPS: {df[df['service_name'] == service]['qps'].mean():.0f}
            """
        )
    
    # 添加边（调用关系）
    for _, row in df.iterrows():
        if pd.notna(row['caller_service']):
            net.add_edge(
                row['caller_service'], 
                row['service_name'],
                value=row['call_count'],  # 边粗细反映调用次数
                title=f"调用次数: {row['call_count']}次"
            )
    
    # 3. 交互控制面板
    with st.sidebar:
        st.header("拓扑图配置")
        layout = st.selectbox("布局算法", ["力导向", "层次", "圆形"])
        show_labels = st.checkbox("显示标签", value=True)
        physics_enabled = st.checkbox("物理模拟", value=True)
        
        # 筛选条件
        min_qps = st.slider("最小QPS", 0, 1000, 10)
        max_error = st.slider("最大错误率", 0.0, 1.0, 0.3)
    
    # 4. 应用筛选条件
    filtered_services = df[
        (df['qps'] >= min_qps) & 
        (df['error_rate'] <= max_error)
    ]['service_name'].unique()
    
    # 5. 生成并显示拓扑图
    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "size": 14,
          "face": "Tahoma"
        }
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "smooth": false
      },
      "physics": {
        "enabled": """ + str(physics_enabled).lower() + """,
        "stabilization": {
          "iterations": 100
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200
      }
    }
    """)
    
    # 保存为HTML并在Streamlit中显示
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, 'r', encoding='utf-8') as f:
            html_content = f.read()
    
    st.components.v1.html(html_content, height=600)
    
    # 6. 附加分析功能
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总服务数", len(services))
    with col2:
        st.metric("异常服务", len([s for s in services if df[df['service_name'] == s]['error_rate'].mean() > 0.1]))
    with col3:
        st.metric("关键路径数", len([e for e in net.edges if net.get_edge_data(e[0], e[1])['value'] > 100]))
    
    # 7. 节点详情面板（点击交互）
    selected_service = st.selectbox("选择服务查看详情", services)
    if selected_service:
        service_data = df[df['service_name'] == selected_service]
        st.subheader(f"服务详情: {selected_service}")
        col1, col2 = st.columns(2)
        with col1:
            st.line_chart(service_data.set_index('timestamp')['response_time'])
        with col2:
            st.bar_chart(service_data['caller_service'].value_counts())
