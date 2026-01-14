import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Stroke Care Dashboard",
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; }
    h1, h2, h3 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- 2. LOAD & PROCESS DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('file.csv') 
    except:
        return None

    # Processing Logic
    env_cols = df.columns[6:16] 
    env_labels_map = {
        df.columns[6]: "สีไม่ชัดเจน", df.columns[7]: "พื้นลื่น/มีพรม",
        df.columns[8]: "ของวางเกะกะ", df.columns[9]: "แสงสว่างน้อย",
        df.columns[10]: "แสงเปลี่ยนกะทันหัน", df.columns[11]: "ไม่มีราวพยุง",
        df.columns[12]: "ห้องนอนชั้นบน", df.columns[13]: "เตียงสูง/ต่ำเกินไป",
        df.columns[14]: "พื้นต่างระดับ", df.columns[15]: "ระบายอากาศไม่ดี"
    }
    
    # 1. Clean Village Name
    def get_moo(address):
        match = re.search(r'(?:หมู่|ม\.|Moo)\.?\s*(\d+)', str(address))
        return f"หมู่ {match.group(1)}" if match else "ไม่ระบุ"
    df['Village'] = df[df.columns[2]].apply(get_moo)

    # 2. EXTRACT SEX FROM NAME
    name_col = df.columns[1] 
    def extract_sex(name):
        n = str(name).strip()
        if n.startswith("นาย"):
            return "ชาย"
        elif n.startswith("นาง") or n.startswith("นางสาว") or n.startswith("น.ส."):
            return "หญิง"
        else:
            return "ไม่ระบุ"
    df['Sex'] = df[name_col].apply(extract_sex)
    
    # 3. Calculate Risk Score
    df['Env_Risk_Score'] = df.apply(lambda row: sum(1 for c in env_cols if "ใช่" in str(row[c]) and "ไม่ใช่" not in str(row[c])), axis=1)
    
    # 4. Calculate ADL Score
    adl_cols = df.columns[16:26]
    df['ADL_Score'] = df[adl_cols].applymap(lambda x: int(str(x).strip()[0]) if pd.notna(x) and str(x).strip()[0].isdigit() else 0).sum(axis=1)
    
    # 5. ADL Group
    def categorize_adl(score):
        if score >= 12: 
            return "กลุ่มที่ 1: ช่วยเหลือตัวเองได้ (12-20)"
        elif score >= 5: 
            return "กลุ่มที่ 2: ดูแลตนเองได้บ้าง (5-11)"
        else: 
            return "กลุ่มที่ 3: ช่วยเหลือตัวเองไม่ได้ (0-4)"
    df['ADL_Group'] = df['ADL_Score'].apply(categorize_adl)

    # 6. Mobility Status
    mobility_col = df.columns[20]
    mobility_map = {'3': "ช่วยเหลือตัวเองได้", '2': "ต้องการผู้ช่วย", '1': "นั่งรถเข็น", '0': "ติดเตียง"}
    df['Mobility_Label'] = df[mobility_col].astype(str).str[0].map(mobility_map).fillna("ไม่ระบุ")

    return df, env_cols, env_labels_map, name_col

data_load = load_data()
if data_load is None:
    st.error("ไม่พบไฟล์ 'file.csv' กรุณาตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์เดียวกัน")
    st.stop()
df, env_cols, env_labels_map, name_col_index = data_load

# KPI Calculations
total_patients = len(df)
critical_df = df[(df['ADL_Score'] < 10) & (df['Env_Risk_Score'] >= 3)]
critical_count = len(critical_df)
risky_homes = len(df[df['Env_Risk_Score'] >= 5])
bedridden = len(df[df['Mobility_Label'] == 'ติดเตียง'])

# --- 3. DASHBOARD LAYOUT ---

# HEADER
st.title("Dashboard สรุปสถานการณ์ผู้ป่วยและการประเมินความเสี่ยง")
st.markdown("โครงการปรับสภาพแวดล้อมที่อยู่อาศัยสำหรับผู้ป่วย Stroke")
st.markdown("---")

# ROW 1: KPI CARDS
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="ผู้ป่วยทั้งหมด (Total)", value=f"{total_patients} คน")
with col2:
    st.metric(label="กลุ่มวิกฤต (Critical)", value=f"{critical_count} คน", delta="ความเสี่ยงสูง", delta_color="inverse")
with col3:
    st.metric(label="บ้านเสี่ยงสูง (>5 จุด)", value=f"{risky_homes} หลัง")
with col4:
    st.metric(label="ผู้ป่วยติดเตียง", value=f"{bedridden} คน")

st.markdown("###")

