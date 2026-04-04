import csv
import urllib.parse
from datetime import date
from io import BytesIO

from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone

try:
    import ping3
    PING3_DISPONIVEL = True
except ImportError:
    PING3_DISPONIVEL = False

from .models import HistoricoPing


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_ip(obj):
    """Retorna o IP do objeto, independente do tipo."""
    return getattr(obj, "ip", None)


def _tipo_dispositivo(model):
    return model.__name__.lower()


def _executar_ping(ip):
    """Executa ping e retorna (status, latencia_ms)."""
    if not PING3_DISPONIVEL:
        return "OFFLINE", None
    try:
        resultado = ping3.ping(ip, timeout=2)
        if resultado is None or resultado is False:
            return "OFFLINE", None
        return "ONLINE", round(resultado * 1000, 2)
    except Exception:
        return "OFFLINE", None


def _salvar_historico(tipo, obj_id, ip, status, latencia):
    HistoricoPing.objects.create(
        dispositivo_tipo=tipo,
        dispositivo_id=obj_id,
        ip=ip,
        status=status,
        latencia_ms=latencia,
    )


# ─── Action: Pingar ───────────────────────────────────────────────────────────

def pingar_dispositivos(modeladmin, request, queryset):
    online = 0
    offline = 0
    sem_ip = 0
    tipo = _tipo_dispositivo(queryset.model)

    for obj in queryset:
        ip = _get_ip(obj)
        if not ip:
            sem_ip += 1
            continue
        status, latencia = _executar_ping(ip)
        _salvar_historico(tipo, obj.pk, ip, status, latencia)
        if status == "ONLINE":
            online += 1
        else:
            offline += 1

    partes = []
    if online:
        partes.append(f"{online} online")
    if offline:
        partes.append(f"{offline} offline")
    if sem_ip:
        partes.append(f"{sem_ip} sem IP cadastrado")

    msg = "Ping concluído: " + ", ".join(partes) + "."
    messages.success(request, msg)


pingar_dispositivos.short_description = "🔔 Pingar dispositivos selecionados"


# ─── Action: Exportar CSV ─────────────────────────────────────────────────────

def exportar_csv(modeladmin, request, queryset):
    model = queryset.model
    model_name = model.__name__.lower()
    hoje = date.today().strftime("%Y%m%d")
    filename = f"{model_name}_{hoje}.csv"

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    campos = [f.name for f in model._meta.fields]
    writer = csv.writer(response)
    writer.writerow(campos)

    for obj in queryset:
        linha = []
        for campo in campos:
            valor = getattr(obj, campo, "")
            if hasattr(valor, "strftime"):
                valor = valor.strftime("%d/%m/%Y %H:%M")
            linha.append(str(valor) if valor is not None else "")
        writer.writerow(linha)

    return response


exportar_csv.short_description = "📥 Exportar CSV"


# ─── Action: Gerar PDF ────────────────────────────────────────────────────────

def gerar_pdf(modeladmin, request, queryset):
    from .reports import gerar_pdf_dispositivos
    return gerar_pdf_dispositivos(queryset)


gerar_pdf.short_description = "📄 Gerar PDF"


# ─── Action: Compartilhar WhatsApp ────────────────────────────────────────────

def compartilhar_whatsapp(modeladmin, request, queryset):
    from django.http import HttpResponseRedirect

    model_name = queryset.model._meta.verbose_name_plural.upper()
    linhas = [f"*{model_name} — NetInventory UFPB*", ""]

    for obj in queryset:
        ip = _get_ip(obj)
        linha = f"• {obj}"
        if ip:
            linha += f" | IP: {ip}"
        linhas.append(linha)

    linhas.append(f"\n_Total: {queryset.count()} dispositivo(s)_")
    texto = "\n".join(linhas)
    url = "https://wa.me/?text=" + urllib.parse.quote(texto)
    return HttpResponseRedirect(url)


compartilhar_whatsapp.short_description = "💬 Compartilhar via WhatsApp"
