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
logger.setLevel(logging.DEBUG)

# Create console handler and set level to debug
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)

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