# --- ROW 2: LOCATION & DEMOGRAPHICS ---
r2_c1, r2_c2 = st.columns(2)

with r2_c1:
    st.subheader("จำนวนผู้ป่วยแยกตามหมู่บ้าน")
    village_counts = df['Village'].value_counts().reset_index()
    village_counts.columns = ['Village', 'Count']
    fig_village = px.bar(village_counts, x='Village', y='Count', text='Count', 
                         color_discrete_sequence=['#475569'])
    fig_village.update_layout(xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig_village, use_container_width=True)

with r2_c2:
    st.subheader("สัดส่วนเพศ (ชาย/หญิง)")
    sex_counts = df['Sex'].value_counts().reset_index()
    sex_counts.columns = ['Sex', 'Count']
    color_map_sex = {'ชาย': '#3b82f6', 'หญิง': '#ec4899', 'ไม่ระบุ': '#94a3b8'}
    
    fig_sex = px.pie(sex_counts, values='Count', names='Sex', hole=0.4,
                     color='Sex', color_discrete_map=color_map_sex)
    fig_sex.update_traces(textposition='outside', texttemplate='%{percent:.0%} ( %{value} คน )<br>%{label}')
    fig_sex.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig_sex, use_container_width=True)

st.markdown("---")

# --- ROW 3: HEALTH STATUS ---
r3_c1, r3_c2 = st.columns(2)

with r3_c1:
    st.subheader("สถานะการเคลื่อนไหว")
    mobility_counts = df['Mobility_Label'].value_counts().reset_index()
    mobility_counts.columns = ['Status', 'Count']
    
    fig_mob = px.bar(mobility_counts, x='Status', y='Count', text='Count',
                     color='Status', color_discrete_sequence=px.colors.sequential.Tealgrn_r)
    fig_mob.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False)
    st.plotly_chart(fig_mob, use_container_width=True)

with r3_c2:
    st.subheader("ระดับความพึ่งพิง (ADL Group)")
    order = [
        "กลุ่มที่ 3: ช่วยเหลือตัวเองไม่ได้ (0-4)",
        "กลุ่มที่ 2: ดูแลตนเองได้บ้าง (5-11)",
        "กลุ่มที่ 1: ช่วยเหลือตัวเองได้ (12-20)"
    ]
    adl_counts = df['ADL_Group'].value_counts().reindex(order, fill_value=0).reset_index()
    adl_counts.columns = ['Group', 'Count']
    
    color_map_adl = {
        "กลุ่มที่ 3: ช่วยเหลือตัวเองไม่ได้ (0-4)": "#ef4444", 
        "กลุ่มที่ 2: ดูแลตนเองได้บ้าง (5-11)": "#f59e0b",
        "กลุ่มที่ 1: ช่วยเหลือตัวเองได้ (12-20)": "#10b981"
    }
    
    fig_adl = px.pie(adl_counts, values='Count', names='Group', hole=0.4,
                     color='Group', color_discrete_map=color_map_adl)
    
    fig_adl.update_traces(textposition='outside', texttemplate='%{label}<br>%{percent:.0%} ( %{value} คน )')
    fig_adl.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig_adl, use_container_width=True)

st.markdown("---")

# --- ROW 4: RISKS & ANALYSIS ---
r4_c1, r4_c2 = st.columns(2)

with r4_c1:
    st.subheader("ความเสี่ยงสภาพแวดล้อมที่พบมากที่สุด")
    risk_data = {}
    for col in env_cols:
        label = env_labels_map.get(col, col)
        count = df[col].astype(str).apply(lambda x: "ใช่" in x and "ไม่ใช่" not in x).sum()
        risk_data[label] = count
    
    risk_df = pd.DataFrame(list(risk_data.items()), columns=['Risk', 'Count']).sort_values('Count', ascending=True)
    
    fig_risk = px.bar(risk_df, x='Count', y='Risk', text='Count', orientation='h',
                      color='Count', color_continuous_scale='Blues')
    fig_risk.update_layout(xaxis_title="จำนวนเคส", yaxis_title=None, showlegend=False)
    st.plotly_chart(fig_risk, use_container_width=True)

