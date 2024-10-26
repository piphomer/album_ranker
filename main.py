import sqlite3
import pandas as pd
import numpy as np
import os
import sys
import xlrd
from datetime import datetime as dt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.options.display.width = 250

album_type_list = ['All','Studio', 'Live', 'Greatest Hits', 'Compilation']

album_type_dict = {'All': 'all_df', 'Studio': 'studio_df', 'Live': 'live_df', 'Greatest Hits': 'greatest_hits_df',
                 'Compilation': 'compilation_df'}

def read_db():

    dbfile = 'C:/Users/phill/AppData/Roaming/MediaMonkey5/MM5.DB' #Slight risk of corruption by working on live DB

    if os.path.isfile(dbfile):
        con = sqlite3.connect(dbfile)
        cur = con.cursor()

        sql = """
            SELECT AlbumArtist,
                    Album,
                    SongTitle,
                    Rating,
                    SongLength,
                    Custom1,
                    Year/10000,
                    LastTimePlayed
            FROM Songs
            """

        for row in cur.execute(sql):

            input_list.append(row)

        con.close

    else:
        print("Database file not found")
        sys.exit()

def create_dataframe(input_list):

    df = pd.DataFrame(input_list, columns=['Artist', 'Album', 'Title', 'Rating', 'Duration', 'Album Type', 'Year', 'Last Played'])

    df['Album'].replace('', np.nan, inplace=True) #replace empty strings with NaN


    return df

