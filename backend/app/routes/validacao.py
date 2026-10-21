
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import supabase

router = APIRouter(
    prefix="/api/validacao",
    tags=["Validação de ingressos"],
)


class ValidarIngressoRequest(BaseModel):
    codigo: UUID


@router.post("/validar")
def validar_ingresso(dados: ValidarIngressoRequest):
    try:
        resultado = supabase.rpc(
            "validar_ingresso",
            {"p_codigo": str(dados.codigo)},
        ).execute()

        if not resultado.data:
            raise HTTPException(
                status_code=500,
                detail="A validação não retornou um resultado.",
            )

        return resultado.data

    except HTTPException:
        raise
    except Exception as erro:
        print(f"Erro na validação do ingresso: {erro!r}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao validar o ingresso.",
        )
