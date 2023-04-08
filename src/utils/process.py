import requests
import json
from utils.watch import logger
from data.update import tech_check_failure  # Add this import

def run_tech_check(target, url_id):
    # Run Tech Check
    logger.debug(f'Running tech check for URL ID: {url_id} and target: {target}')
    response = requests.get(f"https://techcheck.beltway.cloud/extract?url={target}")
    # logger.debug(f'From Process: {response} ')

    if response.status_code == 200:
        logger.debug(f'From Process: {response.json()} ')
        # Parse the results
        data = response.json()
        applications = data.get('applications', [])
        logger.debug(f'From Process: Applications: {applications}')

        # Extract desired fields
        tech_apps = []
        for app in applications:
            app_data = {
                'name': app.get('name'),
                'confidence': app.get('confidence'),
                'version': app.get('version')
            }
            tech_apps.append(app_data)
            logger.debug(f'From Process: App data: {app_data}')

        # Return tech_apps
        logger.debug(f'From Process: Tech apps: {tech_apps}')
        return tech_apps

    else:
        logger.error(f'Error: {response.status_code}. Please check the URL and try again.')
        # Call tech_check_failure and log the result
        result = tech_check_failure(url_id)
        if result:
            logger.info(f'Good failure mark for URL ID: {url_id}')
        else:
            logger.error(f'Bad failure mark for URL ID: {url_id}')
        return False

def scan_axe_it(target):
    logger.debug(f'Starting Axe Check of: {target}')

    # Send Request to Axe
    response = requests.get(f"https://axe-check.beltway.cloud/axe?url={target}")

    # Check response status code
    if response.status_code == 200:
     #  logger.debug(f'From Process: {response.json()} ')
        # Return the response and no error
        return response.json(), None

    else:
        # Log error
        error_msg = f"Error: Received status code {response.status_code} for target {target}"
        logger.error(error_msg)
        # Return None and the error message
        return None, error_msg

def scan_axe_process(response):
    # Select only a few fields from response
    scanned_at = response["scanned_at"]
    inapplicable = response["inapplicable"]
    incomplete = response["incomplete"]
    passes = response["passes"]
    violations = response["violations"]

    return {
        "scanned_at": scanned_at,
        "inapplicable": inapplicable,
        "incomplete": incomplete,
        "passes": passes,
        "violations": violations
    }
























