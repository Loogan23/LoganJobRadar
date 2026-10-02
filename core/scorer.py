import re
import yaml
from typing import Tuple, Optional
from core.models import Job, ScoreResult

class JobFilterAndScorer:
    def __init__(self, config_path: str = "config/profile_config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        self.loc_cfg = self.config.get("location_preferences", {})
        self.sen_cfg = self.config.get("seniority", {})
        self.tracks = self.config.get("tracks", {})
        self.scoring_cfg = self.config.get("scoring", {})
        self.dealbreakers = [d.lower() for d in self.config.get("dealbreakers", [])]
        
        self.allowed_metro = [c.lower() for c in self.loc_cfg.get("allowed_metro_cities", ["fortaleza", "ce"])]
        self.allowed_levels = [l.lower() for l in self.sen_cfg.get("allowed_levels", [])]
        self.negative_levels = [l.lower() for l in self.sen_cfg.get("strict_negative_levels", [])]

    def _normalize(self, text: str) -> str:
        return (text or "").lower()

    def evaluate_job(self, job: Job) -> ScoreResult:
        result = ScoreResult()
        title_lower = self._normalize(job.title)
        loc_lower = self._normalize(job.location)
        desc_lower = self._normalize(job.description)
        combined_text = f"{title_lower} {loc_lower} {desc_lower}"
        
        # 0. Checagem de Dealbreakers proibidos
        for db in self.dealbreakers:
            if db in combined_text:
                result.is_eligible = False
                result.disqualification_reason = f"Termo proibido/dealbreaker detectado: '{db}'"
                return result
        
        # 1. Checagem de Estágio Exclusivo
        is_internship = (
            any(re.search(rf"\b{re.escape(lvl)}\b", title_lower) for lvl in ["estágio", "estagio", "estagiário", "estagiario", "estagiária", "estagiaria", "intern", "internship"])
            or (job.raw_data and job.raw_data.get("type") == "vacancy_type_internship")
            or "estágio" in desc_lower[:200]
            or "estagio" in desc_lower[:200]
        )

        if self.sen_cfg.get("exclusive_internship", False) and not is_internship:
            result.is_eligible = False
            result.disqualification_reason = "Vaga não é de Estágio (filtro exclusivo de estágio ativo)"
            return result

        # 2. Checagem rígida de Senioridade Negativa
        for neg in self.negative_levels:
            pattern = rf"\b{re.escape(neg)}\b"
            if re.search(pattern, title_lower):
                if not is_internship:
                    result.is_eligible = False
                    result.disqualification_reason = f"Senioridade incompatível detectada no título: '{neg.upper()}'"
                    return result

        # 2. Checagem de Localização & Modalidade
        is_remote = (
            job.is_remote 
            or "remoto" in loc_lower 
            or "home office" in loc_lower 
            or "teletrabalho" in loc_lower 
            or "remoto" in title_lower
            or job.modality.lower() == "remoto"
        )
        
        is_local = any(metro in loc_lower for metro in self.allowed_metro)
        
        if not is_remote and not is_local:
            if self.loc_cfg.get("reject_onsite_other_cities", True):
                result.is_eligible = False
                result.disqualification_reason = f"Vaga presencial/híbrida fora de Fortaleza: '{job.location}'"
                return result

        # --- CÁLCULO DE PONTUAÇÃO (MATCH SCORE) ---
        
        # 3. Pontuação de Senioridade (Até 15 pontos)
        seniority_score = 0.0
        has_positive_sen = any(re.search(rf"\b{re.escape(lvl)}\b", title_lower) for lvl in self.allowed_levels)
        if has_positive_sen:
            seniority_score = 15.0
            result.reasons.append("Nível de senioridade perfeito (Estágio/Júnior/Trainee)")
        elif any(re.search(rf"\b{re.escape(lvl)}\b", desc_lower[:300]) for lvl in self.allowed_levels):
            seniority_score = 10.0
            result.reasons.append("Menção a perfil inicial/estudante na descrição")
        else:
            # Não especificado, mas não eliminado
            seniority_score = 7.0

        # 4. Pontuação de Localização (Até 20 pontos)
        location_score = 0.0
        if is_remote:
            location_score = 20.0
            result.reasons.append("Modalidade 100% Remota (máxima conveniência)")
        elif is_local:
            location_score = 20.0
            result.reasons.append("Localizada na Região Metropolitana de Fortaleza")
        else:
            location_score = 10.0

        # 5. Pontuação por Trilha e Título (Até 35 pontos)
        title_score = 0.0
        best_track_name = ""
        best_track_score = 0.0

        for track_id, track_data in self.tracks.items():
            track_name = track_data.get("name", track_id)
            weight = track_data.get("weight", 1.0)
            
            # Checar queries da trilha no título
            track_title_score = 0.0
            for query in track_data.get("search_queries", []):
                q_words = query.lower().split()
                if all(w in title_lower for w in q_words):
                    track_title_score = max(track_title_score, 35.0 * weight)
                elif any(w in title_lower for w in q_words if len(w) > 3):
                    track_title_score = max(track_title_score, 20.0 * weight)

            if track_title_score > best_track_score:
                best_track_score = track_title_score
                best_track_name = track_name

        title_score = min(best_track_score, 35.0)
        if title_score > 0:
            result.matched_track = best_track_name
            result.reasons.append(f"Título altamente aderente à trilha '{best_track_name}'")
        else:
            result.matched_track = "Geral / Tecnologia"

        # 6. Pontuação por Palavras-Chave de Competências (Até 30 pontos)
        keywords_score = 0.0
        matched_kw = []
        
        # Juntar todas as keywords das trilhas ativas
        all_keywords = []
        for track_id, track_data in self.tracks.items():
            for kw in track_data.get("keywords", []):
                all_keywords.append(kw.lower())

        unique_keywords = list(set(all_keywords))
        for kw in unique_keywords:
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, combined_text):
                matched_kw.append(kw)

        # Cada keyword encontrada adiciona pontos até o limite de 30
        points_per_kw = 5.0
        keywords_score = min(len(matched_kw) * points_per_kw, 30.0)
        
        result.matched_keywords = matched_kw[:8]
        if matched_kw:
            result.reasons.append(f"Competências encontradas ({len(matched_kw)}): {', '.join(matched_kw[:4])}")

        # Total Score
        total = seniority_score + location_score + title_score + keywords_score
        
        # Limite
        total = min(100.0, round(total, 1))
        
        result.seniority_score = seniority_score
        result.location_score = location_score
        result.title_score = title_score
        result.keywords_score = keywords_score
        result.total_score = total
        
        min_score = self.scoring_cfg.get("min_score_display", 50.0)
        if total < min_score:
            result.is_eligible = False
            result.disqualification_reason = f"Score ({total:.1f}%) abaixo do limite mínimo ({min_score}%)"

        return result
