import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="รายงานการเงินโครงการ Stroke Care",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    /* Font & Global Colors */
    html, body, [class*="css"] {
        font-family: 'Sarabun', 'Prompt', sans-serif;
        color: #1e293b;
        background-color: #f1f5f9;
    }
    
    /* Headers */
    h1 { color: #0f172a; font-weight: 800; }
    h2, h3 { color: #334155; font-weight: 700; }
    
    /* Metrics */
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 5px solid #3b82f6;
    }
    .metric-label { font-size: 0.9rem; color: #64748b; }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #0f172a; }
    
    /* Charts */
    .chart-container {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Table */
    .styled-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .styled-table th { background-color: #f8fafc; text-align: left; padding: 12px; border-bottom: 2px solid #e2e8f0; }
    .styled-table td { padding: 12px; border-bottom: 1px solid #e2e8f0; }
    
    /* Hide Streamlit elements */
    [data-testid="stElementToolbar"] { display: none; }
    header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA PROCESSING ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel('payment.xlsx', header=1)
    except:
        return None, "File not found"

    # Clean & Rename
    df.columns = df.columns.str.strip()
    col_map = {'รายการ': 'Item', 'รายรับ': 'Income', 'รายจ่าย': 'Expense', 'คงเหลือ': 'Balance'}
    df = df.rename(columns=col_map)
    
    # Numeric Conversion
    for c in ['Income', 'Expense', 'Balance']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    df = df.dropna(subset=['Item'])
    
    # --- LOGIC 1: EXTRACT DATE FROM ITEM ---
    # We look for rows starting with "วันที่" and propagate that date down to subsequent rows
    df['Date_Group'] = df['Item'].apply(lambda x: x if str(x).startswith('วันที่') else None)
    df['Date_Group'] = df['Date_Group'].ffill() # Forward fill the date
    df['Date_Group'] = df['Date_Group'].fillna('ค่าใช้จ่ายอื่นๆ (Start)') # Handle initial rows

    # --- LOGIC 2: BUDGET & CATEGORY ---
    funding_row = df[df['Item'].str.contains('รับเงิน', na=False)].head(1)
    budget = funding_row['Income'].values[0] if not funding_row.empty else df['Income'].max()
    
    def categorize(i):
        i = str(i).lower()
        if any(x in i for x in ['อาหาร', 'เบรก', 'น้ำดื่ม', 'กาแฟ']): return 'ค่าอาหาร/เครื่องดื่ม'
        if any(x in i for x in ['เบี้ยเลี้ยง', 'ประชุม', 'วิทยากร', 'คณะทำงาน']): return 'ค่าตอบแทน/เบี้ยเลี้ยง'
        if any(x in i for x in ['เช่า', 'อุปกรณ์', 'วัสดุ']): return 'ค่าวัสดุ/อุปกรณ์'
        if any(x in i for x in ['ปักหมุด', 'สำรวจ', 'ลงพื้นที่']): return 'ค่าเดินทาง/ลงพื้นที่'
        if any(x in i for x in ['gemini', 'canva', 'รูปเล่ม', 'dadbord']): return 'ซอฟต์แวร์/รายงาน'
        return 'อื่นๆ'
    
    # Filter only actual expense rows (exclude the Date Header rows which usually have 0 expense)
    df_expenses = df[df['Expense'] > 0].copy()
    df_expenses['Category'] = df_expenses['Item'].apply(categorize)
    
    return budget, df_expenses

data = load_data()
if data[0] is None:
    st.error("Error loading data.")
    st.stop()

total_budget, df_exp = data
total_spend = df_exp['Expense'].sum()
balance = total_budget - total_spend
burn_rate = (total_spend / total_budget) * 100

# Prepare Data for Charts
df_exp = df_exp.reset_index(drop=True)
df_exp['Cumulative'] = df_exp['Expense'].cumsum()
df_exp['Run_Balance'] = total_budget - df_exp['Cumulative']

# --- 4. DASHBOARD LAYOUT ---

st.title("รายงานสรุปการเงินโครงการ Stroke Care")
st.markdown(f"**สถานะ:** ใช้งบประมาณ {burn_rate:.1f}% | **ยอดรวม:** ฿{total_budget:,.0f}")
st.markdown("---")

# KPI Cards
c1, c2, c3, c4 = st.columns(4)
def card(label, val, color):
    return f'<div class="metric-card" style="border-left-color: {color}"><div class="metric-label">{label}</div><div class="metric-value" style="color:{color}">{val}</div></div>'

with c1: st.markdown(card("งบประมาณรวม", f"฿{total_budget:,.0f}", "#2563eb"), unsafe_allow_html=True)
with c2: st.markdown(card("ใช้จ่ายไปแล้ว", f"฿{total_spend:,.0f}", "#ef4444"), unsafe_allow_html=True)
with c3: st.markdown(card("คงเหลือ", f"฿{balance:,.0f}", "#10b981"), unsafe_allow_html=True)
with c4: st.markdown(card("จำนวนรายการ", f"{len(df_exp)}", "#64748b"), unsafe_allow_html=True)

st.markdown("###")

# --- ROW 1: Burndown & Donut (Existing) ---
r1c1, r1c2 = st.columns([2, 1])

with r1c1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("กราฟแสดงงบประมาณคงเหลือ (Burndown)")
    fig_burn = go.Figure()
    fig_burn.add_trace(go.Scatter(y=df_exp['Run_Balance'], mode='lines', fill='tozeroy', name='คงเหลือ', line=dict(color='#2563eb')))
    fig_burn.update_layout(height=300, margin=dict(t=20, b=20), xaxis_title="ลำดับการเบิกจ่าย", yaxis_title="บาท")
    st.plotly_chart(fig_burn, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r1c2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("สัดส่วนค่าใช้จ่าย")
    cat_sum = df_exp.groupby('Category')['Expense'].sum().reset_index()
    fig_pie = px.pie(cat_sum, values='Expense', names='Category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Set2)
    fig_pie.update_layout(height=300, margin=dict(t=20, b=20), showlegend=False)
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ROW 2: NEW CHARTS (Daily Trend & Cumulative) ---
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("ยอดใช้จ่ายรายวัน (Daily Spending)")
    # Group by the extracted 'Date_Group'
    daily_sum = df_exp.groupby('Date_Group')['Expense'].sum().reset_index()
    # Attempt to sort by extracting date text if needed, here usually sorting by appearance is safer for mixed formats
    fig_daily = px.bar(daily_sum, x='Date_Group', y='Expense', text='Expense', color='Expense', color_continuous_scale='Reds')
    fig_daily.update_traces(texttemplate='฿%{text:,.0f}', textposition='outside')
    fig_daily.update_layout(height=350, xaxis_title=None, yaxis_title="บาท", showlegend=False)
    st.plotly_chart(fig_daily, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r2c2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("ยอดใช้จ่ายสะสม (Cumulative Spending)")
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(y=df_exp['Cumulative'], mode='lines+markers', name='สะสม', line=dict(color='#ef4444', width=3)))
    fig_cum.update_layout(height=350, xaxis_title="ลำดับรายการ", yaxis_title="บาทสะสม")
    st.plotly_chart(fig_cum, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ROW 3: TOP EXPENSES (Horizontal Bar) ---
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.subheader("10 อันดับ รายจ่ายสูงสุด (Top Spenders)")
top_10 = df_exp.sort_values(by='Expense', ascending=False).head(10)
fig_top = px.bar(top_10, x='Expense', y='Item', orientation='h', text='Expense', color='Expense', color_continuous_scale='Viridis')
fig_top.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="จำนวนเงิน (บาท)", height=400)
fig_top.update_traces(texttemplate='฿%{text:,.0f}', textposition='outside')
st.plotly_chart(fig_top, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- LEDGER ---
st.subheader("รายละเอียดรายการทั้งหมด")
display_df = df_exp[['Item', 'Date_Group', 'Category', 'Expense']].copy()
display_df.columns = ['รายการ', 'วันที่ (อ้างอิง)', 'หมวดหมู่', 'จำนวนเงิน']
display_df['จำนวนเงิน'] = display_df['จำนวนเงิน'].apply(lambda x: f"{x:,.0f}")
st.markdown(display_df.to_html(classes='styled-table', index=False), unsafe_allow_html=True)