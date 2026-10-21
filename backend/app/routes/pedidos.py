
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.database import supabase

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])


class PedidoCreate(BaseModel):
    nome_comprador: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    telefone: str | None = Field(default=None, max_length=30)
    quantidade: int = Field(ge=1, le=20)


@router.post("")
def criar_pedido(pedido: PedidoCreate):
    dados = {
        "nome_comprador": pedido.nome_comprador.strip(),
        "email": pedido.email.strip().lower(),
        "telefone": pedido.telefone,
        "quantidade": pedido.quantidade,
        "valor_total_centavos": pedido.quantidade * 500,
        "status": "pendente",
    }

    try:
        resultado = (
            supabase
            .table("cristoteca_pedidos")
            .insert(dados)
            .execute()
        )

        if not resultado.data:
            raise HTTPException(
                status_code=500,
                detail="Não foi possível registrar o pedido."
            )

        return {
            "mensagem": "Pedido registrado.",
            "pedido": resultado.data[0]
        }

    except HTTPException:
        raise

    except Exception as erro:
        print(f"ERRO AO REGISTRAR PEDIDO: {erro!r}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao registrar o pedido no banco de dados."
        )
