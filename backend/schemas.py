from pydantic import BaseModel
from typing import List

class SimInput(BaseModel):
    site_id: str
    permeability_md: float
    porosity: float
    carbon_price: float
    fit_rate: float
    discount_rate: float
    capacity_factor: float

class SimOutput(BaseModel):
    npv_array: List[float]
    temp_array: List[float]      # 【新增】溫度陣列
    pressure_array: List[float]  # 【新增】壓力陣列
    flow_array: List[float]      # 【新增】流率陣列
    lcoe: float
    irr: float
    dpp: float
    annual_co2_tons: float
    annual_power_mwh: float
    avg_temp_c: float
    avg_pressure_kpa: float
    avg_flow_kg_s: float