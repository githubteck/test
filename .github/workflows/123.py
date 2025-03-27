# 123.py

import requests
import base64

repo_owner = 'githubteck'  # Your GitHub username
repo_name = 'test'  # Your GitHub repository name
file_path = '123.m3u8'  # Path in the GitHub repository where the file will be uploaded
access_token = "${{ secrets.ABC }}"  # Access the token securely from GitHub Secrets

# Fetch raw data
def fetch_tv_data():
    data_url = 'https://raw.githubusercontent.com/aseanic/aseanic.github.io/refs/heads/main/tv'
    response = requests.get(data_url)
    return response.text if response.status_code == 200 else None

# Parse data
def parse_channels(data):
    """Parse the TV data and convert it to M3U8 format."""
    lines = data.split('\\n')
    channels = []

    for line in lines:
        stripped_line = line.strip()
        if stripped_line == '':
            continue  # Ignore empty lines

        # Handle #KODIPROP for authorization
        if stripped_line.startswith("#KODIPROP:inputstream.adaptive.common_headers="):
            token = stripped_line.split('=')[1]
            formatted_line = f'#EXTHTTP:{{"Authorization":"{token}"}}'
            channels.append(formatted_line)
            continue

        # Handle #KODIPROP for drm_legacy (common formats)
        elif stripped_line.startswith("#KODIPROP:inputstream.adaptive.drm_legacy="):
            parts = stripped_line.split('=')
            if len(parts) != 2:
                continue
            
            license_info = parts[1].split('|')
            license_type = license_info[0].strip()  
            license_keys = license_info[1].strip()  

            if ',' in license_keys:
                key_pairs = license_keys.split(',')
                license_key_dict = {}
                for key_pair in key_pairs:
                    key, value = key_pair.split(':')
                    license_key_dict[key.strip()] = value.strip()

                license_key_json = str(license_key_dict).replace("'", '"')
                channels.append(f'#KODIPROP:inputstream.adaptive.license_type={license_type}')
                channels.append(f'#KODIPROP:inputstream.adaptive.license_key={license_key_json}')
            else:
                channels.append(f'#KODIPROP:inputstream.adaptive.license_type={license_type}')
                channels.append(f'#KODIPROP:inputstream.adaptive.license_key={license_keys}')

            continue

        # Retain all other lines as well
        channels.append(stripped_line)

    return channels

# Upload data to GitHub
def upload_to_github(content):
    file_content = base64.b64encode(content.encode()).decode()
    api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}'
    headers = {'Authorization': f'token {access_token}'}
    response = requests.get(api_url, headers=headers)
    sha = response.json().get('sha') if response.status_code == 200 else None
    
    if sha:
        existing_content = requests.get(api_url, headers=headers).json().get('content')
        if existing_content and base64.b64decode(existing_content).decode() == content:
            print("No changes detected. Skipping upload.")
            return

    data = {'message': 'Upload channels.m3u8 file', 'content': file_content}
    if sha:
        data['sha'] = sha
    
    upload_response = requests.put(api_url, json=data, headers=headers)

    if upload_response.status_code in [200, 201]:
        print("File uploaded successfully!")
    else:
        print(f"Failed to upload file. Status Code: {upload_response.status_code}")
        print(f"Response Content: {upload_response.text}")

# Main execution
raw_data = fetch_tv_data()
if raw_data:
    channels = parse_channels(raw_data)
    m3u8_content = "\\n".join(channels)
    upload_to_github(m3u8_content)
