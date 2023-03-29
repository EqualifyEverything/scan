import os
import sys
import psycopg2
import json
import requests
import logging
import time
import uuid

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler and set level to debug
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Add formatter to console handler
ch.setFormatter(formatter)

# Add console handler to logger
logger.addHandler(ch)

# Postgre connection info
db_host = "localhost"
db_port = 8432
db_user = "a11yPython"
db_password = "SnakeInTheWeb"
db_name = "a11y"

# Connect to database
try:
    conn = psycopg2.connect(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
    cur = conn.cursor()
    logger.info(f"Connected to database.")
except psycopg2.Error as e:
    logger.error(f"Could not connect to database: {e}")
    sys.exit(1)

def axe_scan():
    while True:
        # Query the database for a URL to test
        cur.execute("SELECT url, id as \"url_id\" FROM staging.urls WHERE active=true AND NOT scanned_by_axe ORDER BY created_at DESC LIMIT 1")
        result = cur.fetchone()

        if result:
            url = result[0]
            logger.debug(f"URL: {url}")

            # Send GET request to localhost:8083/axe/url={url}
            response = requests.get(f"http://localhost:8083/axe?url={url}")
            if response.status_code != 200:
                # If there's an error, insert the URL into the problem_urls table
                cur.execute("""
                    INSERT INTO results.problem_urls (
                        url, scan_type, status_code, url_id
                    ) VALUES (
                        %s, 'axe', %s, %s
                    )
                """, (url, str(response), result[1]))
                conn.commit()

                cur.execute("""
                    UPDATE staging.urls
                    SET scanned_by_axe = TRUE, axe_scanned_at = NOW()
                    WHERE id = %s
                """, (result[1],))
                conn.commit()


                # Log the error and continue to the next URL
                logger.error(f"{str(response)}: axe scan of {url} ")

            # Good Response from Axe
            if response.status_code == 200:
                # Parse the JSON response into a dictionary
                response_data = json.loads(response.text)

                # Extract the desired fields from the response data
                engine_name = response_data["engine_name"]
                engine_version = response_data["engine_version"]
                env_orientation_angle = response_data["env_orientation_angle"]
                env_orientation_type = response_data["env_orientation_type"]
                env_user_agent = response_data["env_user_agent"]
                env_window_height = response_data["env_window_height"]
                env_window_width = response_data["env_window_width"]
                reporter = response_data["reporter"]
                runner_name = response_data["runner_name"]
                scanned_at = response_data["scanned_at"]
                url = response_data["url"]

                # Generate pyaxe_uuid UUID
                pyaxe_uuid = str(uuid.uuid4())

                # Insert the extracted data into the scans table
                cur.execute("""
                    INSERT INTO results.scans (
                        engine_name, engine_version, env_orientation_angle,
                        env_orientation_type, env_user_agent, env_window_height,
                        env_window_width, reporter, runner_name, scanned_at, url, url_id, pyaxe_uuid
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (engine_name, engine_version, env_orientation_angle, env_orientation_type,
                      env_user_agent, env_window_height, env_window_width, reporter,
                      runner_name, scanned_at, url, result[1], pyaxe_uuid))
                conn.commit()

                # Insert items into the items table
                items = ["inapplicable", "incomplete", "passes", "violations"]
                for item in items:
                    for sub_item in response_data[item]:
                        # Generate piwho_uuid UUID
                        piwho_uuid = str(uuid.uuid4())

                        # Insert item data into the results.items table
                        cur.execute("""
                            INSERT INTO results.items (
                                "type", description, help, help_url, area, impact, tags, pyaxe_uuid, piwho_uuid
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (item, sub_item["description"], sub_item["help"], sub_item["helpUrl"], sub_item["id"], sub_item["impact"], sub_item["tags"], pyaxe_uuid, piwho_uuid))
                        conn.commit()

                        # If the sub_item has nodes data, insert it into the results.nodes table
                        if sub_item["nodes"]:
                            for node in sub_item["nodes"]:
                                logger.debug(f"Node target: {node.get('target')} ")
                                logger.debug(f"Node All: {node.get('any')} ")
                                logger.debug(f"Node All: {node.get('all')} ")
                                logger.debug(f"Node None: {node.get('none')} ")
                                target = node.get("target")
                                if target:
                                    target_str = str(target[0])
                                else:
                                    target_str = None

                                # Flatten the nested dictionary in 'data'
                                data_str = None
                                if node.get("data"):
                                    data_str = json.dumps(node.get("data"))

                                # Insert the node into the results.nodes table
                                cur.execute("""
                                    INSERT INTO results.nodes (
                                        html, impact, target, data, pyaxe_uuid, piwho_uuid
                                    ) VALUES (
                                        %s, %s, %s, %s, %s, %s
                                    )
                                """, (node.get("html"), node.get("impact"), target_str, data_str, pyaxe_uuid, piwho_uuid))
                                conn.commit()

                                # Insert the subnode into the results.subnodes table, if any
                                for node_type in ["any", "all", "none"]:
                                    subnodes = node.get(node_type)
                                    if subnodes:
                                        for subnode in subnodes:
                                            subnode_data_str = None
                                            if subnode.get("data"):
                                                subnode_data_str = json.dumps(subnode.get("data"))
                                            cur.execute("""
                                                INSERT INTO results.subnodes (
                                                    nodey_uuid, data, id, impact, message, pyaxe_uuid, piwho_uuid, node_type
                                                ) VALUES (
                                                    %s, %s, %s, %s, %s, %s, %s, %s
                                                )
                                            """, (str(uuid.uuid4()), subnode_data_str, subnode.get("id"), subnode.get("impact"), subnode.get("message"), pyaxe_uuid, piwho_uuid, node_type))
                                            conn.commit()





                logger.info(f"COMPLETE: axe scan of {url} ")
                cur.execute("""
                    UPDATE staging.urls
                    SET scanned_by_axe = TRUE, axe_scanned_at = NOW()
                    WHERE id = %s
                """, (result[1],))
                conn.commit()



        else:
            # Log when there are no more URLs to test
            logger.info(f"No more URLs to test")

        time.sleep(1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    axe_scan()

