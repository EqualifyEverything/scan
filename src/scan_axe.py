import sys
import json
import time
from utils.watch import logger
from data.select import next_axe_url
from data.insert import scan_axe_new_event
from data.update import mark_url_axe_scanned
from utils.process import scan_axe_it, scan_axe_process
from utils.axe_scan_crack import process_items
sys.path.append(".")


# Roll the Axes
def axe_the_things():
    logger.info('Dropping the Axe')
    target, url_id = next_axe_url()
    logger.debug(f'Next URL {url_id} = {target}')

    # Run Axe Check
    result, error = scan_axe_it(target)
    # logger.debug(f'Scan_Axe: Result: {result}   ')

    # Bad Response
    if error:
        logger.debug(f"Error occurred: {error}")

    # Good Response
    else:
        # logger.debug(f"Received response: {result}")

        # Process the response
        axe_scan_output = scan_axe_process(result)

        # Rename the headers (keys) if needed
        key_mapping = {
            "old_key1": "new_key1",
            "old_key2": "new_key2",
            # Add more key mappings if needed
        }

        for key, new_key in key_mapping.items():
            if key in axe_scan_output:
                axe_scan_output[new_key] = axe_scan_output.pop(key)

        # Map Response from Processing
        scanned_at = axe_scan_output["scanned_at"]
        inapplicable = axe_scan_output["inapplicable"]
        incomplete = axe_scan_output["incomplete"]
        passes = axe_scan_output["passes"]
        violations = axe_scan_output["violations"]

        # Create the scan event
        failure = False
        axe_meta = 1
        scan_event_id = scan_axe_new_event(url_id, scanned_at, failure, axe_meta)

        # Check if scan event returns an integer ie: id
        if not isinstance(scan_event_id, int):
            logger.error(f'Scan Axe Not Int.')
        else:
            logger.debug(f'Scan Event Recorded: {scan_event_id}')

            # Process the results and trigger the functions
            result_types = ["inapplicable", "incomplete", "passes", "violations"]
            for result_type in result_types:
                results = axe_scan_output[result_type]

            logger.info("Processing completed successfully")

           # with open("data.json", "r") as f:
           #     data = json.load(f)

            processed_data = {
                "inapplicable": process_items(url_id, scan_event_id, result["inapplicable"], "inapplicable"),
                "incomplete": process_items(url_id, scan_event_id, result["incomplete"], "incomplete"),
                "passes": process_items(url_id, scan_event_id, result["passes"], "passes"),
                "violations": process_items(url_id, scan_event_id, result["violations"], "violations")
            }

            with open("processed_data.json", "w") as f:
                json.dump(processed_data, f, indent=2)

                # with open("processed_data.json", "w") as f:
                # json.dump(processed_data, f, indent=2)

            # Call the mark_url_axe_scanned function after processing is complete
            mark_url_scanned_result = mark_url_axe_scanned(url_id)

            if mark_url_scanned_result:
                logger.info("URL marked as scanned successfully")
            else:
                logger.critical("Failed to mark URL as scanned")
                time.sleep(60)


def yeet_axes():
    continue_scanning = True
    while continue_scanning:
        axe_the_things()


if __name__ == '__main__':
    yeet_axes()
