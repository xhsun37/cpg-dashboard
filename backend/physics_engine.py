import numpy as np
import os
import joblib
import pandas as pd

try:
    import CoolProp.CoolProp as CP
except ImportError:
    CP = None

# ====================================================
# 【Tier 1 核心】模型註冊表 (Model & Config Registry)
# ====================================================
SITE_REGISTRY = {
    "KYS": {
        "name": "桃園觀音山 (KYS)",
        "model_file": "cpg_rf_model_100yr.joblib",
        "csv_file": "Results-Table-1.csv",  
        "constants": {} 
    }
}

def initialize_site_constants():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for site_id, config in SITE_REGISTRY.items():
        csv_path = os.path.join(current_dir, config.get("csv_file", ""))
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                df.columns = df.columns.str.strip()
                df = df[df['Optimal'].astype(str).str.upper() != 'FALSE']
                config["constants"] = {
                    "CPOR": float(df['CPOR'].median()),
                    "PRPOR": float(df['PRPOR'].median()),
                    "WBP_INJ": float(df['WBP_INJ'].median()),
                    "WBP_PRD": float(df['WBP_PRD'].median()),
                    "WBT_INJ": float(df['WBT_INJ'].median()),
                    "WBT_PRD": float(df['WBT_PRD'].median())
                }
                print(f"[系統初始化] 成功載入 {site_id} 案場動態常數: {config['constants']}")
            except Exception as e:
                print(f"[系統警告] 無法解析 {site_id} 的 CSV 檔案: {e}。將使用預設安全值。")
                config["constants"] = {"CPOR": 5.07e-6, "PRPOR": 7978.96, "WBP_INJ": 22573.38, "WBP_PRD": 22486.62, "WBT_INJ": 25.0, "WBT_PRD": 89.61}
        else:
            print(f"[系統警告] 找不到 {site_id} 的參數檔 ({csv_path})。將使用預設安全值。")
            config["constants"] = {"CPOR": 5.07e-6, "PRPOR": 7978.96, "WBP_INJ": 22573.38, "WBP_PRD": 22486.62, "WBT_INJ": 25.0, "WBT_PRD": 89.61}

initialize_site_constants()

def predict_ml_dynamics(site_id: str, permeability_md: float, porosity: float, years: int = 30):
    if site_id not in SITE_REGISTRY:
        raise ValueError(f"未知的案場 ID: {site_id}")
        
    site_config = SITE_REGISTRY[site_id]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, site_config["model_file"]) 
    
    try:
        rf_model = joblib.load(model_path)
        flow_array_kg_s, temp_array_c, pressure_array_kpa = [], [], []
        consts = site_config["constants"]
        
        for year in range(1, years + 1):
            features = np.zeros((1, 15))
            features[0, 0] = consts["CPOR"]
            features[0, 8] = consts["PRPOR"]
            features[0, 10] = consts["WBP_INJ"]
            features[0, 11] = consts["WBP_PRD"]
            features[0, 12] = consts["WBT_INJ"]
            features[0, 13] = consts["WBT_PRD"]
            features[0, 1] = permeability_md   
            features[0, 2] = permeability_md   
            features[0, 3] = permeability_md   
            features[0, 4] = permeability_md   
            features[0, 5] = permeability_md * 0.1 
            features[0, 6] = permeability_md * 0.1 
            features[0, 7] = porosity          
            features[0, 9] = porosity          
            features[0, 14] = year * 365.25    
            
            feature_cols = ['CPOR', 'PERMI_37', 'PERMI_38', 'PERMJ_37', 'PERMJ_38', 'PERMK_37', 'PERMK_38', 'POR_38', 'PRPOR', 'POR_37', 'WBP_INJ', 'WBP_PRD', 'WBT_INJ', 'WBT_PRD', 'Elapsed Time']
            features_df = pd.DataFrame(features, columns=feature_cols)
            
            prediction = rf_model.predict(features_df)[0]
            
            if len(prediction) >= 6:
                prd_flow_kg_day, prd_pressure_kpa, prd_temp_c = prediction[3], prediction[4], prediction[5]
            else:
                prd_flow_kg_day, prd_pressure_kpa, prd_temp_c = prediction[0], prediction[1], prediction[2]
            
            flow_array_kg_s.append(prd_flow_kg_day / 86400.0)
            temp_array_c.append(prd_temp_c)
            pressure_array_kpa.append(prd_pressure_kpa)
            
        return np.array(flow_array_kg_s), np.array(temp_array_c), np.array(pressure_array_kpa)

    except Exception as e:
        print(f"[ML 載入失敗] {e}")
        return np.zeros(years), np.zeros(years), np.zeros(years)

def calculate_physics(site_id: str, depth_m: float, permeability_md: float, porosity: float, capacity_factor: float):
    years = 30
    FIELD_MULTIPLIER = 6.0  
    
    single_flow_array, temp_array_c, pressure_array_kpa = predict_ml_dynamics(site_id, permeability_md, porosity, years)
    field_flow_array_kg_s = single_flow_array * FIELD_MULTIPLIER
    
    power_mwh_array = []
    temp_list, pressure_list, flow_list = [], [], []
    MIN_TURBINE_TEMP = 31.1 
    
    # 第一階段：先算出 30 年的發電量陣列
    for i in range(years):
        actual_year = i + 1
        m_dot_kg_s = field_flow_array_kg_s[i]
        t_c = temp_array_c[i]
        p_kpa = pressure_array_kpa[i]
        
        temp_list.append(t_c)
        pressure_list.append(p_kpa)
        flow_list.append(m_dot_kg_s)
        
        if actual_year <= 10:
            power_mwh_array.append(0.0)
            continue
            
        if t_c < MIN_TURBINE_TEMP:
            power_mwh_array.append(0.0)
            continue
            
        try:
            T1_K = t_c + 273.15
            P1_Pa = p_kpa * 1000.0
            if CP is not None:
                h_in_J = CP.PropsSI('H', 'T', T1_K, 'P', P1_Pa, 'CO2')
                s_in_J = CP.PropsSI('S', 'T', T1_K, 'P', P1_Pa, 'CO2')
                P2_Pa = 50.0 * 100000.0 
                h_out_ideal_J = CP.PropsSI('H', 'S', s_in_J, 'P', P2_Pa, 'CO2')
                delta_h_ideal_J = max(0.0, h_in_J - h_out_ideal_J)
                power_mw = (m_dot_kg_s * delta_h_ideal_J * 0.85) / 1e6
            else:
                power_mw = max(0.0, m_dot_kg_s * 0.1)
                
            power_mwh_array.append(power_mw * 8760 * capacity_factor)
        except Exception:
            power_mwh_array.append(0.0)
            
    # ====================================================
    # 【新增】LCA 碳盤查動態計算 (取代原本固定的 450 噸)
    # ====================================================
    # 1. 計算 30 年總發電量 (MWh)
    total_mwh = sum(power_mwh_array)
    
    # 2. 轉換為 GWhe (1 GWhe = 1000 MWh)
    total_gwhe = total_mwh / 1000.0
    
    # 3. 計算總碳排 (單位：噸)。17386.7318 kg = 17.3867318 噸
    total_carbon_tons = total_gwhe * 17.3867318
    
    # 4. 年化碳排 (平攤至 30 年)
    annual_co2_tons = total_carbon_tons / years
    
    # 建立長度為 30 的碳排陣列，供財務引擎逐年扣除碳稅
    co2_tons_array = [annual_co2_tons] * years
            
    return power_mwh_array, co2_tons_array, temp_list, pressure_list, flow_list