import sqlite3

DB_FILE = "tweets.db"

def read_tweets():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT text, scraped_from_user FROM liked_tweets")
        tweets = cursor.fetchall()
        conn.close()

        if not tweets:
            print("No tweets found in the database.")
            return

        print(f"--- tweets from @{tweets[0][1]}  saved ---")
        for i, tweet in enumerate(tweets):
            print(f"{i + 1}. {tweet[0]}")
        print(f"\n--- Fin de los tweets ---")

    except sqlite3.OperationalError:
        print(f"Error: Could not find the database '{DB_FILE}'. Make sure the main script has run successfully.")

if __name__ == "__main__":
    read_tweets()
