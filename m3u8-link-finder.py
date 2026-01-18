import requests
import re

# Target URL
url = "https://ace.api.yuppcdn.net/analytics/partner"

# Full data payload as per your curl command
data = {
    "data": '{"dt":"web","dc":"chrome","di":"5","bi":"128ba6c-b509-0879-7315-e690afdce822","sk":"73e64f54-2d70-36bb-8ca1-2cf7ea19adcc","psk":1768705918040,"ui":-1,"pid":-1,"pdn":"mytv","pp":-1,"ps":"playing","meta_id":"channel_live_28_1519870","meta_map":-1,"a1":"{\"networkId\":1,\"packageDuration\":\"\",\"gateway\":\"\",\"packageType\":\"free\",\"networkName\":\"MYTV\",\"masterPackageName\":\"\",\"packageId\":\"-1\",\"isParentControlled\":false}","a2":-1,"sp":-1,"ep":-1,"br":-1,"tvl":-1,"em":-1,"at":-1,"et":15,"av":"v2","ts":1768706658042,"ec":30}'
}

# Analytics ID
analytics_id = "3dd332fa310560920f1399f41f008091"

# Complete URL with query parameter
full_url = f"{url}?analytics_id={analytics_id}"

# Headers mimicking your curl request
headers = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://www.mana2.my",
    "Referer": "https://www.mana2.my/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Brave";v="144")',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Send POST request
response = requests.post(full_url, headers=headers, data=data)

if response.status_code == 200:
    # Search for m3u8 link in response
    pattern = r"https://live\.mana2\.my/[^'\" ]+\.m3u8\?[^'\" ]+"
    matches = re.findall(pattern, response.text)
    if matches:
        print("Found m3u8 link:", matches[0])
    else:
        print("No m3u8 link found in response.")
else:
    print(f"Request failed with status code {response.status_code}")
