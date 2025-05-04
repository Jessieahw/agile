import pandas as pd

# Load the dataset
df = pd.read_csv('players.csv')

# Define relevant columns for each position
columns_by_position = {
    'Forward': ['Name', 'Position', 'Goals', 'Assists', 'Shots', 'Shots on target', 'Shooting accuracy %', 
                'Big chances created', 'Big chances missed', 'Headed goals', 'Goals with right foot', 
                'Goals with left foot', 'Penalties scored', 'Freekicks scored'],
    'Midfielder': ['Name', 'Position', 'Goals', 'Assists', 'Passes', 'Passes per match', 'Big chances created', 
                   'Crosses', 'Cross accuracy %', 'Through balls', 'Accurate long balls', 'Tackles', 
                   'Interceptions', 'Recoveries', 'Duels won', 'Duels lost'],
    'Defender': ['Name', 'Position', 'Tackles', 'Tackle success %', 'Interceptions', 'Clearances', 
                 'Headed Clearance', 'Blocked shots', 'Recoveries', 'Duels won', 'Duels lost', 
                 'Aerial battles won', 'Aerial battles lost', 'Goals', 'Assists', 'Errors leading to goal'],
    'Goalkeeper': ['Name', 'Position', 'Clean sheets', 'Goals conceded', 'Saves', 'Penalties saved', 
                   'Punches', 'High Claims', 'Catches', 'Sweeper clearances', 'Throw outs', 'Goal Kicks']
}

# Split the dataset by position and save to separate files
for position, columns in columns_by_position.items():
    position_df = df[df['Position'] == position][columns]
    position_df.to_csv(f'{position.lower()}s.csv', index=False)

print("Dataset split by position and saved to separate files.")