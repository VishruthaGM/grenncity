import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
# Session State
# =========================
if "city_data" not in st.session_state:
    st.session_state.city_data = pd.DataFrame(columns=[
        "Ward_ID", "Zone", "Battery_ID", "OCV", "Load_Voltage",
        "Current", "Temp", "Resistance", "Status"
    ])
if "battery_count" not in st.session_state:
    st.session_state.battery_count = 0
if "selection" not in st.session_state:
    st.session_state.selection = {"level":"City","zone":None,"ward":None}

# =========================
# Battery Simulation
# =========================
def simulate_battery(ward, zone):
    st.session_state.battery_count += 1
    battery_id = f"BAT{st.session_state.battery_count}"
    ocv = np.round(np.random.uniform(1.2,1.6),2)
    lv = np.round(np.random.uniform(1.1,ocv),2)
    current = np.round(np.random.uniform(0.05,0.5),2)
    temp = np.round(np.random.uniform(20,40),1)
    resistance = np.round((ocv-lv)/current,2)
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
# Add Battery Section
# =========================
st.subheader("⚡ Add a Random Battery to a Ward")
zone_choice = st.selectbox("Select Zone", zones)
ward_choice = st.selectbox("Select Ward", [f"{zone_choice[:3]}-W{i+1}" for i in range(wards_per_zone)])
if st.button("Add Battery"):
    new_bat = simulate_battery(ward_choice, zone_choice)
    st.session_state.city_data = pd.concat([st.session_state.city_data,pd.DataFrame([new_bat])], ignore_index=True)
    st.success(f"✅ {new_bat['Battery_ID']} added to {ward_choice}")

df = st.session_state.city_data

# =========================
# Function to show summary + charts
# =========================
def show_metrics_charts(level_df, level_name="City"):
    total = len(level_df)
    reusable = len(level_df[level_df['Status']=="Reusable"])
    recyclable = len(level_df[level_df['Status']=="Recyclable"])
    hazardous = len(level_df[level_df['Status']=="Hazardous"])

    col1,col2,col3,col4 = st.columns(4)
    col1.metric(f"Total Batteries ({level_name})", total)
    col2.metric("Reusable 💚", reusable)
    col3.metric("Recyclable 🟡", recyclable)
    col4.metric("Hazardous 🔴", hazardous)

    # Bar charts
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
        if metric in ["OCV","Load_Voltage"]: fig.update_yaxes(range=[0,2])
        elif metric=="Temp": fig.update_yaxes(range=[0,50])
        elif metric=="Resistance": fig.update_yaxes(range=[0,2])
        fig.update_layout(showlegend=False, title=metric_titles[metric])
        cols[i].plotly_chart(fig,use_container_width=True)

    # Pie chart
    status_counts = level_df['Status'].value_counts().reset_index()
    status_counts.columns = ["Status","Count"]
    if len(status_counts)>0:
        fig_pie = px.pie(
            status_counts,
            names="Status",
            values="Count",
            color="Status",
            color_discrete_map={"Reusable":"green","Recyclable":"orange","Hazardous":"red"},
            title=f"🥧 Battery Status Breakdown ({level_name})"
        )
        fig_pie.update_traces(textinfo='percent+label', pull=[0.05,0.05,0.05])
        st.plotly_chart(fig_pie,use_container_width=True)

# =========================
# Hierarchical Navigation
# =========================
st.subheader("🏙️ Hierarchical View")
# City Level
if st.button("City: GreenCity"):
    st.session_state.selection = {"level":"City","zone":None,"ward":None}
    show_metrics_charts(df,"City")

# Zone Level
for zone in zones:
    if st.button(f"Zone: {zone}"):
        st.session_state.selection = {"level":"Zone","zone":zone,"ward":None}
        zone_df = df[df["Zone"]==zone]
        show_metrics_charts(zone_df,f"Zone: {zone}")

        # Ward Level
        zone_wards = [w for w in ward_ids if w.startswith(zone[:3])]
        for ward in zone_wards:
            if st.button(f"Ward: {ward}"):
                st.session_state.selection = {"level":"Ward","zone":zone,"ward":ward}
                ward_df = df[df["Ward_ID"]==ward]
                show_metrics_charts(ward_df,f"Ward: {ward}")
