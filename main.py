import pandas as pd
import re
from datetime import datetime
import json
import requests
from enum import Enum
import math
import time

# Specify the folder of where the output will be saved
save_path_prefix = '/home/euberdeveloper/Github/pastauctions/scrapers/pastauctions-vavato-scraper'
# The baseurl of the website
base_url = 'https://vavato.com'
# The allowed prefixes for the auction URLs
allowed_auctions_roots = [
    'https://vavato.com/en/a/car-transport',
    'https://vavato.com/en/a/classic-cars',
    'https://vavato.com/en/a/auto%27s-transport',
    'https://vavato.com/en/a/motorbikes',
    'https://vavato.com/en/a/automobile-transport',
    'https://vavato.com/en/a/golf-carts',
    'https://vavato.com/en/a/recent-cars',
    'https://vavato.com/en/a/fire-brigade',
    'https://vavato.com/en/a/super-cars',
    'https://vavato.com/en/a/new-motorcycles',
    'https://vavato.com/en/a/motorcycle',
    'https://vavato.com/en/a/agricultural-and-earthmoving-machiner'
]
# Specify delay in milliseconds for requests in order to not be blocked
request_delay = 300
# Specify initial retry delay in milliseconds
retry_delay = 1000

# Enum with the possible statuses
class Statuses(Enum):
    OPEN = "BIDDING_OPEN"
    FUTURE = "BIDDING_NOT_YET_OPENED"
    CLOSED = "BIDDING_CLOSED"

    def __str__(self):
        return self.value
    
# Function to get the status query string from array of statuses
def get_status_query_string(statuses):
    return '%2C'.join([str(status) for status in statuses])

# Function to get the HTML from a URL
def get_html_from_url(url, max_retries=5):
    global request_delay
    global retry_delay
    time.sleep(request_delay / 1000)

    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to get HTML from {url}")
        return ''
    
    text = response.text
    if 'The request is blocked' in text:
        print(f"Request was blocked for {url}")
        if max_retries == 0:
            raise Exception(f"Max html fetch retries reached for {url}")
        else:
            print(f"Retrying in {request_delay}ms")
            time.sleep(retry_delay / 1000)
            retry_delay *= 2
            return get_html_from_url(url, max_retries - 1)

    return text

# Function to get the string between two strings
def get_string_between(string, start, end):
    return string.split(start)[1].split(end)[0]

# Function to convert seconds to date
def from_seconds_to_date(seconds: int):
    return datetime.fromtimestamp(seconds).strftime('%d %B %Y')

# Filter the auction URLs to only include the allowed roots
def filter_auction_by_urls(auctions):
    global allowed_auctions_roots
    return [
        auction
        for auction in auctions
        if any(
            auction['Url'].startswith(root)
            for root in allowed_auctions_roots
        )
    ]

def get_auctions_json_from_html(html):
    json_text = get_string_between(html, 'type="application/json">', '</script>')
    json_data = json.loads(json_text)
    return json_data['props']['pageProps']['auctionList']

def get_lots_json_from_html(html):
    json_text = get_string_between(html, 'type="application/json">', '</script>')
    json_data = json.loads(json_text)
    return json_data['props']['pageProps']['lots']

def get_number_of_pages_from_auctions_json(auctions_json):
    auctions_per_page = len(auctions_json['results'])
    total_auctions = int(auctions_json['totalSize'])
    return math.ceil(total_auctions / auctions_per_page)

def get_number_of_pages_from_lots_json(lots_json):
    lots_per_page = int(lots_json['pageSize'])
    total_lots = int(lots_json['totalSize'])
    return math.ceil(total_lots / lots_per_page)

