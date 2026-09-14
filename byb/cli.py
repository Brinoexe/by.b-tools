#!/usr/bin/env python3
"""
by.b :: CLI
Uso:
  by.b recon [url]              -> roda o scan de segurança (padrão: byb.dev.br)
  by.b deadman serve             -> sobe a API do dead man's switch (porta 5005)
  by.b deadman checkin           -> reseta o cronômetro manualmente pelo terminal
  by.b deadman status            -> mostra quanto tempo falta
"""

import argparse
import json
import sys

from . import recon, deadman


def main():
    parser = argparse.ArgumentParser(prog="by.b")
    sub = parser.add_subparsers(dest="comando")

    p_recon = sub.add_parser("recon", help="testa a segurança de um site seu")
    p_recon.add_argument("url", nargs="?", default="https://byb.dev.br")

    p_deadman = sub.add_parser("deadman", help="dead man's switch")
    p_deadman.add_argument(
        "acao", choices=["serve", "checkin", "status"]
    )

    args = parser.parse_args()

    if args.comando == "recon":
        report = recon.run_full_scan(args.url)
        print(json.dumps(report, indent=2, ensure_ascii=False))

    elif args.comando == "deadman":
        if args.acao == "serve":
            print("[by.b] Subindo API do dead man's switch na porta 5005…")
            deadman.iniciar_servidor()
        elif args.acao == "checkin":
            state = deadman.checkin()
            print(f"[by.b] Check-in feito às {state['ultimo_checkin']}")
        elif args.acao == "status":
            state = deadman.load_state()
            config = deadman.load_config()
            horas = deadman.horas_desde_checkin(state)
            prazo = config["deadman"]["prazo_horas"]
            print(f"Último check-in: {state['ultimo_checkin']}")
            print(f"Horas desde então: {horas:.2f} / prazo: {prazo}h")
            print(f"Disparado: {state['disparado']}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
