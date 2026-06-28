import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as gr
import json

# ==========================================
# 1. CORE AEROSPACE ANALYTICS ENGINE (FIXED)
# ==========================================

def calculate_range(fuel_capacity, fuel_burn_rate, true_air_speed):
    """Calculates aircraft range in nautical miles."""
    if fuel_burn_rate <= 0: return 0
    endurance_hours = fuel_capacity / fuel_burn_rate
    return endurance_hours * true_air_speed

def calculate_endurance(fuel_capacity, fuel_burn_rate):
    """Calculates flight endurance in hours."""
    if fuel_burn_rate <= 0: return 0
    return fuel_capacity / fuel_burn_rate

def calculate_aerodynamics(cl, cd, rho, velocity, wing_area):
    """Calculates aerodynamic Lift and Drag forces in Newtons."""
    dynamic_pressure = 0.5 * rho * (velocity ** 2)
    lift = cl * dynamic_pressure * wing_area
    drag = cd * dynamic_pressure * wing_area
    return lift, drag

def calculate_cg_position(moments, weights):
    """Calculates the center of gravity (CG) relative position."""
    total_weight = sum(weights)
    if total_weight <= 0: return 0
    total_moment = sum(moments)
    return total_moment / total_weight

# ==========================================
# 2. FLIGHT TELEMETRY SIMULATOR (AIRBUS SPECIAL)
# ==========================================

def simulate_flight_telemetry(initial_velocity, thrust, cl, cd, rho, wing_area, mass, time_steps=60):
    """
    Simulates real-time time-series telemetry data for flight log analytics.
    Fixes the engineering units clashing bugs from the raw script.
    """
    g = 9.81
    weight = mass * g
    
    time_series = []
    current_velocity = initial_velocity
    current_distance = 0
    altitude = 1000 # Starting cruise altitude in meters
    
    for t in range(time_steps):
        # Aerodynamics recalibrate based on instantaneous velocity
        lift, drag = calculate_aerodynamics(cl, cd, rho, current_velocity, wing_area)
        
        # Physics update engine
        net_force_x = thrust - drag
        acceleration_x = net_force_x / mass
        
        current_velocity += acceleration_x * 1.0 # 1 sec step
        current_distance += current_velocity * 1.0
        
        # Minor altitude variance to simulate turbulence/real-world telemetry
        altitude += np.random.normal(0, 1.5) 
        
        time_series.append({
            "Timestamp_Sec": t,
            "Velocity_m_s": round(current_velocity, 2),
            "Acceleration_m_s2": round(acceleration_x, 4),
            "Distance_Meters": round(current_distance, 2),
            "Altitude_Meters": round(altitude, 2),
            "Lift_N": round(lift, 2),
            "Drag_N": round(drag, 2)
        })
        
    return pd.DataFrame(time_series)

# ==========================================
# 3. STREAMLIT INTERACTIVE DASHBOARD UI
# ==========================================

st.set_page_config(page_title="Telemetry Analytics Platform", layout="wide")
st.title("Integrated Flight Telemetry & Performance Analytics Platform")
st.markdown("---")

# Sidebar Configuration Layout
st.sidebar.header("Aircraft Configuration Panel")

# Section 1: Propulsion & Fuel
st.sidebar.subheader("1. Propulsion & Fuel Specs")
fuel_cap = st.sidebar.slider("Fuel Capacity (Gallons)", 500, 5000, 1000, step=100)
fuel_burn = st.sidebar.slider("Fuel Burn Rate (GPH)", 10, 200, 50)
tas = st.sidebar.slider("True Airspeed (Knots)", 100, 400, 150)

# Section 2: Aerodynamics & Mass
st.sidebar.subheader("2. Aero & Mass Balances")
aircraft_mass = st.sidebar.number_input("Aircraft Mass (kg)", value=5000)
thrust_force = st.sidebar.number_input("Engine Thrust (N)", value=8500) # Increased to keep physics net force positive
wing_surface = st.sidebar.number_input("Wing Area (m²)", value=20)
c_l = st.sidebar.slider("Lift Coefficient (Cl)", 0.1, 2.0, 1.2)
c_d = st.sidebar.slider("Drag Coefficient (Cd)", 0.01, 0.3, 0.04)