def ranking_alg(album_type):

    this_df = input_df.copy(deep=True) #Work on a copy without modifying the original df

    #Add a timerating based on sqrt of duration to reduce influence of long songs
    #and avoid albums dominated by one or more very long song getting overrated
    this_df['sqrt_of_duration'] = this_df['Duration'].pow(0.5)
    this_df['timerating'] = this_df.sqrt_of_duration * this_df.Rating

    #Add a helper column to let us count how many unrated songs in each albun
    this_df['unrated_songs'] = np.where(this_df['Rating'] == -1, 1, 0)

    #Group by album
    this_df.drop(['Title'],axis=1, inplace=True)
    grouped_df = this_df.groupby(['Album', 'Artist'], axis = 0) \
        .agg({'Album Type': 'first',
              'Year': 'first',
              'Rating': 'mean',
              'timerating': 'sum',
              'Duration': 'sum',
              'sqrt_of_duration': 'sum',
              'unrated_songs': 'sum' })



    #Need to drop any album that doesn't have all its songs rated

    #Make a new df with the minimum rating and standard deviation of rating for each album
    #Then merge it with the main df
    helper_df = this_df.groupby(['Album', 'Artist'], axis = 0).agg(
        AlbumMinRating = ('Rating', 'min'),
        AlbumSigma = ('Rating', 'std')) \
        .fillna(0)

    grouped_df = grouped_df.merge(helper_df, how = 'left', on = ['Album', 'Artist'])

    #Get a list of albums that are not fully rated
    unranked_albums_df = grouped_df[grouped_df.AlbumMinRating == -1]
    unranked_albums_df = unranked_albums_df.drop(['Duration', 'AlbumMinRating'], axis = 1)

    print("Number of unranked albums: {}".format(unranked_albums_df.shape[0]))

    #Don't process these types of albums
    grouped_df = grouped_df[grouped_df['Album Type'] != 'Musical']
    grouped_df = grouped_df[grouped_df['Album Type'] != 'Radio Series']

    #Only process the desired album type
    if album_type != 'All':
        grouped_df = grouped_df[grouped_df['Album Type'] == album_type]

    #Drop all rows with min rating -1 (means unrated in MM)
    grouped_df = grouped_df[grouped_df.AlbumMinRating != -1]

    # Cap Album Duration at 100 mins..
    # (There are only very few albums longer than this so do a simple hack to avoid more complicated bin manipulation)
    grouped_df.Duration = grouped_df.Duration.clip(upper=6000000)

    #Calculate version 4 of Piprating(TM)
    grouped_df['piprating_4'] = grouped_df.timerating / grouped_df.sqrt_of_duration * 100 * (1 + grouped_df.AlbumSigma / 60).pow(0.3)
    grouped_df['piprating_4'] = grouped_df['piprating_4'].astype(int)

    #Calculate version 5 of Piprating(TM)

    bin_labels = []

    #Set the lower bound of each set of bins at zero:
    ratings_bin_edges = [0]
    duration_bin_edges = [0]

    for x in range(1,21, 1):
        bin_labels.append(x/2)
        ratings_bin_edges.append(2000 + 8000/20 * x)
        # the hard-coded numbers below represent the -3 sigma and +3 sigma album durations
        # of my music collection at the time of coding.
        duration_bin_edges.append(10.23 + 73*x/20 * 60*1000)

    duration_bin_edges[-1] = 10000000 #set the upper bound unrealistically high

    grouped_df['rating_bin'] = pd.cut(grouped_df['piprating_4'], ratings_bin_edges, labels=bin_labels)
    grouped_df['rating_bin'] = grouped_df['rating_bin'].astype(float)

    grouped_df['duration_bin'] = pd.cut(grouped_df['Duration'], duration_bin_edges, labels=bin_labels)
    grouped_df['duration_bin'] = grouped_df['duration_bin'].astype(float)

    #Boost good/long albums, penalise good/short and bad/long albums
    grouped_df['pipscalefactor'] = (-0.02 * grouped_df['rating_bin'] + 1) * (1 - grouped_df['duration_bin']/10) \
                                   + (0.05 * grouped_df['rating_bin'] + 0.8) * (grouped_df['duration_bin'])/10

    grouped_df['piprating_5'] = grouped_df['piprating_4'] * grouped_df['pipscalefactor']

    grouped_df['piprating_5'] = grouped_df['piprating_5'].astype(int)

    grouped_df['Duration'] = grouped_df['Duration']/1000/60
    grouped_df['Duration'] = grouped_df['Duration'].astype(int)

    #Drop unnecessary columns
    grouped_df.drop(['timerating',
                     'sqrt_of_duration',
                     'AlbumMinRating',
                     'AlbumSigma',
                     'Rating',
                     'unrated_songs'], axis=1,inplace=True)

    unranked_albums_df.drop(['Rating',
                             'timerating',
                             'sqrt_of_duration',
                             'AlbumSigma',
                             'Year'],axis=1,inplace=True)

    ranked_df = grouped_df.sort_values(by="piprating_5", ascending=False)

    ranked_df.reset_index(inplace=True)

    ranked_df.index = np.arange(1, len(ranked_df) + 1)

    unranked_albums_df.sort_values(by="unrated_songs", ascending=True, inplace=True)

    unranked_albums_df.reset_index(inplace=True)

    unranked_albums_df.index = np.arange(1, len(unranked_albums_df) + 1)

    if album_type == 'All':

        print(ranked_df.head(30))

        print("Number of ranked albums: {}".format(ranked_df.shape[0]))

    return ranked_df, unranked_albums_df

def albums_in_need_of_a_listen():

    this_df = input_df.copy(deep=True) #Work on a copy without modifying the original df

    #Drop radio series
    this_df = this_df[this_df['Album Type'] != 'Radio Series']

    #group by album, on last played
    this_df.drop(['Title'],axis=1, inplace=True)
    this_df = this_df.groupby(['Album', 'Artist'], axis = 0) \
        .agg({'Last Played': 'min'})


    #sort by Last Played
    this_df = this_df.sort_values(by="Last Played", ascending=True)

    this_df['Last Played'] =  this_df['Last Played'].apply(lambda x : xlrd.xldate_as_datetime(x, 0).strftime("%d %b %Y"))

    print(this_df.head(20))

    #

def top_heavy_albums():

    #Find albums where the earliest tracks have loads of plays and later tracks have been neglected

    this_df = input_df.copy(deep=True) #Work on a copy without modifying the original df

    #group by album

    this_df.drop(['Title'],axis=1, inplace=True)
    grouped_df = this_df.groupby(['Album', 'Artist'], axis = 0) \
        .agg({'Album Type': 'first',
              'Year': 'first',
              'Rating': 'mean',
              'timerating': 'sum',
              'Duration': 'sum',
              'sqrt_of_duration': 'sum',
              'unrated_songs': 'sum' })


    #sort by Last Played
    this_df = this_df.sort_values(by="Last Played", ascending=True)

    this_df['Last Played'] =  this_df['Last Played'].apply(lambda x : xlrd.xldate_as_datetime(x, 0).strftime("%d %b %Y"))

    print(this_df.head(20))

    #

