import os
import sys
import csv
import json
import yaml

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from typing import List, Dict, Set
from core.models import Job, ScrapingSummary
from core.scorer import JobFilterAndScorer
from scrapers.gupy_scraper import GupyScraper
from scrapers.linkedin_scraper import LinkedInScraper
from reports.html_generator import generate_html_report
from notifiers.telegram_notifier import TelegramNotifier

class JobRadarEngine:
    def __init__(self, config_path: str = "config/profile_config.yaml"):
        self.config_path = config_path
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        self.scorer = JobFilterAndScorer(config_path)
        self.scrapers = []
        
        platforms = self.config.get("platforms", {})
        if platforms.get("gupy", {}).get("enabled", True):
            self.scrapers.append(GupyScraper())
        if platforms.get("linkedin", {}).get("enabled", True):
            self.scrapers.append(LinkedInScraper())

        os.makedirs("output", exist_ok=True)

    def run(self, verbose: bool = True) -> List[Job]:
        all_raw_jobs: List[Job] = []
        seen_keys: Set[str] = set()

        if verbose:
            print("🚀 Iniciando varredura do JobRadar adaptada ao perfil de Logan Oliveira...")
            print("📍 Localização alvo: Fortaleza, CE (Presencial/Híbrido) e 100% Remoto (Brasil)")
            print("🎯 Trilhas ativas: Gestão de TI/Redes, Gestão de Projetos/Scrum, Gente & Gestão/RH Tech")

        tracks = self.config.get("tracks", {})
        
        # Coletar buscas prioritárias - EXCLUSIVAS DE ESTÁGIO
        # 1. Buscas focadas em Fortaleza (Estágio Presencial / Híbrido)
        local_queries = [
            "estagio ti",
            "estagio tecnologia",
            "estagio suporte",
            "estagio redes",
            "estagio projetos",
            "estagio pmo",
            "estagio rh",
            "estagio gente e gestao",
            "estagio desenvolvimento",
            "estagio software",
            "estagio telecomunicacoes",
            "estagio engenharia"
        ]
        
        # 2. Buscas focadas em 100% Remoto (Estágio Brasil)
        remote_queries = [
            "estagio ti",
            "estagio tecnologia",
            "estagio suporte",
            "estagio projetos",
            "estagio scrum",
            "estagio rh",
            "estagio gente e gestao",
            "estagio desenvolvimento",
            "estagio software",
            "estagio python",
            "estagio telecom"
        ]

        # Executar scrapers
        for scraper in self.scrapers:
            if verbose:
                print(f"\n🔍 Consultando fonte: {scraper.name}...")
                
            # Executar buscas locais
            for q in local_queries:
                if verbose:
                    print(f"   [Fortaleza/Local] Buscando: '{q}'...")
                jobs = scraper.search(query=q, location="Fortaleza, Ceará, Brasil", is_remote=False, limit=10)
                for j in jobs:
                    key = f"{j.title.strip().lower()}_{j.company.strip().lower()}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_raw_jobs.append(j)

            # Executar buscas remotas
            for q in remote_queries:
                if verbose:
                    print(f"   [100% Remoto] Buscando: '{q}'...")
                jobs = scraper.search(query=q, location="Brasil", is_remote=True, limit=10)
                for j in jobs:
                    key = f"{j.title.strip().lower()}_{j.company.strip().lower()}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_raw_jobs.append(j)

        if verbose:
            print(f"\n📦 Total de vagas brutas coletadas: {len(all_raw_jobs)}")
            print("⚙️  Processando filtros rígidos e calculando Match Score...")

        eligible_jobs: List[Job] = []
        disqualified_count = 0

        for job in all_raw_jobs:
            score_res = self.scorer.evaluate_job(job)
            if score_res.is_eligible:
                job.match_score = score_res.total_score
                job.score_reasons = score_res.reasons
                job.track_matched = score_res.matched_track
                eligible_jobs.append(job)
            else:
                disqualified_count += 1

        # Ordenar por maior Match Score
        eligible_jobs.sort(key=lambda x: x.match_score, reverse=True)

        # Salvar saídas
        summary = ScrapingSummary(
            total_found=len(all_raw_jobs),
            total_eligible=len(eligible_jobs),
            total_high_match=sum(1 for j in eligible_jobs if j.match_score >= 75.0),
            sources_scraped=[s.name for s in self.scrapers]
        )

        self._export_json(eligible_jobs, "output/vagas_compativeis.json")
        self._export_csv(eligible_jobs, "output/vagas_compativeis.csv")
        generate_html_report(eligible_jobs, summary, "output/relatorio_vagas.html")

        # Disparo de notificações via Telegram se configurado
        tg_cfg = self.config.get("telegram", {})
        if tg_cfg.get("enabled", True):
            notifier = TelegramNotifier()
            if notifier.is_configured():
                min_score = tg_cfg.get("min_score_to_notify", 75.0)
                max_alerts = tg_cfg.get("max_alerts_per_run", 5)
                sent = notifier.notify_top_jobs(eligible_jobs, min_score=min_score, max_notifications=max_alerts)
                if sent > 0 and verbose:
                    print(f"\n📲 {sent} vaga(s) de alta compatibilidade enviada(s) para seu Telegram!")
            elif verbose:
                print("\nℹ️  Telegram não ativado: adicione seu token e chat_id no arquivo .env para receber alertas no celular.")

        if verbose:
            print(f"\n✅ Concluído com sucesso!")
            print(f"   - Vagas Elegíveis: {len(eligible_jobs)} (Descartadas: {disqualified_count})")
            print(f"   - Alta Compatibilidade (≥75%): {summary.total_high_match}")
            print(f"   - Relatório HTML gerado em: output/relatorio_vagas.html")
            print(f"   - Dados JSON salvos em: output/vagas_compativeis.json")

        return eligible_jobs

    def _export_json(self, jobs: List[Job], path: str):
        data = [j.model_dump() for j in jobs]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _export_csv(self, jobs: List[Job], path: str):
        if not jobs:
            return
        fieldnames = ["match_score", "title", "company", "modality", "location", "track_matched", "source", "url", "score_reasons"]
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for j in jobs:
                writer.writerow({
                    "match_score": f"{j.match_score:.1f}%",
                    "title": j.title,
                    "company": j.company,
                    "modality": j.modality,
                    "location": j.location,
                    "track_matched": j.track_matched,
                    "source": j.source,
                    "url": j.url,
                    "score_reasons": " | ".join(j.score_reasons)
                })
