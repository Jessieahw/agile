-- Creation SQL for the BBL part of the database, indexes included. Left out foreign keys for convenience.

CREATE TABLE IF NOT EXISTS BBL_Players (
    player_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS BBL_Matches (
    match_hash TEXT PRIMARY KEY,
    season     TEXT,
    date       TEXT,
    time       TEXT,
    team1      TEXT,
    team2      TEXT,
    winner     TEXT,
    link       TEXT
);

CREATE TABLE IF NOT EXISTS BBL_BattingInnings (
    bat_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id             INTEGER,
    match_hash            TEXT,
    season                TEXT,
    date                  TEXT,
    stadium               TEXT,
    city                  TEXT,
    team_playing          TEXT,
    total_runs_innings    INTEGER,
    total_wickets_innings INTEGER,
    runs                  INTEGER,
    balls                 INTEGER,
    fours                 INTEGER,
    sixes                 INTEGER,
    strike_rate           REAL,
    dismissal             TEXT
);

CREATE TABLE IF NOT EXISTS BBL_BowlingInnings (
    bowl_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id             INTEGER,
    match_hash            TEXT,
    season                TEXT,
    date                  TEXT,
    stadium               TEXT,
    city                  TEXT,
    team_bowling          TEXT,
    overs                 REAL,
    maidens               INTEGER,
    runs                  INTEGER,
    wickets               INTEGER,
    economy               REAL,
    no_balls              INTEGER,
    wides                 INTEGER,
    total_runs_innings    INTEGER,
    total_wickets_innings INTEGER
);

-- Handy indexes
CREATE INDEX IF NOT EXISTS idx_bat_player  ON BBL_BattingInnings(player_id);
CREATE INDEX IF NOT EXISTS idx_bowl_player ON BBL_BowlingInnings(player_id);