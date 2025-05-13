import requests
from base64 import b64encode

# GitHub repo info
repo_owner = 'githubteck'
repo_name = 'test'
file_path = 'direct.text'
access_token = '${{ secrets.ABC }}'  # Use GitHub secrets in actual GitHub Actions

# M3U8 file setup
base_url = 'https://aseanic.github.io/hls/'
files = [
    '26.m3u8', '28.m3u8', '92.m3u8', '98.m3u8', '99.m3u8', '100.m3u8',
    '107.m3u8', '108.m3u8', '109.m3u8', '110.m3u8', '116.m3u8', '117.m3u8',
    '118.m3u8', '119.m3u8', '128.m3u8', '129.m3u8', '130.m3u8', '139.m3u8',
    '140.m3u8', '141.m3u8', '142.m3u8', '143.m3u8', '186.m3u8', '208.m3u8',
    '210.m3u8', '211.m3u8', '212.m3u8', '213.m3u8', '214.m3u8', '215.m3u8',
    '216.m3u8', '217.m3u8', '220.m3u8', '221.m3u8', '222.m3u8', '223.m3u8',
    '225.m3u8', '226.m3u8', '227.m3u8', '284.m3u8', '285.m3u8', '286.m3u8',
    '287.m3u8', '288.m3u8', '314.m3u8'
]

# Extract stream URLs
output_lines = []
for file in files:
    url = base_url + file
    try:
        r = requests.get(url)
        r.raise_for_status()
        lines = r.text.split('\n')
        stream_url = next((line for line in lines if line.startswith('http')), 'Not found')
    except Exception as e:
        stream_url = f'Fetch error: {e}'
    output_lines.append(f'{url} => {stream_url}')

# Save to a text file (optional local save)
with open('direct.text', 'w') as f:
    f.write('\n'.join(output_lines))

# Upload to GitHub
def upload_to_github():
    api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}'

    # Check if file already exists to get SHA
    get_resp = requests.get(api_url, headers={
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json'
    })
    sha = get_resp.json().get('sha') if get_resp.status_code == 200 else None

    data = {
        'message': 'Upload direct.text',
        'content': b64encode('\n'.join(output_lines).encode()).decode(),
        'branch': 'main'
    }
    if sha:
        data['sha'] = sha

    put_resp = requests.put(api_url, headers={
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json'
    }, json=data)

    if put_resp.status_code in [200, 201]:
        print('✅ File uploaded successfully.')
    else:
        print(f'❌ Failed to upload file: {put_resp.json()}')

upload_to_github()
