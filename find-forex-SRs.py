'''
-----------------------------------------------------------------------
 find_sr.py : find S&R resistance zones
-----------------------------------------------------------------------

Algorithm:
On for example a 4H chart:
1. create a list of local maxima & minima
2. identify *clusters* of maxima / minima using kmeans clustering, these are candidate zones
3. count the number of hits = bounces = maxima/minima for each candidate zones
4. keep the N zones with the most hits

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

'''

import argparse
import csv
import datetime
import operator
import pickle
import numpy as np
from sklearn.cluster import KMeans

#
# pre_process() - read OHLC data in to a list
#
def process( csv_filename, curr_pair, from_date, to_date, period, min_ht, zone_width, min_touches ):

    bars = []
    
    #
    # read file into bars[]
    #
    with open( csv_filename ) as csvDataFile:
        csvReader = csv.reader( csvDataFile )
        print( 'Reading ', csv_filename, '...' )
        # skip header record
        first_row = next( csvReader )
        for row in csvReader:

            # content: Datetime with tz,Open,High,Low,Close,Volume - SAMPLE:
	    #31.12.2013 21:00:00.000 GMT-0500,1.45934,1.45934,1.45934,1.45934,0

            #
            # read datetime, no need to localize, we don't care if the hour is correct
            #
            curr_datetime = datetime.datetime.strptime( row[0], '%d.%m.%Y %H:%M:%S.%f %Z%z' )
            curr_date = curr_datetime.date()
            
            #
            # skip records based on --fromdate and --todate
            #
            if curr_date < from_date:
                continue
            if curr_date > to_date:
                break
                
            curr_close= float( row[ 4 ] )
            bars.append( ( curr_date, curr_close ) )
                
        print('bars saved:', len(bars))
            
    #
    # data is now in bars[], find local minima/maxima
    #
    maxima  = []
    idx     = 0
    
    print('Locating local minima/maxima ')
    
    while idx < len( bars ) - 12 :
        incr = 1

        # convert min_ht (percent difference in bar height to constitute a min/max) into a value
        # based on a random bar (the first one)
        th = bars[ idx ][ 1 ] * min_ht / 100

        # bounces could be from 4 to 11 bars wide
        for width in range(4, 12):
            # look for a peak (high) in the middle with all other bars lower, first & last much lower,
            # and second and second-to-last must also be lower
            peak_idx, peak_val = mymax( 1, bars, idx, width)
            if peak_val - bars[ idx+0 ][ 1 ] > th and peak_val - bars[ idx+width-1 ][ 1 ] > th and \
               peak_val > bars[ idx+1 ][ 1 ]      and peak_val > bars[ idx+width-2 ][ 1 ]:
                maxima.append( bars[ peak_idx ] )
                incr = width
                break
            # look for a valley (low) in the middle with all other bars higher, first & last much higher
            # and second and second-to-last must also be higher
            peak_idx, peak_val = mymax( -1, bars, idx, width)
            if bars[ idx+0 ][ 1 ] - peak_val > th and bars[ idx+width-1 ][ 1 ] - peak_val > th and \
               peak_val < bars[ idx+1 ][ 1 ]      and peak_val < bars[ idx+width-2 ][ 1 ]:
                maxima.append( bars[ peak_idx ] )
                incr = width
                break

        idx += incr
        
    #
    # dictionary period_zones_d will contain one item per date, with date as key,
    # and a list of zones *relevant* for that date,
    # ie, SR zones that occurred in the eg year *before* that date
    #
    period_zones_d = {}
    print('consolidating', len(maxima), 'min/max into zones...')
    
    #
    # outer loop: for each day in the time period indicated in the command arguments
    #
    curr_date = from_date - datetime.timedelta( days = 1 )
    while curr_date < to_date:

        curr_date += datetime.timedelta( days = 1 )
        start_date = curr_date + datetime.timedelta( days = -period )
        
        #
        # filter the minima/maxima for curr_date into a new list
        #
        values_l = []
        for date, price in maxima:
            if date >= start_date and date <= curr_date:
                values_l.append( price )
        if len( values_l ) < 25:
            continue
        # capture the min & max close
        min_price = min( values_l )
        max_price = max( values_l )
            
        #
        # find clusters of minima/maxima, these are candidate SR zones
        #
        values_a =  np.asarray(values_l, dtype=float).reshape(-1, 1)
        n_clusters = 16
        kmeans = KMeans( n_clusters=n_clusters ).fit( values_a )
        # convert to list
        clusters_l = np.reshape( kmeans.cluster_centers_, -1 ).tolist()
        
        #
        # now count the bounces for each cluster - the number of minima/maxima within range (one-half zone_width) of the cluster
        #
        zones_l = []
        for cluster in clusters_l:
            count = 0
            for value in values_l:
                if abs( cluster - value ) < zone_width / 2:
                    count += 1
            zones_l.append( ( round(cluster,4), count ) )
        
        #
        # save the N zones that satisfy the minimum number of bounces, 
        # and add the high & low prices during this period
        #
        zones_l2 = []
        for price, count in zones_l:
            if count >= min_touches:
                zones_l2.append( price )
        zones_l2.append( min_price )
        zones_l2.append( max_price )
        zones_l2 = sorted( zones_l2 )
        
        #
        # store it for the NEXT date, but if it's Friday, store it for Sunday AND Monday
        #
        if curr_date.weekday() == 4:
            period_zones_d[ curr_date + datetime.timedelta( days = 2 ) ] = zones_l2
            period_zones_d[ curr_date + datetime.timedelta( days = 3 ) ] = zones_l2
        else:
            period_zones_d[ curr_date + datetime.timedelta( days = 1 ) ] = zones_l2

    # all time periods have been set up, store the results in a file named e.g.
    # SR_EURCAD_daily.pickle
    filename = 'data/SR_' + curr_pair + '_daily.pickle'
    print( 'writing', filename, ':')
    with open( filename, 'wb' ) as pickle_file:
        pickle.dump(period_zones_d, pickle_file, pickle.HIGHEST_PROTOCOL )
    
    print('finished.')
    return

