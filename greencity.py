import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

# =========================
# Page Config
# =========================
st.set_page_config(page_title="💚 GreenCity Dashboard", layout="wide", page_icon="🏙️")
st.title("🏙️ GreenCity: Mini Smart City E-Waste Dashboard")

# =========================
# Setup Zones & Wards
# =========================
zones = ["Residential", "Industrial", "Commercial", "Public Services"]
wards_per_zone = 2
ward_ids = [f"{zone[:3]}-W{i+1}" for zone in zones for i in range(wards_per_zone)]

# =========================
# Session State
# =========================
if "city_data" not in st.session_state:
    st.session_state.city_data = pd.DataFrame(columns=[
        "Ward_ID", "Zone", "Battery_ID", "OCV", "Load_Voltage",
        "Current", "Temp", "Resistance", "Status"
    ])
if "battery_count" not in st.session_state:
    st.session_state.battery_count = 0

# =========================
# Simulate Battery
# =========================
def simulate_battery(ward, zone):
    st.session_state.battery_count += 1
    battery_id = f"BAT{st.session_state.battery_count}"
    ocv = np.round(np.random.uniform(1.2,1.6),2)
    lv = np.round(np.random.uniform(1.1,ocv),2)
    current = np.round(np.random.uniform(0.05,0.5),2)
    temp = np.round(np.random.uniform(20,40),1)
    resistance = np.round((ocv-lv)/current,2)
    
    # Classification
    if temp>40 or resistance>1.0 or ocv<1.3:
        status="Hazardous"
    elif resistance<=0.5 and ocv>=1.5:
        status="Reusable"
    else:
        status="Recyclable"
    
    return {"Ward_ID":ward,"Zone":zone,"Battery_ID":battery_id,"OCV":ocv,
            "Load_Voltage":lv,"Current":current,"Temp":temp,"Resistance":resistance,
            "Status":status}

# =========================
# Add Battery Button
# =========================
st.subheader("⚡ Process Random Battery")
zone_choice = st.selectbox("Select Zone", zones)
ward_choice = st.selectbox("Select Ward", [f"{zone_choice[:3]}-W{i+1}" for i in range(wards_per_zone)])
if st.button("Add Battery to Ward"):
    progress = st.progress(0)
    for i in range(0,101,25):
        time.sleep(0.1)
        progress.progress(i)
    new_bat = simulate_battery(ward_choice, zone_choice)
    st.session_state.city_data = pd.concat([st.session_state.city_data,pd.DataFrame([new_bat])])
    st.success(f"✅ {new_bat['Battery_ID']} added to {ward_choice}")

# =========================
# Prepare Summary
# =========================
df = st.session_state.city_data
total = len(df)
reusable = len(df[df['Status']=="Reusable"])
recyclable = len(df[df['Status']=="Recyclable"])
hazardous = len(df[df['Status']=="Hazardous"])

col1,col2,col3,col4 = st.columns(4)
col1.metric("Total Batteries", total)
col2.metric("Reusable 💚", reusable, f"{reusable/total*100:.1f}%" if total>0 else "0%")
col3.metric("Recyclable 🟡", recyclable, f"{recyclable/total*100:.1f}%" if total>0 else "0%")
col4.metric("Hazardous 🔴", hazardous, f"{hazardous/total*100:.1f}%" if total>0 else "0%")

st.markdown("---")

# =========================
# Ward Grid Heatmap
# =========================
st.subheader("📍 City Ward Status Grid")
if total>0:
    ward_summary = df.groupby("Ward_ID")['Status'].value_counts().unstack(fill_value=0)
    ward_summary["Hazard_Percent"] = ward_summary.get("Hazardous",0)/ward_summary.sum(axis=1)*100
    # Grid display: color-coded hazard %
    for zone in zones:
        st.markdown(f"**{zone} Zone**")
        zone_wards = [w for w in ward_ids if w.startswith(zone[:3])]
        cols = st.columns(len(zone_wards))
        for i,w in enumerate(zone_wards):
            hazard_pct = ward_summary.loc[w]["Hazard_Percent"] if w in ward_summary.index else 0
            color = "green" if hazard_pct<20 else "orange" if hazard_pct<50 else "red"
            cols[i].markdown(f"<div style='background-color:{color};padding:20px;border-radius:10px;text-align:center'><strong>{w}</strong><br>{hazard_pct:.1f}% Hazard</div>",unsafe_allow_html=True)

# =========================
# Ward-level Graphs
# =========================
st.subheader("📊 Ward-level Battery Stats")
if total>0:
    selected_ward = st.selectbox("Select Ward to View Stats", df["Ward_ID"].unique())
    ward_df = df[df["Ward_ID"]==selected_ward]
    
    # OCV Bar Graph
    st.markdown("**🔋 Open Circuit Voltage (V)**")
    fig_ocv = go.Figure()
    for idx,row in ward_df.iterrows():
        color={"Reusable":"green","Recyclable":"orange","Hazardous":"red"}[row["Status"]]
        fig_ocv.add_trace(go.Bar(x=[row["Battery_ID"]],y=[row["OCV"]],
                                 marker_color=color,text=[row["OCV"]],textposition="outside"))
    fig_ocv.update_layout(showlegend=False,yaxis=dict(range=[0,2]))
    st.plotly_chart(fig_ocv,use_container_width=True)
    
    # Pie Chart
    st.markdown("**📊 Status Distribution**")
    ward_counts = ward_df['Status'].value_counts().reindex(['Reusable','Recyclable','Hazardous'],fill_value=0)
    fig_pie = px.pie(names=ward_counts.index, values=ward_counts.values,
                     color=ward_counts.index,
                     color_discrete_map={"Reusable":"green","Recyclable":"orange","Hazardous":"red"})
    st.plotly_chart(fig_pie,use_container_width=True)

# =========================
# Ward Table
# =========================
if total>0:
    st.subheader("📝 Ward Battery Details")
    icon_map = {"Reusable":"💚","Recyclable":"🟡","Hazardous":"🔴"}
    display_df = df.copy()
    display_df["Status"] = display_df["Status"].map(lambda x: f"{icon_map[x]} {x}")
    st.dataframe(display_df)

# =========================
# Hazard Alert
# =========================
if hazardous>0:
    st.warning(f"⚠️ {hazardous} hazardous batteries detected city-wide! Handle with care!")
