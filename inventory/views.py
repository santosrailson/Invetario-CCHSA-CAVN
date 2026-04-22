import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from .models import (
    Switch, Roteador, AccessPoint, Computador,
    EmailInstitucional, Site, Subrede, HistoricoPing, Fabricante,
)

logger = logging.getLogger(__name__)

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


# ─── Varredura de Rede ───────────────────────────────────────────────────────

@staff_member_required
def varredura_rede(request):
    """
    GET  → formulário de varredura
    POST → executa varredura, salva resultados e retorna JSON
    """
    if request.method == "POST":
        cidr = request.POST.get("cidr", "").strip()
        if not cidr:
            return JsonResponse({"erro": "Informe uma faixa de IP válida."}, status=400)

        try:
            from .scanner import scan_network
            resultados, diagnostico = scan_network(cidr)

            novos_fabricantes = 0
            for r in resultados:
                # Atualiza o registro existente ou cria um novo —
                # evita duplicatas: cada IP de varredura tem apenas uma linha.
                HistoricoPing.objects.filter(
                    dispositivo_tipo="varredura",
                    ip=r["ip"],
                ).delete()
                HistoricoPing.objects.create(
                    dispositivo_tipo="varredura",
                    dispositivo_id=None,
                    ip=r["ip"],
                    status=r["status"],
                    latencia_ms=r["latencia_ms"],
                    mac_address=r["mac_address"],
                    fabricante_mac=r["fabricante"],
                )

                # Cadastra o fabricante automaticamente se ainda não existir
                nome_fabricante = (r.get("fabricante") or "").strip()[:100]
                if nome_fabricante:
                    try:
                        _, criado = Fabricante.objects.get_or_create(nome=nome_fabricante)
                        if criado:
                            novos_fabricantes += 1
                    except Exception:
                        logger.exception("Erro ao cadastrar fabricante: %r", nome_fabricante)

            return JsonResponse({
                "cidr": cidr,
                "total": len(resultados),
                "novos_fabricantes": novos_fabricantes,
                "resultados": resultados,
                "diagnostico": diagnostico,
                "aviso": (
                    "MAC e fabricante podem ficar vazios quando o nmap_agent local não está ativo. "
                    "No Windows host, execute: python nmap_agent.py"
                    if diagnostico.get("origem") != "host_agent"
                    else ""
                ),
            })
        except Exception as exc:
            import traceback
            return JsonResponse(
                {"erro": str(exc), "detalhe": traceback.format_exc()},
                status=500,
            )

    return render(request, "admin/inventory/varredura.html", {
        "title": "Varredura de Rede",
    })


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
