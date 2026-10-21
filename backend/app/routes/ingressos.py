
from io import BytesIO

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import supabase


router = APIRouter(
    prefix="/api/ingressos",
    tags=["Ingressos"],
)

# Dados do evento
EVENTO = "Cristoteca Todos os Santos"
DATA_EVENTO = "31 de outubro de 2026"
HORARIO_EVENTO = "19h"
ENDERECO_EVENTO = (
    "Rua Capri, 53 - Jardim Santa Emilia"
)


def gerar_qr(codigo: str) -> BytesIO:
    """Gera a imagem do QR Code com o código único do ingresso."""
    imagem = qrcode.make(codigo)
    arquivo = BytesIO()
    imagem.save(arquivo, format="PNG")
    arquivo.seek(0)
    return arquivo


def gerar_pdf(pedido: dict, ingressos: list) -> BytesIO:
    """Gera um PDF com uma página para cada ingresso."""
    arquivo = BytesIO()
    pdf = canvas.Canvas(arquivo, pagesize=A4)

    largura, altura = A4

    verde = colors.HexColor("#2A4737")
    dourado = colors.HexColor("#C5A46D")

    for numero, ingresso in enumerate(ingressos, start=1):
        # Fundo e cabeçalho
        pdf.setFillColor(verde)
        pdf.rect(0, altura - 190, largura, 190, fill=1, stroke=0)

        pdf.setFillColor(dourado)
        pdf.rect(0, altura - 195, largura, 5, fill=1, stroke=0)

        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawCentredString(
            largura / 2,
            altura - 55,
            "INGRESSO DIGITAL",
        )

        pdf.setFont("Helvetica-Bold", 23)
        pdf.drawCentredString(
            largura / 2,
            altura - 100,
            EVENTO,
        )

        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(
            largura / 2,
            altura - 130,
            "Um encontro de fé, música e comunhão",
        )

        # Informações do ingresso
        pdf.setFillColor(verde)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(50, altura - 245, "DADOS DO EVENTO")

        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica", 11)

        pdf.drawString(
            50, altura - 275, f"Data: {DATA_EVENTO}"
        )
        pdf.drawString(
            50, altura - 298, f"Horário: {HORARIO_EVENTO}"
        )
        pdf.drawString(
            50, altura - 321, f"Local: {ENDERECO_EVENTO}"
        )

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(
            50, altura - 370, "INGRESSO INDIVIDUAL"
        )

        pdf.setFont("Helvetica", 11)
        pdf.drawString(
            50,
            altura - 395,
            f"Comprador: {pedido['nome_comprador']}",
        )
        pdf.drawString(
            50,
            altura - 418,
            f"Ingresso {numero} de {len(ingressos)}",
        )

        # QR Code exclusivo deste ingresso
        imagem_qr = gerar_qr(ingresso["codigo"])

        tamanho_qr = 145
        pdf.drawImage(
            ImageReader(imagem_qr),
            (largura - tamanho_qr) / 2,
            altura - 610,
            width=tamanho_qr,
            height=tamanho_qr,
        )

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(
            largura / 2,
            altura - 630,
            "Apresente este QR Code na entrada",
        )

        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.grey)
        pdf.drawCentredString(
            largura / 2,
            altura - 650,
            f"Codigo: {ingresso['codigo']}",
        )

        pdf.setFillColor(verde)
        pdf.rect(40, 65, largura - 80, 2, fill=1, stroke=0)

        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(
            largura / 2,
            45,
            "Guarde seu ingresso e nao compartilhe seu QR Code.",
        )

        pdf.showPage()

    pdf.save()
    arquivo.seek(0)
    return arquivo


@router.get("/pedido/{pedido_id}/pdf")
def baixar_ingressos_pdf(pedido_id: str):
    """Libera os ingressos em PDF somente após pagamento confirmado."""

    try:
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

        pedido = resultado.data[0]

        if pedido["status"] != "pago":
            raise HTTPException(
                status_code=403,
                detail="Os ingressos só são liberados após a confirmação do pagamento.",
            )

        resultado_ingressos = (
            supabase.table("cristoteca_ingressos")
            .select("*")
            .eq("pedido_id", pedido_id)
            .execute()
        )

        ingressos = resultado_ingressos.data or []

        if len(ingressos) != pedido["quantidade"]:
            raise HTTPException(
                status_code=409,
                detail="A quantidade de ingressos precisa ser conferida.",
            )

        if any(
            ingresso["status"] != "valido"
            for ingresso in ingressos
        ):
            raise HTTPException(
                status_code=409,
                detail="Há ingressos que não estão válidos para emissão.",
            )

        arquivo = gerar_pdf(pedido, ingressos)

        return StreamingResponse(
            arquivo,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="ingressos-{pedido_id}.pdf"'
                )
            },
        )

    except HTTPException:
        raise
    except Exception as erro:
        print(f"Erro ao gerar PDF dos ingressos: {erro!r}")
        raise HTTPException(
            status_code=500,
            detail="Não foi possível gerar os ingressos.",
        )
