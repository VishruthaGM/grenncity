import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import requests

st.set_page_config(page_title="💚 GreenCity Dashboard", layout="wide", page_icon="🏙️")
st.title("🏙️ GreenCity: Smart E-Waste & Battery Intelligence System")
st.markdown("Now with AI prediction, real-world simulation, alerts & map view 🚀")

# =========================
# Zones & Coordinates
# =========================
zones = ["Residential","Industrial","Commercial","Public Services"]
wards_per_zone = 2
ward_ids = [f"{zone[:3]}-W{i+1}" for zone in zones for i in range(wards_per_zone)]

# Fake coordinates for map (can replace with real later)
ward_coords = {
    "Res-W1": [12.92, 79.13],
    "Res-W2": [12.93, 79.14],
    "Ind-W1": [12.91, 79.12],
    "Ind-W2": [12.90, 79.11],
    "Com-W1": [12.94, 79.15],
    "Com-W2": [12.95, 79.16],
    "Pub-W1": [12.96, 79.17],
    "Pub-W2": [12.97, 79.18]
}

# =========================
# Session State
# =========================
if "city_data" not in st.session_state:
    st.session_state.city_data = pd.DataFrame(columns=[
        "Ward_ID", "Zone", "Battery_ID", "OCV", "Load_Voltage",
        "Current", "Temp", "Resistance", "Health", "Status", "Life_%"
    ])
if "battery_count" not in st.session_state:
    st.session_state.battery_count = 0

# =========================
# Realistic Simulation
# =========================
def simulate_battery(ward, zone):
    st.session_state.battery_count += 1
    battery_id = f"BAT{st.session_state.battery_count}"

    health = np.random.uniform(0.5, 1.0)
    ocv = round(1.2 + 0.4 * health + np.random.normal(0, 0.02), 2)

    internal_resistance = round(np.random.uniform(0.1, 0.8) * (1/health), 2)
    current = round(np.random.uniform(0.05, 0.3), 2)
    lv = round(ocv - current * internal_resistance, 2)

    temp = round(25 + (current * 20) + (internal_resistance * 10) + np.random.normal(0,1), 1)

    if ocv < 1.25 or internal_resistance > 0.8:
        status = "Hazardous"
    elif ocv > 1.45 and internal_resistance < 0.3:
        status = "Reusable"
    else:
        status = "Recyclable"

    life = int(health * 100)

    return {
        "Ward_ID": ward, "Zone": zone, "Battery_ID": battery_id,
        "OCV": ocv, "Load_Voltage": lv, "Current": current,
        "Temp": temp, "Resistance": internal_resistance,
        "Health": health, "Status": status, "Life_%": life
    }

# =========================
# Add Battery
# =========================
st.subheader("⚡ Add Battery")
zone_choice = st.selectbox("Zone", zones)
ward_choice = st.selectbox("Ward", [f"{zone_choice[:3]}-W{i+1}" for i in range(wards_per_zone)])

if st.button("Add Battery"):
    new_bat = simulate_battery(ward_choice, zone_choice)
    st.session_state.city_data = pd.concat([
        st.session_state.city_data, pd.DataFrame([new_bat])
    ], ignore_index=True)
    st.success(f"Added {new_bat['Battery_ID']}")

df = st.session_state.city_data

# =========================
# AI Model (Life Prediction)
# =========================
if len(df) > 5:
    model = LinearRegression()
    X = df[["OCV", "Temp", "Resistance"]]
    y = df["Life_%"]
    model.fit(X, y)
    df["Predicted_Life"] = model.predict(X)
else:
    df["Predicted_Life"] = df.get("Life_%", 0)

# =========================
# Alerts
# =========================
def check_alerts(level_df, name):
    if len(level_df) == 0:
        return
    hazard_pct = len(level_df[level_df['Status']=="Hazardous"]) / len(level_df) * 100
    if hazard_pct > 30:
        st.error(f"🚨 ALERT: High Hazard in {name} ({hazard_pct:.1f}%)")

# =========================
# Charts
# =========================
def show_metrics(level_df, name):
    if len(level_df) == 0:
        st.info("No data")
        return

    st.markdown(f"### {name}")
    check_alerts(level_df, name)

    fig = px.bar(level_df, x="Battery_ID", y="OCV", color="Status", title="Voltage Overview")
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.scatter(level_df, x="Temp", y="Resistance", color="Status", size="Life_%", title="Health Analysis")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.pie(level_df, names="Status", title="Battery Status")
    st.plotly_chart(fig3, use_container_width=True)

# =========================
# Map View
# =========================
st.subheader("🗺️ Smart City Map")

if len(df) > 0:
    map_df = df.copy()
    map_df["lat"] = map_df["Ward_ID"].map(lambda x: ward_coords.get(x, [12.92,79.13])[0])
    map_df["lon"] = map_df["Ward_ID"].map(lambda x: ward_coords.get(x, [12.92,79.13])[1])

    fig_map = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        color="Status",
        size="Life_%",
        hover_name="Battery_ID",
        zoom=11,
        height=400
    )
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

# =========================
# Hierarchy View
# =========================
st.subheader("🏙️ City Analysis")

show_metrics(df, "City")

for zone in zones:
    zone_df = df[df["Zone"] == zone]
    with st.expander(f"Zone: {zone}"):
        show_metrics(zone_df, zone)

        for ward in ward_ids:
            if ward.startswith(zone[:3]):
                ward_df = df[df["Ward_ID"] == ward]
                with st.expander(f"Ward: {ward}"):
                    show_metrics(ward_df, ward)

# =========================
# Blynk Integration Placeholder
# =========================
st.subheader("📡 Live IoT Data (Blynk)")

BLYNK_TOKEN = "YOUR_TOKEN"

def get_blynk(pin):
    try:
        url = f"https://blynk.cloud/external/api/get?token={BLYNK_TOKEN}&pin={pin}"
        return float(requests.get(url).text)
    except:
        return None

if st.button("Fetch Live Data"):
    v = get_blynk("V0")
    t = get_blynk("V1")

    if v and t:
        st.metric("Voltage", v)
        st.metric("Temperature", t)
    else:
        st.warning("Connect Blynk Token")
