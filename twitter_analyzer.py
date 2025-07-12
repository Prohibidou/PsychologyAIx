import time
import sqlite3
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os

# Get the absolute path of the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Join this path with the filename to get the absolute path to the db
DB_FILE = os.path.join(script_dir, "tweets.db")
LOGIN_URL = "https://twitter.com/login"

# List of User-Agents to rotate and appear as different browsers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
]

def initialize_db():
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

def save_tweets(tweets, username):
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
    return count

def run_analysis(config):
    yield "Initializing database..."
    initialize_db()

    twitter_user = config.TWITTER_USER
    twitter_pass = config.TWITTER_PASS
    target_user = config.TARGET_USER
    tweet_limit = config.TWEET_LIMIT

    yield "Configuring Selenium..."
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    random_user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={random_user_agent}")
    options.add_argument("--incognito")

    driver = webdriver.Chrome(service=service, options=options)

    try:
        yield "Logging in to Twitter..."
        driver.get(LOGIN_URL)
        user_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']")))
        user_input.send_keys(twitter_user)
        next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Next') or contains(text(), 'Siguiente')]")))
        next_button.click()

        try:
            pass_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
        except:
            yield "Verification step detected. Please solve the CAPTCHA in the browser."
            verification_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']")))
            verification_input.send_keys(twitter_user)
            next_button_2 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Next') or contains(text(), 'Siguiente')]")))
            next_button_2.click()
            WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.NAME, "password")))
            pass_input = driver.find_element(By.NAME, "password")

        pass_input.send_keys(twitter_pass)
        login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Log in') or contains(text(), 'Iniciar sesión')]")))
        login_button.click()
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='SideNav_NewTweet_Button']")))
        yield "Login successful."

        yield f"Scraping tweets and replies from @{target_user}..."
        driver.get(f"https://twitter.com/{target_user}/with_replies")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tweetText']")))

        found_tweets = set()
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0

        while len(found_tweets) < tweet_limit:
            tweet_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweetText']")
            for tweet in tweet_elements:
                if tweet.text and tweet.text not in found_tweets:
                    found_tweets.add(tweet.text)

            yield f"Found {len(found_tweets)} unique tweets..."
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2.5, 4.5))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
                if scroll_attempts >= 3:
                    yield "Reached the end of the page."
                    break
            else:
                scroll_attempts = 0
            last_height = new_height

        tweets_to_save = list(found_tweets)[:tweet_limit]
        count = save_tweets(tweets_to_save, target_user)
        yield f"Saved {count} new tweets."
    except Exception as e:
        yield f"An error occurred during the Twitter scraping process: {e}"

    finally:
        yield "Closing browser..."
        driver.quit()