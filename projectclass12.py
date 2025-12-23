import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="bgsps",
    database="words_db"
)

cursor = conn.cursor()

file_path = "1000words.txt"

with open(file_path, "r", encoding="utf-8") as file:
    for line in file:
        line = line.strip()
        if not line:
            continue

        # Split into word and the rest
        word_split = line.split(":", 1)
        word = word_split[0].strip()

        # Split the rest into meaning, synonyms, antonyms
        rest = word_split[1].split(",")
        meaning = rest[0].strip() if len(rest) > 0 else ""
        synonyms = rest[1].strip() if len(rest) > 1 else ""
        antonyms = rest[2].strip() if len(rest) > 2 else ""

        cursor.execute("""
            INSERT INTO words1000 (word, meaning, synonyms, antonyms)
            VALUES (%s, %s, %s, %s)
        """, (word, meaning, synonyms, antonyms))

conn.commit()
conn.close()

print("Done! All words inserted.")
