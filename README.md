# ChooseLunch

## Overview
A python-based decision maker based on Yelp Fusion API code sample for when you can't decide what to eat for lunch.  A histogram is used to store previously visited locations and bias the probability of choosing a restaurant toward previously unvisited locations.

Refer to http://www.yelp.com/developers/v3/documentation for the API
documentation.

## Installation
To install the dependencies, run:
~~~ bash
$ pip install -r requirements.txt
~~~

## Obtain YELP developer account
1. Sign up for a [yelp deevlopers](https://www.yelp.com/developers) account.
2. Obtain your client id and secret at https://www.yelp.com/developers/v3/manage_app to use their Fusion API.
3. Enter "CLIENT_ID" and "CLIENT_SECRET" as keys in a credentials.json file inside the repo directory.  For example
~~~ bash
$ cat /path/to/choose_lunch/credentials.json
{
 "CLIENT_ID": "abcd",
 "CLIENT_SECRET: "efgh"
}
~~~

## Steps to run
~~~ bash
$ cd /path/to/choose_lunch/
$ python choose.py --term="lunch" --location="Gaithersburg, MD" --visited="visited.json" --max=5
~~~

For help, see
~~~ bash
$ python choose.py -h
~~~
