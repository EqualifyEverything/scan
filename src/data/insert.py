import psycopg2
import json
import traceback
from data.access import connection
from utils.watch import logger

def execute_insert(query, params=None, fetchone=True):
    # logger.debug(f"🗄️✏️ Executing query: {query}")
    logger.debug(f"🗄️✏️ Query parameters: {params}")

    # Connect to the database
    conn = connection()
    conn.open()
    logger.debug("🗄️✏️ Database connection opened")

    # Create a cursor
    cur = conn.conn.cursor()

    try:
        # Execute the query
        cur.execute(query, params)
        conn.conn.commit()
        logger.info("🗄️✏️🟢 Query executed and committed")

        # Fetch the results if requested
        result = None
        if fetchone:
            result = cur.fetchone() or () # return an empty tuple if None is returned
        else:
            result = cur.fetchall() or [] # return an empty list if None is returned
            logger.debug(f'🗄️✏️ Fetched results: {result}')
    except Exception as e:
        logger.error(f"🗄️✏️ Error executing insert query: {e}\n{traceback.format_exc()}")
        result = None


    # Close the cursor and connection
    cur.close()
    conn.close()
    logger.debug("🗄️✏️ Cursor and connection closed")

    return result

#########################################################
## Queries


# Add Tech Apps
def record_tech_apps(name, description, icon, saas, website, pricing, scriptsrc, headers, cookies, dom, implies, cat_implies, js, requires, requires_cat, meta, cats):
    logger.info(f'🗄️✏️ Adding {name} to Tech Apps ')
    query = """
        INSERT INTO ref.tech_apps (
            name,
            description,
            icon,
            saas,
            website,
            pricing,
            scriptsrc,
            headers,
            cookies,
            dom,
            implies,
            cat_implies,
            js,
            requires,
            requires_cat,
            meta,
            cats
        )
        VALUES ( %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE
        SET description = excluded.description,
            icon = excluded.icon,
            saas = excluded.saas,
            website = excluded.website,
            pricing = excluded.pricing,
            scriptsrc = excluded.scriptsrc,
            headers = excluded.headers,
            cookies = excluded.cookies,
            dom = excluded.dom,
            implies = excluded.implies,
            cat_implies = excluded.cat_implies,
            js = excluded.js,
            requires = excluded.requires,
            requires_cat = excluded.requires_cat,
            meta = excluded.meta,
            cats = excluded.cats
        RETURNING id;
    """
    try:
        execute_insert(query, (name, description, icon, saas, website, pricing, scriptsrc, headers, cookies, dom, implies, cat_implies, js, requires, requires_cat, meta, cats))
        # Log Success
        logger.debug(f'🗄️  ✏️UPDATED: {name}')
        return True
    except Exception as e:
        logger.error(f'🗄️  ✏️Failed to complete update: {name} - Error: {e}')  # Display the error message
        return False

def scan_axe_new_event(url_id, scanned_at, failure, axe_meta):
    logger.debug(f'Creating new scan event for {url_id}...')
    query = """
        INSERT INTO events.scans_axe (
            url_id,
            scanned_at,
            failure,
            axe_meta
        )
        VALUES (
            %s, %s, %s, %s
        )
        RETURNING id as scan_event;
    """
    try:
        execute_insert(query, (url_id, scanned_at, failure, axe_meta))
        # Log the Yay!
        logger.debug(f'🗄️  ✏️UPDATED: {url_id}')
        return result
    except Exception as e:
    logger.error(f'🗄️  ✏️Failed to complete update: {url_id} - Error: {e}')
    # Display the error message
    return False

# Add Axe Results
# Add Items
def insert_axe_items(scan_event_id, url_id, type, area, impact, tags):
    logger.debug(f'Insert: Beginning to add items...')
    query = """
        INSERT INTO results.axe_items (
            scan_event_id,
            url_id,
            type,
            area,
            impact,
            tags
        )
        VALUES (
            %s, %s, %s,
            %s, %s, %s
        )
        RETURNING id as insert_id;
    """
    result = execute_insert(query, (url_id, scan_event_id, type, area, impact, tags))
    if result and isinstance(result[0], int):
        logger.info(f'Insert: New Item Added...')
        return True
    else:
        logger.error(f'Insert: Problem adding item...')
        return False

# Add Nodes
def insert_axe_nodes(scan_event_id, url_id, html, impact, target, data, failure_summary):
    logger.debug(f'Insert: Beginning to add nodes...')
    query = """
        INSERT INTO results.axe_nodes (
            scan_event_id,
            url_id,
            html,
            impact,
            target,
            data,
            failure_summary
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s
        )
        RETURNING id as insert_id;
    """
    result = execute_insert(query, (url_id, scan_event_id, html, impact, target, url_id, data, ))
    if result and isinstance(result[0], int):
        logger.info(f'Insert: New Node Added...')
        return True
    else:
        logger.error(f'Insert: Problem adding node...')
        return False

# Add Subnodes
def insert_axe_subnodes(scan_event_id, url_id, data, node_id, impact, message, node_type, related_nodes):
    logger.debug(f'Insert: Beginning to add subnodes...')
    query = """
        INSERT INTO results.axe_subnodes (
            scan_event_id,
            url_id,
            node_id,
            data,
            impact,
            node_type,
            message,
            related_nodes
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING id as insert_id;
    """
    result = execute_insert(query, (scan_event_id, url_id, node_id, data, impact, node_type, message, related_nodes))
    if result and isinstance(result[0], int):
        logger.info(f'Insert: New Subnode Added...')
        return True
    else:
        logger.error(f'Insert: Problem adding subnode...')
        return False




