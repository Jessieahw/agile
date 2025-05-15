from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app ,Flask,jsonify
from extensions import db            
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from models import Submission
from models import PlayerComparison
import os, csv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from forms import NBADataForm




nba_bp = Blueprint(
    'nba', 
    __name__, 
    template_folder='templates/nba', 
    static_folder='static',
    url_prefix='/nba'
)


df = pd.read_csv('database_24_25.csv')[['Player', 'PTS', 'AST', 'STL', 'BLK', 'TRB']].dropna()

# ─── Routes ────────────────────────────────────────────────────────────
@nba_bp.route('/', endpoint='home')
@login_required
def home():
    return render_template('nba.html')


@nba_bp.route('/teams')
@nba_bp.route('/teams.html')
@nba_bp.route('/teams/<team_key>')
def teams(team_key=None):
    team_key = request.args.get('team')
    teams = {
                'ATL': 'Atlanta Hawks',
        'BOS': 'Boston Celtics',
        'BKN': 'Brooklyn Nets',
        'CHA': 'Charlotte Hornets',
        'CHI': 'Chicago Bulls',
        'CLE': 'Cleveland Cavaliers',
        'DAL': 'Dallas Mavericks',
        'DEN': 'Denver Nuggets',
        'DET': 'Detroit Pistons',
        'GS' : 'Golden State Warriors',
        'HOU': 'Houston Rockets',
        'IND': 'Indiana Pacers',
        'LAC': 'Los Angeles Clippers',
        'LAL': 'Los Angeles Lakers',
        'MEM': 'Memphis Grizzlies',
        'MIA': 'Miami Heat',
        'MIL': 'Milwaukee Bucks',
        'MIN': 'Minnesota Timberwolves',
        'NO': 'New Orleans Pelicans',  # or 'NO'
        'NY' : 'New York Knicks',
        'OKC': 'Oklahoma City Thunder',
        'ORL': 'Orlando Magic',
        'PHI': 'Philadelphia 76ers',
        'PHO': 'Pheonix Suns',
        'POR': 'Portland Trail Blazers',
        'SAC': 'Sacramento Kings',
        'SA' : 'San Antonio Spurs',
        'TOR': 'Toronto Raptors',
        'UTA': 'Utah Jazz',
        'WAS': 'Washington Wizards',
    }
    logos = {
        key: url_for('static', filename=f'nba_logos/{key}.png')
        for key in teams
    }
    return render_template(
        'teams.html',
        teams=teams,
        logos=logos,
        selected_team=team_key
    )


@nba_bp.route('/data', methods=['GET', 'POST'])
@nba_bp.route('/data.html', methods=['GET','POST'])
@login_required
def data():
    form = NBADataForm()
    if form.validate_on_submit():
        wpct = form.wpct.data
        pf = form.pf.data
        pa = form.pa.data
        result = form.result.data or 'Unknown'
        try:
            sub = Submission(wpct=wpct, pf=pf, pa=pa, result=result)
            db.session.add(sub)
            db.session.commit()
            current_app.logger.info(f"Saved submission {sub.id}")
            flash('Your team match has been saved!', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving submission: {e}")
            flash('There was an error saving your submission.', 'danger')
        return redirect(url_for('nba.data'))
    return render_template('data.html', form=form)


@nba_bp.route('/player', methods=['GET', 'POST'])
@nba_bp.route('/player.html', methods=['GET', 'POST'])
@login_required
def compare_player():
    match = None
    if request.method == 'POST':
        user_input = [
            float(request.form['pts']),
            float(request.form['ast']),
            float(request.form['stl']),
            float(request.form['blk']),
            float(request.form['trb']),
        ]
        player_stats = df[['PTS', 'AST', 'STL', 'BLK', 'TRB']].values
        distances = euclidean_distances([user_input], player_stats)
        best_idx = distances.argmin()
        match = df.iloc[best_idx]

        # ✅ Save to database
        try:
            comp = PlayerComparison(
                user_id        = current_user.id,
                input_pts=user_input[0],
                input_ast=user_input[1],
                input_stl=user_input[2],
                input_blk=user_input[3],
                input_trb=user_input[4],
                matched_player=match.Player
            )
            db.session.add(comp)
            db.session.commit()
            current_app.logger.info(f"✅ Saved comparison for {match.Player}")
            flash(f'Match saved: {match.Player}', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"❌ Error saving comparison: {e}")
            flash('There was an error saving your player comparison.', 'danger')

    return render_template('player.html', match=match)



@nba_bp.route('/team_players/<team_key>')
def team_players(team_key):
    """
    Return 3 players for <team_key> in 2025:
     1) the overall highest scorer,
     2–3) two other distinct players (random from the next best games).
    """
    # 1) key‐mapping
    key_map = {
        'NY':  'NYK', 'BKN': 'BRK', 'CHA': 'CHO',
        'GS':  'GSW', 'SA':  'SAS', 'NO':  'NOP',
    }
    csv_key = key_map.get(team_key, team_key)

    # 2) load & parse dates
    csv_path = os.path.join(current_app.root_path, 'database_24_25.csv')
    df = pd.read_csv(csv_path, parse_dates=['Data'], dayfirst=False)

    # 3) filter to team & year
    team_df = df[(df['Tm'] == csv_key) & (df['Data'].dt.year == 2025)]
    if team_df.empty:
        return jsonify([])

    # 4) sort by PTS desc, drop duplicate players (keep first = highest game)
    sorted_df = team_df.sort_values('PTS', ascending=False)
    unique_df = sorted_df.drop_duplicates(subset='Player', keep='first')

    # 5) pick top scorer + two more
    top_player = unique_df.iloc[0:1]                     # highest scorer
    others     = unique_df.iloc[1:]                      # the rest
    sample     = others.sample(n=min(2, len(others)), replace=False)

    result_df  = pd.concat([top_player, sample], ignore_index=True)

    # 6) select & rename columns for JSON
    output = (
        result_df
        .loc[:, ['Player','PTS','AST','STL','BLK']]
        .rename(columns={
            'Player': 'name',
            'PTS':    'pts',
            'AST':    'ast',
            'STL':    'stl',
            'BLK':    'blk'
        })
    )

    return jsonify(output.to_dict(orient='records'))
