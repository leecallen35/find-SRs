"""
-----------------------------------------------------------------------
 find_sr.py : find S&R resistance zones
-----------------------------------------------------------------------

Algorithm:
On for example a 4H chart:
1. Create a list of local maxima & minima (price inflections).
2. Identify *clusters* of maxima / minima using kmeans clustering. These are candidate zones.
3. Count the number of maxima / minima within range of each candidate zones.
4. Keep the zones that have at least N hits. Also keep maximum & minimum price during the period.

parameters:
--csvfile	File containing OHLC data -- only C (closes) are used
		Developed using Dukascopy downloads
--pair		currency pair e.g. EUR/USD, used to derive output filename
--fromdate,	range of dates to read and build SR data for (the first few days will be ignored
--todate	until enough min/max patterns are identified)
--period	look-back days: how far back in history each SR zone should reflect
--min_ht	to qualify as a min/max pattern the center bar must be this PERCENT higher than the shoulders
--min_touches	minimum number of times price must bounce off a zone for it to be a valid zone
--zone_width	the width of each SR zone

Good parameters, using H4 data:
find_sr-003.py --csvfile data-4H/EURCAD_Candlestick_4_Hour_BID_01.01.2010-11.12.2021.csv --pair EUR/CAD --fromdate 01/01/2010 --todate 1/11/2022 --period 250 --min_ht 0.02 --zone_width 0.0075 --min_touches 4

"""

import argparse
import csv
import datetime
import pickle
from typing import Callable

import pytz
from dateutil.parser import parse as parse_date
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering


def save_zones(curr_pair, period_zones_d):
    # all time periods have been set up, store the results in a file named e.g.
    # SR_EURCAD_daily.pickle
    filename = 'SR_' + curr_pair + '_daily.pickle'
    print('writing', filename, ':')
    with open(filename, 'wb') as pickle_file:
        pickle.dump(period_zones_d, pickle_file, pickle.HIGHEST_PROTOCOL)


def cluster_zones(extrema, from_date, to_date, min_touches, period, zone_width,
                  cluster_func: Callable[[list[float]],list[float]]):
    #
    # dictionary period_zones_d will contain one item per date, with date as key,
    # and a list of zones *relevant* for that date,
    # ie, SR zones that occurred in the eg year *before* that date
    #
    period_zones_d = {}
    print('consolidating', len(extrema), 'min/max into zones...')
    #
    # outer loop: for each day in the time period indicated in the command arguments
    #
    curr_date = from_date - datetime.timedelta(days=1)
    while curr_date < to_date:

        curr_date += datetime.timedelta(days=1)
        start_date = curr_date + datetime.timedelta(days=-period)

        #
        # filter the minima/maxima for curr_date into a new list
        #
        values_l = []
        for date, price in extrema:
            if start_date <= date <= curr_date:
                values_l.append(price)
        if len(values_l) < 25:
            continue
        # capture the min & max close
        min_price = min(values_l)
        max_price = max(values_l)

        #
        # find clusters of minima/maxima, these are candidate SR zones
        #
        clusters_l = cluster_sk(values_l, cluster_func)

        #
        # now count the bounces for each cluster - the number of minima/maxima within range (one-half zone_width) of the cluster
        #
        zones_l = []
        for cluster in clusters_l:
            count = 0
            for value in values_l:
                if abs(cluster - value) < zone_width / 2:
                    count += 1
            zones_l.append((round(cluster, 4), count))

        #
        # save the N zones that satisfy the minimum number of bounces,
        # and add the high & low prices during this period
        #
        zones_l2 = []
        for price, count in zones_l:
            if count >= min_touches:
                zones_l2.append(price)
        zones_l2.append(min_price)
        zones_l2.append(max_price)
        zones_l2.sort()

        #
        # store it for the NEXT date, but if it's Friday, store it for Sunday AND Monday
        #
        if curr_date.weekday() == 4:
            period_zones_d[curr_date + datetime.timedelta(days=2)] = zones_l2
            period_zones_d[curr_date + datetime.timedelta(days=3)] = zones_l2
        else:
            period_zones_d[curr_date + datetime.timedelta(days=1)] = zones_l2
    return period_zones_d


def cluster_sk(values_l, cluster_func):
    values_a = np.asarray(values_l, dtype=float).reshape(-1, 1)
    fit = cluster_func(n_clusters=args.n_clusters).fit(values_a)
    clusters = [[] for _ in range(args.n_clusters)]
    for v, c in zip(values_l, np.reshape(fit.labels_, -1)):
        clusters[c].append(v)
    centering = np.mean if args.centering == 'mean' else np.median
    centers = [centering(c) for c in clusters]
    return centers


def zones_to_levels(period_zones_d):
    """
    converts an SR data structure of {date:[prices]} to a format of [(price,[start,end])]
    """
    levels = []
    cur_prices:dict[float,datetime.datetime] = {}
    for date, prices in period_zones_d.items():
        cur_price_set = set(cur_prices.keys())
        now_price_set = set(prices)
        to_add = now_price_set - cur_price_set
        to_remove = cur_price_set - now_price_set
        for price in to_add:
            cur_prices[price] = date
        for price in to_remove:
            start = cur_prices.pop(price)
            levels.append((price,(start,date)))
    for price, start in cur_prices.items():
        # noinspection PyUnboundLocalVariable
        levels.append((price, (start, date)))
    return levels


