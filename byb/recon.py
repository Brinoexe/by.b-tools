"""
by.b :: recon
Testes de reconhecimento e postura de segurança para um domínio PRÓPRIO.
Não faz nada além de checar informações públicas do seu próprio site
(headers, TLS, DNS, robots.txt). Não realiza port scan agressivo nem
tentativas de exploração.
"""

import socket
import ssl
import json
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]


def check_headers(url: str) -> dict:
    """Verifica quais cabeçalhos de segurança HTTP estão presentes."""
    req = Request(url, headers={"User-Agent": "by.b-recon/1.0"})
    try:
        with urlopen(req, timeout=10) as resp:
            headers = dict(resp.getheaders())
    except (URLError, HTTPError) as e:
        return {"erro": str(e)}

    result = {}
    for h in SECURITY_HEADERS:
        result[h] = headers.get(h, "AUSENTE")
    result["server"] = headers.get("Server", "não informado")
    return result


def check_tls(hostname: str, port: int = 443) -> dict:
    """Verifica validade e detalhes do certificado TLS."""
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                not_after = datetime.strptime(
                    cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
                ).replace(tzinfo=timezone.utc)
                dias_restantes = (not_after - datetime.now(timezone.utc)).days
                return {
                    "emissor": dict(x[0] for x in cert["issuer"]),
                    "valido_ate": cert["notAfter"],
                    "dias_restantes": dias_restantes,
                    "protocolo": ssock.version(),
                }
    except Exception as e:
        return {"erro": str(e)}


def check_dns(hostname: str) -> dict:
    """Resolve o domínio e mostra os IPs associados."""
    try:
        ips = socket.gethostbyname_ex(hostname)
        return {"hostname": ips[0], "ips": ips[2]}
    except socket.gaierror as e:
        return {"erro": str(e)}


def check_robots(url: str) -> dict:
    """Busca o robots.txt do site."""
    robots_url = url.rstrip("/") + "/robots.txt"
    try:
        with urlopen(robots_url, timeout=10) as resp:
            content = resp.read().decode(errors="ignore")
            return {"encontrado": True, "conteudo": content[:2000]}
    except (URLError, HTTPError):
        return {"encontrado": False}


def check_open_ports(hostname: str, ports=(21, 22, 25, 80, 443, 3306, 8080)) -> dict:
    """Checa rapidamente portas comuns no seu próprio host (timeout curto)."""
    abertas = []
    for port in ports:
        try:
            with socket.create_connection((hostname, port), timeout=2):
                abertas.append(port)
        except (socket.timeout, ConnectionRefusedError, OSError):
            continue
    return {"portas_abertas": abertas, "portas_testadas": list(ports)}


def run_full_scan(url: str) -> dict:
    """Roda todos os testes e devolve um relatório único."""
    hostname = url.replace("https://", "").replace("http://", "").split("/")[0]

    report = {
        "alvo": url,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "headers": check_headers(url),
        "tls": check_tls(hostname),
        "dns": check_dns(hostname),
        "robots_txt": check_robots(url),
        "portas": check_open_ports(hostname),
    }
    return report


if __name__ == "__main__":
    import sys

    alvo = sys.argv[1] if len(sys.argv) > 1 else "https://byb.dev.br"
    print(json.dumps(run_full_scan(alvo), indent=2, ensure_ascii=False))
