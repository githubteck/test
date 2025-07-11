import requests
import os
from lxml import etree
from datetime import datetime, timedelta, timezone
from base64 import b64encode
from copy import deepcopy
import re

# --- GitHub Repo Info ---
repo_owner = 'githubteck'
repo_name = 'test'
target_file_path = 'epg.xml'
access_token = os.getenv('ABC')

# --- EPG URLs with timezone set to Asia/Singapore ---
epg_urls = [
    'https://epg.pw/xmltv/epg_TW.xml?timezone=QXNpYS9TaW5nYXBvcmU%3D',
    'https://epg.pw/xmltv/epg_HK.xml?timezone=QXNpYS9TaW5nYXBvcmU%3D'
]

def fetch_epg(url):
    print(f"Fetching {url}")
    response = requests.get(url)
    response.raise_for_status()
    return etree.fromstring(response.content)

def is_today(time_str):
    """
    Check if the given EPG time string falls on today's date after converting to UTC+8.
    Example input: "20250711120000 +0800"
    """
    match = re.match(r"(\d{14})\s?([+\-]\d{4})?", time_str)
    if not match:
        return False

    dt_str = match.group(1)
    tz_str = match.group(2) or "+0000"

    # Convert timezone offset string to timedelta
    sign = 1 if tz_str[0] == '+' else -1
    hours_offset = int(tz_str[1:3])
    minutes_offset = int(tz_str[3:])
    source_offset = timezone(timedelta(hours=sign * hours_offset, minutes=sign * minutes_offset))

    # Parse datetime with source timezone
    dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S").replace(tzinfo=source_offset)

    # Convert to target timezone +0800 (Asia/Singapore)
    target_offset = timezone(timedelta(hours=8))
    dt_local = dt.astimezone(target_offset)

    # Compare only the date part
    return dt_local.date() == datetime.now(tz=target_offset).date()

def convert_to_timezone(time_str, offset_hours=8):
    """
    Convert an EPG time string to the given timezone offset (e.g., +0800).
    Returns string in same format: 'YYYYMMDDHHMMSS +0800'
    """
    match = re.match(r"(\d{14})\s?([+\-]\d{4})?", time_str)
    if not match:
        return time_str  # fallback to original if malformed

    dt_str = match.group(1)
    tz_str = match.group(2) or "+0000"

    # Parse original timezone
    sign = 1 if tz_str[0] == '+' else -1
    hours_offset = int(tz_str[1:3])
    minutes_offset = int(tz_str[3:])
    original_tz = timezone(timedelta(hours=sign * hours_offset, minutes=sign * minutes_offset))

    dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S").replace(tzinfo=original_tz)

    # Convert to target timezone
    new_tz = timezone(timedelta(hours=offset_hours))
    shifted_dt = dt.astimezone(new_tz)

    # Format back to XMLTV datetime format
    return shifted_dt.strftime("%Y%m%d%H%M%S") + f" +{offset_hours:02}00"

def filter_and_merge_today(epg_roots):
    print("Merging channels and today's programmes only (with time shift to +0800)")

    merged_root = etree.Element("tv")
    channel_ids = set()

    for root in epg_roots:
        for channel in root.xpath("//channel"):
            ch_id = channel.attrib.get("id")
            if ch_id and ch_id not in channel_ids:
                merged_root.append(deepcopy(channel))
                channel_ids.add(ch_id)

    for root in epg_roots:
        for programme in root.xpath("//programme"):
            start = programme.attrib.get("start")
            if start and is_today(start):
                prog_copy = deepcopy(programme)

                # Convert and update start time
                prog_copy.attrib['start'] = convert_to_timezone(prog_copy.attrib['start'], offset_hours=8)

                # Convert and update stop time if present
                stop = prog_copy.attrib.get("stop")
                if stop:
                    prog_copy.attrib['stop'] = convert_to_timezone(stop, offset_hours=8)

                merged_root.append(prog_copy)

    return etree.tostring(merged_root, pretty_print=True, encoding="utf-8", xml_declaration=True)

def upload_to_github(owner, repo, path, content, token):
    print(f"Uploading {path} to GitHub repo {owner}/{repo}")
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    get_resp = requests.get(api_url, headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    data = {
        "message": "Update epg.xml with today's EPG data",
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
