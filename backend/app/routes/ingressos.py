
from io import BytesIO
from textwrap import wrap

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import supabase


router = APIRouter(
    prefix="/api/ingressos",
    tags=["Ingressos"],
)

# Dados do evento
EVENTO = "CRISTOTECA"
SUBTITULO = "TODOS OS SANTOS"
DATA_EVENTO = "31 de outubro de 2026"
HORARIO_EVENTO = "19h"
ENDERECO_EVENTO = "Rua Capri, 53 - Jardim Santa Emilia"

# Identidade visual da página
ROXO = colors.HexColor("#10051E")
ROXO_CARD = colors.HexColor("#1D0B30")
ROSA = colors.HexColor("#FF4EE9")
AMARELO = colors.HexColor("#FFE45C")
BRANCO = colors.HexColor("#FFFFFF")
CINZA = colors.HexColor("#C8BFD3")


def desenhar_texto_ajustado(
    pdf,
    texto: str,
    x: float,
    y: float,
    largura_maxima: float,
    fonte: str = "Helvetica",
    tamanho: int = 10,
):
    """Desenha um texto reduzindo a fonte se ele for muito comprido."""
    tamanho_atual = tamanho

    while (
        stringWidth(str(texto), fonte, tamanho_atual) > largura_maxima
        and tamanho_atual > 7
    ):
        tamanho_atual -= 0.5

    pdf.setFont(fonte, tamanho_atual)
    pdf.drawString(x, y, str(texto))


def gerar_qr(codigo: str) -> BytesIO:
    """Gera o QR Code exclusivo do ingresso."""
    imagem = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    imagem.add_data(codigo)
    imagem.make(fit=True)

    imagem_png = imagem.make_image(
        fill_color="black",
        back_color="white",
    )

    arquivo = BytesIO()
    imagem_png.save(arquivo, format="PNG")
    arquivo.seek(0)

    return arquivo


