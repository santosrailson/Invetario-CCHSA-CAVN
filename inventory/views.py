from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import (
    Switch, Roteador, AccessPoint, Computador,
    EmailInstitucional, Site, Subrede, HistoricoPing,
)

try:
    import ping3
    PING3_DISPONIVEL = True
except ImportError:
    PING3_DISPONIVEL = False


# ─── Ping por IP ──────────────────────────────────────────────────────────────

@require_GET
@staff_member_required
def ping_ip(request, ip):
    status = "OFFLINE"
    latencia_ms = None

    if PING3_DISPONIVEL:
        try:
            resultado = ping3.ping(ip, timeout=2)
            if resultado and resultado is not False:
                status = "ONLINE"
                latencia_ms = round(resultado * 1000, 2)
        except Exception:
            pass

    HistoricoPing.objects.create(
        dispositivo_tipo="manual",
        dispositivo_id=0,
        ip=ip,
        status=status,
        latencia_ms=latencia_ms,
    )

    return JsonResponse({
        "ip": ip,
        "status": status,
        "latencia_ms": latencia_ms,
        "timestamp": timezone.now().isoformat(),
    })


# ─── Dashboard ────────────────────────────────────────────────────────────────

@require_GET
@staff_member_required
def dashboard(request):
    total_switches = Switch.objects.count()
    total_roteadores = Roteador.objects.count()
    total_aps = AccessPoint.objects.count()
    total_computadores = Computador.objects.count()
    total_emails = EmailInstitucional.objects.count()
    total_sites = Site.objects.count()
    total_subredes = Subrede.objects.count()

    total_ips_subredes = sum(s.total_ips() for s in Subrede.objects.all())

    ultimos_pings = HistoricoPing.objects.order_by("-timestamp")[:10]

    online_hoje = HistoricoPing.objects.filter(
        status="ONLINE",
        timestamp__date=timezone.localdate(),
    ).count()
    offline_hoje = HistoricoPing.objects.filter(
        status="OFFLINE",
        timestamp__date=timezone.localdate(),
    ).count()

    context = {
        "title": "Dashboard — NetInventory",
        "totais": {
            "switches": total_switches,
            "roteadores": total_roteadores,
            "access_points": total_aps,
            "computadores": total_computadores,
            "emails": total_emails,
            "sites": total_sites,
            "subredes": total_subredes,
        },
        "total_dispositivos": (
            total_switches + total_roteadores + total_aps + total_computadores
        ),
        "total_ips_subredes": total_ips_subredes,
        "ultimos_pings": ultimos_pings,
        "online_hoje": online_hoje,
        "offline_hoje": offline_hoje,
    }
    return render(request, "admin/dashboard.html", context)


# ─── Relatório Geral PDF ──────────────────────────────────────────────────────

@require_GET
@staff_member_required
def relatorio_geral(request):
    from .reports import gerar_relatorio_geral

    pdf = gerar_relatorio_geral()
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="relatorio_geral_netinventory.pdf"'
    response.write(pdf)
    return response
