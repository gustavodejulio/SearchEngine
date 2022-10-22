from settings import *
import requests
from requests.exceptions import RequestException
import pandas as pd
from storage import DBStorage
from urllib.parse import quote_plus
from datetime import datetime


# Each page of results gives us 10 search results
def search_api(query, pages=int(RESULT_COUNT / 10)):
    # Empty list of dictionaries
    results = []
    for i in range(0, pages):
        # Define the first record on each page (the rank of that record)
        # The rank in the first record in the first page is 1, the first record in the second page is 11
        start = i * 10 + i

        # quote_plus it quotes the query to the url format, replacing blank spaces and other char
        url = SEARCH_URL.format(
            key=SEARCH_KEY,
            cx=SEARCH_ID,
            query=quote_plus(query),
            start=start
        )
        # Make a request to the google search custom API and it's going to be on JSON format
        response = requests.get(url)
        data = response.json()
        # This is going to be a dict
        results += data["items"]

    # Transform the list of dict to DF
    res_df = pd.DataFrame.from_dict(results)

    # This DF will have the fields corresponding to the storage DB fields
    # The rank indicates rank of the result from 1 to 11 for the first page
    res_df["rank"] = list(range(1, res_df.shape[0] + 1))

    # Selecting the columns that we are going to use
    res_df = res_df[["link", "rank", "snippet", "title"]]
    return res_df


def scrape_page(links):
    # This is going to take the full HTML from the link on the list
    html = []
    for link in links:
        try:
            data = requests.get(link, timeout=5)
            html.append(data.text)
        except RequestException:
            html.append("")
            # RequestException is when for whatever reason requests can't download the page properly
    return html


def search(query):
    # First create a list of columns that we want in our search
    # This are the values that we are going to pass into our storage
    columns = ["query", "rank", "link", "title", "snippet", "html", "created"]
    storage = DBStorage()

    # Checking if we already query the values, if so are the results in the database?
    stored_results = storage.query_results(query)
    # If there's more than 0 rows
    if stored_results.shape[0] > 0:
        # Input a data stamp from the search time and saving on the database
        stored_results["created"] = pd.to_datetime(stored_results["created"])

    results = search_api(query)
    # Scrape the pages and store it to the data frame
    results["html"] = scrape_page(results["link"])
    # Removing results when html is empty
    # If there are any problem to download the page just ignore the search result
    results = results[results["html"].str.len() > 0].copy()
    results["query"] = query

    # Transforming the created time stamp of the search to a valid SQL input
    results["created"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    # Removing any irrelevant columns and put the columns into the right order
    results = results[columns]
    # Insert each row to the database
    results.apply(lambda x: storage.insert_row(x), axis=1)

    return results
