import requests
from bs4 import BeautifulSoup

def fetch_data(url):
    """Fetches data from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def parse_channel_list(data):
    """Parses the channel list data."""
    channels = []
    lines = data.strip().split('\n')
    current_genre = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '#genre#' in line:
            current_genre = line.split(',')[0] if ',' in line else line.replace('#genre#', '').strip()
        elif ',' in line:
            parts = line.split(',', 1)
            if len(parts) == 2:
                channel_name = parts[0].strip()
                stream_url = parts[1].strip()
                channels.append({
                    'name': channel_name,
                    'stream_url': stream_url,
                    'genre': current_genre
                })
    return channels

def parse_logo_data(html_content):
    """Parses the guide.html content to extract logo URLs."""
    logo_map = {}
    soup = BeautifulSoup(html_content, 'html.parser')
    try:
        table = soup.find('table')
        if not table:
            print("Warning: Could not find the table in guide.html.")
            return logo_map

        rows = table.find_all('tr')[1:] # Skip the header row

        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                # Assuming the structure is consistent: ID, Name, Logo URL
                channel_id_cell = cells[0]
                channel_name_cell = cells[1]
                logo_url_cell = cells[2]

                channel_id = channel_id_cell.get_text(strip=True)
                channel_name = channel_name_cell.get_text(strip=True)

                # Extract the logo URL, handling potential <code> tags
                logo_url_tag = logo_url_cell.find('code')
                if logo_url_tag:
                    logo_url = logo_url_tag.get_text(strip=True).strip('`')
                else:
                    logo_url = logo_url_cell.get_text(strip=True)

                # Store the logo URL mapped by both ID and Name for better matching
                if channel_id and logo_url:
                    logo_map[channel_id] = logo_url
                if channel_name and logo_url:
                    logo_map[channel_name] = logo_url

    except Exception as e:
        print(f"Error parsing guide.html: {e}")

    return logo_map

def generate_m3u8(channels, logo_map, epg_urls):
    """Generates the M3U8 playlist content."""
    m3u8_content = "#EXTM3U"

    # Add EPG URLs to the header
    for epg_url in epg_urls:
        m3u8_content += f' url-tvg="{epg_url}"'
    m3u8_content += "\n"

    for channel in channels:
        channel_name = channel['name']
        stream_url = channel['stream_url']
        genre = channel['genre']

        # Try to find the logo using the channel name or ID from the logo map
        logo_url = logo_map.get(channel_name) # Prioritize matching by name

        # Construct the #EXTINF line with attributes
        extinf_line = f'#EXTINF:-1'
        if genre:
             extinf_line += f' group-title="{genre}"'
        # Include tvg-id and tvg-name for better compatibility with some players
        extinf_line += f' tvg-id="{channel_name}" tvg-name="{channel_name}"'

        if logo_url:
            extinf_line += f' tvg-logo="{logo_url}"'
        extinf_line += f',{channel_name}\n' # Display name after the comma

        m3u8_content += extinf_line
        m3u8_content += f'{stream_url}\n' # The stream URL on the next line

    return m3u8_content

# --- Main Execution ---

# URLs for the channel list, logo guide, and EPG
channel_list_url = "https://raw.githubusercontent.com/ssili126/tv/refs/heads/main/itvlist.txt"
logo_guide_url = "https://assets.livednow.com/guide.html"
epg_urls = [
    "https://epg.112114.xyz/pp.xml",
    "https://raw.githubusercontent.com/sparkssssssssss/epg/main/pp.xml",
    "https://epg.112114.xyz/pp.xml.gz",
    "https://raw.githubusercontent.com/sparkssssssssss/sparkssssssssss/main/pp.xml.gz"
]

# 1. Fetch Channel List Data
print(f"Fetching channel list from: {channel_list_url}")
channel_list_data = fetch_data(channel_list_url)
if not channel_list_data:
    print("Could not fetch channel list. Exiting.")
    exit()

# 2. Parse Channel List Data
print("Parsing channel list...")
channels = parse_channel_list(channel_list_data)
print(f"Found {len(channels)} channels.")

# 3. Fetch Logo Information
print(f"Fetching logo guide from: {logo_guide_url}")
logo_html_data = fetch_data(logo_guide_url)
logo_map = {}
if logo_html_data:
    print("Parsing logo guide...")
    logo_map = parse_logo_data(logo_html_data)
    print(f"Found {len(logo_map)} logo entries.")
else:
    print("Could not fetch logo guide. Logos will not be included in the playlist.")

# 4. Generate M3U8 Playlist Content
print("Generating M3U8 playlist...")
m3u8_playlist = generate_m3u8(channels, logo_map, epg_urls)

# 5. Output the M3U8 Playlist
print("\n--- Generated M3U8 Playlist ---")
print(m3u8_playlist)

# 6. Optionally, save the playlist to a file
try:
    file_name = "playlist.m3u8"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(m3u8_playlist)
    print(f"\nPlaylist successfully saved to {file_name}")
except IOError as e:
    print(f"Error saving playlist to file {file_name}: {e}")
