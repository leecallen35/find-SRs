# find-forex-SRs
This program detects support & resistance zones in historical forex data. It is written to use Dukascopy downloaded data in CSV format.

My first publicly released Python code and my first Github submission. I am obviously not a Python code. Please be gentle!

Testing to verify code:

Run with the provided EURCAD test file as input.
Use these parameters: 
--pair EUR/CAD --fromdate 01/01/2010 --todate 1/11/2022 --period 250 --min_ht 0.02 --zone_width 0.0075 --min_touches 4
It should produce a file matching the attached SR_EURCAD_daily.pickle
Extract of that output file:
  date: 2022-12-30
  1.33937
  1.3474
  1.3486
  1.3504
  1.3513
  1.353
  1.37764
  date: 2023-01-01
  1.33937
  1.3472
  1.3484
  1.3504
  1.3513
  1.353
  1.37764
  date: 2023-01-02
  1.33937
  1.3472
  1.3484
  1.3504
  1.3513
  1.353
  1.37764
(This represents a "feature" that should probably be eliminated: SR data for 2023-01-02 from historical data ending in 2022-07-29 is inappropriate.)