def ratings_binning(df1):

    df1.loc[df1.Rating < 0, 'Rating'] = 0 #unrated tracks in MM have rating value -1 in the db file

    df1['Rating'] = df1['Rating'] / 20

    df1 = df1.groupby(['Rating'], axis=0).agg({'Title': 'count'})

    return df1

def output_to_excel():

    print("Writing output to Excel...")

    with pd.ExcelWriter('album_rankings.xlsx', engine="xlsxwriter") as writer:
        workbook = writer.book

        for album_df in album_type_df_dict:

            album_type_df_dict[album_df].to_excel(writer, sheet_name = album_df, startrow=1, header=False, index=True)
            # Get the xlsxwriter workbook and worksheet objects.
            worksheet = writer.sheets[album_df]
            # Get the dimensions of the dataframe.
            (max_row, max_col) = album_type_df_dict[album_df].shape
            # Create a list of column headers, to use in add_table().
            column_settings = [{"header": column} for column in album_type_df_dict[album_df].columns]

            column_settings.insert(0,{'header':'#'})
            # Add the Excel table structure. Pandas will add the data.
            worksheet.add_table(0, 0, max_row, max_col, {"columns": column_settings,
                                                         "style": "Table Style Medium 1",
                                                         "banded_rows": True})

            # Make the columns wider for clarity.
            worksheet.set_column(0, 0, 4)
            worksheet.set_column(1, 1, 75)
            worksheet.set_column(2, 2, 38)
            worksheet.set_column(3, 3, 14)


        unranked_df.to_excel(writer, sheet_name="Albums to be ranked", startrow=1, header=False, index=True)
        worksheet = writer.sheets["Albums to be ranked"]
        # Get the dimensions of the dataframe.
        (max_row, max_col) = unranked_df.shape
        # Create a list of column headers, to use in add_table().
        column_settings = [{"header": column} for column in unranked_df.columns]

        column_settings.insert(0,{'header':'#'})
        # Add the Excel table structure. Pandas will add the data.
        worksheet.add_table(0, 0, max_row, max_col, {"columns": column_settings,
                                                     "style": "Table Style Medium 1",
                                                     "banded_rows": True})

        # Make the columns wider for clarity.
        worksheet.set_column(0, 0, 4)
        worksheet.set_column(1, 1, 75)
        worksheet.set_column(2, 2, 38)
        worksheet.set_column(3, 3, 14)

        binned_df.to_excel(writer, sheet_name="Ratings Histogram")
        worksheet = writer.sheets["Ratings Histogram"]

        (max_row, max_col) = binned_df.shape

        worksheet.add_table(0, 0, max_row, max_col, {"columns": [{'header': 'Rating'}, {'header': 'Count'}]})

        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({"categories": "='Ratings Histogram'!$A$2:$A$12",
                          "values": "='Ratings Histogram'!$B$2:$B$12",
                          'data_labels': {'value': True}})
        chart.set_title({'name': 'Ratings Distribution'})
        chart.set_legend({'none': True})

        # Insert the chart into the worksheet.
        worksheet.insert_chart('D2', chart)

        writer.close

if __name__ == '__main__':

    input_list = []

    read_db()

    #Put individual song ratings into bins
    binned_df = create_dataframe(input_list)
    binned_df = ratings_binning(binned_df)

    input_df = create_dataframe(input_list)

    input_df.dropna(subset=['Album'], inplace=True)     #then use dropna to get rid of non-album songs

    album_type_df_dict = {}

    for album_type in album_type_list:

        print("Processing", album_type, "album type")
        #create a df for each type of album in the album list
        album_type_df_dict[album_type], unranked_df = ranking_alg(album_type)

    albums_in_need_of_a_listen()

    output_to_excel()
