from flask import Flask, render_template
from resources import get_current_teams, get_current_clasification
from flask import request
from resources import data

app = Flask(__name__)

@app.route('/')
def index():
    teams = get_current_teams()
    return render_template('index.html', teams=teams)


@app.route('/about')
def post():
    return render_template('about.html')


@app.route('/goal', methods=['POST'])
def goal():

    # scraping table
    list_clasif = get_current_clasification()

    # instanciar clase league
    league = data.League()
    home = request.form['selecthome']
    visit = request.form['selectvisit']

    dataframe_table = league.get_table_result(home, visit)
    league.calculate_strength()

    points_home, points_away = league.predict_points(home, visit)

    # icono del porcentage
    porc_win = 'draw'
    if (league.prob_draw > league.prob_home and league.prob_draw > league.prob_away):
        porc_win = 'draw'
    elif (league.prob_home > league.prob_away):
        porc_win = 'home'
    else: porc_win = 'away'

    object = {
        'home': home,
        'visit': visit,
        'm_marcados_encasa': round(league.df_league_strength.HomeScored[home],2),
        'tm_marcados_encasa': round(league.average_home_scored,2),
        'm_recibidos_encasa': round(league.df_league_strength.HomeConceded[home],2),
        'tm_recibidos_encasa': round(league.average_home_conceded,2),
        'm_marcados_envisita': round(league.df_league_strength.VisitScored[visit],2),
        'tm_marcados_envisita': round(league.average_visit_scored,2),
        'm_recibidos_envisita': round(league.df_league_strength.VisitConceded[visit],2),
        'tm_recibidos_envisita': round(league.average_visit_conceded,2),
        'lambda_local': round(league.lamb_home,2),
        'lambda_visita': round(league.lamb_away,2),
        'puntos_local': points_home, 
        'puntos_visita': points_away,
        'data_home': league.chart_data_home,
        'data_visit': league.chart_data_visit,
        'prob_draw': round(league.prob_draw * 100,2),
        'prob_home': round(league.prob_home * 100,2),
        'prob_away': round(league.prob_away * 100,2),
        'porc_win': porc_win,
        'wins_local': 6,
        'lose_local': 3,
        'pos_local': 1,
        'wins_visita': 1,
        'lose_visita': 8,
        'pos_visita': 4
    }


    return render_template('goal.html', data=object,
                           tables=[dataframe_table.to_html(classes='my-0 table table-striped table-result')],
                           titles=dataframe_table.columns.values,
                           typeChart='bar')


@app.route('/pronostic')
def pronostic():
    league = data.League()
    league.calculate_strength()
    dataframe_pronostic = league.my_pronostic()
    return render_template('pronostic.html',
                            tables=[dataframe_pronostic.to_html(classes='my-0 table table-striped table-result')],
                            titles=dataframe_pronostic.columns.values)

if __name__ == '__main__':
    app.run()
