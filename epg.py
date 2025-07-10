import requests
from base64 import b64encode
import os
from lxml import etree

# --- GitHub Repo Info ---
repo_owner = 'githubteck'
repo_name = 'test'
target_file_path = 'epg.xml'       # ✅ GitHub filename
access_token = os.getenv('ABC')    # ✅ GitHub token in environment

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

def filter_and_merge(epg_roots, timezone='+0800'):
    print(f"Filtering by timezone: {timezone}")
    merged_root = etree.Element("tv")

    channel_ids = set()
    for root in epg_roots:
        # Add unique channels
        for channel in root.xpath("//channel"):
            ch_id = channel.attrib.get("id")
            if ch_id and ch_id not in channel_ids:
                merged_root.append(channel)
                channel_ids.add(ch_id)

        # Filter programmes by timezone
        for programme in root.xpath("//programme"):
            start = programme.attrib.get("start", "")
            if timezone in start:
                merged_root.append(programme)

    return etree.tostring(merged_root, pretty_print=True, encoding="utf-8", xml_declaration=True)

def upload_to_github(owner, repo, path, content, token):
    print(f"Uploading {path} to GitHub repo {owner}/{repo}")
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    # Check if file exists to get SHA
    get_resp = requests.get(api_url, headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    data = {
        "message": "Update epg.xml with +0800 filtered programmes",
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
    merged_xml = filter_and_merge(roots, '+0800')
    upload_to_github(repo_owner, repo_name, target_file_path, merged_xml, access_token)

if __name__ == "__main__":
    main()
