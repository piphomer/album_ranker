import sqlite3
import pandas as pd
import numpy as np
import os
import sys
import ast
import xlrd
from datetime import datetime as dt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.options.display.width = 250

def read_db():

    dbfile = 'C:/Users/phill/AppData/Roaming/MediaMonkey5/MM5.DB' #Slight risk of corruption by working on live DB

    if os.path.isfile(dbfile):
        con = sqlite3.connect(dbfile)
        cur = con.cursor()

        sql = """
            SELECT SongTitle,
                    ExtendedTags,
                    PlayCounter
            FROM Songs
            LIMIT 10
            """

        for row in cur.execute(sql):

            print(row[0])
            print(row[1])

            output = ast.literal_eval(row[1])

            # this_row = dict(row[1])

            # print()

            res = [sub['title'] for sub in output]

            print(res)

            input_list.append(row)

        con.close

    else:
        print("Database file not found")
        sys.exit()

if __name__ == '__main__':

    print("Play Count Anomaly Detector")

    input_list = []

    read_db()

    # print(input_list)