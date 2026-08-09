CPG_Project/
├── backend/                 
│   ├── main.py              # 系統進入點與 CORS 設定
│   ├── schemas.py           # Pydantic 資料規格 (SimInput/SimOutput)
│   ├── api.py               # 路由定義 (接收 HTTP 請求並回傳)
│   └── services/
│       ├── physics_engine.py # 專責處理 CO2 流體與熱提取公式
│       └── finance_engine.py # 專責處理 NPV、LCOE 折現現金流
└── frontend/                
    ├── index.html           # 純 HTML 骨架
    ├── css/
    │   └── style.css        # 獨立的樣式表
    └── js/
        ├── api_client.js    # 專責 Fetch 與防抖動機制
        ├── state.js         # 專責讀取與更新滑桿狀態
        └── dashboard.js     # 未來專責 Plotly 圖表渲染