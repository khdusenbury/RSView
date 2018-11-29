""" Map the global distribution of Respiratory Syncytial Virus (RSV) by collection date, location,
and viral subtype or genotype """

import argparse
import pandas as pd
import numpy as np
import plotly.plotly as py
import matplotlib.pyplot as plt
from matplotlib import colors


JITTER_DICT = {'A':1.0, 'B':-1.0}
DATAFILES = ['./data/RSVG_gb_metadata_0-5000.csv', './data/RSVG_gb_metadata_5000-10000.csv',
             './data/RSVG_gb_metadata_10000-15000.csv', './data/RSVG_gb_metadata_15000+.csv']

def organize_data(datafiles):
    """
    Load .csv files containing RSV sequence data and extract relevant columns. Ensure country
    names to conform to standard names used to retrieve latitude and longitude data. Return a
    DataFrame where each sequence is row containing country, genotype, subtype, and collection date
    information.
    """

    rsv_df = pd.DataFrame()

    for datafile in datafiles:
        temp_df = pd.read_csv(datafile, usecols=['collection_date', 'country', 'subtype',
                                                 'genotype'], parse_dates=['collection_date'])
        rsv_df = rsv_df.append(temp_df, ignore_index=True)

    rsv_df['year'] = rsv_df['collection_date'].apply(lambda x: x.year)

    #Fix specific country names where city is given
    countries_with_cities = ['Brazil', 'China', 'Russia', 'New Zealand', 'Spain', 'Kenya',
                             'Germany', 'Egypt', 'India', 'Japan', 'Canada', 'Italy',
                             'Malaysia', 'Jordan', 'Saudi Arabia', 'Myanmar', 'Netherlands']
    for con in countries_with_cities:
        rsv_df['country'] = np.where(rsv_df['country'].str.contains(con), con, rsv_df['country'])

    #Fix specific country names where lat/lon table uses alternate country name
    rsv_df['country'] = np.where(rsv_df['country'].str.contains('USA'), 'United States',
                                 rsv_df['country'])
    rsv_df['country'] = np.where(rsv_df['country'].str.contains('South Korea'), 'Korea',
                                 rsv_df['country'])
    rsv_df['country'] = np.where(rsv_df['country'].str.contains('Viet Nam'), 'Vietnam',
                                 rsv_df['country'])
    rsv_df['country'] = np.where(rsv_df['country'].str.contains('Laos'), 'Lao PDR',
                                 rsv_df['country'])

    return rsv_df


def count_types(rsv_df, jitter_dict, level):
    """
    Restructure the DataFrame so that each row indicates the total number of RSV sequences
    found in each country, each year, for each subtype or genotype (specified by the level argument)
    """

    #use lat and long so datapoints can be jittered to show multiple subtypes
    #lat and long data from https://worldmap.harvard.edu/data/geonode:country_centroids_az8

    lat_lon = pd.read_csv('./data/country_centroids.csv',
                          usecols=['name', 'brk_a3', 'Longitude', 'Latitude']
                          ).rename(columns={'name':'country', 'brk_a3': 'country_code'})

    if level == 'subtype':
        #count number of rows(seqs) from each country that are each subtype
        df_group = pd.DataFrame({'count' : rsv_df.groupby(['country', 'subtype',
                                                           'year']).size()}).reset_index()

        #compile country-specific subtype count data with lat and long for plotting
        organized_df = df_group.merge(lat_lon, how='left', left_on='country', right_on='country')

    elif level == 'genotype':
        #count number of rows(seqs) from each country that are each subtype
        genotype_subset = rsv_df[rsv_df['genotype'].notnull()]
        df_group = pd.DataFrame(
            {'count' : genotype_subset.groupby(['country', 'subtype', 'genotype',
                                                'year']).size()}).reset_index()

        #compile country-specific subtype count data with lat and long for plotting
        organized_df = df_group.merge(lat_lon, how='left', left_on='country', right_on='country')


    #Jitter points for countries that have multiple subtypes, so markers on map don't overlap
    country_group = organized_df.groupby('country').size()


    #With data separated by year
    organized_df['adj_lon'] = np.where(country_group[organized_df['country']] > 1,
                                       (organized_df['Longitude']+organized_df.subtype.map(
                                           lambda x: jitter_dict[x])), organized_df['Longitude'])

    organized_df['adj_lat'] = np.where(country_group[organized_df['country']] > 1,
                                       (organized_df['Latitude']+organized_df.subtype.map(
                                           lambda x: jitter_dict[x])), organized_df['Latitude'])

    #Find any country names that don't match between sequence DF and lat/lon database
    if len(organized_df[organized_df['adj_lon'].isnull()]) != 0:
        print('Warning: the following country names do not match between sequence DataFrames and\
               "country_centroids.csv"' +
              str(organized_df[organized_df['adj_lon'].isnull()]['country']))

    return organized_df


