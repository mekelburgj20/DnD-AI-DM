# web_crawler.py
#
# This script crawls a website, extracts content from a table of contents,
# and saves the content of each linked page to a text file.
#
# Installation:
# pip install requests beautifulsoup4
#
import requests
from bs4 import BeautifulSoup
import os
import re
import time
from collections import deque

def get_page_content(url, session_cookies=None):
    """Fetches and returns the HTML content of a given URL using session cookies."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, cookies=session_cookies, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def clean_content(soup):
    """Removes common header, footer, and navigation elements from the soup."""
    # Remove known irrelevant sections like navigation and footers
    nav_header = soup.find('nav', class_='p-nav')
    if nav_header:
        nav_header.decompose()
        
    main_nav = soup.find('div', id='mega-menu-target')
    if main_nav:
        main_nav.decompose()
        
    page_header = soup.find('header', class_='page-header')
    if page_header:
        page_header.decompose()

    footer = soup.find('footer', class_='ddb-footer')
    if footer:
        footer.decompose()
        
    # Add any other specific selectors for removal here
    # For example:
    # privacy_banner = soup.find('div', id='privacy-banner')
    # if privacy_banner:
    #     privacy_banner.decompose()

    return soup

def save_content_to_file(filename, content, directory):
    """Saves the given content to a file in the specified directory."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Sanitize filename by removing invalid characters and the anchor
    filename_without_anchor = filename.split('#')[0]
    sanitized_filename = re.sub(r'[\\/*?:"<>|]',"", filename_without_anchor)
    filepath = os.path.join(directory, f"{sanitized_filename}.txt")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved content to {filepath}")

