import sys
import json
from utils.watch import logger
from data.select import next_axe_url
from data.insert import scan_axe_new_event, record_axe_scan_results
from utils.process import scan_axe_it, scan_axe_process
from utils.axe_scan_crack import process_items
sys.path.append(".")

# Emoji Key:


# Roll the Axes
def axe_the_things():
    logger.info('Dropping the Axe')
    target, url_id = next_axe_url()
    logger.debug(f'Next URL {url_id} = {target}')

    # Run Axe Check
    result, error = scan_axe_it(target)

    # Bad Response
    if error:
        logger.debug(f"Error occurred: {error}")
    # Run scan_axe_failure(url_id) if this fails and then move on

    # Good Response
    else:
        logger.debug(f"Received response: {result}")

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

        # Map the URL ID ...
        url_id = url_id

        # Vars are mapped :)

        # Create the scan event
        # if response returned an error, set failure = true, else, False
        failure = False
        axe_meta = 1
        scan_event_id = scan_axe_new_event(url_id, failure, axe_meta)

        # Check if scan event returns an integer ie: id
        if not isinstance(scan_event_id, int):
            # Log the error...
            logger.error(f'Scan Axe Not Int.')
            # Sad :(

        else:
            logger.debug(f'Scan Event Recorded: {scan_event_id}')




            # Process the results and trigger the functions
            result_types = ["inapplicable", "incomplete", "passes", "violations"]
            for result_type in result_types:
                results = axe_scan_output[result_type]
                insert_axe_items(result_type, results)
                insert_axe_nodes(result_type, results)
                insert_axe_subnodes(result_type, results)

            logger.info("Processing completed successfully")


    with open("data.json", "r") as f:
        data = json.load(f)

    processed_data = {
        "inapplicable": process_items(data["inapplicable"], "inapplicable"),
        "incomplete": process_items(data["incomplete"], "incomplete"),
        "passes": process_items(data["passes"], "passes"),
        "violations": process_items(data["violations"], "violations")
    }

    with open("processed_data.json", "w") as f:
        json.dump(processed_data, f, indent=2)