#
# find highest or lowest value in a slice of bars[]
#
def mymax( dir, bars, start, width):
    best_idx = None
    best_val = None
    
    for idx in range(start, start+width):
       val = bars[ idx ][ 1 ]
       if best_val is None:
          best_val = val
          best_idx = idx
       elif dir == 1 and val > best_val:
          best_val = val
          best_idx = idx
       elif dir == -1 and val < best_val:
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

    parser.add_argument( '--csvfile',     action='store', required=True,  dest='csv_filename',  help='Input CSV file containing market' )
    parser.add_argument( '--fromdate',    action='store', required=False, dest='fromdate',      help='Starting date formatted MM/DD/YYYY' )
    parser.add_argument( '--todate',      action='store', required=False, dest='todate',        help='Ending date formatted MM/DD/YYYY' )
    parser.add_argument( '--pair',        action='store', required=True,  dest='curr_pair',     help='Currency pair ex: EUR/USD' )
    parser.add_argument( '--period',       action='store', required=True,  dest='period',         help='Lookback days for S&R' )
    parser.add_argument( '--min_ht',      action='store', required=True,  dest='min_ht',        help='Min center height percent' )
    parser.add_argument( '--zone_width',  action='store', required=True,  dest='zone_width',    help='Width of each SR zone' )
    parser.add_argument( '--min_touches', action='store', required=True,  dest='min_touches',   help='Min number of touches for each SR zone' )
    
    return parser.parse_args()

    main()

########################################################################
# main()
########################################################################

if __name__ == '__main__':
 
    #
    # process parameters from command line
    #
    args = parse_args()

    if args.fromdate is None:
        from_date = datetime.date( '1970, 1, 1' ).date()
    else:
        from_date = datetime.datetime.strptime( args.fromdate, '%m/%d/%Y' ).date()
    
    if args.todate is None:
        to_date = datetime.date( '2099, 12, 31' ).date()
    else:
        to_date = datetime.datetime.strptime( args.todate, '%m/%d/%Y' ).date()
    
    curr_pair = args.curr_pair.split( '/' )
    if len( curr_pair ) < 2:
        print( 'Invalid currency pair given:', args.curr_pair )
        quit()
    if curr_pair[ 0 ] == 'JPY' or curr_pair[ 1 ] == 'JPY' :
        zone_width  = float(args.zone_width)  * 100
    else:
        zone_width  = float(args.zone_width)
        
    #
    # do it
    #
    process( args.csv_filename, curr_pair[ 0 ] + curr_pair[ 1 ], from_date, to_date, \
             int(args.period), float(args.min_ht), zone_width, int(args.min_touches) )

