import os
import sys
import psycopg2
import json
import requests
import logging
import time
import uuid

# Set up logger: "A11yLogger"
logger = logging.getLogger("A11y🪵 ")

logger.setLevel(logging.DEBUG)

# Check if logger already has handlers
if not logger.handlers:
    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
    ch.setFormatter(formatter)

    # Add the console handler to the logger
    logger.addHandler(ch)

# Test the logger
logger.debug("🐛 Debug Test Message")
logger.info("📣ℹ️ Info Test Message")
logger.warning("⚠️ Warning Test Message")
logger.error("❌ Error Test Message")

# Tell everyone who we are
# Turn this off if annoying
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../refs/caequalify.txt")
with open(file_path, "r") as f:
    file_contents = f.read()
print(file_contents)

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
    logger.info(f"🗄️ Connected to database.")
except psycopg2.Error as e:
    logger.error(f"🗄️ Could not connect to database: {e}")
    sys.exit(1)

def axe_scan():
    # Define the maximum number of retries.
    retries = 0 # No, changing this is not a good idea. no touchy
    max_retries = 3 # how many times do you want to try and make this work?

    # Keep trying to connect to the Axe endpoint until the maximum number of retries is reached
    while retries < max_retries:
        try:
            # Query staging.urls for a URL to test
            cur.execute("SELECT url, id as \"url_id\" FROM staging.urls WHERE active=true AND NOT scanned_by_axe ORDER BY RANDOM() LIMIT 1")
            result = cur.fetchone()

            # If there is a URL to test, run the Axe scan
            if result:
                url = result[0]
                logger.debug(f"🪓 URL from 🗄️: {url}") # Let's log the yay!

                logger.info(f"🪓 🧐: {url} ") # Another Yay! to log
                # Send GET request to AxeEndpoint /axe/url={url}
                response = requests.get(f"http://localhost:8083/axe?url={url}") # to-do: make docker var for axe backend

                # If the response status code is not 200, log the error and update the database
                if response.status_code != 200: # If it isn't 200, I don't want it
                    # If there's an error, insert the URL into the rproblem_urls table
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
                    logger.error(f"🪓 ❌ {str(response)}: axe scan of {url} ")

            # Reset the number of retries
            retries = 0

        # If there is a connection error with the Axe endpoint, log a warning and retry after 10 seconds
        except requests.exceptions.ConnectionError:
            logger.warning("💔🪓 endpoint 🔌 disconnected, 🔁retrying in 10 seconds... ⏳")
            time.sleep(10)
            retries += 1

            # If the maximum number of retries is reached without a successful connection, log an error and shut down
            if retries == max_retries:
                logger.error(f"💔🪓 Endpoint disconnected after {max_retries} attempts, 💣 shutting down.")

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


                cur.execute("""
                    UPDATE staging.urls
                    SET scanned_by_axe = TRUE, axe_scanned_at = NOW()
                    WHERE id = %s
                """, (result[1],))
                conn.commit()
            # Send Yay Message about Logging and such!
            logger.info(f"🪓 ✅: {url} ")


        else:
            # Log when there are no more URLs to test
            logger.info(f"🏁🏁🏁 No more URLs to test 🏁🏁🏁")

        time.sleep(1)

if __name__ == '__main__':
    axe_scan()

