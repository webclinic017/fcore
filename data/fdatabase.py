"""Module related to database connections.

The author is Zmicier Gotowka

Distributed under Fcore License 1.1 (see license.md)
"""

import sqlite3
from sqlite3 import Error

import abc

# Exception class for general database errors
class FdatabaseError(Exception):
    """
        Database exception class.
    """

class DBConn(metaclass=abc.ABCMeta):
    """
        Class to represent a database connection.
    """
    def __init__(self, source):
        """
            Initialize the database connection.

            Args:
                source(ReadOnlyData): data source to initialize the database connection.
        """
        self.conn = None
        self.cur = None

        self.source = source

    # Abstract method to connect to db
    @abc.abstractmethod
    def db_connect(self):
        """
            Abstract method to connect to the database. Needs to be overloader for a particular database type.
        """

    # Abstract method to close db connection
    @abc.abstractmethod
    def db_close(self):
        """
            Abstract method to disconnect from the database. Needs to be overloader for a particular database type.
        """

class SQLiteConn(DBConn):
    # Connect to the database
    def db_connect(self):
        """
            Connect to SQLite database.

            Raises:
                FdatabaseError: Can't connect to a database.
        """
        try:
            self.source.conn = sqlite3.connect(self.source.db_name)
        except Error as e:
            raise FdatabaseError(f"An error has happened when trying to connect to a {self.source.db_name}: {e}") from e

        # Set the row factory
        self.source.conn.row_factory = sqlite3.Row

        self.source.cur = self.source.conn.cursor()
        self.source.Error = Error

        # Enable foreign keys
        try:
            self.source.cur.execute("PRAGMA foreign_keys=on;")
        except self.source.Error as e:
            raise FdatabaseError(f"Can't enable foreign keys: {e}") from e

    # Close the connection
    def db_close(self):
        self.source.cur.close()
        self.source.conn.close()
