import sqlite3
conn = sqlite3.connect('tweets.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(liked_tweets)")
print(f"Schema for liked_tweets: {cursor.fetchall()}")
conn.close()