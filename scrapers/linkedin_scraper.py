import urllib.parse
import re
import requests
from bs4 import BeautifulSoup
from typing import List
from core.models import Job
from scrapers.base import BaseScraper

class LinkedInScraper(BaseScraper):
    def __init__(self):
        super().__init__("LinkedIn")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def search(self, query: str, location: str = "Fortaleza, Ceará, Brasil", is_remote: bool = False, limit: int = 15) -> List[Job]:
        jobs: List[Job] = []
        encoded_query = urllib.parse.quote(query)
        
        params = [f"keywords={encoded_query}"]
        if is_remote:
            params.append("geoId=106057199") # ID geográfico oficial do Brasil no LinkedIn
            params.append("f_WT=2") # Filtro de Remoto no LinkedIn
        elif location:
            encoded_loc = urllib.parse.quote(location)
            params.append(f"location={encoded_loc}")

        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{'&'.join(params)}"

        try:
            resp = requests.get(url, headers=self.headers, timeout=12)
            if resp.status_code != 200:
                return jobs

            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.find_all("li")

            for item in items[:limit]:
                title_elem = item.find("h3")
                company_elem = item.find("h4")
                link_elem = item.find("a", class_="base-card__full-link") or item.find("a")
                loc_elem = item.find("span", class_="job-search-card__location")
                time_elem = item.find("time")

                if not title_elem or not link_elem:
                    continue

                title = title_elem.get_text(strip=True)
                company = company_elem.get_text(strip=True) if company_elem else "Empresa Confidencial"
                job_url = link_elem.get("href", "").split("?")[0]
                job_loc = loc_elem.get_text(strip=True) if loc_elem else ("Remoto" if is_remote else location)
                published_at = time_elem.get_text(strip=True) if time_elem else ""

                # Identificador
                urn_match = re.search(r"(\d+)", job_url)
                job_id = f"li_{urn_match.group(1)}" if urn_match else f"li_{hash(job_url)}"

                modality = "Remoto" if is_remote or "remoto" in job_loc.lower() else "Presencial"
                if "híbrido" in job_loc.lower() or "hibrido" in job_loc.lower():
                    modality = "Híbrido"

                jobs.append(Job(
                    id=job_id,
                    title=title,
                    company=company,
                    location=job_loc,
                    city="Fortaleza" if "fortaleza" in job_loc.lower() else "",
                    state="CE" if "ce" in job_loc.lower() or "ceará" in job_loc.lower() else "",
                    is_remote=is_remote or (modality == "Remoto"),
                    modality=modality,
                    url=job_url,
                    source="LinkedIn",
                    description="",
                    published_at=published_at,
                    raw_data={}
                ))

        except Exception as e:
            pass

        return jobs
