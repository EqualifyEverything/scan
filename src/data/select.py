from data.access import connection
from utils.watch import logger

# Log Emoji: 🗄️🔍


def execute_select(query, params=None, fetchone=True):
    # Connect to the database
    conn = connection()
    conn.open()
    # logger.debug("🗄️🔍 Database connection opened")

    # Create a cursor
    cur = conn.conn.cursor()

    # Execute the query
    cur.execute(query, params)
    conn.conn.commit()
    logger.info("🗄️✏️🟢 Query executed and committed")
    # logger.debug(f"🗄️🔍 Executed select query: {query}")
    #   logger.debug(f"🗄️🔍 Query parameters: {params}")

    # Fetch the results if requested
    result = None
    if fetchone:
        result = cur.fetchone() if cur.rowcount > 0 else None
    else:
        result = cur.fetchall()

    # Close the cursor and connection
    cur.close()
    conn.close()
    logger.debug("🗄️🔍 Cursor and connection closed")

    return result


# Queries
def next_tech_url():
    query = """
        SELECT url AS "target",
            id as "url_id"
        FROM staging.urls
        WHERE techs IS NULL
        AND tech_check_failure is NULL
        AND gsa_site_scan_url_id IS NOT null
        ORDER BY RANDOM() LIMIT 1;
    """
    result = execute_select(query)
    if result:
        target, url_id = result
        logger.info(f'🗄️🔍 Next Tech Check URL: {target}')
        return target, url_id
    else:
        logger.error(f'🗄️🔍 Unable to Tech Check URL  - Error: {e}')
        return None, None

def next_axe_url():
    query = """
      SELECT url as "target", id as "url_id"
      FROM targets.urls
      WHERE active_main is True AND active_scan_axe is True
      ORDER BY scanned_at_axe NULLS FIRST, created_at
      LIMIT 100
      OFFSET floor(random() * 100);
   """
    result = execute_select(query)
    if result:
        target, url_id = result
        logger.info(f'Snagged {url_id} : {target}')
        return target, url_id
    else:
        logger.error(f'🗄️🔍 Unable to Get URL - Error: {e}')
        return None, None
