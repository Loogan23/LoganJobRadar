# 📡 JobRadar - Radar Inteligente de Vagas

Sistema automatizado de busca, filtragem e classificação de vagas de emprego e estágio, configurado especificamente para o perfil de **Logan Oliveira de Andrade** (Graduando em Engenharia de Telecomunicações pela UFC).

---

## 🎯 Configuração do Perfil & Filtragem

O robô foi calibrado sob medida para o seu momento de carreira:
1. **Nível de Senioridade:** Foco em **Estágio** e posições de **Júnior / Assistente / Trainee** (perfeito para conciliação com a UFC até 2028). Posições Pleno, Sênior, Especialistas e Diretorias são descartadas automaticamente.
2. **Localização & Modalidades:**
   - **100% Remoto:** Varredura em todo o território nacional.
   - **Híbrido / Presencial:** Apenas em **Fortaleza - CE** e Região Metropolitana. Vagas presenciais em outros estados (SP, RJ, MG, etc.) são eliminadas de imediato.
3. **Trilhas Prioritárias Configuradas:**
   - **Gestão de TI, Suporte Técnico & Redes:** TI Corporativa, Help Desk N2/N3, Infraestrutura e Telecomunicações.
   - **Gestão de Projetos, Agilidade & Produto:** Scrum Master Jr, Assistente de Projetos, PMO Jr, Agile Coach Trainee.
   - **Gente & Gestão & Tech Recruitment:** RH Corporativo, R&S de TI, Atração de Talentos e Gestão de Pessoas.
   - **Diferencial Técnico:** Desenvolvimento Python / TypeScript / Web e Automação de Processos.
4. **Fontes Integradas:**
   - **LinkedIn Jobs** (via Guest Search API em tempo real)
   - **Gupy** (via Next.js SSR Portal API)

---

## 🚀 Como Executar

### 1. Executar Varredura e Filtragem de Vagas
Executa a busca em todos os portais e calcula o Match Score (0 a 100%):
```bash
python main.py run
```

### 2. Abrir o Dashboard Visual Interativo
Abre o relatório visual moderno em HTML no seu navegador com busca dinâmica, badges de score e link direto para candidatura:
```bash
python main.py report
```
Ou abra manualmente com duplo clique no arquivo: `output/relatorio_vagas.html`.

### 3. Testar a Conexão com o Telegram
Envia uma mensagem de teste para o seu Telegram para validar o bot:
```bash
python main.py telegram-test
```

### 4. Execução Automática Contínua (Daemon)
Executa o robô continuamente em segundo plano, repetindo a busca a cada X minutos (ex: a cada 2 horas):
```bash
python main.py daemon --interval 120
```

### 5. Exibir o Perfil e Parâmetros Ativos
```bash
python main.py profile
```

---

## ⏰ Como Rodar Automaticamente sem Precisar Abrir o Terminal

Você tem **3 opções simples** para deixar o JobRadar trabalhando 100% sozinho:

### Opção 1: Agendador de Tarefas do Windows (Recomendada para o PC)
Roda de forma invisível em segundo plano no Windows a cada 3 horas, sem abrir nenhuma janela:
1. Abra o PowerShell e execute:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\agendar_windows.ps1
   ```
2. Pronto! O Windows executará o robô periodicamente e novas vagas chegarão no seu Telegram.
3. Para desativar no futuro:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\remover_agendamento.ps1
   ```

### Opção 2: Modo Daemon no Terminal
Deixe o comando rodando em uma aba minimizada do terminal:
```bash
python main.py daemon --interval 180
```

### Opção 3: 100% na Nuvem via GitHub Actions (Funciona mesmo com o PC desligado)
O projeto já conta com o arquivo `.github/workflows/jobradar_cron.yml`:
1. Suba o projeto para o seu GitHub em um repositório privado.
2. Nas configurações do repositório (*Settings > Secrets and variables > Actions*), adicione os dois secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Os servidores do GitHub rodarão a busca automaticamente 3 vezes ao dia (09:00, 15:00 e 19:00) gratuitamente!

---

## 📲 Configuração do Bot do Telegram

O robô envia automaticamente alertas com links diretos para o seu Telegram sempre que novas vagas compatíveis (≥ 75%) forem encontradas.

### Como configurar em 2 minutos:
1. Abra o Telegram e pesquise por **`@BotFather`**.
2. Envie o comando `/newbot`, escolha um nome e um nome de usuário (ex: `MeuJobRadarBot`).
3. O BotFather fornecerá o seu **`TELEGRAM_BOT_TOKEN`**.
4. Inicie uma conversa com seu novo bot e clique em **Iniciar / Start**.
5. Para descobrir o seu ID de usuário (`TELEGRAM_CHAT_ID`), envie qualquer mensagem para o bot **`@userinfobot`** no Telegram.
6. Copie o arquivo `.env.example` para `.env` e preencha suas chaves:
   ```ini
   TELEGRAM_BOT_TOKEN=123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ
   TELEGRAM_CHAT_ID=123456789
   ```
7. Valide a conexão executando:
   ```bash
   python main.py telegram-test
   ```
8. Ao rodar `python main.py run`, as novas vagas qualificadas serão enviadas diretamente no seu Telegram com botão de candidatura!

---

## 📂 Estrutura do Projeto

```text
JobRadar/
├── config/
│   └── profile_config.yaml       # Configuração editável de critérios, pesos, palavras-chave e exclusões
├── core/
│   ├── models.py                 # Estruturas de dados Pydantic
│   ├── scorer.py                 # Algoritmo de Match Score e filtros eliminatórios
│   └── engine.py                 # Orquestrador da busca, unificação e exportação
├── scrapers/
│   ├── base.py                   # Classe abstrata BaseScraper
│   ├── gupy_scraper.py           # Conector do portal Gupy
│   └── linkedin_scraper.py       # Conector do LinkedIn Jobs (Brasil Remoto & Fortaleza)
├── reports/
│   └── html_generator.py         # Gerador do Dashboard HTML moderno
├── output/
│   ├── relatorio_vagas.html      # Dashboard interativo com filtros dinâmicos
│   ├── vagas_compativeis.json    # Dados brutos estruturados
│   └── vagas_compativeis.csv     # Planilha CSV compatível com Excel
├── main.py                       # CLI principal
├── PERFIL_CANDIDATO.md           # Resumo do perfil profissional
└── curriculo_logan_oliveira.tex  # Currículo original em LaTeX
```

---

## 🛠️ Personalização Rápida

Se quiser alterar termos de pesquisa, incluir novas cidades ou ajustar notas mínimas de corte, basta editar o arquivo:
`config/profile_config.yaml`
As alterações têm efeito imediato na próxima execução de `python main.py run`.
