import requests
import json 
import os 
import time 
import random 
import subprocess

def load_cookie_header(json_path="cookies/seloger_cookies.json"):
    """Charge les cookies Selenium et fabrique un header Cookie valide."""
    with open(json_path, "r") as f:
        cookies = json.load(f)

    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    return cookie_str

def refresh_cookie():
    print("Cookie expiré — ouverture de Chrome pour passer le CAPTCHA...")
    subprocess.run(["python3", "get_cookie.py"])
    print("➡️ Nouveau cookie récupéré.\n")
    
def safe_request(method, url, headers, data=None):
    r = requests.request(method, url, headers=headers, data=data)

    if r.status_code == 403:
        print("403 détecté — Cookie DataDome invalide\n")
        refresh_cookie()  # ➡ ouverture chrome, captcha manuel
        # recharge header avec cookie frais
        headers["Cookie"] = load_cookie_header()
        print("Retry...")
        r = requests.request(method, url, headers=headers, data=data)

    return r

def sl_search(location,size,page):
    cookie_header = load_cookie_header()
    payload = {
        "criteria": {
            "distributionTypes": ["Rent"],
            "estateTypes": ["House", "Apartment"],
            "projectTypes": ["Stock", "Flatsharing"],
            "location": {
                "placeIds": [location]  
            }
        },
        "paging": {
            "page": page,
            "size": size,
            "order": "Default"
        }
    }

    headers = {
        'accept': '*/*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json; charset=utf-8',
        'origin': 'https://www.seloger.com',
        'referer': f'https://www.seloger.com/classified-search?distributionTypes=Rent&estateTypes=House,Apartment&locations={location}&order=Default',
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
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Cookie': cookie_header    }

    payload_json = json.dumps(payload)

    response = safe_request("POST",
                        "https://www.seloger.com/serp-bff/search",
                        headers=headers,
                        data=payload_json)

    print("\n=== DETAIL RESULT ===")
    print(response.status_code)
    print(response.text[:300])
    data = response.json()
    # ⛔ Certaines pages ne contiennent pas 'classifieds'
    if "classifieds" not in data:
        print(f"⚠️ Aucun champ 'classifieds' pour {location} page {page}")
        return data, [], headers

    # ⛔ Parfois classifieds existe mais est vide
    if len(data["classifieds"]) == 0:
        print(f"➡️ Page vide pour {location} page {page}")
        return data, [], headers

    ids = [item["id"] for item in data["classifieds"]]

    os.makedirs("jsons/search_results", exist_ok=True)
    file_path = f"jsons/search_results/{location}_{page}.json"
    with open(file_path,"w") as f: 
        json.dump(data,f,indent=2,ensure_ascii=False)
    time.sleep(random.uniform(1.2, 3.5))
    return data , ids , headers

def get_details(id,headers):
    url_detail = f"https://www.seloger.com/cdp-bff/v1/classified/{id}"

    detail = safe_request("GET", url_detail, headers=headers)

    print("\n=== DETAIL RESULT ===")
    print(detail.status_code)
    print(detail.text[:300])

    d = detail.json()
    os.makedirs("jsons/details", exist_ok=True)
    file_path = f"jsons/details/{id}.json"
    with open(file_path,"w") as f: 
        json.dump(d,f,indent=2,ensure_ascii=False)
    print("JSON saved")
    time.sleep(random.uniform(1.2, 3.5))
    
def scrap(locations,size,maxpage):
    refresh_cookie()
    for l in locations:
        scraped_pages = get_already_scraped_pages(l)
        for page in range(1,maxpage+1): # 50 pages max
            if page in scraped_pages:
                print(f"➡️ Page {page} déjà scrapée, skip.")
                continue
            data , ids , headers = sl_search(l,size,page)
            if len(ids) == 0:
                print(f"Got all the results for {l} stopped at page {page}")
                break 
            for i in ids: 
                get_details(i , headers)
                
def get_already_scraped_pages(location):
    folder = "jsons/search_results"
    if not os.path.exists(folder):
        return set()

    pages = set()
    for file in os.listdir(folder):
        if file.startswith(location) and file.endswith(".json"):
            # Format du fichier : AD08FR28808_3.json
            try:
                page = int(file.split("_")[-1].split(".")[0])
                pages.add(page)
            except:
                pass
    return pages

        
if __name__ == "__main__":
    locations =["AD08FR28808" , "AD08FR31096"] # Lyon et Paris
    size = 30
    max_page = 100
    scrap(locations,size,max_page)