"""
Lunch decision maker based on Yelp Fusion API code sample.

author: nam
"""
from __future__ import print_function

import argparse
import json
import os.path
import pprint
import random
import sys
import urllib

import numpy
import requests

# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote, urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib import quote, urlencode

    from urllib2 import HTTPError

# OAuth credential placeholders that must be filled in by users.
# You can find them on https://www.yelp.com/developers/v3/manage_app
creds = json.load(open("credentials.json", "r"))
CLIENT_ID = creds["CLIENT_ID"]
CLIENT_SECRET = creds["CLIENT_SECRET"]

# API constants, you shouldn't have to change these.
API_HOST = "https://api.yelp.com"
SEARCH_PATH = "/v3/businesses/search"
BUSINESS_PATH = "/v3/businesses/"  # Business ID will come after slash.
TOKEN_PATH = "/oauth2/token"
GRANT_TYPE = "authorization_code"  # "client_credentials"

# Defaults for our simple example.
DEFAULT_TERM = "lunch"
LOCS = ["Gaithersburg, MD"]  # , 'Rockville, MD']
DEFAULT_LOCATION = "Gaithersburg, MD"  # LOCS[random.randint(0, len(LOCS)-1)]
SEARCH_LIMIT = 20
VISITED = "visited.json"


def obtain_bearer_token(host, path):
    """
    Given a bearer token, send a GET request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        str: OAuth bearer token, obtained using client_id and client_secret.

    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url = "{0}{1}".format(host, quote(path.encode("utf8")))
    assert CLIENT_ID, "Please supply your client_id."
    assert CLIENT_SECRET, "Please supply your client_secret."
    data = urlencode(
        {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": GRANT_TYPE,
        }
    )
    headers = {
        "content-type": "application/x-www-form-urlencoded",
    }
    response = requests.request("POST", url, data=data, headers=headers)
    print(response.json())
    bearer_token = response.json()["access_token"]

    return bearer_token


def request(host, path, bearer_token, url_params=None):
    """
    Given a bearer token, send a GET request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        bearer_token (str): OAuth bearer token, obtained using client_id and client_secret.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        dict: The JSON response from the request.

    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = "{0}{1}".format(host, quote(path.encode("utf8")))
    headers = {
        "Authorization": "Bearer %s" % bearer_token,
    }
    response = requests.request("GET", url, headers=headers, params=url_params)

    return response.json()


def search(bearer_token, term, location, limit):
    """
    Query the Search API by a search term and location.

    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.

    Returns:
        dict: The JSON response from the request.
    """
    url_params = {
        "term": term.replace(" ", "+"),
        "location": location.replace(" ", "+"),
        "limit": limit,
    }

    return request(API_HOST, SEARCH_PATH, bearer_token, url_params=url_params)


def get_business(bearer_token, business_id):
    """
    Query the Business API by a business ID.

    Args:
        business_id (str): The ID of the business to query.

    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path, bearer_token)


def assign_prob(hist, businesses):
    """
    Assign the normalized relative probability of choosing a business.

    Args:
        hist (dict): Dictionary of business id's and frequency of past visits.
        businesses (list): List of businesses found by Yelp API.

    Returns:
        ndarray: Ordered array of normalized probabilities.
    """
    prob = []
    for b in [businesses[i]["id"] for i in range(len(businesses))]:
        try:
            hist[b]
        except KeyError:
            prob.append(1.0)
        else:
            prob.append(hist[b] + 1.0)

    prob = numpy.array(prob)
    prob = 1.0 - prob / numpy.sum(prob)  # Bias to visit new restaurants
    prob = prob / numpy.sum(prob)  # Re-normalize

    return prob


def query_api(term, location, histogram, limit):
    """
    Query the API by the input values from the user.

    Prints choice and records the result in the histogram.

    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
        histogram (str): Name of histogram file.
        limit (int): Max number of queries to choose from.
    """
    found = False
    while not found:
        bearer_token = obtain_bearer_token(API_HOST, TOKEN_PATH)
        response = search(bearer_token, term, location, limit)
        businesses = response.get("businesses")

        if not businesses:
            print(u"No businesses for {0} in {1} found.".format(term, location))
            return

        if os.path.isfile(histogram):
            f = open(histogram, "r")
            hist = json.load(f)
            f.close()
        else:
            hist = {}

        # Choose business
        probs = assign_prob(hist, businesses)

        # Biased choice
        choice = numpy.random.choice(numpy.arange(0, len(probs)), p=probs)
        # Random choice
        # choice = random.randint(0, limit-1)

        business_id = businesses[choice]["id"]
        response = get_business(bearer_token, business_id)

        print("Today's choice is...")
        print("********************************************************")
        print(businesses[choice]["name"])
        loc = businesses[choice]["location"]["display_address"][0]
        for i in range(
            1, len(businesses[choice]["location"]["display_address"])
        ):
            loc += ", " + businesses[choice]["location"]["display_address"][i]
        print(loc)
        print(
            "Rating: "
            + str(businesses[choice]["rating"])
            + " with "
            + str(businesses[choice]["review_count"])
            + " reviews"
        )
        print("Is open?: " + str(not businesses[choice]["is_closed"]))
        print("Website: " + str(businesses[choice]["url"]))
        print("********************************************************")

        if business_id in hist:
            hist[business_id] += 1
        else:
            hist[business_id] = 1

        select = False
        while not select:
            input_var = raw_input("Accept this choice? [y/n]: ")
            if ("y" in input_var or "Y" in input_var) and (
                "n" not in input_var and "N" not in input_var
            ):
                # Chose to accept this choice
                select = True
                found = True
            elif ("y" not in input_var and "Y" not in input_var) and (
                "n" in input_var or "N" in input_var
            ):
                # Reject this choice, try again
                select = True
            else:
                # Failed to correctly make a choice, try again
                continue

    f = open(histogram, "w")
    json.dump(hist, f, indent=True, sort_keys=True)
    f.close()


def main():
    """Choose your lunch provider."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-q",
        "--term",
        dest="term",
        default=DEFAULT_TERM,
        type=str,
        help="Search term (default: %(default)s)",
    )
    parser.add_argument(
        "-l",
        "--location",
        dest="location",
        default=DEFAULT_LOCATION,
        type=str,
        help="Search location (default: %(default)s)",
    )
    parser.add_argument(
        "-v",
        "--visited",
        dest="histogram",
        default=VISITED,
        type=str,
        help="Histogram of visited restaurants (default: %(default)s)",
    )
    parser.add_argument(
        "-m",
        "--max",
        dest="limit",
        default=SEARCH_LIMIT,
        type=str,
        help="Number of top queries to choose from (default: %(default)s)",
    )

    input_values = parser.parse_args()

    try:
        query_api(
            input_values.term,
            input_values.location,
            input_values.histogram,
            input_values.limit,
        )
    except HTTPError as error:
        sys.exit(
            "Encountered HTTP error {0} on {1}:\n {2}\nAbort program.".format(
                error.code,
                error.url,
                error.read(),
            )
        )


if __name__ == "__main__":
    main()