with r4_c2:
    st.subheader("Matrix: สุขภาพ vs ความเสี่ยงบ้าน")
    fig_scatter = px.scatter(df, x='ADL_Score', y='Env_Risk_Score', 
                             color='Env_Risk_Score', size_max=15,
                             hover_data=[df.columns[1], 'Village'],
                             color_continuous_scale='Reds',
                             labels={'ADL_Score': 'คะแนนสุขภาพ (ADL)', 'Env_Risk_Score': 'คะแนนความเสี่ยงบ้าน'})
    
    fig_scatter.add_shape(type="rect", x0=0, y0=5, x1=10, y1=10, line=dict(color="Red", width=2, dash="dash"))
    fig_scatter.add_annotation(x=5, y=9.5, text="CRITICAL ZONE", showarrow=False, font=dict(color="red", size=14))
    
    fig_scatter.update_xaxes(range=[-1, 21])
    fig_scatter.update_yaxes(range=[-1, 11])
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- NEW SECTION: PROJECT PROGRESS ---
st.markdown("---")
st.header("📅 ความคืบหน้าโครงการ (Project Progress)")

# Mock Data
progress_data = {
    "Task": [
        "1.การแต่งตั้งคณะทำงาน",
        "2.กระบวนการคัดเลือกกลุ่มตัวอย่าง และจัดเก็บข้อมูล",
        "3.ประชุมคณะทำงาน & ที่ปรึกษา",
        "4.ประชุมอบรม Caregiver และ อสม. ผู้ดูแล",
        "5.ลงสำรวจเก็บข้อมูล Pre-test & ขอความยินยอม",
        "6.ตรวจสอบความถูกต้องและครบถ้วนของข้อมูล",
        "7.การพัฒนาออกแบบ ท่ากายภาพบำบัด ต้นแบบ และการ Training",
        "8.การพัฒนา Software ต้นแบบและการ Training"
    ],
    "Progress": [100, 100, 100, 100, 100, 100, 100, 100]
}
df_progress = pd.DataFrame(progress_data)
# Reverse to show top-down
df_progress = df_progress.iloc[::-1]

# Use Columns to CENTER and REDUCE WIDTH
# [1, 3, 1] means: Left Gap (1 part), Chart (3 parts), Right Gap (1 part)
# This effectively centers the chart and makes it ~60% width.
c_left, c_center, c_right = st.columns([1, 5, 1])

with c_center:
    # Horizontal Bar Chart
    fig_prog = px.bar(df_progress, x='Progress', y='Task', text='Progress', orientation='h',
                      color_discrete_sequence=['#10b981']) # Professional Green

    fig_prog.update_traces(texttemplate='%{text}%', textposition='inside')
    fig_prog.update_layout(
        xaxis_title="ความสำเร็จ (%)",
        yaxis_title=None,
        xaxis=dict(range=[0, 105], showgrid=True),
        height=400,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig_prog, use_container_width=True)

# --- ACTION PLAN ---
st.markdown("---")
st.header("การวิเคราะห์เชิงลึกและแผนดำเนินการ (Action Plan)")

if not village_counts.empty:
    top_village = village_counts.iloc[0]
else:
    top_village = {'Village': 'ไม่มีข้อมูล', 'Count': 0}
if not risk_df.empty:
    top_risk = risk_df.iloc[-1]
else:
    top_risk = {'Risk': 'ไม่มีข้อมูล', 'Count': 0}

st.info(f"**1. พื้นที่เป้าหมายเร่งด่วน:** **{top_village['Village']}** (พบผู้ป่วย {top_village['Count']} ราย) - ควรจัดทีม Mobile Unit ลงพื้นที่นี้เป็นลำดับแรก")
st.error(f"**2. กลุ่มเป้าหมายวิกฤต (Critical Target):** พบผู้ป่วย **{critical_count} ราย** ที่มีปัญหาสุขภาพรุนแรงและอาศัยในบ้านเสี่ยงสูง - การดำเนินการ: ติดตั้งราวจับและปรับพื้นห้องน้ำทันที")
st.warning(f"**3. ความเสี่ยงภาพรวม:** ปัญหาที่พบมากที่สุดคือ **\"{top_risk['Risk']}\"** ({top_risk['Count']} ครัวเรือน) - ควรจัดหางบประมาณเพื่อจัดซื้ออุปกรณ์แก้ไขปัญหานี้โดยเฉพาะ")

# --- PATIENT DATA TABLE ---
st.markdown("---")
st.header("📋 รายชื่อผู้ป่วยและคะแนนประเมิน (Patient List)")

table_df = df[[name_col_index, 'Village', 'ADL_Score', 'Env_Risk_Score', 'ADL_Group']].copy()
table_df.columns = ['ชื่อ-สกุล', 'หมู่บ้าน', 'คะแนน ADL (เต็ม 20)', 'คะแนนความเสี่ยงบ้าน (เต็ม 10)', 'กลุ่มอาการ']
table_df = table_df.sort_values(by='คะแนน ADL (เต็ม 20)', ascending=True)

st.dataframe(table_df, use_container_width=True)