def scrape_auctions_from_page(auctions_url, page):
    try:
        url = f"{auctions_url}&page={page}"
        html = get_html_from_url(url)
        auctions_json = get_auctions_json_from_html(html)
        auctions_data = auctions_json['results']
        auctions = filter_auction_by_urls([
            {
                'Maison': 'Vavato',
                'Name': auction['name'],
                'Start_date': from_seconds_to_date(auction['startDate']),
                'End_date': from_seconds_to_date(auction['endDate']),
                'Location': ','.join([
                    location['city']
                    for location in auction['collectionDays']
                ]),
                'Url': f'{base_url}/en/a/{auction["urlSlug"]}'
            }
            for auction in auctions_data
        ])
        print(f"Scraped {len(auctions)} auctions from page {page}")
        return auctions
    except Exception as e:
        print(f"Failed to scrape page {page}")
        print(str(e))
        return []
    
def scrape_lots_from_page(auction_url, page):
    try:
        url = f"{auction_url}?page={page}"
        html = get_html_from_url(url)
        lots_json = get_lots_json_from_html(html)
        lots_data = lots_json['results']
        lots = [
            {
                'Event URL': auction_url,
                'Vehicle URL': f'{base_url}/en/l/{lot["urlSlug"]}',
            }
            for lot in lots_data
        ]
        print(f"Scraped {len(lots)} lots from page {page}")
        return lots
    except Exception as e:
        print(f"Failed to scrape page {page}")
        print(str(e))
        return []


def scrape_auctions(statuses: list[Statuses]):
    print(f"Scraping auctions with statuses {statuses}")
    status_query_string = get_status_query_string(statuses)
    url = f"{base_url}/en/auctions?auctionBiddingStatuses={status_query_string}"
    print(f"Getting number of pages")
    html = get_html_from_url(url)
    auctions_json = get_auctions_json_from_html(html)
    number_of_pages = get_number_of_pages_from_auctions_json(auctions_json)
    print(f"Number of pages: {number_of_pages}")
    auctions = []
    for page in range(1, number_of_pages + 1):
        print(f"Scraping page {page} of {number_of_pages}")
        auctions.extend(scrape_auctions_from_page(url, page))
    print(f"Scraped {len(auctions)} auctions with statuses {statuses}")
    return auctions

def scrape_lots_of_auction(auction_url: str):
    print(f"Scraping lots of auction {auction_url}")
    html = get_html_from_url(auction_url)
    lots_json = get_lots_json_from_html(html)
    number_of_pages = get_number_of_pages_from_lots_json(lots_json)
    lots = []
    for page in range(1, number_of_pages + 1):
        print(f"Scraping page {page} of {number_of_pages}")
        lots.extend(scrape_lots_from_page(auction_url, page))
    print(f"Scraped {len(lots)} lots of auction {auction_url}")
    return lots

def scrape_lots_of_auctions(auctions: list[dict]):
    print(f"Scraping lots of {len(auctions)} auctions")
    lots = []
    for auction in auctions:
        lots.extend(scrape_lots_of_auction(auction['Url']))
    print(f"Scraped {len(lots)} lots of {len(auctions)} auctions")
    return lots

def save_worksheet_to_excel(writer, data: list[dict], sheet_name: str):
    if data:
        df = pd.DataFrame(data)
        df.to_excel(writer, index=False, sheet_name=sheet_name)

def save_to_excel(open_auctions, closed_auctions, open_auctions_lots, closed_auctions_lots, file_path):
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        save_worksheet_to_excel(writer, open_auctions, 'OpenAuctions')
        save_worksheet_to_excel(writer, closed_auctions, 'ClosedAuctions')
        save_worksheet_to_excel(writer, open_auctions_lots, 'OpenAuctionLots')
        save_worksheet_to_excel(writer, closed_auctions_lots, 'ClosedAuctionLots')

def get_output_path():
    global save_path_prefix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = save_path_prefix + f'/UpcomingAuction_{timestamp}.xlsx'
    return save_path
        
def main():
    open_auctions = scrape_auctions([Statuses.OPEN, Statuses.FUTURE])
    closed_auctions = scrape_auctions([Statuses.CLOSED])
    open_auctions_lots = scrape_lots_of_auctions(open_auctions)
    closed_auctions_lots = scrape_lots_of_auctions(closed_auctions)
    save_to_excel(open_auctions, closed_auctions, open_auctions_lots, closed_auctions_lots, get_output_path())

if __name__ == "__main__":
    main()