def find_extrema(bars, min_ht):
    #
    # data is now in bars[], find local minima/maxima
    #
    maxima = []
    idx = 0
    print('Locating local minima/maxima ')
    while idx < len(bars) - 12:
        incr = 1

        # convert min_ht (percent difference in bar height to constitute a min/max) into a value
        # based on a random bar (the first one)
        th = bars[idx][1] * min_ht / 100

        # bounces could be from 4 to 11 bars wide
        for width in range(4, 12):
            # look for a peak (high) in the middle with all other bars lower, first & last much lower,
            # and second and second-to-last must also be lower
            peak_idx, peak_val = mymax(1, bars, idx, width)
            if peak_val - bars[idx + 0][1] > th and peak_val - bars[idx + width - 1][1] > th and \
                    peak_val > bars[idx + 1][1] and peak_val > bars[idx + width - 2][1]:
                maxima.append(bars[peak_idx])
                incr = width
                break
            # look for a valley (low) in the middle with all other bars higher, first & last much higher
            # and second and second-to-last must also be higher
            peak_idx, peak_val = mymax(-1, bars, idx, width)
            if bars[idx + 0][1] - peak_val > th and bars[idx + width - 1][1] - peak_val > th and \
                    peak_val < bars[idx + 1][1] and peak_val < bars[idx + width - 2][1]:
                maxima.append(bars[peak_idx])
                incr = width
                break

        idx += incr
    return maxima


def load_dukascopy(csv_filename, from_date, to_date):
    bars = []
    #
    # read file into bars[]
    #
    with open(csv_filename) as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        print('Reading ', csv_filename, '...')
        # skip header record
        _first_row = next(csvReader)
        for row in csvReader:

            # content: Datetime with tz,Open,High,Low,Close,Volume - SAMPLE:
            # 31.12.2013 21:00:00.000 GMT-0500,1.45934,1.45934,1.45934,1.45934,0

            #
            # convert all datetimes to UTC
            #
            curr_datetime = parse_date(row[0], dayfirst=True)
            curr_date = curr_datetime

            #
            # skip records based on --fromdate and --todate
            #
            if curr_date < from_date:
                continue
            if curr_date > to_date:
                break

            curr_close = float(row[4])
            bars.append((curr_date, curr_close))

        print('bars saved:', len(bars))
    return bars


#
# find highest or lowest value in a slice of bars[]
#
def mymax(direction, bars, start, width):
    best_idx = None
    best_val = None

    for idx in range(start, start+width):
       val = bars[ idx ][ 1 ]
       if best_val is None:
          best_val = val
          best_idx = idx
       elif direction == 1 and val > best_val:
          best_val = val
          best_idx = idx
       elif direction == -1 and val < best_val:
          best_val = val
          best_idx = idx
    return best_idx, best_val

#
# parse_args()
#
def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Run Lee''s Analyzer in optimize or single-set mode')

    def date(string):
        result = parse_date(string)
        if not result.tzinfo:
            result = result.replace(tzinfo=pytz.UTC)
        return result

    parser.add_argument( '--csvfile',     action='store', required=True,  dest='csv_filename',
								 help='Input CSV file containing market' )
    parser.add_argument( '--fromdate',    action='store', required=False, dest='fromdate',     type=date, default='1970-1-1',
								 help='Starting date formatted MM/DD/YYYY' )
    parser.add_argument( '--todate',      action='store', required=False, dest='todate',       type=date, default='2099-12-31',
								 help='Ending date formatted MM/DD/YYYY' )
    parser.add_argument( '--pair',        action='store', required=True,  dest='curr_pair',
								 help='Currency pair ex: EUR/USD' )
    parser.add_argument( '--period',      action='store', required=True,  dest='period',       type=int,
								 help='Lookback days for S&R' )
    parser.add_argument( '--min_ht',      action='store', required=True,  dest='min_ht',       type=float,
								 help='Min center height percent' )
    parser.add_argument( '--zone_width',  action='store', required=True,  dest='zone_width',   type=float,
								 help='Width of each SR zone' )
    parser.add_argument( '--min_touches', action='store', required=True,  dest='min_touches',  type=int,
								 help='Min number of touches for each SR zone' )
    parser.add_argument( '--plot',        action='store_true',
                                 help='Produce pyplot of prices and SR levels')
    parser.add_argument( '--clustering',  choices=['kmeans','hier','hierarchical'], default='hier')
    parser.add_argument( '--n_clusters', action='store', type=int, required=False, default=16)
    parser.add_argument( '--centering', choices=['mean','median'], default='median')

    return parser.parse_args()


########################################################################
# main()
########################################################################

def main():
    #
    # process parameters from command line
    #

    curr_pair = args.curr_pair.split( '/' )
    if len( curr_pair ) != 2:
        print( 'Invalid currency pair given:', args.curr_pair )
        quit()
    if curr_pair[ 0 ] == 'JPY' or curr_pair[ 1 ] == 'JPY' :
        args.zone_width  *= 100
    pair_name = curr_pair[0] + curr_pair[1]

    #
    # do it
    #
    bars = load_dukascopy(args.csv_filename, args.fromdate, args.todate)
    extrema = find_extrema(bars, args.min_ht)
    cluster_func = {
        'kmeans': KMeans, 'hier': AgglomerativeClustering, 'hierarchical': AgglomerativeClustering,
    }[args.clustering]
    period_zones_d = cluster_zones(extrema, args.fromdate, args.todate, args.min_touches, args.period, args.zone_width,
                                   cluster_func)
    save_zones(pair_name, period_zones_d)
    if args.plot:
        from matplotlib import pyplot as plt
        plt.plot(*zip(*bars))
        levels = zones_to_levels(period_zones_d)
        for price,interval in levels:
            plt.plot(interval,(price,price), color='r')
        plt.show()
        plt.close()
    print('finished.')


if __name__ == '__main__':
    args = parse_args()
    main()