def gerar_pdf(pedido: dict, ingressos: list) -> BytesIO:
    """Gera uma página estilizada para cada ingresso."""
    arquivo = BytesIO()
    pdf = canvas.Canvas(arquivo, pagesize=A4)

    largura, altura = A4
    margem = 30

    for numero, ingresso in enumerate(ingressos, start=1):
        # Fundo da página
        pdf.setFillColor(ROXO)
        pdf.rect(0, 0, largura, altura, fill=1, stroke=0)

        # Moldura externa
        pdf.setStrokeColor(ROSA)
        pdf.setLineWidth(1.2)
        pdf.roundRect(
            margem,
            margem,
            largura - 2 * margem,
            altura - 2 * margem,
            18,
            fill=0,
            stroke=1,
        )

        # Cabeçalho
        pdf.setFillColor(ROXO_CARD)
        pdf.roundRect(
            margem + 1,
            altura - 225,
            largura - 2 * margem - 2,
            190,
            16,
            fill=1,
            stroke=0,
        )

        # Faixa neon
        pdf.setFillColor(ROSA)
        pdf.roundRect(
            margem + 18,
            altura - 57,
            largura - 2 * margem - 36,
            3,
            1,
            fill=1,
            stroke=0,
        )

        pdf.setFillColor(AMARELO)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawCentredString(
            largura / 2,
            altura - 83,
            "INGRESSO DIGITAL",
        )

        pdf.setFillColor(ROSA)
        pdf.setFont("Helvetica-Bold", 32)
        pdf.drawCentredString(
            largura / 2,
            altura - 125,
            EVENTO,
        )

        pdf.setFillColor(AMARELO)
        pdf.setFont("Helvetica-Bold", 17)
        pdf.drawCentredString(
            largura / 2,
            altura - 151,
            SUBTITULO,
        )

        pdf.setFillColor(BRANCO)
        pdf.setFont("Helvetica", 10)
        pdf.drawCentredString(
            largura / 2,
            altura - 178,
            "Uma noite de fe, musica e comunhao",
        )

        # Identificação do ingresso
        pdf.setFillColor(AMARELO)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(
            margem + 24,
            altura - 260,
            "DETALHES DO EVENTO",
        )

        pdf.setStrokeColor(ROSA)
        pdf.setLineWidth(1)
        pdf.line(
            margem + 24,
            altura - 270,
            largura - margem - 24,
            altura - 270,
        )

        # Informações do evento
        x_texto = margem + 24

        pdf.setFillColor(CINZA)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(x_texto, altura - 295, "DATA")
        pdf.drawString(x_texto, altura - 328, "HORARIO")
        pdf.drawString(x_texto, altura - 361, "LOCAL")

        pdf.setFillColor(BRANCO)
        pdf.setFont("Helvetica", 11)
        pdf.drawString(x_texto + 85, altura - 295, DATA_EVENTO)
        pdf.drawString(x_texto + 85, altura - 328, HORARIO_EVENTO)

        desenhar_texto_ajustado(
            pdf,
            ENDERECO_EVENTO,
            x_texto + 85,
            altura - 361,
            largura - (x_texto + 85) - margem - 24,
            tamanho=10,
        )

        # Cartão do ingresso
        y_cartao = altura - 405
        pdf.setFillColor(ROXO_CARD)
        pdf.roundRect(
            margem + 18,
            y_cartao - 63,
            largura - 2 * margem - 36,
            82,
            12,
            fill=1,
            stroke=0,
        )

        pdf.setFillColor(ROSA)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(
            margem + 34,
            y_cartao - 10,
            "INGRESSO INDIVIDUAL",
        )

        pdf.setFillColor(BRANCO)
        desenhar_texto_ajustado(
            pdf,
            f"Comprador: {pedido.get('nome_comprador', 'Participante')}",
            margem + 34,
            y_cartao - 32,
            largura - 2 * margem - 68,
            tamanho=10,
        )

        pdf.setFillColor(AMARELO)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(
            margem + 34,
            y_cartao - 51,
            f"INGRESSO {numero} DE {len(ingressos)}",
        )

        # QR Code em área branca para facilitar a leitura
        imagem_qr = gerar_qr(ingresso["codigo"])
        tamanho_qr = 132
        x_qr = (largura - tamanho_qr) / 2
        y_qr = 105

        pdf.setFillColor(BRANCO)
        pdf.roundRect(
            x_qr - 12,
            y_qr - 12,
            tamanho_qr + 24,
            tamanho_qr + 24,
            10,
            fill=1,
            stroke=0,
        )

        pdf.drawImage(
            ImageReader(imagem_qr),
            x_qr,
            y_qr,
            width=tamanho_qr,
            height=tamanho_qr,
            preserveAspectRatio=True,
            mask="auto",
        )

        pdf.setFillColor(AMARELO)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(
            largura / 2,
            88,
            "APRESENTE O QR CODE NA ENTRADA",
        )

        pdf.setFillColor(CINZA)
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString(
            largura / 2,
            73,
            f"Codigo do ingresso: {ingresso['codigo']}",
        )

        # Rodapé
        pdf.setStrokeColor(ROSA)
        pdf.line(
            margem + 20,
            62,
            largura - margem - 20,
            62,
        )

        pdf.setFillColor(CINZA)
        pdf.setFont("Helvetica", 8)
        pdf.drawCentredString(
            largura / 2,
            47,
            "Guarde seu ingresso. Nao compartilhe seu QR Code.",
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
                detail="Pedido nao encontrado.",
            )

        pedido = resultado.data[0]

        if pedido.get("status") != "pago":
            raise HTTPException(
                status_code=403,
                detail=(
                    "Os ingressos so sao liberados apos "
                    "a confirmacao do pagamento."
                ),
            )

        resultado_ingressos = (
            supabase.table("cristoteca_ingressos")
            .select("*")
            .eq("pedido_id", pedido_id)
            .execute()
        )

        ingressos = resultado_ingressos.data or []

        if len(ingressos) != pedido.get("quantidade"):
            raise HTTPException(
                status_code=409,
                detail="A quantidade de ingressos precisa ser conferida.",
            )

        if any(
            ingresso.get("status") != "valido"
            or not ingresso.get("codigo")
            for ingresso in ingressos
        ):
            raise HTTPException(
                status_code=409,
                detail="Ha ingressos invalidos ou sem codigo para emissao.",
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
            detail="Nao foi possivel gerar os ingressos.",
        )
