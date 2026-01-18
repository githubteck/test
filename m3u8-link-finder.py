import requests
import re

TARGET_URL = "https://www.mana2.my/channel/live/suke-tv"

def find_m3u8_link():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/85.0.4183.102 Safari/537.36"
    }
    response = requests.get(TARGET_URL, headers=headers)

    if response.status_code == 200:
        content = response.text

        # Regex pattern to find m3u8 URLs with token and auth_key
        pattern = r"https://live\.mana2\.my/[^'\" ]+\.m3u8\?[^'\" ]+"

        matches = re.findall(pattern, content)
        if matches:
            print("Found m3u8 link(s):")
            for link in matches:
                print(link)
        else:
            print("No m3u8 link found in the response.")
    else:
        print(f"Failed to fetch page, status code: {response.status_code}")

if __name__ == "__main__":
    find_m3u8_link()
