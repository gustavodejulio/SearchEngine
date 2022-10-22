# This is going to store our results. There are 2 reasons for that
# 1. We don't want to keep querying the api if we already search for something
# 2. We want to store our search history so we can use the data to get better filter and apply ML

import sqlite3
import pandas as pd


# This class is gonna handle all the iterations with the database
class DBStorage():
    def __init__(self):
        # Create a database connection
        self.con = sqlite3.connect("links.db")
        self.setup_tables()

    # Create the table in the database
    def setup_tables(self):

        # This cursor allow to run queries and interact with our database
        cur = self.con.cursor()
        results_table = r"""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY,
                query TEXT,
                rank INTEGER,
                link TEXT,
                title TEXT,
                snippet TEXT,
                html TEXT,
                created DATETIME,
                relevance INTEGER,
                UNIQUE(query, link)
            );
            """

        # Execute the code to create the database
        cur.execute(results_table)

        # Commit the changes to the database
        self.con.commit()

        # Close the db
        cur.close()

    # Query the results
    def query_results(self, query):
        df = pd.read_sql(f"SELECT * FROM results WHERE query='{query}' ORDER BY rank asc;", self.con)
        return df

    # Inserting new values
    def insert_row(self, values):
        cur = self.con.cursor()
        try:
            # Inserting the values to the DB
            cur.execute(
                'INSERT INTO results (query, rank, link, title, snippet, html, created) VALUES(?, ?, ?, ?, ?, ?, ?)',
                values)
            # The question marks is to make sure that we escape the values properly and don't insert anything malicious into our DB
            # We are passing the values as a list of lists

            self.con.commit()
            # Write the changes to the DB

        # If the data already exists in the DB we pass
        except sqlite3.IntegrityError:
            pass
        cur.close()

    # Creating a relevance function to store the relevantes websites and further apply some ML
    def update_relevance(self, query, link, relevance):
        cur = self.con.cursor()
        # We will use sqlite3 to avoid someone messing with the DB in the search
        cur.execute("UPDATE results SET relevance=? WHERE query=? AND link=?", [relevance, query, link])
        self.con.commit()
        cur.close()
