from sqlite3 import Connection

con = Connection("../users.db")
cur = con.cursor()

cur.execute("DELETE FROM users;")
cur.close()
con.commit()
con.close()
