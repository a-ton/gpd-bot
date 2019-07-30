import requests
import json
import Config

def getPerms(app_id):
    req_params = {"country": "US"}

    api = Config.permissions_api

    url = "https://api.appmonsta.com/v1/stores/android/details/%s.json" % app_id

    headers = {'Accept-Encoding': 'deflate, gzip'}

    response = requests.get(url,
                            auth=(api, ""),
                            params=req_params,
                            headers=headers,
                            stream=True).json()

    perm_list = ""

    if "read the contents of your USB storage" in response["permissions"]:
        perm_list += "Read/Modify Storage, "

    if "read your text messages (SMS or MMS)" in response["permissions"]:
        perm_list += "Read/Send SMS, "

    if "record audio" in response["permissions"]:
        perm_list += "Record Audio, "

    if "precise location (GPS and network-based)" or "approximate location (network-based)" in response["permissions"]:
        perm_list += "Location Access, "

    if "take pictures and videos" in response["permissions"]:
        perm_list += "Access Camera, "

    if "view network connections" in response["permissions"]:
        perm_list += "View Wi-Fi Info, "

    if "retrieve running apps" in response["permissions"]:
        perm_list += "Device & App History, "

    if "find accounts on the device" in response["permissions"]:
        perm_list += "Read Identity & Contacts, "

    return perm_list[:-2]
