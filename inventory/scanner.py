"""
Varredura de rede para o NetInventory.

Estratégia (em ordem de prioridade):
  1. nmap_agent.py rodando no host Windows (retorna MAC + fabricante reais)
  2. nmap dentro do container (descobre hosts via ICMP, sem MAC no Windows/bridge)

O agente local é necessário para obter MAC address no Windows + Docker Desktop,
pois o bridge network do Docker não tem acesso L2 direto à rede física.
"""

import json
import logging
import os
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# URL do agente local — pode ser sobrescrita via variável de ambiente
_HOST_AGENT_URL = os.environ.get("NMAP_AGENT_URL", "http://host.docker.internal:9998/scan")
_HOST_AGENT_TIMEOUT = 180  # segundos — suficiente para uma /24

_MAX_PING_WORKERS = 50


def scan_network(cidr: str) -> tuple[list[dict], dict]:
    """
    Varre a faixa CIDR e retorna lista de hosts.

    Cada item:
        ip          str        - endereço IPv4
        status      str        - "ONLINE" | "OFFLINE"
        latencia_ms float|None - latência em ms
        mac_address str        - MAC address (vazio se indisponível)
        fabricante  str        - fabricante via OUI (vazio se indisponível)
    """
    diagnostico = {
        "origem": "host_agent",
        "agent_error": None,
    }

    # Tenta agente local primeiro (tem acesso L2 -> retorna MAC)
    results, agent_error = _scan_via_host_agent(cidr)

    if results is None:
        logger.info("nmap_agent não disponível, usando nmap interno (sem MAC no Windows).")
        diagnostico["origem"] = "container_nmap"
        diagnostico["agent_error"] = agent_error
        results = _scan_in_container(cidr)

    # Mede latência de todos os hosts ONLINE em paralelo
    online = [r for r in results if r["status"] == "ONLINE"]
    if online:
        latencias = _ping_paralelo([r["ip"] for r in online])
        for r in online:
            r["latencia_ms"] = latencias.get(r["ip"])

    results = sorted(results, key=lambda r: _ip_sort_key(r["ip"]))
    diagnostico["mac_disponivel"] = any((r.get("mac_address") or "").strip() for r in results)
    diagnostico["fabricante_disponivel"] = any((r.get("fabricante") or "").strip() for r in results)

    return results, diagnostico


# ── estratégia 1: agente local no Windows ────────────────────────────────────

def _scan_via_host_agent(cidr: str) -> tuple[list[dict] | None, str | None]:
    """
    Chama o nmap_agent.py rodando no host via host.docker.internal:9998.
    Retorna lista de resultados, ou None se o agente não estiver disponível.
    """
    try:
        url = f"{_HOST_AGENT_URL}?cidr={urllib.parse.quote(cidr)}"
        with urllib.request.urlopen(url, timeout=_HOST_AGENT_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        resultados = data.get("resultados", [])
        # Normaliza: garante campos obrigatórios
        for r in resultados:
            r.setdefault("latencia_ms", None)
            r.setdefault("mac_address", "")
            r.setdefault("fabricante", "")
        return resultados, None

    except Exception as exc:
        logger.debug("nmap_agent indisponível: %s", exc)
        return None, str(exc)


# ── estratégia 2: nmap dentro do container ───────────────────────────────────

def _scan_in_container(cidr: str) -> list[dict]:
    """Roda nmap -sn dentro do container. Descobre hosts, mas sem MAC no bridge."""
    try:
        import nmap
    except ImportError:
        logger.error("python-nmap não está instalado.")
        return []

    nm = nmap.PortScanner()
    try:
        nm.scan(hosts=cidr, arguments="-sn --host-timeout 5s")
    except nmap.PortScannerError as exc:
        logger.error("Erro ao executar nmap: %s", exc)
        return []

    results = []
    for host in nm.all_hosts():
        addrs = nm[host].get("addresses", {})
        mac = addrs.get("mac", "")
        fabricante = nm[host].get("vendor", {}).get(mac, "") if mac else ""
        results.append({
            "ip": addrs.get("ipv4", host),
            "status": "ONLINE" if nm[host].state() == "up" else "OFFLINE",
            "latencia_ms": None,
            "mac_address": mac,
            "fabricante": fabricante,
        })

    return results


# ── latência em paralelo ──────────────────────────────────────────────────────

def _ping_paralelo(ips: list[str]) -> dict[str, float | None]:
    """Pinga lista de IPs simultaneamente. Retorna {ip: latencia_ms}."""
    import ping3

    def _medir(ip):
        try:
            result = ping3.ping(ip, timeout=2)
            if result and result is not False:
                return ip, round(result * 1000, 2)
        except Exception:
            pass
        return ip, None

    resultados = {}
    with ThreadPoolExecutor(max_workers=min(_MAX_PING_WORKERS, len(ips))) as pool:
        futures = {pool.submit(_medir, ip): ip for ip in ips}
        for future in as_completed(futures):
            ip, latencia = future.result()
            resultados[ip] = latencia

    return resultados


# ── utils ─────────────────────────────────────────────────────────────────────

def _ip_sort_key(ip: str):
    try:
        return tuple(int(p) for p in ip.split("."))
    except ValueError:
        return (0, 0, 0, 0)
