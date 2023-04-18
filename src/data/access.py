import os
import psycopg2

# TODO Add connection pooling
class connection:


    def __init__(self):
        """
        Initializes a new instance of the connection class with default connection parameters.
        """
        self.host = os.environ.get("DB_HOST", "192.168.1.29")
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

    def get_connection_params(self):
        return {
            'host': self.host,
            'port': self.port,
            'database': self.db_name,
            'user': self.user,
            'password': self.password,
        }

