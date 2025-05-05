# BBL Stager tool

import sqlite3, pandas as pd, hashlib, re, math
from typing import Optional

# --- Paths to the Data ---
BATTING_FILE = 'BBL_Batting_Stats_All_Years.xlsx'
BOWLING_FILE = 'BBL_Bowling_Stats_All_Years.xlsx'
MATCH_FILE   = 'BBL_Match_Stats_All_Years.xlsx'
DB_FILE      = 'data.db'

# --- Utility functions ---
def clean(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    return val

def normalize_player_name(name: Optional[str]) -> Optional[str]:
    """
    Strip out any parenthesized content and trim whitespace.
    E.g. "John Smith (c & wk)" → "John Smith"
    """
    if not name:
        return None
    # remove any " ( ... )" fragments
    cleaned = re.sub(r'\s*\([^)]*\)', '', name).strip()
    return cleaned or None

def make_match_uuid_via_hash(season: str, match_details: str) -> str:
    base = f"{season}|{match_details}"
    return hashlib.sha1(base.encode('utf-8')).hexdigest()[:16]

def parse_teams(match_details: str) -> tuple[Optional[str], Optional[str]]:
    if not match_details:
        return (None, None)
    parts = re.split(r'\bvs\b', str(match_details), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        team1 = parts[0].strip() or None
        team2 = parts[1].split(',')[0].strip() or None
        return (team1, team2)
    return (None, None)

# --- Connect to DB ---
conn = sqlite3.connect(DB_FILE)
cur  = conn.cursor()

# --- Player cache and lookup ---
player_cache: dict[str, int] = {}

def get_player_id(name: str) -> int:
    """
    Return the player_id for 'name'.  Matching happens in this order:
     1) exact (case-insensitive)
     2) substring match (new name in existing name, or vice-versa)
     3) insert new player
    """
    key = name.lower()
    if key in player_cache:
        return player_cache[key]

    # 1) exact match
    cur.execute(
        "SELECT player_id FROM BBL_Players WHERE lower(player_name)=?",
        (key,)
    )
    row = cur.fetchone()
    if row:
        pid = row[0]
    else:
        # 2) substring match
        cur.execute("SELECT player_id, player_name FROM BBL_Players")
        pid = None
        for existing_id, existing_name in cur.fetchall():
            en = existing_name.lower()
            if key in en or en in key:
                pid = existing_id
                break

        # 3) insert new
        if pid is None:
            cur.execute(
                "INSERT INTO BBL_Players (player_name) VALUES (?)",
                (name,)
            )
            pid = cur.lastrowid

    player_cache[key] = pid
    return pid

# --- STEP 1: Load matches ---
print('Loading match list …')
match_df = pd.read_excel(MATCH_FILE)
match_df.columns = match_df.columns.str.strip()

for _, row in match_df.iterrows():
    season        = clean(row.get('Season'))
    match_details = clean(row.get('Teams'))
    mhash         = make_match_uuid_via_hash(season, match_details)
    team1, team2  = parse_teams(match_details)

    cur.execute('''
        INSERT OR IGNORE INTO BBL_Matches (
            match_hash, season, date, time, team1, team2, winner, link
        ) VALUES (?,?,?,?,?,?,?,?)
    ''', (
        mhash,
        season,
        clean(row.get('Date')),
        clean(row.get('Time')),
        team1,
        team2,
        clean(row.get('Winners')),
        clean(row.get('Links'))
    ))
conn.commit()
print('Matches loaded.')

# --- STEP 2: Load batting innings ---
print('Loading batting innings …')
bat_df = pd.read_excel(BATTING_FILE)
bat_df.columns = bat_df.columns.str.strip()

for _, row in bat_df.iterrows():
    raw_name = clean(row.get('Batsman Names'))
    player   = normalize_player_name(raw_name)
    if not player:
        continue

    season = clean(row.get('Season'))
    mhash  = make_match_uuid_via_hash(season, clean(row.get('Match Details')))
    pid    = get_player_id(player)

    cur.execute('''
        INSERT INTO BBL_BattingInnings (
            player_id, match_hash, season, date, stadium, city, team_playing,
            total_runs_innings, total_wickets_innings, runs, balls, fours,
            sixes, strike_rate, dismissal
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        pid,
        mhash,
        season,
        clean(row.get('Date')),
        clean(row.get('Stadium')),
        clean(row.get('City')),
        clean(row.get('Team Playing')),
        clean(row.get('Total Runs')),
        clean(row.get('Total Wickets')),
        clean(row.get('Runs Scored')),
        clean(row.get('Balls Played')),
        clean(row.get('Fours')),
        clean(row.get('Sixes')),
        clean(row.get('Strike Rate')),
        clean(row.get('Out/Not Out'))
    ))
conn.commit()
print('Batting innings loaded.')

# --- STEP 3: Load bowling innings ---
print('Loading bowling innings …')
bowl_df = pd.read_excel(BOWLING_FILE)
bowl_df.columns = bowl_df.columns.str.strip()

for _, row in bowl_df.iterrows():
    raw_name = clean(row.get('Bowler Name'))
    player   = normalize_player_name(raw_name)
    if not player:
        continue

    season = clean(row.get('Season'))
    mhash  = make_match_uuid_via_hash(season, clean(row.get('Match Details')))
    pid    = get_player_id(player)

    cur.execute('''
        INSERT INTO BBL_BowlingInnings (
            player_id, match_hash, season, date, stadium, city, team_bowling,
            overs, maidens, runs, wickets, economy, no_balls, wides,
            total_runs_innings, total_wickets_innings
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        pid,
        mhash,
        season,
        clean(row.get('Date')),
        clean(row.get('Stadium')),
        clean(row.get('City')),
        clean(row.get('Team Bowling')),
        clean(row.get('Overs')),
        clean(row.get('Maidens')),
        clean(row.get('Runs')),
        clean(row.get('Wickets')),
        clean(row.get('Economies')),
        clean(row.get('No Balls')),
        clean(row.get('Wides')),
        clean(row.get('Total Runs Conceeded')),
        clean(row.get('Total Wickets Taken'))
    ))
conn.commit()
print('Bowling innings loaded.')

conn.close()
print('All BBL data successfully staged into the SQLite database!')
