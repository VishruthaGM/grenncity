import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
st.title("🏙️ GreenCity Dashboard (Hierarchical View)")

# Step 1: City (we have only one for now)
if st.button("City: GreenCity"):
    st.subheader("Select Zone")
    
    for zone in zones:
        if st.button(f"Zone: {zone}"):
            st.subheader(f"Select Ward in {zone}")
            zone_wards = [w for w in ward_ids if w.startswith(zone[:3])]
            
            for ward in zone_wards:
                if st.button(f"Ward: {ward}"):
                    st.write(f"### Data for {ward}")

                    # Filter ward data
                    ward_df = df[df["Ward_ID"]==ward]
                    
                    # Ward Summary Cards
                    if len(ward_df)>0:
                        reusable = len(ward_df[ward_df['Status']=="Reusable"])
                        recyclable = len(ward_df[ward_df['Status']=="Recyclable"])
                        hazardous = len(ward_df[ward_df['Status']=="Hazardous"])
                        total = len(ward_df)
                        col1,col2,col3,col4 = st.columns(4)
                        col1.metric("Total Batteries", total)
                        col2.metric("Reusable 💚", reusable)
                        col3.metric("Recyclable 🟡", recyclable)
                        col4.metric("Hazardous 🔴", hazardous)
                    
                    # Bar Charts
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
                        for idx,row in ward_df.iterrows():
                            color = {"Reusable":"green","Recyclable":"orange","Hazardous":"red"}[row["Status"]]
                            fig.add_trace(go.Bar(
                                x=[f"{row['Battery_ID']}"],
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
                    
                    # Pie Chart
                    status_counts = ward_df['Status'].value_counts().reset_index()
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
