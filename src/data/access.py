import os
import psycopg2

# TODO Add connection pooling
class connection:
    """
    A manager for the Postgres Database Connection

    Attributes:
        host (str): The hostname of the database server.
        port (int): The port number to use for the database connection.
        user (str): The username to use for the database connection.
        password (str): The password to use for the database connection.
        db_name (str): The name of the database to connect to.
        conn (psycopg2.extensions.connection): The database connection object.
        cur (psycopg2.extensions.cursor): The database cursor object.

    Methods:
        open()
            Opens a new database connection using the connection parameters specified in the object.
            Returns: None

        close()
            Closes the current database connection and cursor.
            Returns: None

        test()
            Tests the database connection by executing a sample query.
            Returns: bool: True if the query executes successfully, False otherwise.

    Environment Variables:
        DB_HOST (str): The hostname of the database server. Default is "localhost".
        DB_PORT (int): The port number to use for the database connection. Default is 8432.
        DB_USER (str): The username to use for the database connection. Default is "a11yPython".
        DB_PASSWORD (str): The password to use for the database connection. Default is "SnakeInTheWeb".
        DB_NAME (str): The name of the database to connect to. Default is "a11y".

    """

    def __init__(self):
        """
        Initializes a new instance of the connection class with default connection parameters.
        """
        self.host = os.environ.get("DB_HOST", "rightstuff.local")
        self.port = int(os.environ.get("DB_PORT", "5432"))
        self.user = os.environ.get("DB_USER", "a11ydata")
        self.password = os.environ.get("DB_PASSWORD", "a11yAllTheThings!")
        self.db_name = os.environ.get("DB_NAME", "a11ydata")
        self.conn = None
        self.cur = None

        #DB_HOST=rightstuff.local DB_PORT=5432 DB_USER=a11ydata DB_PASSWORD=a11yAllTheThings! DB_NAME=a11ydata python3 utils/intake.py

    def open(self):
        """
        Opens a new database connection using the connection parameters specified in the object.

        Returns:
            None
        """
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db_name
        )
        self.cur = self.conn.cursor()

    def close(self):
        """
        Closes the current database connection and cursor.

        Returns:
            None
        """
        self.cur.close()
        self.conn.close()

    def test(self):
        """
        Tests the database connection by executing a sample query.

        Returns:
            bool: True if the query executes successfully, False otherwise.
        """
        try:
            self.open()
            self.cur.execute("SELECT name FROM meta.orgs WHERE id = 1")
            result = self.cur.fetchone()[0]
            self.close()
            return result == 1
        except:
            return False