# Static Performance Computations
static_range = calculate_range(fuel_cap, fuel_burn, tas)
static_endurance = calculate_endurance(fuel_cap, fuel_burn)

# Run Time-Series Telemetry Engine
df_telemetry = simulate_flight_telemetry(
    initial_velocity=50, thrust=thrust_force, cl=c_l, cd=c_d, 
    rho=1.225, wing_area=wing_surface, mass=aircraft_mass
)

# Render Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Calculated Flight Range", value=f"{static_range:.2f} NM")
col2.metric(label="Flight Endurance", value=f"{static_endurance:.2f} Hours")
col3.metric(label="Terminal Velocity Achieved", value=f"{df_telemetry['Velocity_m_s'].iloc[-1]} m/s")
col4.metric(label="Total Distance Explored", value=f"{df_telemetry['Distance_Meters'].iloc[-1]/1000:.2f} KM")

st.markdown("---")

# Dynamic UI Tabs for Visualization & Logging
tab_plots, tab_data, tab_export = st.tabs(["3D & Time-Series Mission Plots", "Raw Telemetry Streams", " Structural Logs Exporter"])

with tab_plots:
    st.subheader("Mission Trajectory & Dynamic Time-Series Analysis")
    
    # 3D Path plot using Distance, Timestamp and Altitude (Targeting Option B Requirement)
    fig_3d = gr.Figure(data=[gr.Scatter3d(
        x=df_telemetry['Distance_Meters'],
        y=df_telemetry['Timestamp_Sec'],
        z=df_telemetry['Altitude_Meters'],
        mode='lines+markers',
        marker=dict(size=4, color=df_telemetry['Velocity_m_s'], colorscale='Viridis', opacity=0.8),
        line=dict(color='darkblue', width=4)
    )])
    fig_3d.update_layout(title="3D Flight Trajectory Profile", scene=dict(
        xaxis_title='Distance (Meters)',
        yaxis_title='Timeline (Seconds)',
        zaxis_title='Altitude (Meters)'
    ), margin=dict(l=0, r=0, b=0, t=40))
    st.plotly_chart(fig_3d, use_container_width=True)
    
    # 2D Aero Plots
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        fig_vel = gr.Figure()
        fig_vel.add_trace(gr.Scatter(x=df_telemetry['Timestamp_Sec'], y=df_telemetry['Velocity_m_s'], name='Velocity'))
        fig_vel.update_layout(title="Velocity Over Time Stream", xaxis_title="Time (s)", yaxis_title="Velocity (m/s)")
        st.plotly_chart(fig_vel, use_container_width=True)
    with p_col2:
        fig_aero = gr.Figure()
        fig_aero.add_trace(gr.Scatter(x=df_telemetry['Timestamp_Sec'], y=df_telemetry['Lift_N'], name='Lift Force (N)'))
        fig_aero.add_trace(gr.Scatter(x=df_telemetry['Timestamp_Sec'], y=df_telemetry['Drag_N'], name='Drag Force (N)'))
        fig_aero.update_layout(title="Aerodynamic Force Distribution Balance", xaxis_title="Time (s)", yaxis_title="Force (Newtons)")
        st.plotly_chart(fig_aero, use_container_width=True)

with tab_data:
    st.subheader("Real-Time Structuring of System Telemetry Logs")
    st.dataframe(df_telemetry, use_container_width=True)

with tab_export:
    st.subheader("Structured Knowledge Engineering & JSON Pipeline")
    
    # Exporting structured analytics metadata (Targeting Option A Context)
    analytics_metadata = {
        "mission_summary": {
            "range_nm": static_range,
            "endurance_hr": static_endurance,
            "final_distance_m": float(df_telemetry['Distance_Meters'].iloc[-1])
        },
        "system_telemetry_logs": df_telemetry.to_dict(orient="records")
    }
    
    json_string = json.dumps(analytics_metadata, indent=4)
    st.json(analytics_metadata)
    
    st.download_button(
        label="Download Mission Engineering Log (.json)",
        file_name="aircraft_structured_telemetry.json",
        mime="application/json",
        data=json_string
    )