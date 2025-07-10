import requests
from base64 import b64encode
import base64
import os
from lxml import etree
from datetime import datetime, timezone, timedelta
import re

# --- GitHub Repo Info ---
repo_owner = 'githubteck'
repo_name = 'test'
target_file_path = 'epg.xml'       # GitHub filename
access_token = os.getenv('ABC')    # GitHub token from environment

# --- EPG URLs ---
epg_urls = [
    'https://epg.pw/xmltv/epg_TW.xml',
    'https://epg.pw/xmltv/epg_HK.xml'
]

def fetch_epg(url):
    print(f"Fetching {url}")
    response = requests.get(url)
    response.raise_for_status()
    return etree.fromstring(response.content)

def convert_to_plus0800(time_str):
    """
    Convert XMLTV time string like 'YYYYMMDDHHMMSS ±zzzz' to +0800 offset.
    Returns a string formatted 'YYYYMMDDHHMMSS +0800'.
    """
    match = re.match(r"(\d{14})( ?)([+\-]\d{4})", time_str)
    if not match:
        # No offset found, assume UTC
        dt_str = time_str[:14]
        dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt_str, _, offset_str = match.groups()
        dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
        sign = 1 if offset_str[0] == '+' else -1
        offset_hours = int(offset_str[1:3])
        offset_minutes = int(offset_str[3:])
        offset = timedelta(hours=sign*offset_hours, minutes=sign*offset_minutes)
        dt = dt.replace(tzinfo=timezone(offset))

    plus8 = timezone(timedelta(hours=8))
    dt_plus8 = dt.astimezone(plus8)
    new_time_str = dt_plus8.strftime("%Y%m%d%H%M%S +0800")
    return new_time_str

def filter_and_merge_all_with_plus0800(epg_roots):
    print("Merging all channels and programmes, converting times to +0800")

    merged_root = etree.Element("tv")
    channel_ids = set()

    for root in epg_roots:
        # Add unique channels
        for channel in root.xpath("//channel"):
            ch_id = channel.attrib.get("id")
            if ch_id and ch_id not in channel_ids:
                merged_root.append(channel)
                channel_ids.add(ch_id)

        # Add all programmes with start time converted to +0800
        for programme in root.xpath("//programme"):
            start = programme.attrib.get("start")
            if start:
                new_start = convert_to_plus0800(start)
                programme.attrib["start"] = new_start
            merged_root.append(programme)

    return etree.tostring(merged_root, pretty_print=True, encoding="utf-8", xml_declaration=True)

def upload_to_github(owner, repo, path, content, token):
    print(f"Checking existing {path} in GitHub repo {owner}/{repo}")
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    get_resp = requests.get(api_url, headers=headers)
    if get_resp.status_code == 200:
        existing_file = get_resp.json()
        sha = existing_file.get("sha")
        existing_content_b64 = existing_file.get("content", "").strip()
        existing_content = base64.b64decode(existing_content_b64)

        if existing_content == content:
            print("No changes detected in epg.xml — skipping upload.")
            return
        else:
            print("Changes detected — will update epg.xml.")
    else:
        sha = None
        print(f"No existing {path} found — creating new file.")

    data = {
        "message": "Update epg.xml with all programmes converted to +0800",
        "content": b64encode(content).decode('utf-8'),
        "branch": "main"
    }
    if sha:
        data["sha"] = sha

    put_resp = requests.put(api_url, headers=headers, json=data)
    if put_resp.status_code in [200, 201]:
        print("✅ epg.xml uploaded successfully.")
    else:
        print("❌ Failed to upload:", put_resp.status_code, put_resp.text)

def main():
    if not access_token:
        print("❌ GitHub token not found in environment variable 'ABC'")
        return

    roots = [fetch_epg(url) for url in epg_urls]
    merged_xml = filter_and_merge_all_with_plus0800(roots)
    upload_to_github(repo_owner, repo_name, target_file_path, merged_xml, access_token)

if __name__ == "__main__":
    main()
