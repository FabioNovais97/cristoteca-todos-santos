
import os
import requests

from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Request
from dotenv import load_dotenv

from app.database import supabase

load_dotenv()

router = APIRouter(
    prefix="/api/pagamentos",
    tags=["Pagamentos"],
)

MERCADO_PAGO_URL = (
    "https://api.mercadopago.com/checkout/preferences"
)
MERCADO_PAGO_SEARCH_URL = (
    "https://api.mercadopago.com/v1/payments/search"
)

MERCADO_PAGO_PAYMENT_URL = (
    "https://api.mercadopago.com/v1/payments"
)

def obter_token():
    token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")

    if not token:
        raise HTTPException(
            status_code=500,
            detail="Access Token do Mercado Pago não configurado.",
        )

    return token


def obter_pedido(pedido_id: str):
    resultado = (
        supabase.table("cristoteca_pedidos")
        .select("*")
        .eq("id", pedido_id)
        .execute()
    )

    if not resultado.data:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado.",
        )

    return resultado.data[0]


@router.post("/pedido/{pedido_id}")
def criar_checkout(pedido_id: str):
    token = obter_token()

    try:
        pedido = obter_pedido(pedido_id)

        if pedido["status"] != "pendente":
            raise HTTPException(
                status_code=400,
                detail="Este pedido não está pendente.",
            )

        frontend_url = os.getenv(
            "FRONTEND_URL",
            "http://localhost:5173",
        ).rstrip("/")

        preferencia = {
            "items": [
                {
                    "title": "Ingresso Cristoteca Todos os Santos",
                    "quantity": int(pedido["quantidade"]),
                    "unit_price": 5.00,
                    "currency_id": "BRL",
                }
            ],
            "payer": {
                "email": pedido["email"],
            },
            "external_reference": str(pedido["id"]),
            "notification_url": (
        "https://cristoteca-todos-santos.onrender.com"
        "/api/pagamentos/webhook"
    ),
        }

        # URLs de retorno só são enviadas quando o frontend
        # está publicado em um endereço HTTPS público.
        if frontend_url.startswith("https://"):
            parametros = urlencode({
                "pedido_id": str(pedido["id"]),
            })

            preferencia["back_urls"] = {
                "success": (
                    f"{frontend_url}/?{parametros}"
                    "&retorno=sucesso"
                ),
                "pending": (
                    f"{frontend_url}/?{parametros}"
                    "&retorno=pendente"
                ),
                "failure": (
                    f"{frontend_url}/?{parametros}"
                    "&retorno=falha"
                ),
            }

            preferencia["auto_return"] = "approved"

        resposta = requests.post(
            MERCADO_PAGO_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=preferencia,
            timeout=20,
        )

        if resposta.status_code not in (200, 201):
            print(
                "Erro ao criar checkout no Mercado Pago:",
                resposta.status_code,
                resposta.text,
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "Não foi possível criar o pagamento. "
                    "Confira o log do backend."
                ),
            )

        dados = resposta.json()

        link_pagamento = (
            dados.get("sandbox_init_point")
            or dados.get("init_point")
        )

        if not link_pagamento:
            print("Resposta sem link de pagamento:", dados)
            raise HTTPException(
                status_code=502,
                detail="O Mercado Pago não retornou o link de pagamento.",
            )

        return {
            "pedido_id": str(pedido["id"]),
            "preferencia_id": dados.get("id"),
            "link_pagamento": link_pagamento,
            "valor_total": (
                int(pedido["valor_total_centavos"]) / 100
            ),
        }

    except HTTPException:
        raise
    except requests.RequestException as erro:
        print(f"Erro de conexão com Mercado Pago: {erro!r}")
        raise HTTPException(
            status_code=502,
            detail="Falha de comunicação com o Mercado Pago.",
        )
    except Exception as erro:
        print(f"Erro ao criar checkout: {erro!r}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao preparar o pagamento.",
        )


