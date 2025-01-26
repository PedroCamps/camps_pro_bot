from fastapi import FastAPI
from routes.main_routes import router as main_router
# Inicialização do FastAPI
app = FastAPI()

# Registro das rotas de PDFs
app.include_router(main_router)