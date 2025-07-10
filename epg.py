import requests
import os
from lxml import etree
from datetime import datetime, timezone, timedelta
import re
from copy import deepcopy

# --- GitHub Repo Info (for token/env if needed) ---
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

def parse_xmltv_datetime(time_str):
    """
    Parse XMLTV datetime string (YYYYMMDDHHMMSS ±zzzz) to datetime with tzinfo.
    """
    match = re.match(r"(\d{14})( ?)([+\-]\d{4})", time_str)
    if not match:
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
    return dt

def is_today_plus0800(time_str):
    """
    Check if the XMLTV time string falls on today's date in +0800 timezone.
    """
    dt = parse_xmltv_datetime(time_str)
    plus8 = timezone(timedelta(hours=8))
    dt_plus8 = dt.astimezone(plus8)
    today_plus8 = datetime.now(tz=plus8).date()
    return dt_plus8.date() == today_plus8

def convert_to_plus0800(time_str):
    """
    Convert XMLTV time string to +0800 timezone formatted string.
    """
    dt = parse_xmltv_datetime(time_str)
    plus8 = timezone(timedelta(hours=8))
    dt_plus8 = dt.astimezone(plus8)
    return dt_plus8.strftime("%Y%m%d%H%M%S +0800")

def filter_and_merge_today_with_plus0800(epg_roots):
    print("Merging channels and today's programmes only, converting start times to +0800")

    merged_root = etree.Element("tv")
    channel_ids = set()

    # Add all unique channels first
    for root in epg_roots:
        for channel in root.xpath("//channel"):
            ch_id = channel.attrib.get("id")
            if ch_id and ch_id not in channel_ids:
                merged_root.append(deepcopy(channel))
                channel_ids.add(ch_id)

    # Add only today's programmes (in +0800)
    for root in epg_roots:
        for programme in root.xpath("//programme"):
            start = programme.attrib.get("start")
            if start and is_today_plus0800(start):
                prog_copy = deepcopy(programme)
                prog_copy.attrib["start"] = convert_to_plus0800(start)
                merged_root.append(prog_copy)

    return etree.tostring(merged_root, pretty_print=True, encoding="utf-8", xml_declaration=True)

def save_locally(content):
    with open(target_file_path, 'wb') as f:
        f.write(content)
    print(f"Saved {target_file_path} locally.")

def main():
    roots = [fetch_epg(url) for url in epg_urls]
    merged_xml = filter_and_merge_today_with_plus0800(roots)
    save_locally(merged_xml)

if __name__ == "__main__":
    main()
