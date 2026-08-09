from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router # 引入您先前寫好的 api.py 路由

app = FastAPI()

# 核心修正：強制掛載 CORS 中介軟體，發放跨來源通行證
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有前端來源連線 (僅限開發期使用)
    allow_credentials=True,
    allow_methods=["*"],  # 允許 POST, GET, OPTIONS 等所有方法
    allow_headers=["*"],  # 允許所有標頭
)

# 掛載 API 路由
app.include_router(router, prefix="/api")