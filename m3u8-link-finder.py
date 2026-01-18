from selenium import webdriver
import re

TARGET_URL = "https://www.mana2.my/channel/live/suke-tv"

def find_m3u8_link():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    driver.get(TARGET_URL)
    content = driver.page_source

    # Regex pattern to find m3u8 URLs
    pattern = r"https://live\.mana2\.my/[^'\" ]+\.m3u8\?[^'\" ]+"
    matches = re.findall(pattern, content)

    if matches:
        print("Found m3u8 link(s):")
        for link in matches:
            print(link)
    else:
        print("No m3u8 link found in the page source.")

    driver.quit()

if __name__ == "__main__":
    find_m3u8_link()
