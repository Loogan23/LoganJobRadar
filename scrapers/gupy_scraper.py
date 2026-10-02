import urllib.parse
import json
import requests
from bs4 import BeautifulSoup
from typing import List
from core.models import Job
from scrapers.base import BaseScraper

class GupyScraper(BaseScraper):
    def __init__(self):
        super().__init__("Gupy")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def search(self, query: str, location: str = "", is_remote: bool = False, limit: int = 15) -> List[Job]:
        jobs: List[Job] = []
        encoded_query = urllib.parse.quote(query)
        url = f"https://portal.gupy.io/job-search/term={encoded_query}"
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=12)
            if resp.status_code != 200:
                return jobs

            soup = BeautifulSoup(resp.text, "html.parser")
            script_tag = soup.find("script", id="__NEXT_DATA__")
            if not script_tag or not script_tag.string:
                return jobs

            data = json.loads(script_tag.string)
            raw_jobs = data.get("props", {}).get("pageProps", {}).get("initialJobList", {}).get("data", [])

            for item in raw_jobs[:limit]:
                job_id = str(item.get("id", ""))
                title = item.get("name", "")
                company = item.get("careerPageName", "") or "Empresa Confidencial"
                city = item.get("city", "") or ""
                state = item.get("state", "") or ""
                workplace = item.get("workplaceType", "").lower()
                
                job_is_remote = workplace == "remote" or "remoto" in workplace
                if job_is_remote:
                    modality = "Remoto"
                    job_loc = "100% Remoto (Brasil)"
                elif workplace == "hybrid":
                    modality = "Híbrido"
                    job_loc = f"{city} - {state} (Híbrido)" if city else "Híbrido"
                else:
                    modality = "Presencial"
                    job_loc = f"{city} - {state}" if city else "Presencial"

                # Link da vaga
                job_url = item.get("jobUrl", "")
                if not job_url and job_id:
                    job_url = f"https://portal.gupy.io/job-search/term={job_id}"

                description = item.get("description", "")
                published_at = item.get("publishedDate", "")

                jobs.append(Job(
                    id=f"gupy_{job_id}",
                    title=title,
                    company=company,
                    location=job_loc,
                    city=city,
                    state=state,
                    is_remote=job_is_remote,
                    modality=modality,
                    url=job_url,
                    source="Gupy",
                    description=description,
                    published_at=published_at,
                    raw_data=item
                ))

        except Exception as e:
            # Fallback silencioso em caso de instabilidade de rede
            pass

        return jobs
