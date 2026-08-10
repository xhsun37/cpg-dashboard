# 引入 pydantic 的 BaseModel，用於定義 API 的嚴格資料驗證模型 (防呆機制)
from pydantic import BaseModel
# 引入 List 型態，用於定義陣列結構
from typing import List

# 定義前端傳送給後端的輸入資料結構 (Request Payload)
class SimInput(BaseModel):
    site_id: str             # 案場代號 (例如 "KYS")，用於選擇對應的 AI 模型與地質常數
    permeability_md: float   # 滲透率 (mD)，影響流體在岩層中的流動能力
    porosity: float          # 孔隙率 (%)，影響地層的儲集空間
    carbon_price: float      # 碳稅價格 (NTD/ton)，用於計算碳洩漏的懲罰成本
    fit_rate: float          # 躉購費率 (NTD/kWh)，政府收購綠電的單價
    discount_rate: float     # 折現率 (%)，用於計算資金的時間價值與 NPV
    capacity_factor: float   # 容量因子 (%)，電廠實際發電量與滿載發電量的比例

# 定義後端回傳給前端的輸出資料結構 (Response Payload)
class SimOutput(BaseModel):
    npv_array: List[float]       # 30 年的累積淨現值陣列 (NTD)
    temp_array: List[float]      # 30 年的井底溫度衰退陣列 (°C)
    pressure_array: List[float]  # 30 年的井底壓力衰退陣列 (kPa)
    flow_array: List[float]      # 30 年的 CO2 循環流率陣列 (kg/s)
    lcoe: float                  # 均化發電成本 (NTD/kWh)
    irr: float                   # 內部報酬率 (%)
    dpp: float                   # 折現回收期 (年)
    annual_co2_tons: float       # 年化碳排成本 (LCA 生命週期總碳排平攤)
    annual_power_mwh: float      # 預估年發電量 (MWh)
    avg_temp_c: float            # 發電期平均井底溫度 (°C)
    avg_pressure_kpa: float      # 發電期平均井底壓力 (kPa)
    avg_flow_kg_s: float         # 發電期平均 CO2 流率 (kg/s)
