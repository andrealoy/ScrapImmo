from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json
import os
import sys 
import threading 

def input_with_timeout(prompt, timeout=30):
    print(prompt)
    user_input = [None]

    def wait_input():
        user_input[0] = sys.stdin.readline().strip()

    thread = threading.Thread(target=wait_input)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    # Si aucune entrée de l'utilisateur dans le délai :
    if thread.is_alive():
        print(f"\n⏱️ Pas d'entrée utilisateur pendant {timeout} secondes, on continue automatiquement...\n")
        return None

    return user_input[0]

def get_cookie():
    options = Options()

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    options.binary_location = "/usr/bin/google-chrome"

    driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })

    driver.get("https://www.seloger.com/")
    print("Résous le CAPTCHA puis appuie sur Entrée dans la console.\n")
    input_with_timeout("Appuie sur Entrée quand le captcha est validé... (30s timeout)", timeout=30)
    
    cookies = driver.get_cookies()
    os.makedirs("cookies", exist_ok=True)
    with open("cookies/seloger_cookies.json", "w") as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)

    print("Cookies sauvegardés.")
    driver.quit()


if __name__ == "__main__":
    get_cookie()
