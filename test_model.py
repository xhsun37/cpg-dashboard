import joblib
import numpy as np
import pandas as pd

# 1. 載入你訓練好的模型
print("載入模型中...")
model = joblib.load('backend/cpg_rf_model_100yr.joblib')

feature_cols = [
    'CPOR', 'PERMI_37', 'PERMI_38', 'PERMJ_37', 'PERMJ_38', 
    'PERMK_37', 'PERMK_38', 'POR_38', 'PRPOR', 'POR_37', 
    'WBP_INJ', 'WBP_PRD', 'WBT_INJ', 'WBT_PRD', 'Elapsed Time'
]

def test_prediction(perm, por, year):
    features = np.zeros((1, 15))
    features[0, 0] = por          # CPOR
    features[0, 7] = por          # POR_38
    features[0, 8] = 3e-6         # PRPOR
    features[0, 9] = por          # POR_37
    features[0, 1:5] = perm       # PERMI, PERMJ
    features[0, 5:7] = perm * 0.1 # PERMK
    features[0, 10] = 25000.0     # WBP_INJ
    features[0, 11] = 18000.0     # WBP_PRD
    features[0, 12] = 40.0        # WBT_INJ
    features[0, 13] = 90.0        # WBT_PRD
    features[0, 14] = year * 365.25 # Elapsed Time (天)

    df = pd.DataFrame(features, columns=feature_cols)
    pred = model.predict(df)[0]
    
    # 假設 index 3 是生產井流率 (kg/day)
    raw_flow_kg_day = pred[3] if len(pred) >= 6 else pred[0]
    field_flow_kg_s = (raw_flow_kg_day / 86400.0) * 6
    
    print(f"測試條件 -> 滲透率: {perm} mD, 孔隙率: {por}, 第 {year} 年")
    print(f"   [模型原始輸出] 生產井流率: {raw_flow_kg_day:,.2f} kg/day")
    print(f"   [換算全場流率] {field_flow_kg_s:.4f} kg/s")
    print("-" * 50)

# 2. 進行極端值與平滑度測試
print("\n=== 開始模型壓力測試 ===")
test_prediction(50, 0.15, 21)  # 基準組 (應該要很高)
test_prediction(45, 0.13, 21)  # 微調組 (應該要平滑下降)
test_prediction(38, 0.10, 21)  # 你截圖的參數 (看看是不是真的暴跌)