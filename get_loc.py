import requests
import json
import subprocess
from pathlib import Path


def load_cookie() -> str:
    """Charge le cookie depuis le fichier, ou lance get_cookie.py si absent"""
    cookie_path = Path("cookies/seloger_cookies.json")
    
    if not cookie_path.exists():
        print("⚠️  Cookies introuvables, lancement de get_cookie.py...")
        subprocess.run(["python3", "get_cookie.py"], check=True)
        
        if not cookie_path.exists():
            raise FileNotFoundError("Échec de la création du fichier de cookies")
    
    with open(cookie_path) as f:
        cookies = json.load(f)
    
    return "; ".join([f"{c['name']}={c['value']}" for c in cookies])


def location_autocomplete(text: str) -> dict:
    """Recherche une location et retourne les suggestions"""
    url = "https://www.seloger.com/search-mfe-bff/autocomplete"

    payload = json.dumps({
        "text": text,
        "limit": 10,
        "placeTypes": ["NBH1", "NBH3", "AD09", "NBH2", "AD08", "AD06", "AD04", "POCO", "AD02"],
        "parentTypes": ["NBH1", "NBH3", "AD09", "NBH2", "AD08", "AD06", "AD04", "POCO", "AD02"],
        "locale": "fr"
    })
    
    headers = {
        'sec-ch-ua-full-version-list': '"Chromium";v="142.0.7444.176", "Google Chrome";v="142.0.7444.176", "Not_A Brand";v="99.0.0.0"',
        'sec-ch-ua-platform': '"Windows"',
        'Referer': 'https://www.seloger.com/',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-model': '""',
        'sec-ch-device-memory': '8',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-arch': '"x86"',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Cookie': load_cookie()
    }

    response = requests.post(url, headers=headers, data=payload)
    data = response.json()
    
    if data and len(data) > 0:
        location_id = data[0].get('id')
        location_name = data[0].get('labels', [''])[0] if data[0].get('labels') else None
        return location_id, location_name
    return None, None


if __name__ == "__main__":
    # Exemple d'utilisation
    city = input("Ville à rechercher: ")
    id , name = location_autocomplete(city)
    print(id , name)

