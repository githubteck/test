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

def is_today_after_offset(time_str, offset_hours=8):
    """
    Check if the datetime (in UTC) minus offset_hours falls within today in UTC+8.
    For example: 20250714020000 - 8h = 20250713180000 → still today in UTC+8
    """
    match = re.match(r"(\d{14})", time_str)
    if not match:
        return False

    dt_utc = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
    dt_adjusted = dt_utc - timedelta(hours=offset_hours)

    today_utc8 = datetime.utcnow() + timedelta(hours=offset_hours)
    return dt_adjusted.date() == today_utc8.date()

def filter_and_merge_today(epg_roots):
    print("Merging channels and programmes that fall on today's date in UTC+8 (timestamps kept, timezone changed to +0800)")

    merged_root = etree.Element("tv")
    channel_ids = set()

    # Add unique channels
    for root in epg_roots:
        for channel in root.xpath("//channel"):
            ch_id = channel.attrib.get("id")
            if ch_id and ch_id not in channel_ids:
                merged_root.append(deepcopy(channel))
                channel_ids.add(ch_id)

    # Filter and include programmes falling in today (UTC+8), then patch time zone string
    for root in epg_roots:
        for programme in root.xpath("//programme"):
            start = programme.attrib.get("start")
            stop = programme.attrib.get("stop")

            if start and is_today_after_offset(start):
                prog_copy = deepcopy(programme)

                # Replace +0000 with +0800 (without adjusting actual time)
                if '+0000' in start:
                    prog_copy.attrib['start'] = start.replace('+0000', '+0800')
                elif re.match(r"\d{14}$", start):
                    prog_copy.attrib['start'] = start + ' +0800'

                if stop:
                    if '+0000' in stop:
                        prog_copy.attrib['stop'] = stop.replace('+0000', '+0800')
                    elif re.match(r"\d{14}$", stop):
                        prog_copy.attrib['stop'] = stop + ' +0800'

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
        "message": "Update epg.xml with today's EPG data (timezone suffix changed to +0800)",
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