def map_rsv(organized_df, level):
    """
    Use ploy.ly to map RSV sequences onto a global map, with bubbles indicating the virus
    collection location. Bubbles are colored according to subtype or genotype (indicated by the
    level argument) and their size is proportional to the number of sequences collected from the
    given location. Maps are separated temporally by collection date and the slider at the bottom of
    the plot allows the user to scroll through time to see how RSV distribution changes over time.
    """

    year_range = [yr for yr in range(int(organized_df.year.min()), int(organized_df.year.max()))]

    if level == 'subtype':
        type_list = ['A', 'B']
        cmap = {'A':'royalblue', 'B':'salmon'}

    elif level == 'genotype':
        a_genotypes = list(set(organized_df[organized_df['subtype'] == 'A']['genotype'].tolist()))
        b_genotypes = list(set(organized_df[organized_df['subtype'] == 'B']['genotype'].tolist()))
        type_list = a_genotypes + b_genotypes

        cmap = {}
        blues = plt.get_cmap('Blues')
        reds = plt.get_cmap('Reds')

        for a_genotype in a_genotypes:
            cmap[a_genotype] = colors.to_hex(
                blues((a_genotypes.index(a_genotype)+1.0)/len(a_genotypes)))
        for b_genotype in b_genotypes:
            cmap[b_genotype] = colors.to_hex(
                reds((b_genotypes.index(b_genotype)+1.0)/len(b_genotypes)))

    scale_markers = 1
    map_list = []

    for i in range(len(organized_df)):

        map_country = dict(
            type='scattergeo',
            lat=[organized_df.loc[i, 'adj_lat']],
            lon=[organized_df.loc[i, 'adj_lon']],
            marker=dict(
                size=[np.min([organized_df.loc[i, 'count']*scale_markers, 75])],
                sizemin=5,
                color=cmap[organized_df.loc[i, level]],
                line=dict(width=0.5, color='rgb(40,40,40)'),
                opacity=0.5,
                sizemode='diameter'),
            hovertext=(organized_df.loc[i, 'country'] + ', ' + str(level) + ' ' +
                       organized_df.loc[i, level] + ' : ' + str(organized_df.loc[i, 'count'])+
                       'sequences'),
            name=organized_df.loc[i, 'country']+' '+organized_df.loc[i, level],
            legendgroup=organized_df.loc[i, level],
            showlegend=False,
            hoverinfo='text'
        )
        map_list.append(map_country)

    #Work around for showing legend
    for subtype in type_list:
        subtype_legend = dict(
            type='scattergeo',
            lat=[180.0],
            lon=[180.0],
            marker=dict(
                size=scale_markers*10,
                color=cmap[subtype],
                opacity=0.5,
                sizemode='area'),
            legendgroup=subtype,
            name=str(level)+ ' ' + subtype,
            showlegend=True,
            hovertext=None,
            )
        map_list.append(subtype_legend)

    steps = []
    for year in year_range:
        step = dict(
            method='restyle',
            label=year,
            args=['visible', [False] * (len(organized_df)+len(type_list))])
        for i in range(len(organized_df)):
            if organized_df.loc[i, 'year'] == year:
                step['args'][1][i] = True # Toggle i'th year to "visible"
        for subtype in type_list:
            step['args'][1][(len(organized_df)+type_list.index(subtype))] = True
        steps.append(step)

    layout = dict(
        title='Global distribution of RSV',
        sliders=[dict(
            steps=steps)],
        geo=dict(
            scope='world',
            showland=True,
            landcolor='rgb(217, 217, 217)',
            countrywidth=1,
            ),)

    fig = dict(data=map_list, layout=layout)
    py.plot(fig)


def main(level):
    """
    Run organize_data, count_types, map_rsv
    """
    rsv_df = organize_data(DATAFILES)
    organized_df = count_types(rsv_df, JITTER_DICT, level)
    map_rsv(organized_df, level)


if __name__ == '__main__':

    PARSER = argparse.ArgumentParser(description="Plot global distribution of RSV")
    PARSER.add_argument(
        'level', type=str, choices=['subtype', 'genotype'],
        help="Specify whether the subtype or genotype of RSV sequences should be plotted")
    ARGS = PARSER.parse_args()

    main(ARGS.level)