import json
import random
import time
import requests
import subprocess
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any


# -------------------------------------------------------------------------
# UTILITAIRES
# -------------------------------------------------------------------------

def normalize_city(name: str) -> str:
    """Nettoie un nom de ville (simplifié)."""
    name = name.lower()
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"[, ]+", "_", name).strip("_")
    return name


def save_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    
def get_last_scraped_page(city_slug: str) -> int:
    pages_dir = Path("jsons") / city_slug / "pages"
    if not pages_dir.exists():
        return 0
    pages = []
    for f in pages_dir.glob("page_*.json"):
        try:
            num = int(f.stem.split("_")[1])
            pages.append(num)
        except:
            pass
    return max(pages) if pages else 0


# -------------------------------------------------------------------------
# HTTP CLIENT (avec cookies + retry + délai)
# -------------------------------------------------------------------------

class HttpClient:
    def __init__(
        self,
        cookie_path: str,
        base_headers: Dict[str, str],
        min_delay: float = 1.2,
        max_delay: float = 3.5,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> None:
        self.cookie_path = Path(cookie_path)
        self.base_headers = base_headers
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.session = requests.Session()
        self._cookie_cache: str | None = None

    # ---- cookies ----
    def _load_cookie(self, force_reload: bool = False) -> str:
        """
        Charge le cookie depuis le fichier.
        Si le fichier n'existe pas, lance get_cookie.py une seule fois.
        """
        if self._cookie_cache is None or force_reload:
            if not self.cookie_path.exists():
                print("⚠️ Cookies introuvables, lancement de get_cookie.py...")
                self._refresh_cookie()
                if not self.cookie_path.exists():
                    raise FileNotFoundError(
                        f"Échec création cookies: {self.cookie_path}"
                    )

            with self.cookie_path.open(encoding="utf-8") as f:
                cookies = json.load(f)

            self._cookie_cache = "; ".join(
                f"{c['name']}={c['value']}" for c in cookies
            )
        return self._cookie_cache

    def _refresh_cookie(self) -> None:
        """Appelle get_cookie.py et invalide le cache."""
        print("🔑 Refresh cookie via get_cookie.py...")
        subprocess.run(["python3", "get_cookie.py"], check=True)
        self._cookie_cache = None

    # ---- headers ----
    def build_headers(self, referer: str | None = None) -> Dict[str, str]:
        headers = self.base_headers.copy()
        headers["Cookie"] = self._load_cookie()
        if referer:
            headers["referer"] = referer
        return headers

    # ---- requête avec retry cookie + délai aléatoire ----
    def request(
        self,
        method: str,
        url: str,
        *,
        data: str | None = None,
        json_body: Dict[str, Any] | None = None,
        referer: str | None = None,
    ) -> requests.Response:
        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                headers = self.build_headers(referer=referer)
                resp = self.session.request(
                    method,
                    url,
                    headers=headers,
                    data=data,
                    json=json_body,
                    timeout=30,
                )

                # Gestion 403 (cookie expiré)
                if resp.status_code == 403:
                    if attempt < self.max_retries:
                        print(f"⚠️ 403 détecté, refresh cookie (tentative {attempt})")
                        self._refresh_cookie()
                        continue
                    raise RuntimeError("403 après refresh cookie, abandon.")

                # délai entre requêtes
                time.sleep(random.uniform(self.min_delay, self.max_delay))
                return resp

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exc = e
                if attempt < self.max_retries:
                    print(f"⚠️ Erreur réseau {e}, retry dans {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"Échec réseau après retries: {last_exc}") from e

        raise RuntimeError(f"Erreur inattendue dans HttpClient.request: {last_exc}")


# -------------------------------------------------------------------------
# CONFIG SCRAPER
# -------------------------------------------------------------------------

@dataclass
class ScraperConfig:
    city: str
    location_id: str
    base: Path

    @classmethod
    def from_city(cls, city_name: str, location_id: str) -> "ScraperConfig":
        clean = normalize_city(city_name)
        base = Path("jsons") / clean
        return cls(clean, location_id, base)

    @property
    def pages(self) -> Path:
        return self.base / "pages"

    @property
    def annonces(self) -> Path:
        return self.base / "annonces"


# -------------------------------------------------------------------------
# SCRAPER PRINCIPAL
# -------------------------------------------------------------------------

class SeLogerScraper:
    BASE = "https://www.seloger.com"
    SEARCH = BASE + "/serp-bff/search"
    DETAIL = BASE + "/cdp-bff/v1/classified/{}"

    # ⬇ headers repris de ta version d'origine (important pour éviter les 403)
    HEADERS = {
        'accept': '*/*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json; charset=utf-8',
        'origin': 'https://www.seloger.com',
        'sec-ch-device-memory': '8',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Chromium";v="142.0.7444.176", "Google Chrome";v="142.0.7444.176", "Not_A Brand";v="99.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/142.0.0.0 Safari/537.36'
        ),
    }

    def __init__(
        self,
        city_name: str,
        location_id: str,
        cookie_path: str = "cookies/seloger_cookies.json",
    ) -> None:
        self.cfg = ScraperConfig.from_city(city_name, location_id)
        self.http = HttpClient(cookie_path, self.HEADERS)

        self.cfg.pages.mkdir(parents=True, exist_ok=True)
        self.cfg.annonces.mkdir(parents=True, exist_ok=True)

    # ---- payload recherche ----
    def payload(self, page: int, size: int) -> Dict[str, Any]:
        return {
            "criteria": {
                "distributionTypes": ["Rent"],
                "estateTypes": ["House", "Apartment"],
                "projectTypes": ["Stock", "Flatsharing"],
                "location": {"placeIds": [self.cfg.location_id]},
            },
            "paging": {"page": page, "size": size, "order": "Default"},
        }

    # ---- récupération d'une page de résultats ----
    def search_page(self, page: int, size: int):
        referer = (
            f"{self.BASE}/classified-search"
            f"?distributionTypes=Rent"
            f"&estateTypes=House,Apartment"
            f"&locations={self.cfg.location_id}"
            f"&order=Default"
        )

        payload_json = json.dumps(self.payload(page, size))
        resp = self.http.request(
            "POST",
            self.SEARCH,
            data=payload_json,
            referer=referer,
        )
        data = resp.json()
        ads = data.get("classifieds", [])
        return ads, data

    # ---- récupération d'une annonce ----
    def scrape_ad(self, ad_id: str) -> None:
        path = self.cfg.annonces / f"{ad_id}.json"
        if path.exists():
            return

        if Path("stop_scraping.flag").exists():
            raise KeyboardInterrupt("Stop requested")

        url = self.DETAIL.format(ad_id)
        resp = self.http.request("GET", url)
        save_json(resp.json(), path)

    # ---- récupération d'une page complète ----
    def scrape_page(self, page: int, size: int) -> int:
        ads, data = self.search_page(page, size)
        if not ads:
            return 0

        for ad in ads:
            self.scrape_ad(str(ad["id"]))

        save_json(data, self.cfg.pages / f"page_{page}.json")
        return len(ads)


# -------------------------------------------------------------------------
# SCRAPER MULTI-VILLES EN ALTERNANCE
# -------------------------------------------------------------------------

def run_scraping(cities: Dict[str, str], size: int = 30, max_page: int = 999):
    scrapers = {name: SeLogerScraper(name, loc) for name, loc in cities.items()}
    stats = {name: {"pages": 0, "ads": 0, "done": False} for name in cities}
    alive = set(cities.keys())

    # page de départ par ville
    current_page = {city: get_last_scraped_page(city) + 1 for city in cities}

    while alive:
        for city in list(alive):
            s = scrapers[city]
            page = current_page[city]

            print(f"\n=== {city} → page {page} ===")

            n = s.scrape_page(page, size)
            stats[city]["pages"] = page
            stats[city]["ads"] += n

            if n == 0:
                print(f"Fin du scraping pour {city} (page vide)")
                alive.remove(city)
            else:
                current_page[city] += 1

    return stats


# -------------------------------------------------------------------------
# UTILITAIRE POUR MATCH 2 VILLES
# -------------------------------------------------------------------------

def exec_scraping(city1: str, city2: str):
    from get_loc import location_autocomplete

    id1, name1 = location_autocomplete(city1)
    id2, name2 = location_autocomplete(city2)

    cities = {name1: id1, name2: id2}

    print(f"\n🏙️ {city1} VS {city2}\n")
    return run_scraping(cities, size=30, max_page=100)


if __name__ == "__main__":
    c1 = input("Ville 1: ")
    c2 = input("Ville 2: ")
    print(exec_scraping(c1, c2))
