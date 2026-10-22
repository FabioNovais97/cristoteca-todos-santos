
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import pagamentos
from app.routes.pedidos import router as pedidos_router
from app.routes.ingressos import router as ingressos_router
from app.routes.validacao import router as validacao_router

app = FastAPI(
    title="Cristoteca Todos os Santos API",
    description="API do sistema de ingressos",
    version="0.2.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://cristoteca-todos-santos(-[a-z0-9-]+)?-fabio1997\.vercel\.app|https://cristoteca-todos-santos\.vercel\.app",
    allow_origins=[
        "http://localhost:5173",
        "https://cristoteca-todos-santos.vercel.app",
        "https://cristoteca-todos-santos-iyg6-bikv8f510-fabio1997.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


app.include_router(pedidos_router)
app.include_router(pagamentos.router)
app.include_router(ingressos_router)
app.include_router(validacao_router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "event": "Cristoteca Todos os Santos",
    }


@app.get("/api/evento")
def evento():
    return {
        "nome": "Cristoteca Todos os Santos",
        "data": "2026-10-31",
        "horario": "19:00",
        "endereco": "Rua Capri, 53 - Jardim Santa Emília",
        "preco_centavos": 500,
        "moeda": "BRL",
    }
