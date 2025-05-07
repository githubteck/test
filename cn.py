import requests
import base64
import os

# Replace with your repository details
repo_owner = 'githubteck'
repo_name = 'test'
file_path = 'cn.m3u8'

# Get the GitHub Token from environment variables set by GitHub Actions
# Make sure to pass this as an environment variable in your workflow
access_token = os.environ.get('GITHUB_TOKEN')

def generate_m3u8_content():
    # Your existing logic to generate the M3U8 content goes here
    # For example:
    content = "#EXTM3U\n"
    content += "#EXTINF:-1,Example Channel 1\n"
    content += "http://example.com/stream1.m3u8\n"
    content += "#EXTINF:-1,Example Channel 2\n"
    content += "http://example.com/stream2.m3u8\n"
    return content

def upload_to_github(content):
    """
    Uploads or updates the cn.m3u8 file on GitHub.
    Checks if the file exists and uses the SHA for updates.
    """
    file_content_base64 = base64.b64encode(content.encode()).decode()
    api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}'
    headers = {'Authorization': f'token {access_token}'}

    # 1. Check if the file exists to get the current SHA
    response = requests.get(api_url, headers=headers)
    sha = None
    if response.status_code == 200:
        # File exists, get the SHA for updating
        sha = response.json()['sha']
        print(f"File exists on GitHub. Current SHA: {sha}")
    elif response.status_code == 404:
        # File does not exist, we'll create it
        print("File does not exist on GitHub. Will create it.")
    else:
        # Handle other potential errors during the GET request
        print(f"Error checking file status: {response.status_code} - {response.text}")
        response.raise_for_status() # Raise an exception for bad status codes

    # 2. Prepare the payload for PUT request
    payload = {
        "message": "Update cn.m3u8" if sha else "Create cn.m3u8",
        "content": file_content_base64,
    }
    if sha:
        # Add the SHA if we are updating an existing file
        payload["sha"] = sha

    # 3. Send the PUT request to create or update the file
    put_response = requests.put(api_url, headers=headers, json=payload)

    if put_response.status_code in [200, 201]:
        action = "Updated" if sha else "Created"
        print(f"File {action} successfully on GitHub.")
    else:
        print(f"Error {action.lower()}ing file on GitHub: {put_response.status_code} - {put_response.text}")
        put_response.raise_for_status() # Raise an exception for bad status codes

if __name__ == "__main__":
    m3u8_content = generate_m3u8_content()
    upload_to_github(m3u8_content)
