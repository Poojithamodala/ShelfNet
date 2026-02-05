from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.user_routes import router as user_router
from routes.warehouse_routes import router as warehouse_router
from routes.batch_routes import router as batch_router
from routes.sensor_routes import router as sensor_router
from routes.ingestion_routes import router as ingestion_router
from routes.prediction_routes import router as prediction_router
from routes.alert_routes import router as alert_router
from routes.manager_dashboard_routes import router as manager_router
from routes.admin_dashboard_routes import router as admin_router
from routes.sales_dashboard_routes import router as sales_router
from routes.auth_routes import router as auth_router

app = FastAPI(title="ShelfNet Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/users")
app.include_router(warehouse_router, prefix="/warehouses")
app.include_router(batch_router, prefix="/batches")
app.include_router(sensor_router, prefix="/sensors")
app.include_router(ingestion_router, prefix="/sensors")
app.include_router(prediction_router, prefix="/predict")
app.include_router(alert_router, prefix="/alerts")
app.include_router(manager_router)
app.include_router(admin_router)
app.include_router(sales_router)
app.include_router(auth_router)
