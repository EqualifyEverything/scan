import psycopg2
import json
import traceback
from data.access import connection
from utils.watch import logger
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime, timezone

# Set use_pooling to True to enable connection pooling
use_pooling = True

# Connection pool
pool = None

if use_pooling:
    conn_params = connection().get_connection_params()
    pool = SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        **conn_params
    )



def connection_pooling():
    return pool.getconn()

def release_pooling(conn):
    pool.putconn(conn)

# Singular Updates

def execute_update(query, params=None, fetchone=True):
 #  logger.debug(f'🗄️   🔧 Executing query: {query}')
 #  logger.debug(f'🗄️   🔧 Query parameters: {params}... ')

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


# # # # # # # # # #

# Bulk Updates

def execute_bulk_update(query, params_list):
   # Connect to the database
   if use_pooling:
      conn = connection_pooling()
   else:
      conn = connection()
      conn.open()

   # Create a cursor
   cur = conn.cursor()

   try:
      # Execute the query
      with conn:
          cur.executemany(query, params_list)
          logger.info("🗄️✏️🟢 Query executed and committed")
   except Exception as e:
      logger.error(f"🗄️✏️ Error executing bulk insert query: {e}\n{traceback.format_exc()}")

   # Close the cursor and connection
   cur.close()
   if use_pooling:
      release_pooling(conn)
   else:
      conn.close()


   #########################################################
   ## Queries

def tech_check_failure(url_id):
   logger.info(f'🗄️   🔧 Logging Tech Check Failure')
   query = """
       UPDATE targets.urls
       SET active_scan_tech = False,
         scanned_at_tech = %s
       WHERE id = %s
   """
   try:
       execute_update(query, (datetime.now(timezone.utc), url_id))
       logger.debug(f'🗄️   🔧 Marked Failure: {url_id}')
       return True
   except Exception as e:  # Add 'Exception as e' to capture the exception details
       logger.error(f'🗄️   🔧 Failed to Mark Failure: {url_id} - Error: {e}')  # Display the error message
       return False

def mark_url_axe_scanned(url_id):

    query = """
        UPDATE targets.urls
        SET scanned_at_axe = %s
        WHERE id = %s;
   """
    try:
       execute_update(query, (datetime.now(timezone.utc), url_id))
       logger.debug(f'🗄️   🔧 Marked {url_id} as Scanned')
       return True
    except Exception as e:  # Add 'Exception as e' to capture the exception details
      logger.error(f'🗄️   🔧 Failed to mark as Scanned: {url_id} - Error: {e}')  # Display the error message
      return False


def tech_mark_url(url_id):
   query = """
      UPDATE targets.urls
         SET scanned_at_tech = %s
         WHERE id = %s;
   """
   try:
       execute_update(query, (datetime.now(timezone.utc), url_id))
       logger.debug(f'🗄️   🔧 Marked {url_id} as Teched')
       return True
   except Exception as e:  # Add 'Exception as e' to capture the exception details
      logger.error(f'🗄️   🔧 Failed to mark as Teched: {url_id} - Error: {e}')  # Display the error message
      return False


def update_status_codes(url_status_list):
       query = """
           UPDATE targets.urls
           SET uppies_code = %s, uppies_at = %s
           WHERE id = %s;
       """
       now = datetime.now(timezone.utc)
       params_list = [(status_code, now, url_id) for url_id, status_code in url_status_list]

       try:
           execute_bulk_update(query, params_list)
           for url_id, status_code in url_status_list:
               logger.debug(f'🗄️🔧 Updated status code for URL ID {url_id} to {status_code}')
       except Exception as e:
           logger.error(f'🗄️🔧 Failed to update status codes in bulk - Error: {e}')
