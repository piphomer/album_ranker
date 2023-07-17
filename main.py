import sqlite3
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def read_db():
    dbfile = 'C:/Users/phill/Music/MM_20230717212635.DB'
    con = sqlite3.connect(dbfile)
    cur = con.cursor()

    sql = """
        SELECT AlbumArtist, Album, SongTitle, Rating, SongLength
        FROM Songs
        WHERE length(Album) > 0
        """

    for row in cur.execute(sql):

        output_list.append(row)

    con.close

def create_dataframe(input_list):

    album_df = pd.DataFrame(input_list, columns=['Artist', 'Album', 'Title', 'Rating', 'Duration'])
    album_df['timerating'] = album_df.Duration * album_df.Rating

    return album_df

def create_test_dataframe():

    test_list = [
        ('Oasis', 'Definitely Maybe', 'Rock & Roll Star', 40, 328217),
        ('Oasis', 'Definitely Maybe', 'Shakermaker', 40, 313217),
        ('Oasis', 'Definitely Maybe', 'Live Forever', 90, 281642),
        ('Oasis', 'Definitely Maybe', 'Up In The Sky', 50, 273668),
        ('Oasis', 'Definitely Maybe', 'Columbia', 40, 381763),
        ('Oasis', 'Definitely Maybe', 'Supersonic', 80, 288486),
        ('Oasis', 'Definitely Maybe', 'Bring It On Down', 40, 262593),
        ('Oasis', 'Definitely Maybe', 'Cigarettes & Alcohol', 60, 294149),
        ('Oasis', 'Definitely Maybe', 'Slide Away', 80, 397489),
        ('Oasis', 'Definitely Maybe', 'Married With Children', 70, 197130),
        ('The National', 'Alligator', 'Secret Meeting', 80, 233736),
        ('The National', 'Alligator', 'Abel', 70, 225928),
        ('The National', 'Alligator', 'The Geese Of Beverly Road', 60, 305672),
        ('The National', 'Alligator', 'City Middle', 50, 276488),
        ('The National', 'Alligator', 'Mr. November', 60, 249480),
        ('The National', 'Alligator', 'Karen', 80, 248072),
        ('The National', 'Alligator', 'Lit Up', 60, 183944),
        ('The National', 'Alligator', 'Looking For Astronauts', 40, 212104),
        ('The National', 'Alligator', 'Daughters Of The Soho Riots', 70, 247560),
        ('The National', 'Alligator', 'Friend Of Mine', 40, 214152),
        ('The National', 'Alligator', 'Val Jester', 40, 189576),
        ('The National', 'Alligator', 'All The Wine', 60, 204296),
        ('Rickie Lee Jones', 'Rickie Lee Jones', 'On Saturday Afternoons In 1963', 60, 155506),
        ('Rickie Lee Jones', 'Rickie Lee Jones', 'Night Train', 80, 198896),
        ('Rickie Lee Jones', 'Rickie Lee Jones', 'Young Blood', 50, 247849),
        ('Rickie Lee Jones', 'Rickie Lee Jones', 'Easy Money', 60, 200280),
        ('Rickie Lee Jones', 'Rickie Lee Jones', 'The Last Chance Texaco', 40, 248241),
        ('Rickie Lee Jones', 'Rickie Lee Jones', 'Coolsville', 50, 232829),
        ('Rickie Lee Jones', 'Rickie Lee Jones', 'Weasel & The White Boys Cool', 80, 363859),
        ('Rickie Lee Jones', 'Rickie Lee Jones', 'Company', 40, 294817),
        ('Rickie Lee Jones', 'Rickie Lee Jones', 'After Hours', 40, 134243),
        ('Sarah Blasko', 'The Overture & The Underscore', 'All Coming Back', 40, 195976),
        ('Sarah Blasko', 'The Overture & The Underscore', 'Beautiful Secrets', -1, 204296),
        ('Sarah Blasko', 'The Overture & The Underscore', 'Always Worth It', 50, 227080),
        ('Sarah Blasko', 'The Overture & The Underscore', 'At Your Best', 50, 216584),
        ('Sarah Blasko', 'The Overture & The Underscore', 'Counting Sheep', 50, 261256),
        ('Sarah Blasko', 'The Overture & The Underscore', 'Perfect Now', 60, 213640),
        ('Sarah Blasko', 'The Overture & The Underscore', 'Sweet November', -1, 235400),
        ('Sarah Blasko', 'The Overture & The Underscore', 'Cinders', 50, 249480),
        ('Sarah Blasko', 'The Overture & The Underscore', 'True Intentions', 40, 251784),
        ('Sarah Blasko', 'The Overture & The Underscore', 'Remorse', 40, 938504),
        ('Laura Marling', "A Creature I Don't Know", 'The Muse', 60, 221335),
        ('Laura Marling', "A Creature I Don't Know", 'I Was Just A Card', 60, 210755),
        ('Laura Marling', "A Creature I Don't Know", "Don't Ask Me Why", 40, 238968),
        ('Laura Marling', "A Creature I Don't Know", 'Salinas', 60, 277342),
        ('Laura Marling', "A Creature I Don't Know", 'The Beast', 60, 345573),
        ('Laura Marling', "A Creature I Don't Know", 'Night After Night', 60, 308532),
        ('Laura Marling', "A Creature I Don't Know", 'My Friends', 60, 238367),
        ('Laura Marling', "A Creature I Don't Know", 'Rest In Bed', 40, 188525),
        ('Laura Marling', "A Creature I Don't Know", 'Sophia', 80, 291996),
        ('Laura Marling', "A Creature I Don't Know", 'All My Rage', 60, 171650)


    ]

    test_df = pd.DataFrame(test_list,columns=['Artist', 'Album', 'Title', 'Rating', 'Duration'])

    test_df['timerating'] = test_df.Duration * test_df.Rating

    return test_df

def ranking_alg(df):

    #Group by album
    df.drop(['Title'],axis=1, inplace=True)
    grouped_df = df.groupby(['Artist','Album'], axis = 0).agg({'timerating': 'sum', 'Duration': 'sum'})

    #Need to drop any album that doesn't have all its songs rated

    #Make a new df with the minimum rating from each album
    #Then merge it with the main df
    elimination_df = df.groupby(['Artist', 'Album'], axis = 0).agg({'Rating': 'min'})
    elimination_df.rename(columns = {'Rating':'AlbumMinRating'}, inplace =True)

    grouped_df = grouped_df.merge(elimination_df, how = 'left', on = ['Artist', 'Album'])

    #Calculate the Piprating (TM). This is an extremely basic first attempt (simple time-weighted average)
    grouped_df['piprating'] = grouped_df.timerating / grouped_df.Duration

    #Drop all rows with min rating -1 (means unrated in MM)
    grouped_df = grouped_df[grouped_df.AlbumMinRating != -1]

    #Drop unnecessary columns
    grouped_df.drop(['timerating','Duration', 'AlbumMinRating'], axis=1,inplace=True)

    return grouped_df


if __name__ == '__main__':

    output_list = []

    read_db()

    output_df = create_dataframe(output_list)

    # output_df = create_test_dataframe() #uncomment this line to use the test df

    ranked_df = ranking_alg(output_df).sort_values(by = "piprating", ascending = False)

    print(ranked_df)

