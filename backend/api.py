# 引入 FastAPI 主程式與靜態檔案託管模組
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import os

# 引入自定義的資料結構與計算引擎
from schemas import SimInput, SimOutput
from physics_engine import calculate_physics
from finance_engine import calculate_economics

# 建立 FastAPI 實例
app = FastAPI(title="CPG Economic Analysis API")

# 設定 CORS，允許前端跨域請求 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定義 API 路由，接收前端參數並回傳模擬結果
@app.post("/api/simulate", response_model=SimOutput)
async def run_simulation(req: SimInput):
    # 1. 呼叫物理引擎，取得 30 年的發電量與物理動態陣列
    power_mwh_array, co2_tons_array, temp_array, pressure_array, flow_array = calculate_physics(
        req.site_id, 1700.0, req.permeability_md, req.porosity, req.capacity_factor
    )
    
    # 2. 呼叫財務引擎，取得 NPV 陣列與商業指標 (LCOE, IRR, DPP)
    npv_array, lcoe, dpp, irr = calculate_economics(
        req.carbon_price, req.fit_rate, req.discount_rate, power_mwh_array, co2_tons_array, req.capacity_factor
    )
    
    # 3. 計算發電期 (第 11~30 年，陣列索引 10:30) 的平均 KPI 供前端顯示
    avg_co2 = float(np.mean(co2_tons_array[10:30])) if len(co2_tons_array) >= 30 else 0.0
    avg_power = float(np.mean(power_mwh_array[10:30])) if len(power_mwh_array) >= 30 else 0.0
    avg_flow = float(np.mean(flow_array[10:30])) if len(flow_array) >= 30 else 0.0

    # 4. 打包所有數據回傳給前端
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
# 前後端合體設定：讓 FastAPI 直接託管前端網頁
# ==========================================
# 取得 frontend 資料夾的絕對路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(current_dir), "frontend")

# 將 frontend 資料夾掛載到根目錄 "/"，並開啟 html=True 自動尋找 index.html
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
