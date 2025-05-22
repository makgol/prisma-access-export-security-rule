import requests
import json
import argparse
from datetime import datetime
import pytz
import csv
import os


def paAuth(pacred):
    url = "https://auth.apps.paloaltonetworks.com/oauth2/access_token"
    headers = {
               "Content-Type": "application/x-www-form-urlencoded",
            }
    data = "grant_type=client_credentials&scope=tsg_id:" + pacred.tsgid
    getResponse = requests.post(url, headers=headers, data=data, auth=(pacred.uid, pacred.secret))
    jsonData = json.loads(getResponse.text)
    responseHeades = getResponse.headers
    token = jsonData["access_token"]
    date = responseHeades["date"]
    expires_in = jsonData["expires_in"]
    
    return token, date, expires_in

def remove_duplicates_preserve_order(lst):
    seen = set()
    return [x for x in lst if not (x in seen or seen.add(x))]

def getObjects(token, current_time, urlList):
    limit = 200
    rootDir = "exported_csv_files"
    fileDir = os.path.join(rootDir, current_time)
    os.makedirs(fileDir, exist_ok=True)

    headers = {
         "Accept": "application/json",
         "Authorization": "Bearer " + token,
    }
    scopes = [
         "Mobile Users",
         "Remote Networks",
    ]
    for url in urlList:
        for scope in scopes:
            params = {
                "folder": scope,
                "limit": limit,
            }
            i = 0
            rules = []
            while True:
                params["offset"] = i
                getResponse = requests.get(urlList[url], headers=headers, params=params)
                jsonData = json.loads(getResponse.text)
                if len(jsonData["data"]) == 0:
                    break
                rules = rules + jsonData["data"]
                i += limit
            filename = "./%s/%s-%s.csv" % (fileDir, scope.replace(" ", ""), url)
            fieldnames = []
            for rule in rules:
                keyList = rule.keys()
                fieldnames = remove_duplicates_preserve_order(fieldnames + list(keyList))
    
            with open(filename, "w") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for rule in rules:
                    writer.writerow(rule)

def validateToken(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
            if len(data) == 0:
                return False, None
            jsonData = json.loads(data)
        date = jsonData["date"]
        dt_object_naive = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")
        gmt_timezone = pytz.timezone('GMT')
        given_dt_aware = gmt_timezone.localize(dt_object_naive)
        current_utc_dt = datetime.now(pytz.utc)
        time_difference = current_utc_dt - given_dt_aware
        if time_difference.total_seconds() < jsonData["expires_in"]:
            return True, jsonData["token"]
        else:
            return False, None
    except FileNotFoundError:
        return False, None

def main():
    current_time = datetime.now().astimezone().strftime('%Y-%m-%d-%H-%M-%S-%Z')
    parser = argparse.ArgumentParser()
    parser.add_argument("--uid", help="User ID of service account for Prisma Access.")
    parser.add_argument("--secret", help="Secret of service account for Prisma Access.")
    parser.add_argument("--tsgid", help="Prisma Access TSG ID.")
    paCredentials = parser.parse_args()
    tokenFolder = "token"
    os.makedirs(tokenFolder, exist_ok=True)
    tokenfile = "./%s/token.json" % tokenFolder
    validateTokenResult, token = validateToken(tokenfile)
    if not validateTokenResult:
        token, date, expires_in = paAuth(paCredentials)
        writeData = {
            "token": token,
            "date": date,
            "expires_in": expires_in,
        }
        with open(tokenfile, "w") as f:
            json.dump(writeData, f, indent=4, ensure_ascii=False)
    urlList = {
        "SecurityRule": "https://api.sase.paloaltonetworks.com/sse/config/v1/security-rules",
        "Addresses": "https://api.sase.paloaltonetworks.com/sse/config/v1/addresses",
        "AddressGroups": "https://api.sase.paloaltonetworks.com/sse/config/v1/address-groups",
    }
    getObjects(token, current_time, urlList)

if __name__=="__main__":
    main()

