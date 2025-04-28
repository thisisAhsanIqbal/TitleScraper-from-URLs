import os
import pandas as pd
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tqdm import tqdm
import time
import logging
from aiohttp import ClientTimeout
from typing import List, Dict
import platform
from datetime import datetime
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Timeout and concurrency settings
TIMEOUT = ClientTimeout(total=10)
MAX_CONCURRENT_REQUESTS = 50
CHUNK_SIZE = 1000

async def get_page_title(session: aiohttp.ClientSession, url: str) -> Dict:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        async with session.get(url, headers=headers, timeout=TIMEOUT) as response:
            if response.status != 200:
                return {'URL': url, 'Title': f"Error: HTTP {response.status}"}
            
            html = await response.text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')

            h1 = soup.find('h1')
            if h1 and h1.text.strip():
                return {'URL': url, 'Title': h1.text.strip()}
            
            title = soup.find('title')
            if title and title.text.strip():
                return {'URL': url, 'Title': title.text.strip()}
            
            return {'URL': url, 'Title': "No title found"}
            
    except Exception as e:
        return {'URL': url, 'Title': f"Error: {str(e)}"}

async def process_url_chunk(urls: List[str]) -> List[Dict]:
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [get_page_title(session, url) for url in urls]
        return await asyncio.gather(*tasks)

async def process_all_urls(urls: List[str]) -> List[Dict]:
    results = []
    chunks = [urls[i:i + CHUNK_SIZE] for i in range(0, len(urls), CHUNK_SIZE)]
    
    with tqdm(total=len(urls), desc="🔎 Scraping URLs") as pbar:
        for chunk in chunks:
            chunk_results = await process_url_chunk(chunk)
            results.extend(chunk_results)
            pbar.update(len(chunk))
    
    return results

def save_to_excel(df: pd.DataFrame, output_path: str) -> str:
    """Save DataFrame to Excel with a timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_path}_{timestamp}.xlsx"
    df.to_excel(filename, index=False)
    return filename

def read_all_txt_files(folder_path: str) -> Dict[str, List[str]]:
    """Read all TXT files inside a folder and return a dictionary of {filename: [urls]}"""
    txt_files = [file for file in os.listdir(folder_path) if file.endswith('.txt')]
    all_urls = {}
    
    for txt_file in txt_files:
        file_path = os.path.join(folder_path, txt_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
            all_urls[txt_file] = urls
    
    return all_urls

def main():
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    input_folder = "output"
    output_folder = "URLTitles"

    # Check and Create output folder if not exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📂 'URLTitles' folder created.")
    else:
        print(f"📂 'URLTitles' folder already exists.")

    # Read all .txt files from input folder
    if not os.path.exists(input_folder):
        print(f"❌ 'output' folder not found. Please check.")
        return

    all_urls_dict = read_all_txt_files(input_folder)
    
    if not all_urls_dict:
        print(f"❌ No TXT files found in 'output' folder.")
        return

    print(f"✅ Found {len(all_urls_dict)} TXT files to process.\n")

    total_files = len(all_urls_dict)
    file_counter = 1

    for file_name, urls in all_urls_dict.items():
        if not urls:
            print(f"⚠️ Skipping empty file: {file_name}")
            continue
        
        print(f"\n📄 Working on file {file_counter}/{total_files}: {file_name}")
        print(f"🔢 Total URLs in file: {len(urls)}")

        start_time = time.time()

        # Process URLs
        results = asyncio.run(process_all_urls(urls))

        # Save to Excel
        domain_part = file_name.replace('.txt', '')
        save_path = os.path.join(output_folder, domain_part)
        df = pd.DataFrame(results)

        try:
            excel_filename = save_to_excel(df, save_path)
            print(f"✅ Titles saved to: {excel_filename}")
        except Exception as e:
            print(f"❌ Error saving Excel file: {str(e)}")
        
        end_time = time.time()
        processing_time = end_time - start_time

        print(f"⏱️ Processing time for this file: {processing_time:.2f} seconds")
        print(f"✅ URLs processed: {len(results)}")

        file_counter += 1

    print(f"\n🎉 All files processed successfully!")

if __name__ == "__main__":
    main()
