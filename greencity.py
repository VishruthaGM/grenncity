import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =========================
# Page Setup
# =========================
st.set_page_config(page_title="💚 GreenCity Dashboard", layout="wide", page_icon="🏙️")
st.title("🏙️ GreenCity: Mini Smart City E-Waste Dashboard")
st.markdown("Simulated dashboard for battery health & e-waste in a smart city.")

# =========================
# Zones & Wards
# =========================
zones = ["Residential","Industrial","Commercial","Public Services"]
wards_per_zone = 2
ward_ids = [f"{zone[:3]}-W{i+1}" for zone in zones for i in range(wards_per_zone)]

# =========================
# Session State for Data
# =========================
if "city_data" not in st.session_state:
    st.session_state.city_data = pd.DataFrame(columns=[
        "Ward_ID", "Zone", "Battery_ID", "OCV", "Load_Voltage",
        "Current", "Temp", "Resistance", "Status"
    ])
if "battery_count" not in st.session_state:
    st.session_state.battery_count = 0

# =========================
# Simulate Battery Function
# =========================
def simulate_battery(ward, zone):
    st.session_state.battery_count += 1
    battery_id = f"BAT{st.session_state.battery_count}"
    ocv = np.round(np.random.uniform(1.2,1.6),2)
    lv = np.round(np.random.uniform(1.1,ocv),2)
    current = np.round(np.random.uniform(0.05,0.5),2)
    temp = np.round(np.random.uniform(20,40),1)
    resistance = np.round((ocv-lv)/current,2)

    # Status classification
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
# Add Battery
# =========================
st.subheader("⚡ Add a Random Battery to a Ward")
zone_choice = st.selectbox("Select Zone", zones)
ward_choice = st.selectbox("Select Ward", [f"{zone_choice[:3]}-W{i+1}" for i in range(wards_per_zone)])
if st.button("Add Battery"):
    new_bat = simulate_battery(ward_choice, zone_choice)
    st.session_state.city_data = pd.concat([st.session_state.city_data,pd.DataFrame([new_bat])], ignore_index=True)
    st.success(f"✅ {new_bat['Battery_ID']} added to {ward_choice}")

df = st.session_state.city_data
total = len(df)

# =========================
# Summary Metrics
# =========================
st.subheader("📊 Summary Metrics")
reusable = len(df[df['Status']=="Reusable"])
recyclable = len(df[df['Status']=="Recyclable"])
hazardous = len(df[df['Status']=="Hazardous"])

col1,col2,col3,col4 = st.columns(4)
col1.metric("Total Batteries", total)
col2.metric("Reusable 💚", reusable)
col3.metric("Recyclable 🟡", recyclable)
col4.metric("Hazardous 🔴", hazardous)

# =========================
# Ward Grid (with number of batteries)
# =========================
st.subheader("📍 Ward Grid Status")
if total > 0:
    ward_summary = df.groupby("Ward_ID")['Status'].value_counts().unstack(fill_value=0)
    ward_summary["Hazard_Percent"] = ward_summary.get("Hazardous",0)/ward_summary.sum(axis=1)*100
    ward_summary["Battery_Count"] = ward_summary.sum(axis=1)
    
    for zone in zones:
        st.markdown(f"**{zone} Zone**")
        zone_wards = [w for w in ward_ids if w.startswith(zone[:3])]
        cols = st.columns(len(zone_wards))
        for i, w in enumerate(zone_wards):
            if w in ward_summary.index:
                hazard_pct = ward_summary.loc[w]["Hazard_Percent"]
                battery_count = int(ward_summary.loc[w]["Battery_Count"])
            else:
                hazard_pct = 0
                battery_count = 0
            
            color = "green" if hazard_pct < 20 else "orange" if hazard_pct < 50 else "red"
            cols[i].markdown(
                f"<div style='background-color:{color};padding:20px;border-radius:10px;"
                f"text-align:center;box-shadow:2px 2px 10px rgba(0,0,0,0.2)'>"
                f"<strong>{w}</strong><br>"
                f"{hazard_pct:.1f}% Hazard<br>"
                f"🔋 {battery_count} Batteries"
                f"</div>",
                unsafe_allow_html=True
            )
# =========================
# Level selection (Ward / Zone / City) -- applies to both bar and pie charts
# =========================
st.subheader("📊 Battery Metrics Overview & Status Distribution")
level_choice = st.radio("Select Level", ["Ward","Zone","City"])

if level_choice=="Ward":
    selected_ward = st.selectbox("Select Ward", df["Ward_ID"].unique(), key="level_select")
    level_df = df[df["Ward_ID"]==selected_ward]
elif level_choice=="Zone":
    selected_zone = st.selectbox("Select Zone", df["Zone"].unique(), key="level_select")
    level_df = df[df["Zone"]==selected_zone]
else:
    level_df = df.copy()

# =========================
# Bar Charts in One Row
# =========================
metrics = ["OCV","Load_Voltage","Temp","Resistance"]
metric_titles = {
    "OCV":"🔋 Open Circuit Voltage (V)",
    "Load_Voltage":"⚡ Load Voltage (V)",
    "Temp":"🌡️ Temperature (°C)",
    "Resistance":"🛠️ Internal Resistance (Ω)"
}

cols = st.columns(4)
for i, metric in enumerate(metrics):
    fig = go.Figure()
    for idx,row in level_df.iterrows():
        color = {"Reusable":"green","Recyclable":"orange","Hazardous":"red"}[row["Status"]]
        fig.add_trace(go.Bar(
            x=[f"{row['Battery_ID']} ({row['Ward_ID']})"],
            y=[row[metric]],
            marker_color=color,
            text=[row[metric]],
            textposition="outside"
        ))
    if metric in ["OCV","Load_Voltage"]:
        fig.update_yaxes(range=[0,2])
    elif metric=="Temp":
        fig.update_yaxes(range=[0,50])
    elif metric=="Resistance":
        fig.update_yaxes(range=[0,2])
    fig.update_layout(showlegend=False, title=metric_titles[metric])
    cols[i].plotly_chart(fig,use_container_width=True)

# =========================
# Pie Chart for Same Level
# =========================
status_counts = level_df['Status'].value_counts().reset_index()
status_counts.columns = ["Status","Count"]

if len(status_counts)>0:
    fig_pie = px.pie(
        status_counts,
        names="Status",
        values="Count",
        color="Status",
        color_discrete_map={"Reusable":"green","Recyclable":"orange","Hazardous":"red"},
        title="🥧 Battery Status Breakdown"
    )
    fig_pie.update_traces(textinfo='percent+label', pull=[0.05,0.05,0.05])
    st.plotly_chart(fig_pie,use_container_width=True)
