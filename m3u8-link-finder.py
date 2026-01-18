import requests
import urllib.parse
import re

# The URL endpoint
url = "https://ace.api.yuppcdn.net/analytics/partner"

# The payload data (encoded as form data)
payload = {
    "data": '{"dos":"Win32","pln":"jwplayer","plv":"jw_8_14","cdn":"alibaba","nf":"channel/live/suke-tv","is":"0","appv":-1,"cnt":-1,"ip":"60.53.34.19","np":-1,"ap":true,"su":"https://live.mana2.my/SukeTv/index.m3u8","dt":"web","dc":"chrome","di":"5","bi":"128ba6c-b509-0879-7315-e690afdce822","sk":"73e64f54-2d70-36bb-8ca1-2cf7ea19adcc","psk":1768705918040,"ui":-1,"pid":-1,"pdn":"mytv","pp":-1,"ps":"idle","meta_id":"channel_live_28_1519870","meta_map":-1,"a1":"{\"networkId\":1,\"packageDuration\":\"\",\"gateway\":\"\",\"packageType\":\"free\",\"networkName\":\"MYTV\",\"masterPackageName\":\"\",\"packageId\":\"-1\",\"isParentControlled\":false}","a2":-1,"sp":-1,"ep":-1,"br":-1,"tvl":-1,"em":-1,"at":-1,"et":1,"av":"v2","ts":1768705918040,"ec":1}'
}

# Extract the analytics_id
analytics_id = "3dd332fa310560920f1399f41f008091"

# Build the full URL with the query parameter
full_url = f"{url}?analytics_id={analytics_id}"

# Send POST request with form data
response = requests.post(full_url, data=payload)

if response.status_code == 200:
    # Check response content
    print("Response received.")
    # Try to find an m3u8 link in the response
    pattern = r"https://live\.mana2\.my/[^'\" ]+\.m3u8\?[^'\" ]+"
    matches = re.findall(pattern, response.text)
    if matches:
        print("Found m3u8 link:", matches[0])
    else:
        print("No m3u8 link found in response.")
else:
    print(f"Request failed with status code {response.status_code}")
