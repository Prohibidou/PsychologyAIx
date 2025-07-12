import sqlite3
import os

# Get the absolute path of the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Join this path with the filename to get the absolute path to the db
DB_FILE = os.path.join(script_dir, "tweets.db")

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

        print(f"--- Saved tweets from @{tweets[0][1]} ---")
        for i, tweet in enumerate(tweets):
            print(f"{i + 1}. {tweet[0]}")
        print(f"\n--- End of tweets ---")

    except sqlite3.OperationalError:
        print(f"Error: Could not find the database '{DB_FILE}'. Make sure the scraper script has run successfully.")

if __name__ == "__main__":
    read_tweets()