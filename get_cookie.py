from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import os
import time 

def get_cookie():
    """Récupère les cookies SeLoger en ouvrant Chrome et en attendant la résolution du CAPTCHA"""
    
    # Configuration de Chrome
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.binary_location = "/usr/bin/google-chrome"

    # Lancer Chrome
    driver = webdriver.Chrome(options=options)

    # Masquer le fait que c'est un webdriver automatisé
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })

    # Ouvrir SeLoger
    driver.get("https://www.seloger.com/")
    
    print("\n" + "="*60)
    print("🔒 CAPTCHA détecté - Action requise")
    print("="*60)
    print("\n1. Résous le CAPTCHA dans le navigateur Chrome qui s'est ouvert")
    
    time.sleep(8)
    
    # Récupérer et sauvegarder les cookies
    cookies = driver.get_cookies()
    os.makedirs("cookies", exist_ok=True)
    
    with open("cookies/seloger_cookies.json", "w") as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)

    print("\n✅ Cookies sauvegardés avec succès dans cookies/seloger_cookies.json")
    print("="*60 + "\n")
    
    driver.quit()


if __name__ == "__main__":
    get_cookie()
