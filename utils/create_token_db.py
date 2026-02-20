from sqlite3 import Connection

con = Connection("../tokens.db")
cur = con.cursor()

cur.execute("CREATE TABLE revoked_tokens (jti WORD)")

con.commit()
con.close()
