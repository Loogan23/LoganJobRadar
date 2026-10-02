import os
import sys
import time
import requests
from dotenv import load_dotenv, set_key

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def auto_detect_chat_id():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN não encontrado no .env")
        return None

    print("📡 Conectando à API do Telegram...")
    resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
    data = resp.json()

    if not data.get("ok"):
        print(f"❌ Erro na API do Telegram: {data}")
        return None

    results = data.get("result", [])
    if not results:
        print("⏳ Nenhuma mensagem recente encontrada.")
        print("👉 Por favor, abra o Telegram, procure por @LoganJobRadarBot e clique em 'COMEÇAR' / 'INICIAR' (ou envie /start).")
        return None

    # Pegar o chat_id da última mensagem
    last_update = results[-1]
    chat = last_update.get("message", {}).get("chat", {})
    chat_id = str(chat.get("id", ""))
    first_name = chat.get("first_name", "")
    username = chat.get("username", "")

    if chat_id:
        print(f"🎉 Chat ID identificado: {chat_id} (Usuário: {first_name} @{username})")
        # Salvar no .env
        env_path = os.path.abspath(".env")
        set_key(env_path, "TELEGRAM_CHAT_ID", chat_id)
        print("💾 CHAT_ID salvo com sucesso no arquivo .env!")
        return chat_id
    else:
        print("❌ Não foi possível extrair o Chat ID da mensagem.")
        return None

if __name__ == "__main__":
    auto_detect_chat_id()
