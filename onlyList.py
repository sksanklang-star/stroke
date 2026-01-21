import streamlit as st
import pandas as pd
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Stroke Care Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS: CUSTOM TABLE STYLING (NOWRAP & LEFT HEADER) ---
st.markdown("""
<style>
    /* Global Font Settings */
    body, .stMarkdown, h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        color: black !important;
    }
    
    /* Header Title Style */
    h1, h2, h3 {
        font-size: 24px !important;
        font-weight: bold !important;
        margin-bottom: 20px !important;
    }

    /* --- CUSTOM TABLE STYLE --- */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 16px; !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
        border: 1px solid #dddddd;
    }
    
    .styled-table thead tr {
        background-color: #f0f2f6;
        color: black;
        font-weight: bold;
    }
    
    /* --- CHANGED: Target TH directly for alignment --- */
    .styled-table th {
        text-align: left !important; /* Force Left Align */
        padding: 12px 15px;
        color: black !important;
        border-bottom: 1px solid #dddddd;
        white-space: nowrap !important;
    }

    .styled-table td {
        padding: 12px 15px;
        color: black !important;
        border-bottom: 1px solid #dddddd;
        white-space: nowrap !important; /* Prevent line breaks */
    }
    
    .styled-table tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #ffffff;
    }
    
    .styled-table tbody tr:last-of-type {
        border-bottom: 2px solid #009879;
    }

    /* Hide toolbar */
    [data-testid="stElementToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# --- 3. LOAD & PROCESS DATA ---
@st.cache_data
def load_data():
    try:
        # Replace 'file.csv' with your actual file path
        df = pd.read_csv('file.csv') 
    except:
        return None

    # Processing Logic
    env_cols = df.columns[6:16] 
    
    # 1. Clean Village Name
    def get_moo(address):
        match = re.search(r'(?:หมู่|ม\.|Moo)\.?\s*(\d+)', str(address))
        return f"หมู่ {match.group(1)}" if match else "ไม่ระบุ"
    df['Village'] = df[df.columns[2]].apply(get_moo)

    # 2. Extract Name Column Index
    name_col = df.columns[1] 
    
    # 3. Calculate Risk Score
    df['Env_Risk_Score'] = df.apply(lambda row: sum(1 for c in env_cols if "ใช่" in str(row[c]) and "ไม่ใช่" not in str(row[c])), axis=1)
    
    # 4. Calculate ADL Score
    adl_cols = df.columns[16:26]
    df['ADL_Score'] = df[adl_cols].applymap(lambda x: int(str(x).strip()[0]) if pd.notna(x) and str(x).strip()[0].isdigit() else 0).sum(axis=1)
    
    # 5. ADL Group
    def categorize_adl(score):
        if score >= 12: return "กลุ่มที่ 1: ช่วยเหลือตัวเองได้ (12-20)"
        elif score >= 5: return "กลุ่มที่ 2: ดูแลตนเองได้บ้าง (5-11)"
        else: return "กลุ่มที่ 3: ช่วยเหลือตัวเองไม่ได้ (0-4)"
    df['ADL_Group'] = df['ADL_Score'].apply(categorize_adl)

    return df, name_col

data_load = load_data()

if data_load is None:
    st.error("ไม่พบไฟล์ 'file.csv' กรุณาตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์เดียวกัน")
    st.stop()

df, name_col_index = data_load

# --- 4. PREPARE TABLE DATA ---
table_df = df[[name_col_index, 'Village', 'ADL_Score', 'Env_Risk_Score', 'ADL_Group']].copy()
table_df.columns = ['ชื่อ-สกุล', 'หมู่บ้าน', 'คะแนน ADL (เต็ม 20)', 'คะแนนความเสี่ยงบ้าน (เต็ม 10)', 'กลุ่มอาการ']
table_df = table_df.sort_values(by='คะแนน ADL (เต็ม 20)', ascending=True)

# --- 5. RENDER PAGE ---

st.header("รายชื่อผู้ป่วยและคะแนนประเมิน (Patient List)")

# Convert DataFrame to HTML with the custom class
html_table = table_df.to_html(classes="styled-table", index=False, escape=False)

# Wrap in a div with overflow-x:auto to allow horizontal scrolling if the screen is too narrow
st.markdown(f'<div style="overflow-x: auto;">{html_table}</div>', unsafe_allow_html=True)