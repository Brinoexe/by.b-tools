"""
by.b :: deadman
Dead Man's Switch: se você não fizer "check-in" dentro do prazo definido,
uma mensagem é enviada automaticamente pro WhatsApp de um contato de
confiança, via CallMeBot (https://www.callmebot.com/blog/free-api-whatsapp-messages/).

Componentes:
- state.json         -> guarda o último check-in e se já disparou
- watchdog_loop()     -> roda em segundo plano checando o prazo
- Flask app           -> expõe /status e /checkin pro botão do HTML
"""

import json
import os
import time
import threading
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import urlopen

from flask import Flask, jsonify, request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH = os.path.join(BASE_DIR, "state.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        state = {
            "ultimo_checkin": datetime.now(timezone.utc).isoformat(),
            "disparado": False,
        }
        save_state(state)
        return state
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def horas_desde_checkin(state: dict) -> float:
    ultimo = datetime.fromisoformat(state["ultimo_checkin"])
    agora = datetime.now(timezone.utc)
    return (agora - ultimo).total_seconds() / 3600


def enviar_whatsapp(mensagem: str, config: dict):
    """Envia mensagem via CallMeBot. Requer telefone + apikey já
    autorizados previamente (ver README para o passo de ativação)."""
    telefone = config["whatsapp"]["telefone"]
    apikey = config["whatsapp"]["apikey"]
    texto = quote(mensagem)
    url = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={telefone}&text={texto}&apikey={apikey}"
    )
    try:
        with urlopen(url, timeout=15) as resp:
            return resp.read().decode(errors="ignore")
    except Exception as e:
        return f"erro ao enviar: {e}"


def checkin():
    """Reseta o cronômetro do switch."""
    state = load_state()
    state["ultimo_checkin"] = datetime.now(timezone.utc).isoformat()
    state["disparado"] = False
    save_state(state)
    return state


def watchdog_loop(intervalo_checagem_segundos: int = 60):
    """Roda pra sempre, verificando se o prazo estourou."""
    while True:
        config = load_config()
        state = load_state()
        prazo_horas = config["deadman"]["prazo_horas"]

        if not state["disparado"] and horas_desde_checkin(state) >= prazo_horas:
            resultado = enviar_whatsapp(config["deadman"]["mensagem"], config)
            state["disparado"] = True
            state["disparado_em"] = datetime.now(timezone.utc).isoformat()
            state["resultado_envio"] = resultado
            save_state(state)
            print(f"[by.b] Switch disparado. Resultado: {resultado}")

        time.sleep(intervalo_checagem_segundos)


# ---------------------------------------------------------------------------
# API pro botão de check-in na página HTML
# ---------------------------------------------------------------------------

app = Flask(__name__)


def _autenticado(req) -> bool:
    config = load_config()
    token_esperado = config["deadman"]["api_token"]
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {token_esperado}"


@app.route("/status", methods=["GET"])
def status():
    state = load_state()
    config = load_config()
    horas_passadas = horas_desde_checkin(state)
    prazo = config["deadman"]["prazo_horas"]
    return jsonify({
        "ultimo_checkin": state["ultimo_checkin"],
        "horas_desde_checkin": round(horas_passadas, 2),
        "prazo_horas": prazo,
        "horas_restantes": round(prazo - horas_passadas, 2),
        "disparado": state["disparado"],
    })


@app.route("/checkin", methods=["POST"])
def api_checkin():
    if not _autenticado(request):
        return jsonify({"erro": "não autorizado"}), 401
    state = checkin()
    return jsonify({"ok": True, "novo_checkin": state["ultimo_checkin"]})


def iniciar_servidor(porta: int = 5005):
    threading.Thread(target=watchdog_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=porta)


if __name__ == "__main__":
    iniciar_servidor()
