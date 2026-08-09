import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib

# 引入神經網路與標準化套件
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

def process_cpg_data_and_train():
    # ---------------------------------------------------------
    # 步驟 1: 讀取資料
    # ---------------------------------------------------------
    print("1. 讀取參數檔與 63 萬筆結果檔...")
    df_params = pd.read_csv('Results-Table-1.csv')
    df_results = pd.read_csv('KYS_AI_TimeSeries-yearly.csv')

    df_params.columns = df_params.columns.str.strip()
    df_results.columns = df_results.columns.str.strip()
    
    print("結果檔清洗後真實欄位:", df_results.columns.tolist())

    # ---------------------------------------------------------
    # 步驟 1.5: 篩除 Optimal 為 False 的垃圾數據
    # ---------------------------------------------------------
    print("1.5 排除 Optimal == False 的實驗組...")
    initial_count = len(df_params)
    df_params = df_params[df_params['Optimal'].astype(str).str.upper() != 'FALSE']
    filtered_count = len(df_params)
    print(f"   => 參數檔過濾完成：從 {initial_count} 筆縮減至 {filtered_count} 筆。")

    # ---------------------------------------------------------
    # 步驟 2: 處理結果檔 (Long to Wide Pivot)
    # ---------------------------------------------------------
    print("2. 執行樞紐轉換 (Pivot)，攤平 63 萬筆資料... (這可能需要幾分鐘與較大記憶體)")
    df_res_wide = df_results.pivot_table(
        index=['Experiment ID', 'Elapsed Time'], 
        columns=['Origin Name', 'Parameter'], 
        values='Value'
    ).reset_index()

    df_res_wide.columns = ['_'.join(str(c) for c in col if c).strip() for col in df_res_wide.columns.values]
    
    # ---------------------------------------------------------
    # 步驟 3: 合併參數與結果 (SQL Inner Join)
    # ---------------------------------------------------------
    print("3. 合併物理參數與模擬結果...")
    df_res_wide['Experiment ID'] = df_res_wide['Experiment ID'].astype(str)
    df_params['ID'] = df_params['ID'].astype(str)

    df_merged = pd.merge(
        df_res_wide, 
        df_params, 
        left_on='Experiment ID', 
        right_on='ID',      
        how='inner'
    )
    print(f"   -> [診斷] 合併成功，初始資料共: {len(df_merged)} 筆")

    # ---------------------------------------------------------
    # 步驟 4: 定義 X (輸入特徵) 與 Y (輸出目標)
    # ---------------------------------------------------------
    print("4. 定義機器學習特徵與目標...")
    feature_cols = [
        'CPOR', 'PERMI_37', 'PERMI_38', 'PERMJ_37', 'PERMJ_38', 
        'PERMK_37', 'PERMK_38', 'POR_38', 'PRPOR', 'POR_37', 
        'WBP_INJ', 'WBP_PRD', 'WBT_INJ', 'WBT_PRD',
        'Elapsed Time' 
    ]
    
    target_cols = [
        col for col in df_merged.columns 
        if 'Gas Mass Rate(CO2) SC' in col or 'Well bottom hole temperature' in col or 'Well Bottom-hole Pressure' in col
    ]
    print(f"自動偵測到的預測目標包含: {target_cols}")

    # ---------------------------------------------------------
    # 步驟 4.5: 精確空值處理
    # ---------------------------------------------------------
    print("4.5 執行空值填補與過濾...")
    df_merged[target_cols] = df_merged[target_cols].fillna(0)
    df_merged = df_merged.dropna(subset=feature_cols)
    print(f"   -> [診斷] 空值清理完畢，進入訓練集的有效資料共: {len(df_merged)} 筆")

    if len(df_merged) == 0:
        raise ValueError("【致命錯誤】資料依然全數歸零！請檢查您的 14 個特徵欄位名稱是否與 Excel 標題完全一致。")

    X = df_merged[feature_cols]
    Y = df_merged[target_cols]

    # ---------------------------------------------------------
    # 步驟 5: 訓練多輸出神經網路 AI (MLPRegressor)
    # ---------------------------------------------------------
    print("5. 開始訓練神經網路模型 (這會提供平滑連續的物理預測)...")
    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
    
    # 使用 Pipeline 自動將特徵標準化 (Scaler)，並串接神經網路
    ml_model = make_pipeline(
        StandardScaler(),
        MLPRegressor(hidden_layer_sizes=(128, 64, 32), activation='relu', max_iter=1000, random_state=42)
    )
    
    ml_model.fit(X_train, y_train)

    # ---------------------------------------------------------
    # 步驟 6: 評估與匯出
    # ---------------------------------------------------------
    print("6. 評估與匯出實體 AI 模型檔...")
    mse = mean_squared_error(y_test, ml_model.predict(X_test))
    print(f"測試集均方誤差 (MSE): {mse:.4f}")
    
    # 為了不改動後端程式碼，我們依然將檔名命名為 cpg_rf_model_100yr.joblib
    joblib.dump(ml_model, 'cpg_rf_model_100yr.joblib')
    joblib.dump(feature_cols, 'model_features.joblib')
    print("✅ 訓練完成！神經網路模型已成功匯出。")

if __name__ == "__main__":
    process_cpg_data_and_train()