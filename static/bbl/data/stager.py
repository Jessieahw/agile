# BBL Stager tool

import sqlite3, pandas as pd, hashlib, re, math
from typing import Optional
# Setup global file paths for ease of use.
BATTING_FILE = 'BBL_Batting_Stats_All_Years.xlsx'
BOWLING_FILE = 'BBL_Bowling_Stats_All_Years.xlsx'
MATCH_FILE   = 'BBL_Match_Stats_All_Years.xlsx'
DB_FILE      = 'data.db'

# Utility functions
def clean(val):
    if (val is None or (isinstance(val, float) and math.isnan(val))):
        return None
    else:
        return val

# UUID Function for each Match
def make_match_uuid_via_hash(season: str, match_details: str) -> str:
    base = f"{season}|{match_details}"
    return hashlib.sha1(base.encode('utf-8')).hexdigest()[:16]

# Function to parse team names, from blanks to two teams, using regex recognition of 'vs' (case insensitive) split just once if it is matched.
# Returns (team1, team2) where either or both could be None.
def parse_teams(match_details: str) -> tuple[Optional[str], Optional[str]]:
    if match_details is None:
        return (None, None)
    parts = re.split(r' vs | Vs | VS ', str(match_details), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) >= 2:
        team1 = parts[0].strip()
        team2 = parts[1].split(',')[0].strip()
        return (team1, team2)
    return (None, None)

# SQLite Connection + Cahce
conn = sqlite3.connect(DB_FILE)
cur  = conn.cursor()

# Cache for faster lookups.
player_cache: dict[str, int] = {}

# Certain search function that converts names to the specific id.
def get_player_id(name: str) -> int:
    # First check the cache and short circuit the rest to return it fast if found. Otherwise continue.
    if name in player_cache:
        return player_cache[name]
    # Get the first matching name.
    cur.execute('SELECT player_id FROM BBL_Players WHERE player_name = ?', (name,))
    res = cur.fetchone()
    if res:
        # Get player id if it exists.
        pid = res[0]
    else:
        # If no player id is found, create one and use that one instead.
        cur.execute('INSERT INTO BBL_Players (player_name) VALUES (?)', (name,))
        pid = cur.lastrowid

    # Add it to the cache, then return it
    player_cache[name] = pid
    return pid

# FIRST: We will load matches.
print('Loading match list …')
match_df = pd.read_excel(MATCH_FILE)
# Clean column names of trailing or preceding blanks.
match_df.columns = match_df.columns.str.strip()

# Iterate through each row via Panda's iterrows() function:
for _, row in match_df.iterrows():
    # Extract and clean the season, match details, generate the uuid hash, and get the team names (if any).
    season        = clean(row.get('Season'))
    match_details = clean(row.get('Teams'))
    mhash         = make_match_uuid_via_hash(season, match_details)
    team1, team2  = parse_teams(match_details)

    # Insert to the DB.
    cur.execute('''INSERT OR IGNORE INTO BBL_Matches (
            match_hash, season, date, time, team1, team2, winner, link)
            VALUES (?,?,?,?,?,?,?,?)''', (
        mhash, season, clean(row.get('Date')), clean(row.get('Time')),
        team1, team2, clean(row.get('Winners')), clean(row.get('Links'))
    ))
# Commit all changes:
conn.commit()
print('Matches loaded.')

# SECOND: We will load the batting innings next.
print('Loading batting innings …')
bat_df = pd.read_excel(BATTING_FILE)
bat_df.columns = bat_df.columns.str.strip()

# Iterate through each row via Pandas function as done before:
for _, row in bat_df.iterrows():
    # Get Player name if it exists. In any case, continue.
    player = clean(row.get('Batsman Names'))
    if not player:
        continue

    # Get the clean season [name], uuid hash, and the player id.
    season = clean(row.get('Season'))
    mhash  = make_match_uuid_via_hash(season, clean(row.get('Match Details')))
    pid    = get_player_id(player)

    # Insert to the database.
    cur.execute('''INSERT INTO BBL_BattingInnings (
            player_id, match_hash, season, date, stadium, city, team_playing,
            total_runs_innings, total_wickets_innings, runs, balls, fours,
            sixes, strike_rate, dismissal)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
        pid, mhash, season, clean(row.get('Date')), clean(row.get('Stadium')),
        clean(row.get('City')), clean(row.get('Team Playing')),
        clean(row.get('Total Runs')), clean(row.get('Total Wickets')),
        clean(row.get('Runs Scored')), clean(row.get('Balls Played')),
        clean(row.get('Fours')), clean(row.get('Sixes')),
        clean(row.get('Strike Rate')), clean(row.get('Out/Not Out'))
    ))
# Commit all changes.
conn.commit()
print('Batting innings loaded.')

# THIRD (and final step): We will load the bowling innings data.
print('Loading bowling innings …')
bowl_df = pd.read_excel(BOWLING_FILE)
# As before, clean up the column names.
bowl_df.columns = bowl_df.columns.str.strip()

# Iterate through the rows of the data:
for _, row in bowl_df.iterrows():
    # Get the bowler name if it exists.
    player = clean(row.get('Bowler Name'))
    if not player:
        continue

    # Get the clean season name, uuid hash of the match, and the player id.
    season = clean(row.get('Season'))
    mhash  = make_match_uuid_via_hash(season, clean(row.get('Match Details')))
    pid    = get_player_id(player)

    # Insert the row to the database
    cur.execute('''INSERT INTO BBL_BowlingInnings (
            player_id, match_hash, season, date, stadium, city, team_bowling,
            overs, maidens, runs, wickets, economy, no_balls, wides,
            total_runs_innings, total_wickets_innings)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
        pid, mhash, season, clean(row.get('Date')), clean(row.get('Stadium')),
        # Clean the city, overs, wickets, no balls, and total runs conceded columns before executed the parameterized query.
        clean(row.get('City')), clean(row.get('Team Bowling')),
        clean(row.get('Overs')), clean(row.get('Maidens')), clean(row.get('Runs')),
        clean(row.get('Wickets')), clean(row.get('Economies')),
        clean(row.get('No Balls')), clean(row.get('Wides')),
        clean(row.get('Total Runs Conceeded')), clean(row.get('Total Wickets Taken'))
    ))
# Commit all changes, close the connection, and done.
conn.commit()
print('Bowling innings loaded.')

conn.close()
print('All BBL data successfully staged into the SQLite database!')
