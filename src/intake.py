import requests
import sys
import json
import time
from utils.watch import logger
from src.data.insert import record_tech_apps


# Emoji Key:    🧰 🚚 Use as a prefix to logs

# Wappalyzer Import Functions

# Import Wapplayzer Techs from: https://github.com/wappalyzer/wappalyzer/blob/master/src/technologies

def import_tech_apps():
    logger.info(f'🧰 🚚 Importing Tech Apps')

    # List of files to import from the Wappalyzer repository
    files = ['_','a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
             'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

   # Loop through each file and import its contents
    for file in files:
        logger.debug(f'🧰 🚚 Sending request to {file}.json now')
        response = requests.get(f"https://raw.githubusercontent.com/wappalyzer/wappalyzer/master/src/technologies/{file}.json")
        logger.debug(f'🧰 🚚 Response Status Code: {response.status_code}')
        if response.status_code == 200:
            # Response was good
            # Parse the response to insert into Postgres
            data = response.json()
            for app_name, app_data in data.items():
                # Values must be in this format before sending to postgres
                name = app_name
                description = app_data.get('description')
                icon = app_data.get('icon')
                saas = app_data.get('implies') is not None
                website = app_data.get('website')
                pricing = app_data.get('pricing')
                scriptsrc = app_data.get('scriptSrc')
                headers = app_data.get('headers')
                cookies = app_data.get('cookies')
                dom = app_data.get('dom')
                implies = app_data.get("implies") if app_data.get("implies") is not None else None
                cat_implies = app_data.get("cats") if app_data.get("cats") is not None else None
                requires = app_data.get("requires") if app_data.get("requires") is not None else None
                requires_cat = app_data.get("requiresCategory") if app_data.get("requiresCategory") is not None else None
                cats = app_data.get("cats")
                js = app_data.get('js')
                meta = app_data.get('meta')

                # Properly format scriptSrc as an array containing the regex pattern
                if isinstance(scriptsrc, str):
                    scriptsrc = [scriptsrc]
                elif scriptsrc is None:
                    scriptsrc = []

                # Properly format dom as an array containing the regex pattern(s)
                if isinstance(dom, str):
                    dom = [dom]
                elif dom is None or dom == []:
                    dom = None
                else:
                    dom = dom

                # Properly format dom as an array containing the regex pattern(s)
                if isinstance(dom, str):
                    dom = [dom]
                elif dom is None or dom == []:
                    dom = None
                else:
                    dom = dom

                # Convert dictionaries to JSON strings
                headers = json.dumps(headers) if headers is not None else 'null'
                cookies = json.dumps(cookies) if cookies is not None else 'null'
                js = json.dumps(js) if js is not None else 'null'
                meta = json.dumps(meta) if meta is not None else 'null'

                #Insert each value into Postgres
                if record_tech_apps(name, description, icon, saas, website, pricing, scriptsrc, headers, cookies, dom, implies, cat_implies, js, requires, requires_cat, meta, cats):
                    logger.info(f'App Added: {name}')
                else:
                    logger.error(f'App Add Error: {name}')
                    time.sleep(.25)

        else:
            logger.error(f'Error: {response.status_code}. Please check the URL and try again.')

        # When all apps inserted from this file, move to next file
        logger.info(f'All {file}.json Apps Inserted, moving on...')

    # If all files have been processed, run this log and complete
    logger.info('All Apps & Files Processed... calling it a day... ')



if __name__ == '__main__':
    import_tech_apps()
