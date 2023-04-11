
import os
import sys
import psycopg2
import json
import subprocess
import logging

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

# logger.info(f" ")

def axe_scan():
    # Define header mapping
    with open('../maps/axe.json') as f:
        header_mapping = json.load(f)

    while True:
        # Query the database for a URL to test
        cur.execute("SELECT url, id as \"url_id\" FROM staging.urls WHERE active=true AND gsa_site_scan_url_id IS NOT NULL ORDER BY Random() LIMIT 1")
        result = cur.fetchone()

        if result:
            url = result[0]
            cmd = f'axe {url} --chromedriver-path /usr/local/bin/chromedriver --chrome-options="no-sandbox" --stdout'
            try:
                output = subprocess.check_output(cmd, shell=True)
                response = json.loads(output.decode('utf-8'))
                #logger.debug(f" Response: {response} ")


                # Get top-level values to insert into the scans table
                engine_name = response.get('engine_name')
                engine_version = response.get('engine_version')
                env_orientation_angle = response.get('env_orientation_angle')
                env_orientation_type = response.get('env_orientation_type')
                env_user_agent = response.get('env_user_agent')
                env_window_height = response.get('env_window_height')
                env_window_width = response.get('env_window_width')
                reporter = response.get('reporter')
                runner_name = response.get('runner_name')
                scanned_at = response.get('scanned_at')

                # Insert top-level values into scans table
                cur.execute("""
                    INSERT INTO results.scans (
                        engine_name, engine_version, env_orientation_angle, env_orientation_type, env_user_agent,
                        env_window_height, env_window_width, reporter, runner_name, scanned_at,
                        url
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s
                    )
                """, (
                    engine_name, engine_version, env_orientation_angle, env_orientation_type, env_user_agent,
                    env_window_height, env_window_width, reporter, runner_name, scanned_at,
                    url
                ))

                # Log the completion of the scan
                logger.info(f"COMPLETE: {runner_name} scan of {url} ")

            except subprocess.CalledProcessError as e:
                # If there's an error, insert the URL into the problem_urls table
                cur.execute("""
                    INSERT INTO results.problem_urls (
                        url, scan_type, response, url_id
                    ) VALUES (
                        %s, 'axe', %s, %s
                    )
                """, (url, str(e), result[1]))
                conn.commit()

                # Log the error and continue to the next URL
                logger.error(f"{str(e)}: axe scan of {url} ")
                continue

            except Exception as e:
                # If there's an error, insert the URL into the problem_urls table
                cur.execute("""
                    INSERT INTO results.problem_urls (
                        url, scan_type, response, url_id
                    ) VALUES (
                        %s, 'axe', %s, %s
                    )
                """, (url, str(e), result[1]))
                conn.commit()

                # Log the error and continue to the next URL
                logger.error(f"{str(e)}: axe scan of {url} ")
                continue

            # Process response
            fixed_axe = fix_axe(response, header_mapping)

        else:
            # Log when there are no more URLs to test
            logger.info(f"No more URLs to test")

def fix_axe(response_dict, mapping):
            processed = {}
            try:
                for key, value in response_dict.items():
                    if isinstance(value, dict):
                        for inner_key, inner_value in value.items():
                            combined_key = f"{key}.{inner_key}"
                            new_key = mapping.get(combined_key)
                            if new_key:
                                processed[new_key] = inner_value
                            else:
                                processed[combined_key] = inner_value
                    else:
                        new_key = mapping.get(key)
                        if new_key:
                            processed[new_key] = value
                        else:
                            processed[key] = value
                logger.info(f"Axe Fixed ")
            except Exception as e:
                logger.error(f"Error fixing Axe: {str(e)}")
            return processed

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    axe_scan()