@router.get("/pedido/{pedido_id}/status")
def consultar_status_pagamento(pedido_id: str):
    token = obter_token()

    try:
        pedido = obter_pedido(pedido_id)

        valor_esperado = (
            int(pedido["valor_total_centavos"]) / 100
        )

        resposta = requests.get(
            MERCADO_PAGO_SEARCH_URL,
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "external_reference": str(pedido_id),
                "sort": "date_created",
                "criteria": "desc",
                "limit": 20,
            },
            timeout=20,
        )

        if resposta.status_code != 200:
            print(
                "Erro ao consultar pagamentos:",
                resposta.status_code,
                resposta.text,
            )
            raise HTTPException(
                status_code=502,
                detail="Não foi possível consultar o Mercado Pago.",
            )

        pagamentos = resposta.json().get("results", [])

        aprovado = next(
            (
                pagamento
                for pagamento in pagamentos
                if pagamento.get("status") == "approved"
                and pagamento.get("currency_id") == "BRL"
                and str(pagamento.get("external_reference"))
                == str(pedido_id)
                and abs(
                    float(
                        pagamento.get("transaction_amount") or 0
                    )
                    - valor_esperado
                ) < 0.01
            ),
            None,
        )

        if not aprovado:
            return {
                "pedido_id": str(pedido_id),
                "status_pagamento": "pendente",
                "status_pedido": pedido["status"],
                "mensagem": (
                    "Ainda não foi localizado um pagamento "
                    "aprovado para este pedido."
                ),
            }

        pagamento_id = str(aprovado["id"])

        pagamento_existente = (
            supabase.table("cristoteca_pagamentos")
            .select("id")
            .eq("mercado_pago_id", pagamento_id)
            .execute()
        )

        dados_pagamento = {
            "pedido_id": str(pedido_id),
            "mercado_pago_id": pagamento_id,
            "status": "aprovado",
            "valor_centavos": int(
                pedido["valor_total_centavos"]
            ),
        }

        if pagamento_existente.data:
            (
                supabase.table("cristoteca_pagamentos")
                .update({
                    "status": "aprovado",
                    "valor_centavos": int(
                        pedido["valor_total_centavos"]
                    ),
                })
                .eq("mercado_pago_id", pagamento_id)
                .execute()
            )
        else:
            (
                supabase.table("cristoteca_pagamentos")
                .insert(dados_pagamento)
                .execute()
            )

        supabase.table("cristoteca_pedidos").update({
            "status": "pago",
        }).eq("id", pedido_id).execute()

        ingressos_existentes = (
            supabase.table("cristoteca_ingressos")
            .select("id")
            .eq("pedido_id", pedido_id)
            .execute()
        )

        quantidade_existente = len(
            ingressos_existentes.data or []
        )

        quantidade_faltante = (
            int(pedido["quantidade"]) - quantidade_existente
        )

        if quantidade_faltante > 0:
            novos_ingressos = [
                {
                    "pedido_id": str(pedido_id),
                    "status": "valido",
                }
                for _ in range(quantidade_faltante)
            ]

            (
                supabase.table("cristoteca_ingressos")
                .insert(novos_ingressos)
                .execute()
            )

        conferidos = (
            supabase.table("cristoteca_ingressos")
            .select("id")
            .eq("pedido_id", pedido_id)
            .execute()
        )

        total_ingressos = len(conferidos.data or [])

        if total_ingressos != int(pedido["quantidade"]):
            raise HTTPException(
                status_code=500,
                detail=(
                    "Pagamento aprovado, mas a quantidade de "
                    "ingressos precisa ser conferida."
                ),
            )

        return {
            "pedido_id": str(pedido_id),
            "status_pagamento": "aprovado",
            "status_pedido": "pago",
            "quantidade_ingressos": total_ingressos,
            "mensagem": (
                "Pagamento confirmado e ingressos liberados."
            ),
        }

    except HTTPException:
        raise
    except requests.RequestException as erro:
        print(f"Erro de conexão ao consultar pagamento: {erro!r}")
        raise HTTPException(
            status_code=502,
            detail="Falha de comunicação com o Mercado Pago.",
        )
    except Exception as erro:
        print(
            f"Erro ao consultar pagamento/liberar ingressos: "
            f"{erro!r}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Erro interno ao consultar o pagamento "
                "ou liberar ingressos."
            ),
        )


@router.post("/webhook")
async def receber_webhook_mercado_pago(request: Request):
    try:
        body = await request.json()

        tipo = (
            request.query_params.get("type")
            or request.query_params.get("topic")
            or body.get("type")
            or body.get("topic")
        )

        dados = body.get("data") or {}
        pagamento_id = (
            request.query_params.get("data.id")
            or dados.get("id")
        )

        # Notificação não relacionada a pagamento:
        # recebe o evento sem realizar alterações.
        if tipo != "payment" or not pagamento_id:
            return {"recebido": True}

        token = obter_token()

        resposta = requests.get(
            f"{MERCADO_PAGO_PAYMENT_URL}/{pagamento_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )

        # Simulações podem usar IDs fictícios.
        # Não aprovar pedidos com base nesses eventos.
        if resposta.status_code == 404:
            print(
                "Pagamento não encontrado; possível simulação:",
                pagamento_id,
            )
            return {
                "recebido": True,
                "processado": False,
                "motivo": "Pagamento ainda não encontrado.",
            }

        if resposta.status_code != 200:
            print(
                "Falha ao consultar pagamento do webhook:",
                resposta.status_code,
                resposta.text,
            )
            raise HTTPException(
                status_code=502,
                detail="Não foi possível validar o pagamento.",
            )

        pagamento = resposta.json()

        if pagamento.get("status") != "approved":
            return {
                "recebido": True,
                "processado": False,
                "status_pagamento": pagamento.get("status"),
            }

        pedido_id = pagamento.get("external_reference")

        if not pedido_id:
            return {"recebido": True, "processado": False}

        resultado = consultar_status_pagamento(str(pedido_id))

        return {
            "recebido": True,
            "processado": resultado.get("status_pedido") == "pago",
        }

    except HTTPException:
        raise
    except Exception as erro:
        print(f"Erro ao processar webhook do Mercado Pago: {erro!r}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar a notificação.",
        )
