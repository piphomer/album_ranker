import sqlite3
import pandas as pd
import numpy as np
import os
import sys

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.options.display.width = 250

def read_db():
    dbfile = 'C:/Users/phill/Music/MM_20230726222029.DB'
    if os.path.isfile(dbfile):
        con = sqlite3.connect(dbfile)
        cur = con.cursor()

        sql = """
            SELECT AlbumArtist, Album, SongTitle, Rating, SongLength
            FROM Songs
            WHERE length(Album) > 0
            """

        for row in cur.execute(sql):

            input_list.append(row)

        con.close

    else:
        print("Database file not found")
        sys.exit()

def create_dataframe(input_list):

    df = pd.DataFrame(input_list, columns=['Artist', 'Album', 'Title', 'Rating', 'Duration'])

    return df

def ranking_alg(df):

    #Add a timerating column
    df['timerating'] = df.Duration * df.Rating

    #Add a timerating based on sqrt of duration
    #This is intended to reduce influence of long songs
    #and avoid albums dominated by one or more very long song getting overrated
    #e.g. Alice's Restaurant
    df['sqrt_of_duration'] = df['Duration'].pow(0.5)
    df['timerating_2'] = df.sqrt_of_duration * df.Rating

    #Make higher rated songs count more
    df['rating_squared'] = df.Rating.pow(2) / 100
    df['timerating_3'] = df.rating_squared * df.sqrt_of_duration

    #Group by album
    df.drop(['Title'],axis=1, inplace=True)
    grouped_df = df.groupby(['Album', 'Artist'], axis = 0)\
        .agg({'Rating': 'mean', 'timerating': 'sum', 'timerating_2': 'sum', 'timerating_3': 'sum', 'Duration': 'sum', 'sqrt_of_duration': 'sum'})

    #Need to drop any album that doesn't have all its songs rated

    #Make a new df with the minimum rating and standard deviation of rating for each album
    #Then merge it with the main df
    helper_df = df.groupby(['Album', 'Artist'], axis = 0).agg(
                                                            AlbumMinRating = ('Rating', 'min'),
                                                            AlbumSigma = ('Rating', 'std'),
                                                            AlbumDuration = ('Duration', 'sum'))\
                                                            .fillna(0)

    grouped_df = grouped_df.merge(helper_df, how = 'left', on = ['Album', 'Artist'])

    #Get a list of albums that are not fully rated
    unranked_albums_df = grouped_df[grouped_df.AlbumMinRating == -1]
    unranked_albums_df = unranked_albums_df.drop(['timerating', 'Duration', 'AlbumMinRating'], axis = 1)

    print("Number of unranked albums: {}".format(unranked_albums_df.shape[0]))

    #Drop all rows with min rating -1 (means unrated in MM)
    grouped_df = grouped_df[grouped_df.AlbumMinRating != -1]

    #Get mean and sigma of album lengths

    AlbumMeanLength = grouped_df.AlbumDuration.mean() / 1000 / 60
    print("Album Mean Length = {}".format(AlbumMeanLength))

    AlbumLengthSigma = grouped_df.AlbumDuration.std() / 1000 / 60
    print("Album Length Sigma = {}".format(AlbumLengthSigma))

    print("Album Max Length = {}".format(grouped_df.AlbumDuration.max()))

    #Calculate the Piprating (TM). This is an extremely basic first attempt (simple time-weighted average)
    grouped_df['piprating'] = grouped_df.timerating / grouped_df.Duration * 100
    grouped_df['piprating'] = grouped_df['piprating'].astype(int)

    #Calculate version 2 of Piprating(TM)
    grouped_df['piprating_2'] = grouped_df.timerating_2 / grouped_df.sqrt_of_duration * 100
    grouped_df['piprating_2'] = grouped_df['piprating_2'].astype(int)

    #Calculate version 3 of Piprating(TM)
    grouped_df['piprating_3'] = grouped_df.timerating_3 / grouped_df.sqrt_of_duration * 100
    grouped_df['piprating_3'] = grouped_df['piprating_3'].astype(int)

    #Calculate version 4 of Piprating(TM)
    grouped_df['piprating_4'] = grouped_df.timerating_2 / grouped_df.sqrt_of_duration * 100 * (1 + grouped_df.AlbumSigma / 60).pow(0.2)
    grouped_df['piprating_4'] = grouped_df['piprating_4'].astype(int)

    #Calculate version 5 of Piprating(TM)
    bin_labels = [1,2,3,4,5,6,7,8,9,10]
    grouped_df['rating_bin'] = pd.cut(grouped_df['piprating_4'], bins = 10, labels=bin_labels)
    grouped_df['rating_bin'] = grouped_df['rating_bin'].astype(int)

    grouped_df['duration_bin'] = pd.cut(grouped_df['AlbumDuration'], bins = 10, labels=bin_labels)
    grouped_df['duration_bin'] = grouped_df['duration_bin'].astype(int)
    # print(grouped_df.AlbumDuration.describe(percentiles=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1])/60000)
    grouped_df['pipscalefactor'] = (-0.03 * grouped_df['rating_bin'] +1 ) * (1-(grouped_df['duration_bin']-1)/9) \
                                    + (0.06 * grouped_df['rating_bin'] + 0.6) * (grouped_df['duration_bin']-1)/9

    grouped_df['piprating_5'] = grouped_df['piprating_4'] * grouped_df['pipscalefactor']


    #Drop unnecessary columns
    grouped_df.drop(['timerating', 'Duration', 'timerating_2',
                     'sqrt_of_duration','timerating_3','AlbumMinRating'
                     ,'AlbumSigma', 'AlbumDuration'], axis=1,inplace=True)

    return grouped_df, unranked_albums_df

def ratings_binning(df1):

    df1.loc[df1.Rating < 0, 'Rating'] = 0 #unrated tracks in MM have rating value -1 in the db file

    df1 = df1.groupby(['Rating'], axis=0).agg({'Title': 'count'})

    return df1


if __name__ == '__main__':

    input_list = []

    read_db()

    input_df = create_dataframe(input_list)

    ranked_df, unranked_df = ranking_alg(input_df)

    ranked_df.sort_values(by="piprating_5", ascending = False, inplace = True)

    ranked_df.reset_index(inplace=True)

    ranked_df.index = np.arange(1, len(ranked_df) + 1)

    print(ranked_df)

    print("Number of ranked albums: {}".format(ranked_df.shape[0]))

    #Put individual song ratings into bins
    binned_df = create_dataframe(input_list)
    binned_df = ratings_binning(binned_df)

    with pd.ExcelWriter('album_rankings.xlsx') as writer:
        ranked_df.to_excel(writer, sheet_name = "Album Rankings")
        unranked_df.to_excel(writer, sheet_name="Albums to be ranked")
        binned_df.to_excel(writer, sheet_name="Ratings Histogram")