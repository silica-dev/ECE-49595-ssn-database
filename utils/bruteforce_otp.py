from random import randrange, shuffle
import requests
import time

TEST_USER = "amia"
TEST_PASSWD = "Va9^bhvdPu@7fH"

list = list(range(1000000))
shuffle(list)

start = time.time_ns()
for i in list[0:39]:
    otp = f"{i:06d}"
    payload = {"username": TEST_USER, "password": TEST_PASSWD, "otp": otp}
    res = requests.post(url="http://localhost:3939/login", data=payload)
    if "amia" in str(res.content):
        print(f"OTP that worked: f{otp}")
        print(res)

stop = time.time_ns()
print(f"took {(stop - start) / 10**9} seconds to run 40 queries")
print(
    f"total time for all values: {(stop - start) / 10**9 * 10**6 / 40 / 60 / 60} hours"
)
