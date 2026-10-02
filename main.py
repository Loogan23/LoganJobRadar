import sys
import os
import argparse
import webbrowser
import yaml

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.engine import JobRadarEngine

def show_profile(config_path: str = "config/profile_config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cand = cfg.get("candidate", {})
    loc = cfg.get("location_preferences", {})
    tracks = cfg.get("tracks", {})

    print("\n" + "="*60)
    print("👤 PERFIL CONFIGURADO NO JOBRADAR")
    print("="*60)
    print(f"Nome: {cand.get('name')}")
    print(f"Formação: {cand.get('academic', {}).get('course')} - {cand.get('academic', {}).get('institution')}")
    print(f"Previsão de Conclusão: {cand.get('academic', {}).get('expected_graduation')}")
    print(f"E-mail: {cand.get('email')} | Tel: {cand.get('phone')}")
    print(f"LinkedIn: {cand.get('linkedin')}")
    print("-" * 60)
    print("📍 PREFERÊNCIAS DE LOCALIZAÇÃO & MODALIDADE:")
    print(f"Base: {loc.get('home_city')} - {loc.get('home_state')}")
    print(f"Aceita 100% Remoto: {'Sim' if loc.get('accept_remote') else 'Não'}")
    print(f"Aceita Fortaleza & Região Metropolitana: Sim")
    print(f"Eliminar vagas presenciais em outras cidades: {'Sim' if loc.get('reject_onsite_other_cities') else 'Não'}")
    print("-" * 60)
    sen = cfg.get("seniority", {})
    if sen.get("exclusive_internship"):
        print("🎓 NÍVEL DE SENIORIDADE: Exclusivamente VAGAS DE ESTÁGIO (100% UFC)")
    else:
        print("🎓 NÍVEL DE SENIORIDADE: Estágio e Júnior")
    print("-" * 60)
    print("🎯 TRILHAS PRIORITÁRIAS SELECIONADAS:")
    for key, data in tracks.items():
        print(f" • [{data.get('priority')}] {data.get('name')}")
    print("="*60 + "\n")

def run_daemon(interval_minutes: int = 120, config_path: str = "config/profile_config.yaml"):
    import time
    from datetime import datetime, timedelta

    print("\n" + "="*60)
    print("🔄 MODO AUTOMÁTICO JOBRADAR ATIVO")
    print(f"Intervalo entre buscas: {interval_minutes} minutos")
    print("Os alertas de novas vagas serão enviados diretamente no seu Telegram.")
    print("Pressione Ctrl + C para pausar ou encerrar a qualquer momento.")
    print("="*60 + "\n")
    
    engine = JobRadarEngine(config_path)
    cycle = 1
    while True:
        try:
            now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            print(f"[{now_str}] 🚀 Executando ciclo #{cycle} de varredura...")
            engine.run(verbose=True)
            cycle += 1
            next_time = (datetime.now() + timedelta(minutes=interval_minutes)).strftime("%H:%M:%S")
            print(f"\n😴 Próxima varredura em {interval_minutes} minutos (às {next_time})...")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n🛑 Modo automático finalizado pelo usuário.")
            break
        except Exception as e:
            print(f"\n⚠️ Erro no ciclo #{cycle}: {e}. Aguardando 5 minutos antes de retentar...")
            time.sleep(300)

def main():
    parser = argparse.ArgumentParser(description="JobRadar - Robô de Busca e Filtragem Inteligente de Vagas")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "profile", "report", "test", "telegram-test", "daemon"],
                        help="Comando a executar (padrão: run)")
    parser.add_argument("--config", default="config/profile_config.yaml", help="Caminho do arquivo de configuração")
    parser.add_argument("--interval", type=int, default=120, help="Intervalo em minutos para o modo daemon (padrão: 120)")
    args = parser.parse_args()

    if args.command == "daemon":
        run_daemon(interval_minutes=args.interval, config_path=args.config)
        return

    if args.command == "profile":
        show_profile(args.config)
        return

    if args.command == "telegram-test":
        from notifiers.telegram_notifier import TelegramNotifier
        notifier = TelegramNotifier()
        if not notifier.is_configured():
            print("\n❌ Telegram não está configurado.")
            print("Para configurar, crie o arquivo .env a partir de .env.example com:")
            print("TELEGRAM_BOT_TOKEN=seu_token_aqui")
            print("TELEGRAM_CHAT_ID=seu_chat_id_aqui\n")
        else:
            print("\n📡 Enviando mensagem de teste para o seu Telegram...")
            if notifier.send_test_message():
                print("✅ Mensagem de teste enviada com sucesso! Verifique seu Telegram.\n")
            else:
                print("❌ Falha ao enviar mensagem. Verifique seu token e chat_id.\n")
        return

    if args.command == "report":
        report_file = os.path.abspath("output/relatorio_vagas.html")
        if os.path.exists(report_file):
            print(f"Abrindo relatório no navegador: {report_file}")
            webbrowser.open(f"file://{report_file}")
        else:
            print("Relatório ainda não foi gerado. Execute 'python main.py run' primeiro.")
        return

    # Executar o motor
    engine = JobRadarEngine(args.config)
    results = engine.run(verbose=True)

    print("\n" + "="*60)
    print(f"🎉 TOP VAGAS MAIS COMPATÍVEIS ({len(results)} encontradas)")
    print("="*60)
    for idx, job in enumerate(results[:8], 1):
        remote_tag = "🌐 Remoto" if job.is_remote else f"📍 {job.location}"
        print(f"{idx}. [{job.match_score:.0f}% Match] {job.title} | {job.company}")
        print(f"   Trilha: {job.track_matched} | {remote_tag} | Fonte: {job.source}")
        print(f"   Link: {job.url}")
        if job.score_reasons:
            print(f"   Destaques: {' • '.join(job.score_reasons[:2])}")
        print()

    print("="*60)
    print("💡 DICA: Para abrir o Dashboard interativo no navegador, execute:")
    print("   python main.py report")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
