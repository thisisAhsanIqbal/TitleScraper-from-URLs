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
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure timeout and limits
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
            
            # Try to get H1 first
            h1 = soup.find('h1')
            if h1 and h1.text.strip():
                return {'URL': url, 'Title': h1.text.strip()}
            
            # If no H1 or H1 is empty, get page title
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
    
    with tqdm(total=len(urls), desc="Processing URLs") as pbar:
        for chunk in chunks:
            chunk_results = await process_url_chunk(chunk)
            results.extend(chunk_results)
            pbar.update(len(chunk))
    
    return results

def save_to_excel(df: pd.DataFrame, base_filename: str, max_attempts: int = 5) -> str:
    """Try to save DataFrame to Excel with timestamp, handling potential permission errors."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for attempt in range(max_attempts):
        try:
            if attempt == 0:
                filename = f"{base_filename}_{timestamp}.xlsx"
            else:
                filename = f"{base_filename}_{timestamp}_{attempt}.xlsx"
            
            df.to_excel(filename, index=False)
            return filename
        except PermissionError:
            if attempt == max_attempts - 1:
                raise
            continue

def main():
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Get the domain name from the first URL in the file
    with open('celebrationsathomeblog.com_post_urls.txt', 'r', encoding='utf-8') as f:
        first_url = f.readline().strip()
        domain = urlparse(first_url).netloc
        domain = domain.replace('www.', '')
    
    # Read URLs from the text file
    with open(f'{domain}_post_urls.txt', 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"\nProcessing {len(urls)} URLs using async I/O...")
    start_time = time.time()
    
    # Process URLs with async I/O
    results = asyncio.run(process_all_urls(urls))
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    try:
        # Try to save with timestamp
        excel_filename = save_to_excel(df, f"{domain}_titles")
        print(f"\nResults saved to {excel_filename}")
    except Exception as e:
        print(f"\nError saving Excel file: {str(e)}")
        # Fallback to CSV if Excel fails
        csv_filename = f"{domain}_titles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"Results saved to CSV instead: {csv_filename}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"Total URLs processed: {len(results)}")
    print(f"Processing time: {processing_time:.2f} seconds")
    print(f"Average time per URL: {processing_time/len(results):.2f} seconds")
    print(f"URLs per second: {len(results)/processing_time:.2f}")

if __name__ == "__main__":
    main() 