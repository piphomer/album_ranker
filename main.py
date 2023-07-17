import sqlite3
import pandas as pd

def read_db():
    dbfile = 'C:/Users/phill/Music/MM_20230716212410 - Copy.DB'
    con = sqlite3.connect(dbfile)
    cur = con.cursor()

    sql = """
        SELECT Artist, Album, SongTitle, Rating, SongLength
        FROM Songs
        WHERE length(Album) > 0
        """

    for row in cur.execute(sql):
        # print(row)
        output_list.append(row)

    con.close

    print(output_list)


def ranking_alg(df):

    #Group by album
    df.drop(['Title'],axis=1, inplace=True)
    df = df.groupby(['Artist','Album'], axis = 0).agg({'timerating': 'sum', 'Duration': 'sum'})
    df['piprating'] = df.timerating / df.Duration
    df.drop(['timerating','Duration'], axis=1,inplace=True)

    return df



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
        ('Sarah Blasko', 'The Overture & The Underscore', 'Remorse', 40, 938504)


    ]

    test_df = pd.DataFrame(test_list,columns=['Artist', 'Album', 'Title', 'Rating', 'Duration'])

    test_df['timerating'] = test_df.Duration * test_df.Rating

    return test_df

if __name__ == '__main__':

    output_list = []

    read_db()

    output_df = pd.DataFrame(output_list, columns=['Artist', 'Album', 'Title', 'Rating', 'Duration'])


    #for now use a test df

    output_df = create_test_dataframe()

    print(output_df)

    ranked_df = ranking_alg(output_df)

    print(ranked_df)

