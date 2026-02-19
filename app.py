from flask import Flask, render_template, request
import pyargon2, string
from sqlite3 import Connection
from hashlib import sha1
import requests, uuid
import random
import pyotp

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/login")
def login_form():
    return "get login page"


@app.post("/login")
def login():
    return "do the login"


@app.get("/register")
def register_form():
    return render_template("register.html")


@app.post("/register")
def register():
    username = request.form["username"]
    password = request.form["password"]
    ssn = request.form["ssn"]
    # validate input with equal cold and hot paths
    con = Connection("users.db")
    cur = con.cursor()
    cur = cur.execute("SELECT * FROM users WHERE username == ?", (username,))
    username_valid = len(cur.fetchall()) == 0
    password_valid = len(password) >= 8 and len(password) <= 128
    ssn_valid = len(ssn) == 9

    # password breach check
    sha1_hash = sha1(password.encode("utf-8")).hexdigest().upper()
    breach_check = requests.get(
        f"https://api.pwnedpasswords.com/range/{sha1_hash[0:5]}"
    )
    breached_passwd = False
    for line in str(breach_check.content).splitlines():
        if sha1_hash[6:] in line:
            breached_passwd = True
        else:
            breached_passwd = breached_passwd
    password_valid = password_valid and not breached_passwd

    if not (username_valid and password_valid and ssn_valid):
        return render_template(
            "register.html", message="Username, password, or SSN invalid."
        )

    # actually store info
    salt = "".join(random.choices(string.printable, k=16))
    hashword = pyargon2.hash(
        password=password, salt=salt, time_cost=1, memory_cost=47104, parallelism=1
    )

    user_id = uuid.uuid4().bytes

    # otp setup
    otp_secret = pyotp.random_base32()

    cur = cur.execute(
        "INSERT INTO users(id, username, ssn, passhash, otp_secret, salt) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username, ssn, hashword, otp_secret, salt),
    )
    con.commit()
    con.close()
    return render_template("otp_setup.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3939, debug=True)
