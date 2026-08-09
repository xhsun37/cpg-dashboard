from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import os

from schemas import SimInput, SimOutput
from physics_engine import calculate_physics
from finance_engine import calculate_economics

# 改用 FastAPI 實例取代 APIRouter，方便直接執行
app = FastAPI(title="CPG Economic Analysis API")

# 設定 CORS (允許跨域請求)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由 (注意：路徑改為 /api/simulate)
@app.post("/api/simulate", response_model=SimOutput)
async def run_simulation(req: SimInput):
    power_mwh_array, co2_tons_array, temp_array, pressure_array, flow_array = calculate_physics(
        req.site_id, 1700.0, req.permeability_md, req.porosity, req.capacity_factor
    )
    
    npv_array, lcoe, dpp, irr = calculate_economics(
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
        "avg_pressure_kpa": round(float(np.mean(pressure_array[10:30])), 2)
    }

# ==========================================
# 前後端合體設定：讓 FastAPI 託管前端檔案
# ==========================================
from fastapi.staticfiles import StaticFiles

# 取得 frontend 資料夾的絕對路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(current_dir), "frontend")

# 【核心修正】將 frontend 資料夾直接掛載到根目錄 "/"，並開啟 html=True
# 這樣 FastAPI 會自動在根目錄尋找 index.html，且網頁也能正確載入同層級的 main.js
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")