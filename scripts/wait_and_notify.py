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

from core.engine import JobRadarEngine
from notifiers.telegram_notifier import TelegramNotifier

def main():
    load_dotenv(override=True)
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("❌ Token não encontrado no .env")
        return

    print("📡 Aguardando você clicar em 'COMEÇAR' / 'INICIAR' no @LoganJobRadarBot...")
    
    chat_id = None
    for attempt in range(20):
        try:
            resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=5)
            data = resp.json()
            results = data.get("result", [])
            if results:
                last_msg = results[-1]
                chat = last_msg.get("message", {}).get("chat", {})
                chat_id = str(chat.get("id", ""))
                first_name = chat.get("first_name", "")
                if chat_id:
                    print(f"🎉 Detectado! Usuário: {first_name} | Chat ID: {chat_id}")
                    env_path = os.path.abspath(".env")
                    set_key(env_path, "TELEGRAM_CHAT_ID", chat_id)
                    os.environ["TELEGRAM_CHAT_ID"] = chat_id
                    break
        except Exception as e:
            pass
        time.sleep(2)

    if not chat_id:
        print("⏳ Nenhuma mensagem recebida ainda.")
        return

    # Enviar mensagem de boas-vindas
    notifier = TelegramNotifier(token=token, chat_id=chat_id)
    print("📲 Enviando confirmação de boas-vindas...")
    notifier.send_test_message()

    # Enviar as melhores vagas encontradas
    print("🚀 Disparando as principais vagas compatíveis...")
    engine = JobRadarEngine()
    results = engine.run(verbose=False)
    sent = notifier.notify_top_jobs(results, min_score=75.0, max_notifications=5)
    print(f"✅ Sucesso! {sent} vagas enviadas diretamente para o seu Telegram.")

if __name__ == "__main__":
    main()
