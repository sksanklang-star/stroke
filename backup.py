import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Stroke Care Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. MODERN UI SYSTEM (CSS) ---
st.markdown("""
<style>
    /* Import Google Font 'Sarabun' for professional Thai text */
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;700&display=swap');
    
    * { font-family: 'Sarabun', sans-serif; }

    /* App Background */
    .stApp {
        background-color: #f1f5f9; /* Slate-100 */
    }

    /* Top Navigation Bar Styling */
    .nav-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    /* Card Styling */
    .css-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
        border: 1px solid #e2e8f0;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricLabel"] { font-size: 14px; color: #64748b; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #0f172a; font-weight: 700; }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: white;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        padding: 0 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0f172a; /* Dark Slate */
        color: white;
    }
    
    /* Headers */
    h1 { color: #0f172a; font-weight: 700; font-size: 28px; margin-bottom: 0; }
    h3 { color: #334155; font-size: 18px; font-weight: 600; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA PROCESSING ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('file.csv') 
    except:
        st.error("System Error: 'file.csv' not found. Please ensure the file is in the same folder.")
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

    # 2. Extract Sex
    name_col = df.columns[1] 
    def extract_sex(name):
        n = str(name).strip()
        if n.startswith("นาย"): return "ชาย"
        elif n.startswith("นาง") or n.startswith("นางสาว") or n.startswith("น.ส."): return "หญิง"
        else: return "ไม่ระบุ"
    df['Sex'] = df[name_col].apply(extract_sex)
    
    # 3. Risk Score
    df['Env_Risk_Score'] = df.apply(lambda row: sum(1 for c in env_cols if "ใช่" in str(row[c]) and "ไม่ใช่" not in str(row[c])), axis=1)
    
    # 4. ADL Score
    adl_cols = df.columns[16:26]
    df['ADL_Score'] = df[adl_cols].applymap(lambda x: int(str(x).strip()[0]) if pd.notna(x) and str(x).strip()[0].isdigit() else 0).sum(axis=1)
    
    # 5. ADL Group
    def categorize_adl(score):
        if score >= 12: return "กลุ่มที่ 1: ช่วยเหลือตัวเองได้ (12-20)"
        elif score >= 5: return "กลุ่มที่ 2: ดูแลตนเองได้บ้าง (5-11)"
        else: return "กลุ่มที่ 3: ช่วยเหลือตัวเองไม่ได้ (0-4)"
    df['ADL_Group'] = df['ADL_Score'].apply(categorize_adl)

    # 6. Mobility Status
    mobility_col = df.columns[20]
    mobility_map = {'3': "ช่วยเหลือตัวเองได้", '2': "ต้องการผู้ช่วย", '1': "นั่งรถเข็น", '0': "ติดเตียง"}
    df['Mobility_Label'] = df[mobility_col].astype(str).str[0].map(mobility_map).fillna("ไม่ระบุ")

    return df, env_cols, env_labels_map, name_col

# Load Data
data_load = load_data()
if data_load is None:
    st.stop()
df_original, env_cols, env_labels_map, name_col_index = data_load

# --- 4. TOP CONTROL BAR (Nav & Filters) ---
with st.container():
    # Header Section
    c1, c2 = st.columns([2, 1])
    with c1:
        st.title("Stroke Care Intelligence")
        st.markdown("<div style='color: #64748b; margin-top: -10px;'>ระบบวิเคราะห์ข้อมูลผู้ป่วยและสภาพแวดล้อมเพื่อการตัดสินใจ</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Filter Section (Moved to Top)
    with st.expander("ตัวกรองข้อมูล (Filters)", expanded=True):
        f1, f2, f3 = st.columns([1, 1, 2])
        with f1:
            all_villages = sorted(df_original['Village'].unique())
            selected_villages = st.multiselect("เลือกหมู่บ้าน:", all_villages, default=all_villages)
        with f2:
            all_sex = sorted(df_original['Sex'].unique())
            selected_sex = st.multiselect("เลือกเพศ:", all_sex, default=all_sex)
        with f3:
            st.markdown("") # Spacer

# Apply Filters
df = df_original.copy()
if selected_villages:
    df = df[df['Village'].isin(selected_villages)]
if selected_sex:
    df = df[df['Sex'].isin(selected_sex)]

# --- 5. MAIN DASHBOARD CONTENT ---

# KPI Calculations
total_patients = len(df)
critical_df = df[(df['ADL_Score'] < 10) & (df['Env_Risk_Score'] >= 3)]
critical_count = len(critical_df)
risky_homes = len(df[df['Env_Risk_Score'] >= 5])
bedridden = len(df[df['Mobility_Label'] == 'ติดเตียง'])

st.markdown("### ภาพรวมโครงการ (Project Overview)")

# KPI ROW
k1, k2, k3, k4 = st.columns(4)
k1.metric("ผู้ป่วยทั้งหมด", f"{total_patients} คน")
k2.metric("กลุ่มวิกฤต (Critical)", f"{critical_count} คน", "High Priority", delta_color="inverse")
k3.metric("บ้านเสี่ยงสูง (>5 จุด)", f"{risky_homes} หลัง", "Need Improvement", delta_color="inverse")
k4.metric("ผู้ป่วยติดเตียง", f"{bedridden} คน", "Special Care")

st.markdown("###") # Spacer

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["ภาพรวมพื้นที่", "สุขภาพผู้ป่วย", "ความเสี่ยงบ้าน", "ฐานข้อมูล"])

# --- TAB 1: OVERVIEW ---
with tab1:
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown('<div class="css-card"><h3>จำนวนผู้ป่วยแยกตามหมู่บ้าน</h3>', unsafe_allow_html=True)
        village_counts = df['Village'].value_counts().reset_index()
        village_counts.columns = ['Village', 'Count']
        fig_v = px.bar(village_counts, x='Village', y='Count', text='Count', color_discrete_sequence=['#334155'])
        fig_v.update_traces(textposition='outside')
        fig_v.update_layout(xaxis_title=None, yaxis_title=None, plot_bgcolor='white', margin=dict(t=10, b=10))
        st.plotly_chart(fig_v, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="css-card"><h3>สัดส่วนเพศ</h3>', unsafe_allow_html=True)
        sex_counts = df['Sex'].value_counts().reset_index()
        sex_counts.columns = ['Sex', 'Count']
        fig_s = px.pie(sex_counts, values='Count', names='Sex', hole=0.6,
                       color='Sex', color_discrete_map={'ชาย': '#6366f1', 'หญิง': '#ec4899', 'ไม่ระบุ': '#cbd5e1'})
        fig_s.update_traces(textposition='outside', texttemplate='%{percent:.0%} (%{value})<br>%{label}')
        
        # FIX: Increased margins to prevent overflow
        fig_s.update_layout(showlegend=False, margin=dict(t=30, b=30, l=60, r=60))
        
        st.plotly_chart(fig_s, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Action Plan (Styled Box)
    st.markdown("### แผนดำเนินการเร่งด่วน (Action Plan)")
    
    if not village_counts.empty: top_moo = village_counts.iloc[0]['Village']
    else: top_moo = "-"
    
    risk_data_all = {}
    for col in env_cols:
        count = df[col].astype(str).apply(lambda x: "ใช่" in x and "ไม่ใช่" not in x).sum()
        risk_data_all[env_labels_map[col]] = count
    if risk_data_all:
        top_risk_name = max(risk_data_all, key=risk_data_all.get)
    else:
        top_risk_name = "-"

    ap1, ap2, ap3 = st.columns(3)
    ap1.info(f"**พื้นที่เป้าหมายหลัก:**\n\n### {top_moo}\n\nพบผู้ป่วยหนาแน่นที่สุด ควรลงพื้นที่ก่อน")
    ap2.error(f"**กลุ่มวิกฤต:**\n\n### {critical_count} ราย\n\nต้องติดตั้งราวจับ/ปรับพื้นทันที")
    ap3.warning(f"**จุดเสี่ยงสำคัญ:**\n\n### {top_risk_name}\n\nจัดซื้องบประมาณแก้ไขจุดนี้")

# --- TAB 2: HEALTH ---
with tab2:
    h1, h2 = st.columns(2)
    
    with h1:
        st.markdown('<div class="css-card"><h3>สถานะการเคลื่อนไหว</h3>', unsafe_allow_html=True)
        mob_counts = df['Mobility_Label'].value_counts().reset_index()
        mob_counts.columns = ['Status', 'Count']
        fig_mob = px.bar(mob_counts, x='Status', y='Count', text='Count', 
                         color='Status', color_discrete_sequence=px.colors.qualitative.Prism)
        fig_mob.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False, plot_bgcolor='white')
        st.plotly_chart(fig_mob, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with h2:
        st.markdown('<div class="css-card"><h3>ระดับความพึ่งพิง (ADL Group)</h3>', unsafe_allow_html=True)
        order_adl = ["กลุ่มที่ 3: ช่วยเหลือตัวเองไม่ได้ (0-4)", "กลุ่มที่ 2: ดูแลตนเองได้บ้าง (5-11)", "กลุ่มที่ 1: ช่วยเหลือตัวเองได้ (12-20)"]
        adl_counts = df['ADL_Group'].value_counts().reindex(order_adl, fill_value=0).reset_index()
        adl_counts.columns = ['Group', 'Count']
        
        # Colors: Red -> Amber -> Emerald
        color_map_adl = {
            "กลุ่มที่ 3: ช่วยเหลือตัวเองไม่ได้ (0-4)": "#ef4444", 
            "กลุ่มที่ 2: ดูแลตนเองได้บ้าง (5-11)": "#f59e0b",
            "กลุ่มที่ 1: ช่วยเหลือตัวเองได้ (12-20)": "#10b981"
        }
        fig_adl = px.pie(adl_counts, values='Count', names='Group', hole=0.5, color='Group', color_discrete_map=color_map_adl)
        fig_adl.update_traces(textposition='outside', texttemplate='%{label}<br>%{percent:.0%} (%{value})')
        
        # FIX: Increased margins heavily for ADL Chart because labels are long
        fig_adl.update_layout(showlegend=False, margin=dict(t=50, b=50, l=80, r=80))
        
        st.plotly_chart(fig_adl, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: RISKS ---
with tab3:
    r1, r2 = st.columns(2)
    
    with r1:
        st.markdown('<div class="css-card"><h3>ความเสี่ยงที่พบมากที่สุด</h3>', unsafe_allow_html=True)
        # Recalculate
        risk_data = {}
        for col in env_cols:
            lbl = env_labels_map.get(col, col)
            cnt = df[col].astype(str).apply(lambda x: "ใช่" in x and "ไม่ใช่" not in x).sum()
            risk_data[lbl] = cnt
        risk_df = pd.DataFrame(list(risk_data.items()), columns=['Risk', 'Count']).sort_values('Count', ascending=True)
        
        # Colorscale 'Blues' (Safe built-in scale)
        fig_r = px.bar(risk_df, x='Count', y='Risk', text='Count', orientation='h', color='Count', color_continuous_scale='Blues')
        fig_r.update_layout(xaxis_title="จำนวนหลัง", yaxis_title=None, showlegend=False, plot_bgcolor='white', height=400)
        st.plotly_chart(fig_r, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with r2:
        st.markdown('<div class="css-card"><h3>Matrix: สุขภาพ vs ความเสี่ยงบ้าน</h3>', unsafe_allow_html=True)
        fig_sc = px.scatter(df, x='ADL_Score', y='Env_Risk_Score', color='Env_Risk_Score', 
                            size_max=15, hover_data=[name_col_index, 'Village'], color_continuous_scale='Reds')
        
        # Critical Zone
        fig_sc.add_shape(type="rect", x0=0, y0=5, x1=10, y1=10, line=dict(color="Red", width=2, dash="dash"))
        fig_sc.add_annotation(x=5, y=9.5, text="CRITICAL ZONE", showarrow=False, font=dict(color="red", size=14))
        
        fig_sc.update_xaxes(range=[-1, 21], title="ADL Score (สุขภาพ)")
        fig_sc.update_yaxes(range=[-1, 11], title="Risk Score (บ้าน)")
        fig_sc.update_layout(plot_bgcolor='#f8fafc', height=400)
        st.plotly_chart(fig_sc, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: DATABASE ---
with tab4:
    st.markdown("### ฐานข้อมูลผู้ป่วย (Database)")
    
    table_df = df[[name_col_index, 'Village', 'Sex', 'ADL_Score', 'ADL_Group', 'Env_Risk_Score', 'Mobility_Label']].copy()
    table_df.columns = ['ชื่อ-สกุล', 'หมู่บ้าน', 'เพศ', 'คะแนน ADL', 'กลุ่ม ADL', 'คะแนนความเสี่ยง', 'การเคลื่อนไหว']
    
    # Highlight Logic
    def highlight_critical(row):
        # Light Red background for Critical
        if row['คะแนน ADL'] < 10 and row['คะแนนความเสี่ยง'] >= 3:
            return ['background-color: #fee2e2; color: #991b1b'] * len(row)
        return [''] * len(row)

    st.dataframe(
        table_df.style.apply(highlight_critical, axis=1), 
        use_container_width=True,
        height=600
    )