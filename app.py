from flask import Flask, request, jsonify
from search import search
import html
from filter import Filter
from storage import DBStorage

# Initialize the Flask application
app = Flask(__name__)

# Styling the results
styles = """
<style>
.site {
    font-size: .8rem;
    color: green;
}

.snippet {
    font-size: .9rem;
    color: grey;
    margin-bottom: 30px;
}


.rel-button {
    cursor: pointer;
    color: blue;
}
</style>
<script>
const relevant = function(query,link){
    fetch("/relevant", {
        method: 'POST'
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
            
        },
        body: JSON.stringify({
            "query": query,
            "link" link
        })
    });
}
</script>
"""

# This is a template for the search page in HTML
search_template = styles + """
<form action="/" method="post">
    <input type="text" name="query">
    <input type="submit" value="Search">
</form>
"""

# This is a template for the results in HTML
result_template = """
<p class="site">{rank}: {link} <span class="rel-button" onclick='relevant("{query}", "{link}");'>Relevant</span></p>
<a href="{link}">{title}</a>
<p class="snippet">{snippet}</p>
"""


def show_search_form():
    return search_template


def run_search(query):
    results = search(query)
    # Re-rank the results using the filter
    fi = Filter(results)
    results = fi.filter()
    rendered = search_template
    # Making sure that the contents of the snippet is not treated as a HTML
    results["snippet"] = results["snippet"].apply(lambda x: html.escape(x))

    # Iterating across each of the rows in the results
    for index, row in results.iterrows():
        # Row is a dict that contains the columns from our search function
        # "query", "rank", "link", "title", "snippet", "html", "created"
        rendered += result_template.format(**row)
    return rendered


# Create a new route that allow get and post requests
# Is basic URL that you can to to the web server
# Get return the status code
# Post return the response text
@app.route("/", methods=["GET", "POST"])
def search_form():
    if request.method == "POST":
        # Post is actually searching for something
        query = request.form["query"]
        return run_search(query)
    else:
        return show_search_form()

# Enabling the user to mark if the results is relevant or not
@app.route("/relevant", methods=["POST"])
def mark_relevant():
    data = request.get_json()
    query = data["query"]
    link = data["link"]
    storage = DBStorage()
    # Every time that someone press the relevant link, it will set the value of relevant to 10
    # This can be personalized
    storage.update_relevance(query, link, 10)
    # Just a message to check if the relevance mark was successfully made
    return jsonify(success=True)