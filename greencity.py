import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px

# =========================
# Page Config
# =========================
st.set_page_config(page_title="💚 GreenCell Dashboard", layout="wide", page_icon="💚")
st.title("💚 GreenCell: Smart Battery Analyzer Dashboard")

# =========================
# Session State
# =========================
if "tested_batteries" not in st.session_state:
    st.session_state.tested_batteries = pd.DataFrame(columns=[
        "Battery_ID", "Open_Circuit_Voltage", "Load_Voltage",
        "Current", "Temperature", "Internal_Resistance", "Status"
    ])
if "battery_count" not in st.session_state:
    st.session_state.battery_count = 0

# =========================
# Simulate Battery
# =========================
def simulate_battery():
    st.session_state.battery_count += 1
    battery_id = f"BAT{st.session_state.battery_count}"
    ocv = np.round(np.random.uniform(1.2, 1.6), 2)
    lv = np.round(np.random.uniform(1.1, ocv), 2)
    current = np.round(np.random.uniform(0.05, 0.5), 2)
    temp = np.round(np.random.uniform(20, 40), 1)
    resistance = np.round((ocv - lv)/current, 2)
    
    if temp > 40 or resistance > 1.0 or ocv < 1.3:
        status = "Hazardous"
    elif resistance <= 0.5 and ocv >= 1.5:
        status = "Reusable"
    else:
        status = "Recyclable"
    
    return {
        "Battery_ID": battery_id,
        "Open_Circuit_Voltage": ocv,
        "Load_Voltage": lv,
        "Current": current,
        "Temperature": temp,
        "Internal_Resistance": resistance,
        "Status": status
    }

# =========================
# Add Battery Button
# =========================
st.subheader("⚡ Process a New Battery")
if st.button("Add Battery"):
    progress = st.progress(0)
    for i in range(0, 101, 20):
        time.sleep(0.2)
        progress.progress(i)
    
    new_battery = simulate_battery()
    st.session_state.tested_batteries = pd.concat([
        st.session_state.tested_batteries,
        pd.DataFrame([new_battery])
    ])
    st.success(f"✅ {new_battery['Battery_ID']} processed!")

# =========================
# Prepare Data
# =========================
df = st.session_state.tested_batteries
total = len(df)

# =========================
# Summary Cards
# =========================
reusable = len(df[df['Status']=="Reusable"]) if total>0 else 0
recyclable = len(df[df['Status']=="Recyclable"]) if total>0 else 0
hazardous = len(df[df['Status']=="Hazardous"]) if total>0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Batteries", total)
col2.metric("Reusable 💚", reusable, f"{reusable/total*100:.1f}%" if total>0 else "0%")
col3.metric("Recyclable 🟡", recyclable, f"{recyclable/total*100:.1f}%" if total>0 else "0%")
col4.metric("Hazardous 🔴", hazardous, f"{hazardous/total*100:.1f}%" if total>0 else "0%")

st.markdown("---")

# =========================
# Layout: Bar Graphs + Temperature + Pie Chart
# =========================
if total > 0:
    left_col, mid_col, right_col = st.columns([2,2,2])
    
    # --- OCV Bar Graph ---
    with left_col:
        st.subheader("🔋 Open Circuit Voltage (V)")
        fig_ocv = go.Figure()
        for idx, row in df.iterrows():
            color = {"Reusable":"green","Recyclable":"orange","Hazardous":"red"}[row["Status"]]
            fig_ocv.add_trace(go.Bar(
                x=[row["Battery_ID"]],
                y=[row["Open_Circuit_Voltage"]],
                marker_color=color,
                text=[f"{row['Open_Circuit_Voltage']} V"],
                textposition='outside'
            ))
        fig_ocv.update_layout(yaxis=dict(range=[0,2]), showlegend=False)
        st.plotly_chart(fig_ocv, use_container_width=True)
    
    # --- Internal Resistance Graph ---
    with mid_col:
        st.subheader("⚡ Internal Resistance (Ω)")
        fig_res = go.Figure()
        for idx, row in df.iterrows():
            color = {"Reusable":"green","Recyclable":"orange","Hazardous":"red"}[row["Status"]]
            fig_res.add_trace(go.Bar(
                x=[row["Battery_ID"]],
                y=[row["Internal_Resistance"]],
                marker_color=color,
                text=[f"{row['Internal_Resistance']} Ω"],
                textposition='outside'
            ))
        fig_res.update_layout(yaxis=dict(range=[0,2]), showlegend=False)
        st.plotly_chart(fig_res, use_container_width=True)
    
    # --- Temperature Graph ---
    with right_col:
        st.subheader("🌡️ Temperature (°C)")
        fig_temp = go.Figure()
        for idx, row in df.iterrows():
            color = {"Reusable":"green","Recyclable":"orange","Hazardous":"red"}[row["Status"]]
            fig_temp.add_trace(go.Bar(
                x=[row["Battery_ID"]],
                y=[row["Temperature"]],
                marker_color=color,
                text=[f"{row['Temperature']} °C"],
                textposition='outside'
            ))
        fig_temp.update_layout(yaxis=dict(range=[0,50]), showlegend=False)
        st.plotly_chart(fig_temp, use_container_width=True)
    
    # --- Pie Chart (Below) ---
    st.subheader("📊 Battery Status Distribution")
    status_counts = df['Status'].value_counts().reindex(['Reusable','Recyclable','Hazardous'], fill_value=0)
    fig_pie = px.pie(
        names=status_counts.index,
        values=status_counts.values,
        color=status_counts.index,
        color_discrete_map={"Reusable":"green","Recyclable":"orange","Hazardous":"red"},
        title="Status Distribution"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# =========================
# Battery Details Table
# =========================
if total > 0:
    st.subheader("📝 Battery Details")
    icon_map = {"Reusable":"💚","Recyclable":"🟡","Hazardous":"🔴"}
    display_df = df.copy()
    display_df["Status"] = display_df["Status"].map(lambda x: f"{icon_map[x]} {x}")
    st.dataframe(display_df)

# =========================
# Hazard Alert
# =========================
if hazardous > 0:
    st.warning(f"⚠️ {hazardous} hazardous batteries detected! Handle with care!")
