from bs4 import BeautifulSoup
from urllib.parse import urlparse
from settings import *

with open("blacklist.txt") as f:
    # Read the file as unique values and split by line
    bad_domains_list = set(f.read().split("\n"))


# Is going to strip all of the HTML out of a page and just get the text back
def get_page_content(row):
    # Using the library to take all the HTML
    soup = BeautifulSoup(row["html"])

    # Taking only the text from the HTML
    text = soup.get_text()
    return text


def tracker_urls(row):
    # Parse the HTML
    soup = BeautifulSoup(row["html"])
    # Searching for the specifics tags (script) and Specific attributes (src)
    # We are looking for any script tag in our html that has the property src = True
    # This is usually used to load third-part JS like Google Analytics, Tag Manager...
    scripts = soup.find_all("script", {"src": True})
    # Getting the URL that the script is being loaded from
    srcs = [s.get("src") for s in scripts]

    # Taking the links that are stored in the 'a' tag
    links = soup.find_all("a", {"href": True})
    # Get where the link is pointing
    href = [l.get("href") for l in links]

    # This is going to loop through our list of urls in both lists of srcs and href and pull out the host name
    # If the script is pointing to something like: "https://www.google.com/script.js" the parse returns: "google.com"
    all_domains = [urlparse(s).hostname for s in srcs + href]
    # Checking if our domain is in a list of bad domains
    bad_domains = [a for a in all_domains if a in bad_domains_list]
    return len(bad_domains)


class Filter():
    # Initializing and passing a list of results
    def __init__(self, results):
        # Passing a dataframe of results and storing as part of the class
        self.filtered = results.copy()

    # This function is to check how many words has in the website, and if the amount of words in the site is less than
    # the medium of words in all the research, so if you have a little content on the page, the rank is going to be low
    def content_filter(self):
        # Applying the get_page_content function to each rom of the filtered dataframe
        page_content = self.filtered.apply(get_page_content, axis=1)

        # Counting how many words are in each pages
        word_count = page_content.apply(lambda x: len(x.split(" ")))

        # This is checking if the count of words in the page is bigger or lower than the medium of the results
        # This is assuming that if the count of words is to low, then the result is a low quality and have mostly
        # ads, pictures and affiliated links
        # Applying a penalty to the ranked based on the content, if has enough words or not
        word_count /= word_count.median()

        # If the content has less than half as many words as the median
        word_count[word_count <= .5] = RESULT_COUNT

        # Penalizing by pushing it down to the end of the rank
        word_count[word_count != RESULT_COUNT] = 0

    # This function is going to filter any results that have a lot of ads, tracking links or a lot of JS tracking
    def tracker_filter(self):
        tracker_count = self.filtered.apply(tracker_urls, axis=1)
        # If the tracker count is bigger than the median of trackers counts in all links, we penalize the rank *2
        tracker_count[tracker_count > tracker_count.median()] = RESULT_COUNT * 2
        # Add to the rank
        self.filtered["rank"] += tracker_count

    def filter(self):
        self.content_filter()
        self.tracker_filter()
        # Ranking the dataframe filtered by rank in ascending values
        self.filtered = self.filtered.sort_values("rank", ascending=True)
        self.filtered["rank"] = self.filtered["rank"].round()
        return self.filtered
