# forms.py
from flask_wtf import FlaskForm
from wtforms import IntegerField, DecimalField, PasswordField, StringField, SubmitField, FloatField
from wtforms.validators import InputRequired, NumberRange, DataRequired

class BBLStatsForm(FlaskForm):
    # Batting
    bat_innings = IntegerField("Innings Played",   validators=[InputRequired(), NumberRange(min=0)])
    bat_runs    = IntegerField("Total Runs",       validators=[InputRequired(), NumberRange(min=0)])
    bat_high    = IntegerField("Highest Score",    validators=[InputRequired(), NumberRange(min=0)])
    bat_avg     = DecimalField("Batting Average",  validators=[InputRequired(), NumberRange(min=0)])
    bat_sr      = DecimalField("Strike‑Rate",      validators=[InputRequired(), NumberRange(min=0)])
    # Bowling
    bowl_overs  = DecimalField("Overs Bowled",     validators=[InputRequired(), NumberRange(min=0)])
    bowl_wkts   = IntegerField("Wickets Taken",    validators=[InputRequired(), NumberRange(min=0)])
    bowl_runs   = IntegerField("Runs Conceded",    validators=[InputRequired(), NumberRange(min=0)])
    bowl_avg    = DecimalField("Bowling Average",  validators=[InputRequired(), NumberRange(min=0)])
    bowl_eco    = DecimalField("Economy Rate",     validators=[InputRequired(), NumberRange(min=0)])
    submit      = SubmitField("Compare my stats")

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Register')

class TemplateDataNBA(FlaskForm):
    wpct = DecimalField("Win %", validators=[InputRequired(), NumberRange(min=0)], places=1)
    pf = DecimalField("Points per Game (for)", validators=[InputRequired(), NumberRange(min=0)], places=1)
    pa = DecimalField("Points per Game (against)", validators=[InputRequired(), NumberRange(min=0)], places=1)
    submit = SubmitField("Save Match")

class EPLTeamForm(FlaskForm):
    avgShots = FloatField('Average Shots per Match', validators=[DataRequired(), NumberRange(min=0, max=50)])
    avgGoals = FloatField('Average Goals per Match', validators=[DataRequired(), NumberRange(min=0, max=10)])
    avgFouls = FloatField('Fouls per Match', validators=[DataRequired(), NumberRange(min=0, max=50)])
    avgCards = FloatField('Cards per Match', validators=[DataRequired(), NumberRange(min=0, max=10)])
    shotAccuracy = FloatField('Shot Accuracy', validators=[DataRequired(), NumberRange(min=0, max=1)])
    submit = SubmitField('Find Your EPL Team')

