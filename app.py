from flask import Flask, redirect, render_template, request, url_for
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    jwt_required,
    get_current_user,
    set_access_cookies,
    unset_jwt_cookies,
)
from datetime import timedelta
import pyargon2, string
from sqlite3 import Connection
from hashlib import sha1
import requests, uuid
import random
import pyotp, dotenv, os, binascii

_ = dotenv.load_dotenv()

ACCESS_EXPIRES = timedelta(hours=1)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_KEY", "please_change_this")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
jwt = JWTManager(app)


def passwd_hash(password: str, salt: str):
    return pyargon2.hash(
        password=password, salt=salt, time_cost=1, memory_cost=47104, parallelism=1
    )


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    res = redirect(url_for("login"))
    unset_jwt_cookies(res)
    return res


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    uuid = binascii.a2b_hex(jwt_data["sub"])
    con = Connection("users.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id == ?", (uuid,))
    res = cur.fetchall()
    if len(res) == 0:
        return None
    return res[0]


@jwt.token_in_blocklist_loader
def check_for_revoked_token(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    con = Connection("tokens.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM revoked_tokens WHERE jti == ?", (jti,))
    res = cur.fetchall()
    con.close()
    return len(res) != 0


@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    con = Connection("tokens.db")
    cur = con.cursor()
    cur.execute("INSERT INTO revoked_tokens(jti) VALUES (?)", (jti,))
    con.commit()
    con.close()
    res = redirect(url_for("index"))
    unset_jwt_cookies(res)
    return res


@app.route("/")
@jwt_required(optional=True)
def index():
    user = get_current_user()
    if user is None:
        return render_template("index.html")
    return render_template("index.html", username=user[1], ssn=user[2])


@app.get("/login")
def login_form():
    return render_template("login.html")


@app.post("/login")
def login():
    login_fail = False
    username = request.form["username"]
    password = request.form["password"]
    otp = request.form["otp"]
    con = Connection("users.db")
    cur = con.cursor()
    cur = cur.execute("SELECT * FROM users WHERE username == ?", (username,))
    user_info = cur.fetchall()
    if len(user_info) == 0:
        login_fail = True
        user_hash: str = ""
        user_salt: str = ""
        user_secret: str = pyotp.random_base32()
    else:
        user_hash: str = user_info[0][3]
        user_salt: str = user_info[0][5]
        user_secret: str = user_info[0][4]

    challenging_hash = passwd_hash(password, user_salt)
    if challenging_hash != user_hash:
        login_fail = True

    mfa = pyotp.totp.TOTP(s=user_secret)
    if not mfa.verify(otp):
        login_fail = True

    if login_fail:
        return render_template(
            "login.html", message="Invalid username, password, or 2FA code"
        )

    # actually log in
    access_token = create_access_token(
        identity=binascii.b2a_hex(user_info[0][0]).decode("ascii")
    )
    resp = redirect(url_for("index"))
    set_access_cookies(resp, access_token)
    return resp


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
    hashword = passwd_hash(password, salt)

    user_id = uuid.uuid4().bytes

    # otp setup
    otp_secret = pyotp.random_base32()

    url = pyotp.totp.TOTP(otp_secret).provisioning_uri(
        name=f"{username}", issuer_name="SSN Database"
    )

    cur = cur.execute(
        "INSERT INTO users(id, username, ssn, passhash, otp_secret, salt) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username, ssn, hashword, otp_secret, salt),
    )
    con.commit()
    con.close()
    return render_template("otp_setup.html", otp_uri=url, otp_secret=otp_secret)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3939, debug=True)
