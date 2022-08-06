SRzone Detector app for quantitative finace developers
==============================

[![TravisCI](https://travis-ci.org/finance/SRzone Detector.svg?branch=master)](https://travis-ci.org/finance/SRzone Detector)

[![Coverage Status](https://coveralls.io/repos/finance/SRzone Detector/badge.png)](https://coveralls.io/finance/SRzone Detector)

[![Github Badge](https://github.com/leecallen35)](https://github.com/leecallen35)

What Is This?
-------------

This program detects evidence for support & resistance (sr) zones in historical [forex] data. It's a project of the reddit r/algotrading community. It's intended purpose is to facilitate backtesting of strategies: either to exploit S&R zones, or to avoid trading near them.

My first publicly released Python code and my first Github submission. I am obviously not a Python coder. Please be gentle.

The program is written to use the Dukascopy download CSV format. Since it's Python it can be easily modified to use any other format, all it needs is date (or date/time depending on the timeframe of SR zones you want to create) and closing price.

Usage suggestion: If testing a strategy to trade S&R zones, use 'conservative' parameters to produce a smaller list of high probability zones. I.e., higher values of min_ht and min_touches and narrow zones. If testing a strategy to *avoid* trading in S&R zones, use 'aggressive' parameters to produce a larger list of zones.



How To Use This
---------------

1. Navigate over to https://github.com/leecallen35/find-SRs, and fork this repo to your own account.
2. Register a new GitHub Account and go through their new user workflows.
3. Fill in the relevant information in the `config.json` file in the root folder and add your client id and secret as the environment variables `UBER_CLIENT_ID` and `UBER_CLIENT_SECRET`.
4. For detailed qustions on Dukascopy data visit `https://www.dukascopy.com/wiki/en/development/strategy-api/practices/get-data-from-csv`, Run `export UBER_CLIENT_ID="`*{your client id}*`"&&export UBER_CLIENT_SECRET="`*{your client secret}*`"`
5. Run `pip install -r requirements.txt` to install dependencies
6. Run `python find-SRs.py`
7. Navigate to http://localhost:7000 in your browser


Testing
-------

1. Install the dependencies with `make bootstrap`, or `python3 pip -n install requirements.txt`, or?
2. Run the command `make test`, or `python3 manage.py runserver`, or ...
3. Run with the provided EURCAD test file as input.
4. Optional parameters
   1. `--pair EUR/CAD`
   2. `--fromdate 01/01/2010`
   3. `--todate 1/11/2022`
   4. `--period 250`
   5. `--min_ht 0.02`
   6. `--zone_width 0.0075`
   7. `--min_touches 4`
5. It should produce a file matching the attached SR_EURCAD_daily.pickle
### Extract of that output file
`
date: 2022-12-30
  1.33937
  1.3474
  1.3486
  1.3504
  1.3513
  1.353
  1.37764`
  
  `date: 2023-01-01
  1.33937
  1.3472
  1.3484
  1.3504
  1.3513
  1.353
  1.37764`
  
  `date: 2023-01-02
  1.33937
  1.3472
  1.3484
  1.3504
  1.3513
  1.353
  1.37764`

(This represents a "feature" that should probably be eliminated: I ran it using historical data ending in 2022-07-29, so it really shouldn't calculate SR zones for 2023-01-02)

6. Suggestions on how to install or conditional issues you choose to cover.


Development
-----------

If you want to work on this application we’d love your pull requests and tickets on GitHub!

1. If you open up a ticket, please make sure it describes the problem or feature request fully.
2. If you send us a pull request, make sure you add a test for what you added, and make sure the full test suite runs with `make test`.

Deploy to (Heroku, AWS, GCP)
----------------

Click the button below to set up this sample app on Heroku:

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

After creating your app on Heroku, you have to configure the redirect URL for your Uber OAuth app. Use a `https://`*{your-app-name}*`.herokuapp.com/submit` URL.
You will also want to configure the heroku environment variable FLASK_DEBUG=False in order to properly serve SSL traffic.

Future Features
---------------

- [] Add functionality for an interface either headless or basic django server 
- [] Format so this can be run inside a docker then Navigate to http://localhost:7000 in your browser etc
- [] Provide link and example of what the Dukascopy format is.
- [] Add more tests
- [] Add database selector for user preference. csv, tsv, parquet, sqlite, MySQL, PostGreSQL, Cassandra, NoSQL
- [] Add datasource connection
- [] Future API options
- [] What else should we add


Making Requests
---------------

- [] Please check `Future Features` section
