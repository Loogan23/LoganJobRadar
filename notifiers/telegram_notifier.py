import os
import json
import html
import requests
from typing import List, Set
from dotenv import load_dotenv
from core.models import Job

load_dotenv()

class TelegramNotifier:
    def __init__(self, token: str = None, chat_id: str = None, history_file: str = "output/notified_jobs.json"):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.history_file = history_file
        self.notified_ids: Set[str] = self._load_history()

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def _load_history(self) -> Set[str]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def _save_history(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(list(self.notified_ids), f, ensure_ascii=False, indent=2)

    def send_message(self, text: str) -> bool:
        if not self.is_configured():
            print("⚠️ Telegram não configurado. Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no arquivo .env.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return True
            else:
                print(f"❌ Erro ao enviar mensagem Telegram: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"❌ Falha de conexão com o Telegram: {e}")
            return False

    def notify_top_jobs(self, jobs: List[Job], min_score: float = 75.0, max_notifications: int = 5) -> int:
        if not self.is_configured():
            return 0

        # Filtrar vagas acima da nota de corte e ainda não notificadas
        candidates = [
            j for j in jobs 
            if j.match_score >= min_score and j.id not in self.notified_ids
        ]

        if not candidates:
            return 0

        sent_count = 0
        for job in candidates[:max_notifications]:
            remote_tag = "🌐 <b>100% Remoto</b>" if job.is_remote else f"📍 <b>{html.escape(job.location)}</b>"
            reasons_text = ""
            if job.score_reasons:
                reasons_text = f"\n💡 <i>{' • '.join(html.escape(r) for r in job.score_reasons[:2])}</i>"

            msg = (
                f"🚨 <b>NOVA VAGA COMPATÍVEL ({job.match_score:.0f}% Match)</b>\n\n"
                f"💼 <b>Cargo:</b> {html.escape(job.title)}\n"
                f"🏢 <b>Empresa:</b> {html.escape(job.company)}\n"
                f"{remote_tag}\n"
                f"🎯 <b>Trilha:</b> {html.escape(job.track_matched or 'Geral')}\n"
                f"📌 <b>Fonte:</b> {html.escape(job.source)}{reasons_text}\n\n"
                f"👉 <a href='{job.url}'><b>Clique aqui para se candidatar</b></a>"
            )

            if self.send_message(msg):
                self.notified_ids.add(job.id)
                sent_count += 1

        self._save_history()
        return sent_count

    def send_test_message(self) -> bool:
        if not self.is_configured():
            print("⚠️ Credenciais ausentes. Crie o arquivo .env com TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID.")
            return False

        msg = (
            "🤖 <b>JobRadar conectado com sucesso!</b>\n\n"
            "Seu robô de busca de vagas está ativo e configurado para o perfil de <b>Logan Oliveira</b>.\n"
            "Você receberá alertas automáticos aqui sempre que novas vagas compatíveis (≥ 75%) forem encontradas."
        )
        return self.send_message(msg)
