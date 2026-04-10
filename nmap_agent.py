#!/usr/bin/env python3
"""
Agente local de varredura nmap para o NetInventory.

Execute este script diretamente no Windows (FORA do Docker):
    python nmap_agent.py

Requisitos no Windows:
    pip install python-nmap
    nmap instalado em: https://nmap.org/download.html

O Django (dentro do Docker) chamará este agente via:
    http://host.docker.internal:9998/scan?cidr=10.10.100.0/24
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 9998


class ScanHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        cidr = params.get("cidr", [""])[0].strip()

        if not cidr:
            self._json({"erro": "Parâmetro 'cidr' obrigatório."}, status=400)
            return

        print(f"[nmap-agent] Varrendo: {cidr}")
        try:
            import nmap
            nm = nmap.PortScanner()
            nm.scan(hosts=cidr, arguments="-sn --host-timeout 5s")

            results = []
            for host in nm.all_hosts():
                addrs = nm[host].get("addresses", {})
                mac = addrs.get("mac", "")
                vendor = nm[host].get("vendor", {}).get(mac, "") if mac else ""
                results.append({
                    "ip": addrs.get("ipv4", host),
                    "status": "ONLINE" if nm[host].state() == "up" else "OFFLINE",
                    "mac_address": mac,
                    "fabricante": vendor,
                })

            print(f"[nmap-agent] {len(results)} host(s) encontrado(s).")
            self._json({"resultados": results})

        except ImportError:
            self._json({"erro": "python-nmap não instalado. Execute: pip install python-nmap"}, status=500)
        except Exception as exc:
            self._json({"erro": str(exc)}, status=500)

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # silencia logs padrão do HTTPServer


if __name__ == "__main__":
    try:
        import nmap  # noqa — só valida a instalação na inicialização
    except ImportError:
        print("ERRO: python-nmap não está instalado.")
        print("Execute: pip install python-nmap")
        sys.exit(1)

    server = HTTPServer(("0.0.0.0", PORT), ScanHandler)
    print(f"nmap-agent rodando em http://0.0.0.0:{PORT}")
    print("Aguardando requisições do Docker... (Ctrl+C para parar)\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nnmap-agent encerrado.")
