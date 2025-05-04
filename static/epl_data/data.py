import pandas as pd


df = pd.read_csv('results.csv', encoding='latin1')

# Fill missing values with 0 for critical columns
df.fillna({
    'HS': 0, 'HST': 0, 'HF': 0, 'HY': 0, 'HR': 0,
    'AS': 0, 'AST': 0, 'AF': 0, 'AY': 0, 'AR': 0
}, inplace=True)

# Initialize an empty dictionary to store aggregated data
team_stats = {}

# Loop through each match and update stats for home and away teams
for index, match in df.iterrows():
    # Process Home Team Data
    home_team = match['HomeTeam']
    if home_team not in team_stats:
        team_stats[home_team] = {
            'shots': 0, 'shots_on_target': 0, 'goals': 0, 'fouls': 0, 
            'yellow_cards': 0, 'red_cards': 0, 'matches': 0
        }
    team_stats[home_team]['shots'] += match['HS']
    team_stats[home_team]['shots_on_target'] += match['HST']
    team_stats[home_team]['goals'] += match['FTHG']
    team_stats[home_team]['fouls'] += match['HF']
    team_stats[home_team]['yellow_cards'] += match['HY']
    team_stats[home_team]['red_cards'] += match['HR']
    team_stats[home_team]['matches'] += 1

    # Process Away Team Data
    away_team = match['AwayTeam']
    if away_team not in team_stats:
        team_stats[away_team] = {
            'shots': 0, 'shots_on_target': 0, 'goals': 0, 'fouls': 0, 
            'yellow_cards': 0, 'red_cards': 0, 'matches': 0
        }
    team_stats[away_team]['shots'] += match['AS']
    team_stats[away_team]['shots_on_target'] += match['AST']
    team_stats[away_team]['goals'] += match['FTAG']
    team_stats[away_team]['fouls'] += match['AF']
    team_stats[away_team]['yellow_cards'] += match['AY']
    team_stats[away_team]['red_cards'] += match['AR']
    team_stats[away_team]['matches'] += 1

# Calculate league averages
league_avg_shots = sum(stats['shots'] for stats in team_stats.values()) / sum(stats['matches'] for stats in team_stats.values())
league_avg_fouls = sum(stats['fouls'] for stats in team_stats.values()) / sum(stats['matches'] for stats in team_stats.values())

# Calculate averages and prepare the result list
result = []
for team, stats in team_stats.items():
    # Skip teams with zero matches
    if stats['matches'] == 0:
        print(f"Skipping team with zero matches: {team}")
        continue

    # Impute default values for teams with zero shots
    if stats['shots'] == 0:
        stats['shots'] = league_avg_shots
        stats['fouls'] = league_avg_fouls
        print(f"Imputed default values for team: {team}")

    # Calculate averages
    avg_shots = stats['shots'] / stats['matches']
    avg_goals = stats['goals'] / stats['matches']
    avg_fouls = stats['fouls'] / stats['matches']
    avg_cards = (stats['yellow_cards'] + stats['red_cards']) / stats['matches']
    shot_accuracy = stats['shots_on_target'] / stats['shots'] if stats['shots'] > 0 else 0  # Avoid division by 0

    # Skip teams with zero in their final data
    if avg_shots == 0 or avg_goals == 0 or avg_fouls == 0 or avg_cards == 0 or shot_accuracy == 0:
        print(f"Skipping team with zero in final data: {team}")
        continue

    # Append data to the result list
    result.append({
        'Team': team,
        'Average Shots per Match': avg_shots,
        'Average Goals per Match': avg_goals,
        'Average Fouls per Match': avg_fouls,
        'Average Cards per Match': avg_cards,
        'Shot Accuracy': shot_accuracy
    })

# Convert result list to DataFrame
result_df = pd.DataFrame(result)

# Export to a new CSV
result_df.to_csv('team_comparison_stats.csv', index=False)

print("CSV file 'team_comparison_stats.csv' has been created.")