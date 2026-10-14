import json

rest = open(".env").read().split("GOOGLE_SERVICE_ACCOUNT_JSON=", 1)[1]
lines = rest.splitlines()
info = None
for i in range(len(lines), 0, -1):
    cand = "\n".join(lines[:i]).strip().strip('"').strip("'")
    try:
        info = json.loads(cand)
        break
    except json.JSONDecodeError:
        continue
print(info["client_email"])
