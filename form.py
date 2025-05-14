from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class EPLTeamForm(FlaskForm):
    avgShots = FloatField('Average Shots per Match', validators=[DataRequired(), NumberRange(min=0, max=50)])
    avgGoals = FloatField('Average Goals per Match', validators=[DataRequired(), NumberRange(min=0, max=10)])
    avgFouls = FloatField('Fouls per Match', validators=[DataRequired(), NumberRange(min=0, max=50)])
    avgCards = FloatField('Cards per Match', validators=[DataRequired(), NumberRange(min=0, max=10)])
    shotAccuracy = FloatField('Shot Accuracy', validators=[DataRequired(), NumberRange(min=0, max=1)])
    submit = SubmitField('Find Your EPL Team')