def save_raw_html(content, filename="page_source.html"):
    """Saves the raw HTML content to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved raw HTML to {filename}")

def main(toc_selector=".compendium-toc-full-text a", content_selector="section.p-article-content"):
    """
    Main function to drive the web crawling process.
    
    :param toc_selector: The CSS selector to find the table of contents links on the main page.
    :param content_selector: The CSS selector to find the main content block on content pages.
    """
    # TODO: Replace with the starting URL of the D&D Beyond content
    base_url = "https://www.dndbeyond.com/sources/dnd/basic-rules-2014"
    
    print(f"Starting crawl at: {base_url}")
    
    # To use this script with a logged-in session, you must provide your
    # browser's session cookies.
    # 1. Log in to D&D Beyond in your browser.
    # 2. Open Developer Tools (F12), go to the Network tab.
    # 3. Refresh the page, click on the main document request.
    # 4. Find the 'Cookie' header under 'Request Headers' and copy its entire value.
    # 5. Paste the cookie string into the 'cookie_string' variable below.
    
    cookie_string = "ResponsiveSwitch.DesktopMode=1; optimizelyEndUserId=oeu1762627756121r0.22598739957223613; LoginState=39de774d-4b77-494c-8c0d-dfe0e7746b27; g_state={\"i_l\":0,\"i_ll\":1762638422596}; CobaltSession=eyJhbGciOiJkaXIiLCJlbmMiOiJBMTI4Q0JDLUhTMjU2In0..0kL2qwo6wf0hPF0GWcjnbQ.Fg6DhX3OEadtxJfzXq9gK_2QvRv1RIdZD6mcg1Yft0n37dYDDku78GAMAmAmUvmS.Y7_b6r_pL0dMwuU-t3uddA; Preferences.Language=1; __stripe_mid=972a62aa-a0ad-4d35-8cf5-741e715f67c3d0944e; optimizelySession=1762888044359; NEXT_LOCALE=en; Ratings=null; Preferences.TimeZoneID=1; Geo={%22region%22:%22NV%22%2C%22country%22:%22US%22%2C%22continent%22:%22NA%22}; cookie-consent=denied; Preferences=undefined; sublevel=MASTER; RequestVerificationToken=65a4d400-5359-4a74-9ba0-d6ad07242e6c; AWSALBTG=0GU0R3HvJHC3KzzbPUGdcV3L3PAY6cstdRw3U9x1kNIHF+mXW3eN1nQkXHFhZVBQkinzW6XYNudAbeMSYVAZHJAILBMEBM7Zus6E4fevBnCRPgZ+u2kdAEEcGqinIREoMoDCxYMdBI9zRJt4FOqbpdID+OxHMoEPvZX3dh7dNix5VWuAJiQ=; AWSALBTGCORS=0GU0R3HvJHC3KzzbPUGdcV3L3PAY6cstdRw3U9x1kNIHF+mXW3eN1nQkXHFhZVBQkinzW6XYNudAbeMSYVAZHJAILBMEBM7Zus6E4fevBnCRPgZ+u2kdAEEcGqinIREoMoDCxYMdBI9zRJt4FOqbpdID+OxHMoEPvZX3dh7dNix5VWuAJiQ=; AWSALB=SQkXXhxgqiW5yW2QIV2ZO0xQ3uHssy7yb5pRZz/DbZzo9diC4nPevxuF2yOqEOGAStPhG5+FjxHa6WiDN2YuQwWQd/mEAEb/nQ2lfhejdQTx1IM7g/1PJYloOYmx; AWSALBCORS=SQkXXhxgqiW5yW2QIV2ZO0xQ3uHssy7yb5pRZz/DbZzo9diC4nPevxuF2yOqEOGAStPhG5+FjxHa6WiDN2YuQwWQd/mEAEb/nQ2lfhejdQTx1IM7g/1PJYloOYmx; WarningNotification.Lock=1"
    
    if "PASTE_YOUR_COOKIE_STRING_HERE" in cookie_string:
        print("ERROR: Please update the 'cookie_string' variable in the script with your browser's session cookies.")
        return

    # Parse the cookie string into a dictionary
    session_cookies = {c.split('=')[0].strip(): c.split('=', 1)[1].strip() for c in cookie_string.split(';')}
    
    html_content = get_page_content(base_url, session_cookies)
    
    if not html_content:
        print("Could not retrieve the main page. Exiting.")
        return

    save_raw_html(html_content)
        
    soup = BeautifulSoup(html_content, 'html.parser')

    # --- Dynamic Directory Creation ---
    # Extract the book title from the <title> tag
    page_title_full = soup.title.string if soup.title else "untitled_book"
    # Take the part before the first hyphen
    book_title = page_title_full.split(' - ')[0].strip()
    # Convert to snake_case for the directory name
    sanitized_title = re.sub(r'[^a-zA-Z0-9\s]', '', book_title).lower()
    book_directory_name = re.sub(r'\s+', '_', sanitized_title)
    
    output_directory = os.path.join("books", book_directory_name)
    print(f"Content will be saved to: {output_directory}")
    
    # This selector finds all links within the table of contents.
    # --- Get All Links from Main Page ---
    # Find the main content container of the source page
    toc_container = soup.select_one(toc_selector)
    
    if not toc_container:
        print(f"Could not find the ToC container with selector: '{toc_selector}'. Exiting.")
        return

    # Gather all valid links from the main content area
    all_links = toc_container.select('a[href]')
    
    processed_urls = set()
    crawling_queue = deque()

    for link in all_links:
        href = link.get('href')
        # We are interested in internal source/compendium links
        if href and ('/sources/' in href or '/compendium/' in href):
            full_url = href
            if not href.startswith('http'):
                full_url = "https://www.dndbeyond.com" + href

            base_url_no_anchor = full_url.split('#')[0]
            if base_url_no_anchor not in processed_urls:
                crawling_queue.append(full_url)
                processed_urls.add(base_url_no_anchor)

    if not crawling_queue:
        print("No valid content links found on the main page.")
        return
        
    print(f"Found {len(crawling_queue)} unique content links to process.")

    while crawling_queue:
        current_url = crawling_queue.popleft()

        print(f"Processing link: {current_url}")
        content_html = get_page_content(current_url, session_cookies)
        
        if content_html:
            content_soup = BeautifulSoup(content_html, 'html.parser')
            page_title = content_soup.title.string if content_soup.title else "untitled"

            # Clean the soup by removing unwanted elements
            cleaned_soup = clean_content(content_soup)

            # This selector finds the main content block on the page.
            content_block = cleaned_soup.select_one(content_selector)
            
            if content_block:
                # Extract text from the main content block
                text_content = content_block.get_text(separator='\n', strip=True)
            else:
                # Fallback to getting all text from the page
                print("Content block not found. Falling back to all page text.")
                text_content = cleaned_soup.get_text(separator='\n', strip=True)
                
            save_content_to_file(page_title, text_content, output_directory)
            
            # Be a good web citizen and don't hammer their servers
            time.sleep(3)

if __name__ == "__main__":
    # Selectors for "Xanathar's Guide to Everything"
    # This selector now directly targets the links within the ToC container.
    toc_selector = ".compendium-toc-full-text"
    content_selector = ".p-article-content.u-typography-format"
    main(toc_selector=".compendium-toc-full-text", content_selector=".p-article-content.u-typography-format")
