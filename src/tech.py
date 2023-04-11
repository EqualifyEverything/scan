import sys
import requests
import json
import time
from utils.watch import logger
from data.select import next_tech_url
from data.update import tech_mark_url
from data.insert import add_tech_results
from utils.process import run_tech_check
from multiprocessing import Process

sys.path.append(".")

def check_tech_main():
    # Get the next URL
    logger.debug('Getting Next Tech URL')
    target, url_id = next_tech_url()
    logger.debug(f'Next URL = {target}')

    # Run Tech Check
    response = run_tech_check(target, url_id)
    if response == False:
        logger.error('From Tech: Bad Check :( ... ')
    else:
        tech_apps = response
        # Record Results
        if add_tech_results(url_id, tech_apps):
            logger.info('From Tech: Good Update... ')
            if tech_mark_url(url_id):
                logger.debug('Marked G2G... ROLL IT...')
                # If true, lets go again!
                # If false, log an error
            # Wait for a few seconds before the next iteration
           # time.sleep(.25)

        # Update staging.urls with Tech Info
        else:
            logger.info('From Tech: Bad pdate... ')
            # Wait for 5 seconds before the next iteration
            time.sleep(0)

def run_check_tech_main():
    # Run Tech Check
    while True:
        check_tech_main()

if __name__ == '__main__':
    num_processes = 30
    processes = []

    # Spawn multiple processes
    for i in range(num_processes):
        process = Process(target=run_check_tech_main)
        processes.append(process)
        process.start()

    # Wait for all processes to finish
    for process in processes:
        process.join()
