# pastauctions-vavato-scraper
A web scraper to scrape the content of some car auctions from Vavato.

## How to use it

Notes: you will need python and pipenv installed in your system.

1. Clone the repository
2. Install the dependencies with `pipenv install`
3. Run the script with `pipenv run python main.py`

Some adjustemnts:
- You should change the destination folder `save_path_prefix`
- You can filter the "categories" of auctions from the variable `allowed_auctions_roots`
- You can change the request delay in order to not be blocked because of too many requests by changing the variable `request_delay`
- In case a block happens, the seconds before retrying can be changed in the variable `retry_delay`. At every retry it gets doubled.

## What does it do

The script gets the auctions information and for each auction it gets the urls to the cars in the lots. Everything is divided into archived auctions and current/future actions. The result is an excel file with four sheets, one for the auctions and another for the car lots, for both archived and new auctions. 

In `example_result` some example files are available.

## More technical notes

The script uses normal http requests to navigate the website and get the information. This is much faster than using for example Selenium. The websites returns content that is already rendered and does not use AJAX to load the content. This makes it possible to get the content of the pages with requests.

In particular, each page has in the end a tag `<script type="application/json">` that contains the information of the page. This is the information that is used to get the number of pages and the content for each page.
