import json
from typing import List
from core.models import Job, ScrapingSummary

def generate_html_report(jobs: List[Job], summary: ScrapingSummary, output_path: str = "output/relatorio_vagas.html"):
    jobs_sorted = sorted(jobs, key=lambda x: x.match_score, reverse=True)
    
    total_vagas = len(jobs_sorted)
    vagas_alta = sum(1 for j in jobs_sorted if j.match_score >= 75)
    vagas_remotas = sum(1 for j in jobs_sorted if j.is_remote)
    vagas_fortaleza = sum(1 for j in jobs_sorted if not j.is_remote and "fortaleza" in (j.location or "").lower())
    
    # Gerar JSON dos jobs para busca dinâmica via JS
    jobs_json = []
    for j in jobs_sorted:
        jobs_json.append({
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "modality": j.modality,
            "is_remote": j.is_remote,
            "score": j.match_score,
            "track": j.track_matched,
            "source": j.source,
            "url": j.url,
            "reasons": j.score_reasons,
            "published_at": j.published_at
        })

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JobRadar | Oportunidades Selecionadas - Logan Oliveira</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0b0f19;
            --bg-card: #111827;
            --bg-card-hover: #17223b;
            --border-color: #1f2937;
            --text-primary: #f9fafb;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --accent-green: #10b981;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-orange: #f59e0b;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        body {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2.5rem 1.5rem;
        }}

        .container {{
            max-width: 1240px;
            margin: 0 auto;
        }}

        /* Header */
        header {{
            background: linear-gradient(135deg, rgba(31, 41, 55, 0.7) 0%, rgba(17, 24, 39, 0.9) 100%);
            border: 1px solid var(--border-color);
            border-radius: 1.25rem;
            padding: 2rem 2.5rem;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1.5rem;
            backdrop-filter: blur(10px);
        }}

        .profile-badge {{
            display: inline-block;
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        h1 {{
            font-size: 1.9rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 0.5rem;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 0.95rem;
            line-height: 1.5;
        }}

        /* Stats Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.25rem 1.5rem;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s;
        }}

        .stat-card:hover {{
            transform: translateY(-2px);
        }}

        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 800;
            color: #ffffff;
        }}

        .stat-card.green .stat-value {{ color: var(--accent-green); }}
        .stat-card.blue .stat-value {{ color: var(--accent-blue); }}
        .stat-card.purple .stat-value {{ color: var(--accent-purple); }}

        /* Filter Controls */
        .controls-bar {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.25rem;
            margin-bottom: 2rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
        }}

        .search-box {{
            flex: 1;
            min-width: 260px;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            background: rgba(11, 15, 25, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 0.75rem 1rem;
            color: #fff;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }}

        .search-box input:focus {{
            border-color: var(--accent-blue);
        }}

        .filter-select {{
            background: rgba(11, 15, 25, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 0.75rem 1rem;
            color: #fff;
            font-size: 0.9rem;
            outline: none;
            cursor: pointer;
        }}

        /* Job Cards */
        .jobs-list {{
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}

        .job-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.75rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            transition: all 0.2s ease;
        }}

        .job-card:hover {{
            background-color: var(--bg-card-hover);
            border-color: rgba(59, 130, 246, 0.4);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }}

        .job-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .job-title-group {{
            flex: 1;
        }}

        .job-title {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.35rem;
        }}

        .job-company {{
            color: #60a5fa;
            font-weight: 600;
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
        }}

        .badge-source {{
            font-size: 0.75rem;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-secondary);
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-weight: 500;
        }}

        .score-pill {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            padding: 0.5rem 1rem;
            border-radius: 0.75rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .score-number {{
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--accent-green);
        }}

        .score-label {{
            font-size: 0.7rem;
            text-transform: uppercase;
            font-weight: 600;
            color: var(--text-secondary);
            letter-spacing: 0.05em;
        }}

        .job-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
        }}

        .meta-tag {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 0.35rem 0.75rem;
            border-radius: 0.5rem;
        }}

        .meta-tag.remote {{
            background: rgba(16, 185, 129, 0.1);
            color: #34d399;
            border-color: rgba(16, 185, 129, 0.2);
            font-weight: 600;
        }}

        .meta-tag.track {{
            background: rgba(139, 92, 246, 0.1);
            color: #c084fc;
            border-color: rgba(139, 92, 246, 0.2);
            font-weight: 600;
        }}

        .match-reasons {{
            background: rgba(0, 0, 0, 0.25);
            border-left: 3px solid var(--accent-blue);
            padding: 0.75rem 1rem;
            border-radius: 0 0.5rem 0.5rem 0;
            font-size: 0.85rem;
            color: #d1d5db;
        }}

        .job-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 0.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .apply-btn {{
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #fff;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            padding: 0.65rem 1.25rem;
            border-radius: 0.5rem;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .apply-btn:hover {{
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
            transform: translateY(-1px);
        }}

        .no-results {{
            text-align: center;
            padding: 4rem 1rem;
            color: var(--text-muted);
            font-size: 1.1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div>
                <span class="profile-badge">Target Perfil Ativo</span>
                <h1>JobRadar | Radar de Oportunidades</h1>
                <p class="subtitle">
                    Filtro Personalizado para <strong>Logan Oliveira de Andrade</strong> (UFC - Eng. Telecom)<br>
                    Trilhas: <strong>Gestão de TI & Redes</strong> | <strong>Gestão de Projetos & Scrum</strong> | <strong>Gente & Gestão / RH</strong>
                </p>
            </div>
            <div style="text-align: right;">
                <p style="font-size: 0.8rem; color: var(--text-muted);">Última varredura</p>
                <p style="font-size: 0.95rem; font-weight: 600; color: var(--text-secondary);">{summary.timestamp}</p>
            </div>
        </header>

        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card blue">
                <div class="stat-label">Vagas Compatíveis</div>
                <div class="stat-value" id="stat-total">{total_vagas}</div>
            </div>
            <div class="stat-card green">
                <div class="stat-label">Alta Compatibilidade (Match ≥ 75%)</div>
                <div class="stat-value">{vagas_alta}</div>
            </div>
            <div class="stat-card purple">
                <div class="stat-label">Vagas 100% Remotas</div>
                <div class="stat-value">{vagas_remotas}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Locais (Fortaleza & Região)</div>
                <div class="stat-value">{vagas_fortaleza}</div>
            </div>
        </div>

        <!-- Controls -->
        <div class="controls-bar">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Pesquisar por cargo, empresa, tecnologia..." onkeyup="filterJobs()">
            </div>
            <select class="filter-select" id="modalityFilter" onchange="filterJobs()">
                <option value="all">Todas as Modalidades</option>
                <option value="remote">Apenas 100% Remoto</option>
                <option value="local">Fortaleza e Região</option>
            </select>
            <select class="filter-select" id="trackFilter" onchange="filterJobs()">
                <option value="all">Todas as Trilhas</option>
                <option value="ti">Gestão de TI & Redes</option>
                <option value="projetos">Gestão de Projetos & Agilidade</option>
                <option value="rh">Gente & Gestão / RH</option>
            </select>
        </div>

        <!-- Jobs List -->
        <div class="jobs-list" id="jobsContainer">
            <!-- Gerado via Javascript dinâmico -->
        </div>
    </div>

    <script>
        const jobsData = {json.dumps(jobs_json, ensure_ascii=False)};

        function renderJobs(jobs) {{
            const container = document.getElementById("jobsContainer");
            if (jobs.length === 0) {{
                container.innerHTML = '<div class="no-results">Nenhuma vaga encontrada para os filtros selecionados.</div>';
                return;
            }}

            container.innerHTML = jobs.map(job => {{
                const reasonsList = job.reasons.length > 0 
                    ? `<div class="match-reasons"><strong>Motivos do Match:</strong> ${{job.reasons.join(' • ')}}</div>` 
                    : '';

                const remoteBadge = job.is_remote 
                    ? '<span class="meta-tag remote">🌐 100% Remoto</span>' 
                    : `<span class="meta-tag">📍 ${{job.location}}</span>`;

                const trackBadge = job.track 
                    ? `<span class="meta-tag track">🎯 ${{job.track}}</span>` 
                    : '';

                return `
                    <div class="job-card">
                        <div class="job-card-header">
                            <div class="job-title-group">
                                <h2 class="job-title">${{job.title}}</h2>
                                <div class="job-company">
                                    ${{job.company}}
                                    <span class="badge-source">${{job.source}}</span>
                                </div>
                            </div>
                            <div class="score-pill">
                                <span class="score-number">${{job.score.toFixed(0)}}%</span>
                                <span class="score-label">Match Score</span>
                            </div>
                        </div>

                        <div class="job-meta">
                            ${{remoteBadge}}
                            <span class="meta-tag">💼 ${{job.modality}}</span>
                            ${{trackBadge}}
                        </div>

                        ${{reasonsList}}

                        <div class="job-footer">
                            <span style="font-size: 0.8rem; color: var(--text-muted);">${{job.published_at ? 'Publicado: ' + job.published_at : 'Coletado via Radar'}}</span>
                            <a href="${{job.url}}" target="_blank" rel="noopener noreferrer" class="apply-btn">
                                Acessar Vaga Oficial ↗
                            </a>
                        </div>
                    </div>
                `;
            }}).join('');
        }}

        function filterJobs() {{
            const search = document.getElementById("searchInput").value.toLowerCase();
            const modality = document.getElementById("modalityFilter").value;
            const track = document.getElementById("trackFilter").value;

            const filtered = jobsData.filter(job => {{
                const matchesSearch = (job.title + " " + job.company + " " + job.location + " " + job.track).toLowerCase().includes(search);
                
                let matchesModality = true;
                if (modality === "remote") matchesModality = job.is_remote;
                if (modality === "local") matchesModality = !job.is_remote && job.location.toLowerCase().includes("fortaleza");

                let matchesTrack = true;
                if (track === "ti") matchesTrack = (job.track || "").toLowerCase().includes("ti") || (job.track || "").toLowerCase().includes("rede");
                if (track === "projetos") matchesTrack = (job.track || "").toLowerCase().includes("projeto") || (job.track || "").toLowerCase().includes("agil");
                if (track === "rh") matchesTrack = (job.track || "").toLowerCase().includes("gente") || (job.track || "").toLowerCase().includes("rh");

                return matchesSearch && matchesModality && matchesTrack;
            }});

            renderJobs(filtered);
        }}

        // Inicializar renderização
        renderJobs(jobsData);
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
