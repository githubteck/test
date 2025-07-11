import requests
import os
from lxml import etree
from datetime import datetime, timedelta
from base64 import b64encode
from copy import deepcopy
import re

# --- GitHub Repo Info ---
repo_owner = 'githubteck'
repo_name = 'test'
target_file_path = 'epg.xml'
access_token = os.getenv('ABC')

# --- EPG URLs (no timezone parameter, source provides +0000 by default) ---
epg_urls = [
    'https://epg.pw/xmltv/epg_TW.xml',
    'https://epg.pw/xmltv/epg_HK.xml'
]

def fetch_epg(url):
    print(f"Fetching {url}")
    response = requests.get(url)
    response.raise_for_status()
    return etree.fromstring(response.content)

def is_today(time_str):
    """
    Check if the start time is today in local (UTC+8) time.
    """
    match = re.match(r"(\d{14})", time_str)
    if not match:
        return False
    dt_str = match.group(1)
    dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
    # Assume the time is in UTC, shift to UTC+8 for date comparison
    dt += timedelta(hours=8)
    return dt.date() == datetime.now().date()

def shift_time_back_8_hours(time_str):
    """
    Shift a datetime string back by 8 hours.
    Keep format: 'YYYYMMDDHHMMSS +0000'
    """
    match = re.match(r"(\d{14})\s?([+\-]\d{4})?", time_str)
    if not match:
        return time_str
    dt = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
    dt_shifted = dt - timedelta(hours=8)
    return dt_shifted.strftime("%Y%m%d%H%M%S") + " +0000"

def filter_and_merge_today(epg_roots):
    print("Merging channels and today's programmes only (shifting -8 hours)")

    merged_root = etree.Element("tv")
    channel_ids = set()

    # Add unique channels
    for root in epg_roots:
        for channel in root.xpath("//channel"):
            ch_id = channel.attrib.get("id")
            if ch_id and ch_id not in channel_ids:
                merged_root.append(deepcopy(channel))
                channel_ids.add(ch_id)

    # Filter and adjust today's programmes
    for root in epg_roots:
        for programme in root.xpath("//programme"):
            start = programme.attrib.get("start")
            if start and is_today(start):
                prog_copy = deepcopy(programme)
                prog_copy.attrib['start'] = shift_time_back_8_hours(start)
                stop = prog_copy.attrib.get('stop')
                if stop:
                    prog_copy.attrib['stop'] = shift_time_back_8_hours(stop)
                merged_root.append(prog_copy)

    return etree.tostring(merged_root, pretty_print=True, encoding="utf-8", xml_declaration=True)

def upload_to_github(owner, repo, path, content, token):
    print(f"Uploading {path} to GitHub repo {owner}/{repo}")
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    # Check if file exists
    get_resp = requests.get(api_url, headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    data = {
        "message": "Update epg.xml with today's EPG data (shifted -8h)",
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
    merged_xml = filter_and_merge_today(roots)
    upload_to_github(repo_owner, repo_name, target_file_path, merged_xml, access_token)

if __name__ == "__main__":
    main()
