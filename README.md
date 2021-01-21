choose_lunch
===========

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

## Overview
A python-based decision maker based on Yelp Fusion API code sample for when you 
can't decide what to eat for lunch.  A histogram is used to store previously 
visited locations and bias the probability of choosing a restaurant toward 
previously unvisited locations.

Refer to their website for the API
[documentation](https://www.yelp.com/developers/documentation/v3), and this 
[tutorial](https://python.gotrained.com/yelp-fusion-api-tutorial/0) for more 
information on usage.

## Installation
To install the dependencies, run:
~~~ bash
$ pip install -r requirements.txt
~~~

## Obtain Yelp developer account
1. Sign up for a [yelp developers](https://www.yelp.com/developers) account.
2. Obtain your client id and secret from your account 
([Manage App](https://www.yelp.com/developers/v3/manage_app)) to use their 
Fusion API.
3. Enter your "API_KEY" in a credentials.json file inside the repo directory.  
For example
~~~ bash
$ cat /path/to/choose_lunch/credentials.json
{
 "API_KEY": "qwertyuiopasdfghjklzxcvbnm"
}
~~~

## Steps to run
~~~ bash
$ cd /path/to/choose_lunch/
$ python choose.py --term="lunch" --location="Gaithersburg, MD" --visited="visited.json" --max=100 --credentials="credentials.json"
~~~

For help, see
~~~ bash
$ python choose.py -h
~~~
