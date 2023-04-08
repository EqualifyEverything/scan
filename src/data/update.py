import psycopg2
import json
from datetime import datetime, timezone
from utils.watch import logger
from data.access import connection

# Log Emoji: 🗄️_🔧

def execute_update(query, params=None, fetchone=True):
 #  logger.debug(f'🗄️   🔧 Executing query: {query}')
   logger.debug(f'🗄️   🔧 Query parameters: {params}... ')

   # Connect to the database
   conn = connection()
   conn.open()
   logger.debug(f'🗄️   🔧 Database connection opened')

   # Create a cursor
   cur = conn.conn.cursor()

   try:
      # Execute the query
      cur.execute(query, params)
      conn.conn.commit()
      logger.info(f'🗄️   🔧 Query executed and committed')

      # Fetch the results if requested
      result = None
      if fetchone:
            result = cur.fetchone() or ()  # return an empty tuple if None is returned
      else:
            result = cur.fetchall() or []  # return an empty list if None is returned
            logger.debug(f'🗄️   🔧 Fetched results: {result}')
   except Exception as e:
      #  logger.error(f'🗄️   🔧 Error executing update query: {e}')
        result = None

   # Close the cursor and connection
   cur.close()
   conn.close()
   logger.debug(f'🗄️   🔧 Cursor and connection closed')

   return result


def add_tech_results(url_id, tech_apps):
    logger.info(f'🗄️   🔧 Adding Tech Results')
    query = """
        UPDATE staging.urls
        set techs = %s,
           tech_checked_at = %s
        WHERE id = %s
    """
    try:
        execute_update(query, (json.dumps(tech_apps), datetime.now(timezone.utc), url_id))
        logger.debug(f'🗄️   🔧 UPDATED: {url_id}')
        return True
    except Exception as e:  # Add 'Exception as e' to capture the exception details
        logger.error(f'🗄️   🔧 Failed to complete update: {url_id} - Error: {e}')  # Display the error message
        return False


def tech_check_failure(url_id):
   logger.info(f'🗄️   🔧 Logging Tech Check Failure')
   query = """
       UPDATE staging.urls
       SET tech_check_failure = %s
       WHERE id = %s
   """
   try:
       execute_update(query, (datetime.now(timezone.utc), url_id))
       logger.debug(f'🗄️   🔧 Marked Failure: {url_id}')
       return True
   except Exception as e:  # Add 'Exception as e' to capture the exception details
       logger.error(f'🗄️   🔧 Failed to Mark Failure: {url_id} - Error: {e}')  # Display the error message
       return False
