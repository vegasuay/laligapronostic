from re import split
from flask import Flask, render_template
from resources import \
    get_current_teams, get_current_clasification, get_current_jornada, get_next_jornada_index, runInParallel
from flask import request
from resources import data
import unidecode
import math

app = Flask(__name__)

@app.route('/')
def index():
    teams = get_current_teams()
    obj_jornada = get_next_jornada_index(teams)

    return render_template('index.html', 
        teams=teams,
        resultados = obj_jornada['array_resultados'])


@app.route('/about')
def post():
    return render_template('about.html')


@app.route('/goal', methods=['POST'])
def goal():

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

    # leer apustas
    uni_home = unidecode.unidecode(home.upper())
    uni_visit= unidecode.unidecode(visit.upper())    
    
    #bwinValue, willianValue, pokerValue  = data.multiTasks(uni_home, uni_visit, porc_win)
    bwinValue, willianValue, pokerValue = runInParallel(uni_home, uni_visit, porc_win)

    # scraping table clasification
    pos_local= wins_local= lose_local= emp_local= pts_local = jug_local = \
        pos_visita= wins_visita= lose_visita = emp_visita= pts_visita= jug_visita = 0
    list_clasif = get_current_clasification()
    
    for obj in list_clasif:
        if pos_local==0 and obj.isTeam(home):
            pos_local = obj.pos;
            wins_local= obj.pg;
            lose_local= obj.pp;
            emp_local = obj.pe;
            pts_local = obj.pts;
            jug_local = obj.pj;
            continue;

        if pos_visita==0 and obj.isTeam(visit):
            pos_visita = obj.pos;
            wins_visita = obj.pg;
            lose_visita = obj.pp;
            emp_visita = obj.pe;
            pts_visita = obj.pts;
            jug_visita = obj.pj;
            continue;

    #TODO: ponderar por posicion temporada

    # comprobar nan values
    league.df_league_strength.HomeScored[home] = \
        0 if math.isnan(league.df_league_strength.HomeScored[home]) else league.df_league_strength.HomeScored[home]
    league.df_league_strength.HomeConceded[home] = \
        0 if math.isnan(league.df_league_strength.HomeConceded[home]) else league.df_league_strength.HomeConceded[home]
    league.df_league_strength.VisitScored[visit] = \
        0 if math.isnan(league.df_league_strength.VisitScored[visit]) else league.df_league_strength.VisitScored[visit]
    league.df_league_strength.VisitConceded[visit] = \
        0 if math.isnan(league.df_league_strength.VisitConceded[visit]) else league.df_league_strength.VisitConceded[visit]
            

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
        'pos_local': pos_local,
        'wins_local': wins_local,
        'emp_local': emp_local,
        'lose_local': lose_local,
        'pts_local': pts_local,
        'jug_local': jug_local,
        'pos_visita': pos_visita,
        'wins_visita': wins_visita,
        'lose_visita': lose_visita,
        'emp_visita': emp_visita,
        'pts_visita': pts_visita,
        'jug_visita': jug_visita,
        'bwin': bwinValue,
        'william': willianValue,
        'poker': pokerValue
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

@app.route('/quiniela', methods=['POST','GET'])
def quiniela():
    league = data.League()
    league.calculate_strength()

    jornada='none'
    if request.args.get('btnjornada-ant'):
        jornada=request.args.get('btnjornada-ant')
    if request.args.get('btnjornada-sig'):
        jornada=request.args.get('btnjornada-sig')
    if jornada=='none' and request.args.get('jornada'):
        jornada=request.args.get('jornada')

    obj_jornada = get_current_jornada(jornada, league)
    jor_actual=int(obj_jornada['current_jornada'].split(" ")[1])

    #bwinValue, willianValue, pokerValue  = data.multiTasks(None, None, None, obj_jornada['array_resultados'])
    bwinValue, willianValue, pokerValue = runInParallel(None, None, None, obj_jornada['array_resultados'])

    # num of jornadas
    jornadas = list(range(1,obj_jornada['total_jornadas']))

    return render_template('quiniela.html', 
        jornadas=jornadas,
        int_jornada=jor_actual,
        tit_table=obj_jornada['current_jornada'],
        date_event = obj_jornada['fecha_evento'],
        resultados = obj_jornada['array_resultados'])

if __name__ == '__main__':
    app.run()
