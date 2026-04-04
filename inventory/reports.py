from datetime import datetime
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

INSTITUICAO = "UFPB — Universidade Federal da Paraíba"
SISTEMA = "NetInventory — Inventário de Infraestrutura de Rede"
COR_PRIMARIA = colors.HexColor("#0e86c7")
COR_CABECALHO = colors.HexColor("#0369a1")
COR_LINHA_PAR = colors.HexColor("#f0f9ff")


# ─── Cabeçalho / Rodapé de página ─────────────────────────────────────────────

def _cabecalho_rodape(canvas, doc):
    canvas.saveState()
    largura, altura = A4

    # Cabeçalho
    canvas.setFillColor(COR_PRIMARIA)
    canvas.rect(0, altura - 2 * cm, largura, 2 * cm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(1 * cm, altura - 1.1 * cm, SISTEMA)
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(largura - 1 * cm, altura - 1.1 * cm, INSTITUICAO)

    # Rodapé
    canvas.setFillColor(COR_PRIMARIA)
    canvas.rect(0, 0, largura, 1.2 * cm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    agora = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
    canvas.drawString(1 * cm, 0.4 * cm, f"Gerado em: {agora}")
    canvas.drawCentredString(largura / 2, 0.4 * cm, f"Página {doc.page}")
    canvas.drawRightString(largura - 1 * cm, 0.4 * cm, "NetInventory © UFPB")

    canvas.restoreState()


# ─── Estilos ──────────────────────────────────────────────────────────────────

def _estilos():
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        fontSize=18,
        textColor=COR_PRIMARIA,
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Normal"],
        fontSize=11,
        textColor=COR_CABECALHO,
        spaceBefore=12,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    normal = ParagraphStyle(
        "Normal2",
        parent=styles["Normal"],
        fontSize=9,
    )
    return titulo, subtitulo, normal


# ─── Tabela genérica ──────────────────────────────────────────────────────────

def _tabela_dispositivos(queryset, campos=None):
    model = queryset.model
    if campos is None:
        campos = [f.name for f in model._meta.fields if f.name != "id"]

    cabecalho = [f.verbose_name.title() if hasattr(f, "verbose_name") else f.name
                 for f in model._meta.fields if f.name in campos]

    dados = [cabecalho]
    for obj in queryset:
        linha = []
        for campo in campos:
            valor = getattr(obj, campo, "")
            if valor is None:
                valor = "—"
            elif hasattr(valor, "strftime"):
                valor = timezone.localtime(valor).strftime("%d/%m/%Y %H:%M") if hasattr(valor, "hour") else valor.strftime("%d/%m/%Y")
            elif hasattr(valor, "__str__") and not isinstance(valor, (str, int, float, bool)):
                valor = str(valor)
            else:
                valor = str(valor)
            linha.append(Paragraph(valor[:60], ParagraphStyle("cell", fontSize=8)))
        dados.append(linha)

    num_cols = len(cabecalho)
    col_width = (A4[0] - 2 * cm) / num_cols

    tabela = Table(dados, colWidths=[col_width] * num_cols, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_LINHA_PAR]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tabela


# ─── PDF de dispositivos (action) ─────────────────────────────────────────────

def gerar_pdf_dispositivos(queryset):
    model = queryset.model
    model_name = model._meta.verbose_name_plural
    hoje = timezone.localtime(timezone.now()).strftime("%d/%m/%Y às %H:%M")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=2.5 * cm,
        bottomMargin=1.8 * cm,
    )

    titulo_style, subtitulo_style, normal_style = _estilos()
    elementos = []

    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(Paragraph(f"Relatório: {model_name}", titulo_style))
    elementos.append(Paragraph(f"Gerado em {hoje}", normal_style))
    elementos.append(Paragraph(f"Total de registros: {queryset.count()}", normal_style))
    elementos.append(Spacer(1, 0.4 * cm))
    elementos.append(HRFlowable(width="100%", thickness=1, color=COR_PRIMARIA))
    elementos.append(Spacer(1, 0.3 * cm))

    campos = [f.name for f in model._meta.fields if f.name not in ("id",)]
    elementos.append(_tabela_dispositivos(queryset, campos))

    doc.build(elementos, onFirstPage=_cabecalho_rodape, onLaterPages=_cabecalho_rodape)

    pdf = buffer.getvalue()
    buffer.close()

    filename = f"{model.__name__.lower()}_relatorio.pdf"
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write(pdf)
    return response


# ─── PDF geral de todos os dispositivos ───────────────────────────────────────

def gerar_relatorio_geral():
    from .models import Switch, Roteador, AccessPoint, Computador, EmailInstitucional, Site, Subrede

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=2.5 * cm,
        bottomMargin=1.8 * cm,
    )

    titulo_style, subtitulo_style, normal_style = _estilos()
    agora = timezone.localtime(timezone.now())
    hoje = agora.strftime("%d/%m/%Y às %H:%M")
    elementos = []

    # Capa / Sumário
    elementos.append(Spacer(1, 1 * cm))
    elementos.append(Paragraph("Relatório Geral de Inventário", titulo_style))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph(INSTITUICAO, ParagraphStyle(
        "inst", fontSize=11, alignment=TA_CENTER, textColor=colors.grey
    )))
    elementos.append(Paragraph(f"Emitido em {hoje}", ParagraphStyle(
        "data", fontSize=10, alignment=TA_CENTER, spaceBefore=6
    )))
    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(HRFlowable(width="100%", thickness=2, color=COR_PRIMARIA))
    elementos.append(Spacer(1, 0.5 * cm))

    secoes = [
        ("Switches", Switch, ["nome", "ip", "modelo", "fabricante", "localizacao", "quantidade_portas", "ativo"]),
        ("Roteadores", Roteador, ["nome", "ip", "modelo", "fabricante", "localizacao", "ativo"]),
        ("Access Points", AccessPoint, ["nome", "ip", "ssid", "frequencia", "fabricante", "localizacao", "ativo"]),
        ("Computadores", Computador, ["nome", "hostname", "ip", "sistema_operacional", "usuario_responsavel", "departamento"]),
        ("E-mails Institucionais", EmailInstitucional, ["endereco", "usuario", "departamento", "servidor_email", "cota_mb"]),
        ("Sites", Site, ["nome", "url", "ip_servidor", "responsavel", "certificado_expiracao", "ativo"]),
        ("Subredes", Subrede, ["cidr", "gateway", "vlan", "finalidade", "faixa_inicio", "faixa_fim"]),
    ]

    # Sumário
    elementos.append(Paragraph("Sumário", subtitulo_style))
    sumario_dados = [["Tipo", "Quantidade"]]
    for nome_secao, model, _ in secoes:
        total = model.objects.count()
        sumario_dados.append([nome_secao, str(total)])

    sumario_tabela = Table(sumario_dados, colWidths=[12 * cm, 4 * cm])
    sumario_tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_LINHA_PAR]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(sumario_tabela)
    elementos.append(PageBreak())

    # Seções por tipo
    for nome_secao, model, campos in secoes:
        qs = model.objects.all()
        elementos.append(Paragraph(nome_secao, subtitulo_style))
        elementos.append(Paragraph(f"Total: {qs.count()} registro(s)", normal_style))
        elementos.append(Spacer(1, 0.2 * cm))

        if qs.exists():
            elementos.append(_tabela_dispositivos(qs, campos))
        else:
            elementos.append(Paragraph("Nenhum registro cadastrado.", normal_style))

        elementos.append(Spacer(1, 0.6 * cm))
        elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        elementos.append(Spacer(1, 0.4 * cm))

    doc.build(elementos, onFirstPage=_cabecalho_rodape, onLaterPages=_cabecalho_rodape)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf
