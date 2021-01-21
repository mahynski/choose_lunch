"""
Created on Wed Jan 20 17:06:32 2021

@author: nam
"""

import requests
import json
import os
import numpy
import argparse
from urllib.error import HTTPError
import sys

def search(term, 
           location, 
           search_limit,
           credentials
           ):
    """
    Search Yelp using Fusion API.
    
    Parameters
    ----------
    term : str
        Search term to use.
    location : str
        Geographic location use.
    search_limit : int
        Max number of hits to return.
    credentials : str
        Name of json file with user's API_KEY in it.
        
    Returns
    -------
    restaurants : list(dict)
        List of top results from search.
    """
    # Read your API_KEY
    try:
        api_key = json.load(open(credentials, "r"))["API_KEY"]
    except Exception as e:
        raise Exception("Unable to load credentials : {}".format(e))

    headers = {"Authorization": "Bearer %s" % api_key}
    search_params = {
            "term":term,
            "location":location,
            "search_limit":search_limit
            }
    
    req = requests.get("https://api.yelp.com/v3/businesses/search", 
                       params=search_params, 
                       headers=headers)

    if req.status_code == 200: # Code 200 = success
        restaurants = json.loads(req.text)["businesses"]
    else:
        raise Exception("Bad search criteria")
        
    return restaurants

def assign_prob(hist, restaurants):
    """
    Assign the normalized relative probability of choosing a restaurant.

    Parameters
    ----------
    hist : dict
        Dictionary of business id's and frequency of past visits.
    restaurants : list(dict)
        List of businesses found from search() function.

    Returns
    -------
    prob : ndarray
        Normalized probability of choosing each restaurant.
    """
    prob = []
    for b in [restaurants[i]["id"] for i in range(len(restaurants))]:
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

def decide(term, location, search_limit, histogram, credentials):
    """
    Decide where to go for lunch.
    
    Will make a decision biased toward places not previously visited.  The user
    will be prompted to accept this choice.  If accepted, the histogram is
    updated and written to disk.
    
    Parameters
    ----------
    term : str
        Search term to use.
    location : str
        Geographic location use.
    search_limit : int
        Max number of hits to return.
    histogram : str
        Name of file where histogram of previous visits is stored.
    credentials : str
        Name of json file with user's API_KEY in it.
        
    """
    # Yelp search
    try:
        restaurants = search(term, location, search_limit, credentials)
    except Exception as e:
        raise Exception("Unable to decide : {}".format(e))
        
    # Load history of choices
    if os.path.isfile(histogram):
        f = open(histogram, "r")
        hist = json.load(f)
        f.close()
    else:
        hist = {}
            
    # Assign bias
    probs = assign_prob(hist, restaurants)

    decided = False
    while not decided:
        # Make biased choice
        choice = numpy.random.choice(numpy.arange(0, len(probs)), p=probs)
            
        # Display choice
        print("Today's choice is...")
        print("********************************************************")
        print(restaurants[choice]["name"])
        loc = restaurants[choice]["location"]["display_address"][0]
        for i in range(
            1, len(restaurants[choice]["location"]["display_address"])
        ):
            loc += ", " + restaurants[choice]["location"]["display_address"][i]
        print(loc)
        print(
            "Rating: "
            + str(restaurants[choice]["rating"])
            + " with "
            + str(restaurants[choice]["review_count"])
            + " reviews"
        )
        print("Is open?: " + str(not restaurants[choice]["is_closed"]))
        print("Website: " + str(restaurants[choice]["url"]))
        print("********************************************************")
        
        # Prompt user to accept this?
        select = False
        while not select:
            input_var = input("Accept this choice? [y/n]: ")
            if ("y" in input_var or "Y" in input_var) and (
                "n" not in input_var and "N" not in input_var
            ):
                # Accept this choice
                select = True
                decided = True
                
                # Increment histogram
                business_id = restaurants[choice]["id"]
                if business_id in hist:
                    hist[business_id] += 1
                else:
                    hist[business_id] = 1
            elif ("y" not in input_var and "Y" not in input_var) and (
                "n" in input_var or "N" in input_var
            ):
                # Reject this choice, try again
                select = True
            else:
                # User failed to correctly specify a choice, try again
                continue
            
    # Dump updated histogram
    f = open(histogram, "w")
    json.dump(hist, f, indent=True, sort_keys=True)
    f.close()
        
if __name__ == "__main__":
    """Choose your lunch provider."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-t",
        "--term",
        dest="term",
        default="lunch",
        type=str,
        help="Search term (default: %(default)s)",
    )
    parser.add_argument(
        "-l",
        "--location",
        dest="location",
        default="Gaithersburg, MD",
        type=str,
        help="Search location (default: %(default)s)",
    )
    parser.add_argument(
        "-v",
        "--visited",
        dest="histogram",
        default="visited.json",
        type=str,
        help="Histogram of visited restaurants (default: %(default)s)",
    )
    parser.add_argument(
        "-m",
        "--max",
        dest="search_limit",
        default=100,
        type=int,
        help="Number of top queries to choose from (default: %(default)d)",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        dest="credentials",
        default="credentials.json",
        type=str,
        help="Number of top queries to choose from (default: %(default)s)",
    )

    input_values = parser.parse_args()

    try:
        decide(input_values.term, 
               input_values.location, 
               input_values.search_limit, 
               input_values.histogram, 
               input_values.credentials)
    except HTTPError as error:
        sys.exit(
            "Encountered HTTP error {0} on {1}:\n {2}\nAbort program.".format(
                error.code,
                error.url,
                error.read(),
            )
        )        