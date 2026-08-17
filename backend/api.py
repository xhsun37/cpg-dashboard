from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import os

from schemas import SimInput, SimOutput
from physics_engine import calculate_physics
from finance_engine import calculate_economics

app = FastAPI(title="CPG Economic Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/simulate", response_model=SimOutput)
async def run_simulation(req: SimInput):
    power_mwh_array, co2_tons_array, temp_array, pressure_array, flow_array = calculate_physics(
        req.site_id, 1700.0, req.permeability_md, req.porosity, req.capacity_factor
    )
    
    # 【必須接收 5 個值】
    npv_array, lcoe, dpp, irr, design_power_mw = calculate_economics(
        req.carbon_price, req.fit_rate, req.discount_rate, power_mwh_array, co2_tons_array, req.capacity_factor
    )
    
    avg_co2 = float(np.mean(co2_tons_array[10:30])) if len(co2_tons_array) >= 30 else 0.0
    avg_power = float(np.mean(power_mwh_array[10:30])) if len(power_mwh_array) >= 30 else 0.0
    avg_flow = float(np.mean(flow_array[10:30])) if len(flow_array) >= 30 else 0.0

    return {
        "npv_array": npv_array,           
        "temp_array": temp_array,         
        "pressure_array": pressure_array, 
        "flow_array": flow_array,         
        "lcoe": round(float(lcoe), 4), 
        "irr": round(float(irr), 2), 
        "dpp": round(float(dpp), 2),
        "annual_co2_tons": round(avg_co2, 2),
        "annual_power_mwh": round(avg_power, 2),
        "avg_flow_kg_s": round(avg_flow, 4),
        "avg_temp_c": round(float(np.mean(temp_array[10:30])), 2),
        "avg_pressure_kpa": round(float(np.mean(pressure_array[10:30])), 2),
        "design_power_mw": round(float(design_power_mw), 2) # 【必須回傳】
    }

current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(current_dir), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
