from sqlite3 import Connection

con = Connection("../users.db")
cur = con.cursor()

cur.execute(
    "CREATE TABLE users (id BLOB PRIMARY KEY, username WORD, ssn INT, passhash WORD, otp_secret WORD, salt WORD)"
)
cur.close()
con.commit()
con.close()
