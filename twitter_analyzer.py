import time
import sqlite3
import random
import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import config

# Archivo de base de datos
DB_FILE = "tweets.db"
LOGIN_URL = "https://twitter.com/login"

# Lista de User-Agents para rotar y parecer diferentes navegadores
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
]

# Database configuration
def inicializar_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS liked_tweets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL UNIQUE,
        scraped_from_user TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def guardar_tweets(tweets, username):
    if not tweets:
        return 0
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    count = 0
    for tweet_text in tweets:
        try:
            cursor.execute("INSERT INTO liked_tweets (text, scraped_from_user) VALUES (?, ?)", (tweet_text, username))
            count += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    print(f"Guardados {count} nuevos tweets en la base de datos.")
    return count

# --- Funciones de Web Scraping con Selenium ---

def iniciar_sesion(driver, twitter_user, twitter_pass):
    try:
        driver.get(LOGIN_URL)
        
        # 1. Enter username
        print("login page loaded. Entering username...")
        user_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']")))
        user_input.send_keys(twitter_user)
        
        # 2. Click "Next"
        next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Siguiente')]")))
        next_button.click()
        print("'next' button clicked.")

        # 3. Handle potential verification step
        try:
            # Check if it's asking for password directly
            print("Looking for password field...")
            pass_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
            print("Password field found.")

        except:
            # If password not found, it's likely the verification page
            print("No password field found. Assuming verification page.")
            # The verification page asks for username/phone again
            verification_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']")))
            print("Entering username again for verification.")
            verification_input.send_keys(twitter_user)
            
            # Click "Next" again
            next_button_2 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Siguiente')]")))
            next_button_2.click()
            print("'next' button clicked again.")

            # Wait for manual CAPTCHA solving
            print("Please solve the CAPTCHA in the browser. The script will continue when the password field is detected...")
            while True:
                try:
                    pass_input = driver.find_element(By.NAME, "password")
                    if pass_input:
                        print("Password field found after verification.")
                        break
                except:
                    time.sleep(1)

        # 4. Enter password and log in
        pass_input.send_keys(twitter_pass)
        
        # Find and click the "Log in" button
        login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Iniciar sesión')]")))
        login_button.click()
        print("Password entered. Waiting for main page to load...")

        # 5. Wait for main page to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='SideNav_NewTweet_Button']")))
        print("Login completed successfully.")
        return True
    except Exception as e:
        print(f"Error during login: {e}")
        print("The script cannot continue. Check your credentials or if Twitter changed its login page.")
        driver.quit()
        return False

def scrapear_likes(driver, target_user, limite_tweets):
    print(f"Navegando a los likes de @{target_user}...")
    driver.get(f"https://twitter.com/{target_user}/likes")

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tweetText']")))
    except Exception:
        print("No tweets loaded on the likes page. The profile may be private or have no likes.")
        driver.save_screenshot("likes_page.png")
        return []

    print("Likes page loaded. Starting to scrape...")
    tweets_encontrados = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    intentos_scroll = 0

    while len(tweets_encontrados) < limite_tweets:
        tweet_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweetText']")
        nuevos_encontrados = 0
        for tweet in tweet_elements:
            if tweet.text and tweet.text not in tweets_encontrados:
                tweets_encontrados.add(tweet.text)
                nuevos_encontrados += 1

        print(f"Unique tweets found so far: {len(tweets_encontrados)}/{limite_tweets}")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Random pause to simulate human behavior
        time.sleep(random.uniform(2.5, 4.5))

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            intentos_scroll += 1
            print(f"there isnt any content to load (attempt {intentos_scroll}/3)")
            if intentos_scroll >= 3:
                print("Reached the end of the likes page.")
                break
        else:
            intentos_scroll = 0 # Reset counter if new content is found
        last_height = new_height

    return list(tweets_encontrados)[:limite_tweets]

# --- Main Flow ---

def main():
    inicializar_db()

    twitter_user = config.TWITTER_USER
    twitter_pass = config.TWITTER_PASS
    target_user = config.TARGET_USER
    limite_tweets = config.LIMITE_TWEETS

    # --- Selenium Configuration with Anti-Detection Options ---
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()

    # 1. User-Agent Rotation
    random_user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={random_user_agent}")
    print(f"Using User-Agent: {random_user_agent}")

    # 2. (Optional) Proxy Configuration. Uncomment and edit if you have a proxy.
    # proxy_server = "http://your_proxy_ip:port"
    # options.add_argument(f'--proxy-server={proxy_server}')

    # Start in incognito mode for a cleaner session
    options.add_argument("--incognito")

    driver = webdriver.Chrome(service=service, options=options)

    try:
        if iniciar_sesion(driver, twitter_user, twitter_pass):
            tweets = scrapear_likes(driver, target_user, limite_tweets)
            if tweets:
                guardar_tweets(tweets, target_user)
                print(f"\nProceso completado. Se han guardado los tweets en 'tweets.db'.")
                print("next step is to run the analysis with Gemini." )
            else:
                print(" it couldnt scrapped any tweet. Check if the target user has public likes or if the profile is private.")
    finally:
        print("Closing the browser.")
        driver.quit()

if __name__ == "__main__":
    main()
