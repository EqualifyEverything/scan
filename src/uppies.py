from utils.watch import logger
from data.select import get_uppies_url_batch
from data.update import update_status_codes
import requests
from concurrent.futures import ThreadPoolExecutor


def get_status_code(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {url} - {str(e)}")
        return 999
    except UnicodeError as e:
        logger.error(f"Encoding error with URL: {url} - {str(e)}")
        return 998


def process_url(url, url_id):
    status_code = get_status_code(url)
    logger.debug(f'Status Code for {url}: {status_code}')
    return (url_id, status_code)


def main():
    batch_size = 25
    max_workers = 5

    while True:
        urls = get_uppies_url_batch(batch_size)

        if not urls:
            break

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(lambda url_id_url: process_url(*url_id_url), urls))

        update_status_codes(results)


if __name__ == "__main__":
    main()