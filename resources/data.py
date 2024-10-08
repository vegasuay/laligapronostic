import pandas as pd
from pandas.core.frame import DataFrame
from scipy.stats import poisson
import datetime, time
import glob
import os
import requests
import asyncio
from multiprocessing import Process, Manager
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from sqlalchemy import null
from resources import clasif
import unidecode
from resources.bit_constants import \
    BWIN, BWIN_URL, WILLIAM, WILLIAM_URL, POKER, POKER_URL, \
        FOOTBALL_DATA_URL,TU_LIGA, RESULTADOS_AS, AS

#driver = webdriver.Chrome()
chrome_options = webdriver.ChromeOptions()
#chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN") //TODO: quitar para heroku
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")


def get_current_teams(country='SP1'):

    # si estamos en mes mayor a 7, cambiar temporada
    current_year = (datetime.datetime.now()).year
    current_month = (datetime.datetime.now()).month
    index_year = int(str(current_year)[2:4])
    if current_month >= 7:
        index_year += 1

    #df = pd.read_csv(FOOTBALL_DATA_URL + str(index_year-1) + str(index_year) + "/"+ country + ".csv")
    teams = pd.DataFrame(columns=['AwayTeam','HomeTeam'])
    try:
        df = _read_football_data(index_year-1, index_year)

        df_all = [df['AwayTeam'], df['HomeTeam']]
        teams = pd.concat(df_all)
        return teams.unique()
    except Exception as ex:
        return pd.DataFrame(columns=['Liga no comenzada'])

def get_current_clasification():
    """
    obtiene de la web siguetuliga.com la posicion, partidos, puntos

    :return: list<dict>
    """
    list_classif = []
    cabecera = True

    url = TU_LIGA
    html = requests.get(url).content
    soup = BeautifulSoup(html)
    table = soup.find(id='clasificacion')

    # get files <tr>
    for row in table.find_all("tr"):
        td = row.find_all("td")
        if cabecera:
            cabecera = False
            continue

        list_classif.append(clasif.Santander(
            td[1].find_all("span")[0].contents[2],                     # team
            td[0].find_all("a")[0].contents[0],                        # pos
            td[2].find_all("a")[0].find_all("strong")[0].contents[0],  # pts
            td[3].find_all("a")[0].contents[0],                        # pj
            td[4].find_all("a")[0].contents[0],                        # pg
            td[5].find_all("a")[0].contents[0],                        # pe
            td[6].find_all("a")[0].contents[0],                        # pp
        ))

    return list_classif

def _common_jornada():
     # si estamos en mes mayor a 7, cambiar temporada
    current_year = (datetime.datetime.now()).year
    current_month = (datetime.datetime.now()).month
    index_year = int(str(current_year)[2:4])
    if current_month > 7:
        index_year += 1

    url = RESULTADOS_AS + "jornada/"
    html = requests.get(url).content
    soup = BeautifulSoup(html)

    array_jornadas = soup.find_all("span", {"class": "tit-jornada"})
    fecha_evento = soup.find_all("span", {"class": "fecha-evento"})
    resultados = soup.find_all("li", {"class": "list-resultado"})

    return array_jornadas, fecha_evento, resultados

def get_next_jornada_index(list_sp_teams):
    """
    obtiene de la web de as los resultados de enfrentamientos

    :return: object
    """
    array_jornadas, fecha_evento, resultados = _common_jornada()

    current_jornada = array_jornadas[0].contents[0]
    array_resultados = []

    for row in resultados:
        #if (len(row.find_all("a", {"class": "resultado"})) > 0):
        #    txt_result = row.find_all("a", {"class": "resultado"})[0].contents[0]
        #    txt_result = txt_result.replace('\n', '').split("-")
            

        if (len(row.find_all("div", {"class": "equipo-local"})) > 0):
            txt_result = ["",""]
            txt_result[0] = row.find_all("div", {"class": "equipo-local"})[0].text
            txt_result[1] = row.find_all("div", {"class": "equipo-visitante"})[0].text
            #txt_result = txt_result.replace('\n', '')

        else:
            break
                
        info_event = row.find_all("div", {"class": "info-evento"})[0].contents[1]
        info_event = info_event.text.replace('\n', '').lstrip()
        
        if len(txt_result) > 1:
            result_local = txt_result[0].replace('\n', '').strip()
            result_visita = txt_result[1].replace('\n', '').strip()
        elif len(txt_result) == 1:
            fecha_partido = txt_result[0].strip().split(" ")
            result_local = fecha_partido[0]
            result_visita = fecha_partido[1]

        array_resultados.append({
            'local': AS[result_local],
            'visitante': AS[result_visita],
            'hora': info_event.split(" ")[1],
            'dia': info_event.split(" ")[0]
        })

    return {
        'array_resultados': array_resultados
    }

def get_current_jornada(jornada='none', cLeague=None):
    """
    obtiene de la web de as los resultados de enfrentamientos

    :return: object
    """
    array_jornadas, fecha_evento, resultados = _common_jornada()

    current_jornada = array_jornadas[0].contents[0]

    list_sp_teams = get_current_teams()
    array_resultados = []
    for idx, row in enumerate(resultados):
        result_local = 'A'
        result_visita = 'P'
        if (len(row.find_all("a", {"class": "resultado"})) > 0):
            txt_result = row.find_all("a", {"class": "resultado"})[0].contents[0]
            txt_result = txt_result.replace('\n', '').split("-")

            if len(txt_result) > 1:
                result_local = txt_result[0].strip()
                result_visita = txt_result[1].strip()
            elif len(txt_result) == 1:
                fecha_partido = txt_result[0].strip().split(" ")
                result_local = fecha_partido[0]
                result_visita = fecha_partido[1]

        def find_team(team):
            i = 0
            uni_team = unidecode.unidecode(team.upper())
            # ñapa
            if uni_team == 'ATLETICO': uni_team = 'ATH MADRID'
            if uni_team == 'ATHLETIC': uni_team = ' ATH BILBAO'
            if uni_team == 'ESPANYOL': uni_team = 'ESPANOL'
            if uni_team == 'RAYO': uni_team = 'VALLECANO'
            while i < len(list_sp_teams):
                if uni_team == list_sp_teams[i].upper():
                    return list_sp_teams[i]
                elif list_sp_teams[i].upper() in uni_team:
                    return list_sp_teams[i]

                i += 1

            return team

        strLocal = row.find_all(
            "span", {"class": "nombre-equipo"})[0].contents[0]
        strVisita = row.find_all(
            "span", {"class": "nombre-equipo"})[1].contents[0]

        # Predecir resultado
        points_home, points_away = cLeague.predict_points(
            find_team(strLocal),
            find_team(strVisita))

        # calcular acierto o fallo
        porc_win = 'draw'
        if (cLeague.prob_draw > cLeague.prob_home and cLeague.prob_draw > cLeague.prob_away):
            porc_win = 'draw'
        elif (cLeague.prob_home > cLeague.prob_away):
            porc_win = 'home'
        else: porc_win = 'away'
        acierto = False
        icono = 'close'
        try:
            if (float(result_local) > float(result_visita)) \
                and (points_home > points_away):
                acierto = True
                icono = 'done'
            elif (float(result_local) < float(result_visita)) \
                and (points_home < points_away):
                acierto = True
                icono = 'done'
            elif (float(result_local) == float(result_visita)) \
                and (points_home == points_away):
                acierto = True
                icono = 'done'
        except Exception as ex:
            acierto = None
            icono = 'noplay'
            pass

        array_resultados.append({
            'local': strLocal,
            'visitante': strVisita,
            'result_local': result_local,
            'result_visita': result_visita,
            'pronost_local': points_home,
            'pronost_visita': points_away,
            'porc_win': porc_win,
            'acierto': acierto,
            'icono': icono,
            'count': idx + 1,
            'bwin': 'Diferencia',
            'william': 'Diferencia',
            'poker': 'Diferencia'
        })

    return {
        'current_jornada': current_jornada,
        'total_jornadas': len(array_jornadas),
        'fecha_evento': fecha_evento[0].contents[0],
        'array_resultados': array_resultados
    }

def _get_chromeoptions(class_name, url):
    

    if (os.environ.get("PRODUCTION")):
        # para heroku
        print("heroku")
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        driver = webdriver.Chrome(executable_path=os.environ.get(
            "CHROMEDRIVER_PATH"), options=chrome_options)
    else:
        # para desarrollo
        print("desarrollo")
        driver = webdriver.Chrome(options=chrome_options)

    # div partidos
    # waiting for partidos to load
    partidos_container = None
    try:
        delay = 10  # seconds
        wait = WebDriverWait(driver, delay)
        driver.get(url)
        time.sleep(3)
        partidos_container = wait.until(
            EC.presence_of_all_elements_located((
                By.CLASS_NAME, class_name)))
    except TimeoutException:
        print("Loading took too much time!")
        pass

    return partidos_container

def confirmar_apuestas(valor1, valorx, valor2, alg_win):
    # fix convert to float
    valor1 = valor1.replace(",",".")
    valor2 = valor2.replace(",",".")
    valorx = valorx.replace(",",".")
    if (float(valor1) < float(valorx)) \
        and (float(valor1) < float(valor2)):
        return 'Acierto' if alg_win == 'home' else 'Diferencia'

    elif (float(valor2) < float(valorx)) \
        and (float(valor2) < float(valor1)):
        return 'Acierto' if alg_win == 'away' else 'Diferencia'

    elif (float(valorx) < float(valor1)) \
        and (float(valorx) < float(valor2)):
        return 'Acierto' if alg_win == 'draw' else 'Diferencia'

    else:
        return 'Diferencia'
                
def _read_football_data(y_from, y_to, country = 'SP1'):
    return pd.read_csv(FOOTBALL_DATA_URL + 
         str(y_from) + 
         str(y_to) + "/" + 
         country + ".csv")

def get_pocker_bit(home, visit, alg_win, quix_jornada, dict_return):
    print("start pocker:")
    obj_return = {
        'valor_1' :'-', 'valor_2': '-', 'valor_x':'-', 
        'found': 'False',
        'text': 'No encontrado'}
    uni_home_poker = POKER[home] if home is not None else null
    uni_visit_poker = POKER[visit] if visit is not None else null

    for partido in _get_chromeoptions("eventView-soccer", POKER_URL):
        try:
            # div equipos
            teams = partido.find_elements_by_class_name('event-schedule-participants-name')
            home_read=unidecode.unidecode(teams[0].text.strip().upper())
            visit_read=unidecode.unidecode(teams[1].text.strip().upper())

            # viene de quiniela
            if quix_jornada is not null:
                for match in quix_jornada:
                    uni_home_poker = POKER[unidecode.unidecode(match['local'].upper())]
                    uni_visit_poker = POKER[unidecode.unidecode(match['visitante'].upper())]

                    if home_read == uni_home_poker and visit_read == uni_visit_poker:
                        apuestas = partido.find_elements_by_class_name("button__bet__odds")
                        porc_win = 'draw'
                        if (match['pronost_local'] > match['pronost_visita']):
                            porc_win = 'home'
                        elif (match['pronost_local'] < match['pronost_visita']):
                            porc_win = 'away'

                        valor_1 = apuestas[0].text.strip()
                        valor_x = apuestas[1].text.strip()
                        valor_2 = apuestas[2].text.strip()
                        match['poker'] = confirmar_apuestas(valor_1,valor_x, valor_2, porc_win)

                        break
            else:
                # partido encontrado
                if home_read == uni_home_poker and visit_read == uni_visit_poker:
                    apuestas = partido.find_elements_by_class_name("button__bet__odds")

                    obj_return['valor_1'] = apuestas[0].text.strip()
                    obj_return['valor_x'] = apuestas[1].text.strip()
                    obj_return['valor_2'] = apuestas[2].text.strip()
                    obj_return['found'] = 'True'
                    obj_return['text'] = confirmar_apuestas(obj_return['valor_1'],obj_return['valor_x'], obj_return['valor_2'], alg_win)
                    break   

        except Exception as ex:
            pass

    print("end poker:")
    dict_return['pocker'] = obj_return

def get_william_bit(home, visit, alg_win, quix_jornada, dict_return):
    print("start william:")
    bQuiniela = False if quix_jornada is null else True
    obj_return = {
        'valor_1' :'-', 'valor_2': '-', 'valor_x':'-', 
        'found': 'False',
        'text': 'No encontrado'}
    uni_home_william = WILLIAM[home] if home is not None else null
    uni_visit_william = WILLIAM[visit] if visit is not None else null

    partidos_container = _get_chromeoptions("football-app", WILLIAM_URL)     
    for partido in partidos_container[0].find_elements(By.CSS_SELECTOR, 'article.sp-o-market'):
        try:

            title= partido.find_element(By.CSS_SELECTOR, 'main.sp-o-market__title')
            if (title.text.__contains__(' ₋ ')):
                # div equipos
                teams = title.text.split(' ₋ ')
                home_read = unidecode.unidecode(teams[0].strip().upper())
                visit_read = unidecode.unidecode(teams[1].strip().upper())

                # viene de quiniela
            if bQuiniela:
                for match in quix_jornada:
                    uni_home_william = WILLIAM[unidecode.unidecode(match['local'].upper())]
                    uni_visit_william = WILLIAM[unidecode.unidecode(match['visitante'].upper())]

                    if home_read == uni_home_william and visit_read == uni_visit_william:
                        apuestas = partido.find_elements(By.CSS_SELECTOR, 'button.sp-betbutton')
                        
                        valor_1 = apuestas[0].text.strip()
                        valor_x = apuestas[1].text.strip()
                        valor_2 = apuestas[2].text.strip()
                        match['william'] = confirmar_apuestas(valor_1,valor_x, valor_2, match['porc_win'])

                        break
            else:
                # partido encontrado
                if home_read == uni_home_william and visit_read == uni_visit_william:
                    apuestas = partido.find_elements(By.CSS_SELECTOR, 'button.sp-betbutton')
                    
                    obj_return['valor_1'] = apuestas[0].text.strip()
                    obj_return['valor_x'] = apuestas[1].text.strip()
                    obj_return['valor_2'] = apuestas[2].text.strip()
                    obj_return['found'] = 'True'
                    obj_return['text'] = confirmar_apuestas(obj_return['valor_1'],obj_return['valor_x'], obj_return['valor_2'], alg_win)
                    break    
        
        except Exception as ex:
            pass            

    print("end william:")
    if not bQuiniela:
        dict_return['william'] = obj_return

def get_bwin_bit(home, visit, alg_win, quix_jornada, dict_return):
    print("start bwin:")
    bQuiniela = False if quix_jornada is null else True
    obj_return = {
        'valor_1' :'-', 'valor_2': '-', 'valor_x':'-', 
        'found': 'False',
        'text': 'No encontrado'}

    uni_home_bwin = BWIN[home] if home is not None else null
    uni_visit_bwin = BWIN[visit] if visit is not None else null

    for partido in _get_chromeoptions("grid-event-wrapper", BWIN_URL):
        try:
            # div equipos
            teams = partido.find_elements(By.CLASS_NAME, "participant")
            home_read = unidecode.unidecode(teams[0].text.strip().upper())
            visit_read = unidecode.unidecode(teams[1].text.strip().upper())

            # viene de quiniela
            if bQuiniela:
                for match in quix_jornada:
                    uni_home_bwin = BWIN[unidecode.unidecode(match['local'].upper())]
                    uni_visit_bwin = BWIN[unidecode.unidecode(match['visitante'].upper())]

                    if home_read == uni_home_bwin and visit_read == uni_visit_bwin:
                        apuestas = partido.find_elements(By.CLASS_NAME,"option-indicator")
                        """
                        porc_win = 'draw'
                        if (match['pronost_local'] > match['pronost_visita']):
                            porc_win = 'home'
                        elif (match['pronost_local'] < match['pronost_visita']):
                            porc_win = 'away'
                        """
                        valor_1 = apuestas[0].find_element(By.CLASS_NAME,'option-value').text.strip()
                        valor_x = apuestas[1].find_element(By.CLASS_NAME,'option-value').text.strip()
                        valor_2 = apuestas[2].find_element(By.CLASS_NAME,'option-value').text.strip()
                        match['bwin'] = confirmar_apuestas(valor_1,valor_x, valor_2, match['porc_win'])

                        dict_return['bwin'].append(match)
                        break

            else:
                # viene de pronostico partido
                if home_read == uni_home_bwin and visit_read == uni_visit_bwin:
                    apuestas = partido.find_elements(By.CLASS_NAME, "option-indicator")
                    
                    obj_return['valor_1'] = apuestas[0].find_element(By.CLASS_NAME,'option-value').text.strip()
                    obj_return['valor_x'] = apuestas[1].find_element(By.CLASS_NAME,'option-value').text.strip()
                    obj_return['valor_2'] = apuestas[2].find_element(By.CLASS_NAME,'option-value').text.strip()
                    obj_return['found'] = 'True'
                    obj_return['text'] = confirmar_apuestas(obj_return['valor_1'],obj_return['valor_x'], obj_return['valor_2'], alg_win)

                    #dict_return['bwin'] = obj_return
                    break                

        except Exception as ex:
            pass

    print("end bwin:")
    if not bQuiniela:
        dict_return['bwin'] = obj_return

def runInParallel(home, visit, alg_win, quiniela=null):
    manager = Manager()
    dict_return = manager.dict()
    funcs = [get_bwin_bit,get_william_bit]

    proc = []
    for f in funcs:
        p = Process(target=f,args=(home, visit, alg_win, quiniela, dict_return))
        p.start()
        proc.append(p)
    
    for p in proc:
        p.join()
        
    print('All tasks are done', flush=True)

    return dict_return['bwin'], dict_return['william'], None

def multiTasks(home, visit, alg_win, quiniela=null):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop._stopping = False
    tasks = [
        loop.create_task(get_bwin_bit(home, visit, alg_win, quiniela)),
        loop.create_task(get_william_bit(home, visit, alg_win, quiniela)),
        loop.create_task(get_pocker_bit(home, visit, alg_win, quiniela)),
    ]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
    return tasks[0]._result, tasks[1]._result, tasks[2]._result

class League():

    def __init__(self, country='SP1'):
        self.country = country
        self.dict_historical_data = {}
        self.df_league_strength = DataFrame

        frames = []

        # si estamos en mes mayor a 7, cambiar temporada
        current_year = (datetime.datetime.now()).year
        current_month = (datetime.datetime.now()).month
        index_year = int(str(current_year)[2:4])
        if current_month >= 7:
            index_year +=1

        # leer desde historico csv
        path = os.getcwd()
        for i in range(index_year - 4, index_year):
            df = pd.read_csv(os.path.join(path + "/resources/files/" + str(i - 1) + str(i) + "_" + country + ".csv"))
            frames.append(self.__filter_important_column(self, df, i))

        # leer liga actual desde url
        #df = pd.read_csv("http://www.football-data.co.uk/mmz4281/" + str(index_year - 1) + str(index_year) + "/" + country + ".csv")
        df = _read_football_data(index_year-1, index_year)
        frames.append(self.__filter_important_column(self, df, index_year))

        self.dict_historical_data[country] = pd.concat(frames)

    def get_table_result(self, home, visit):
        return self.dict_historical_data[self.country][
            (self.dict_historical_data[self.country]['HomeTeam'] == home) &
            (self.dict_historical_data[self.country]['VisitTeam'] == visit)] \
                .rename(columns=
                {
                    'Date': 'Fecha',
                    'HomeTeam': 'Local',
                    'HomeGoals': 'Goles Local',
                    'VisitGoals': 'Goles Visita',
                    'VisitTeam': 'Visita',
                    'Season': 'Temp.'
                })

    def calculate_strength(self):
        """
        se suman todos los goles metidos jugando en casa y encajados (ultimos 5 años)
        por cada equipo se hace la media de sus goles metidos y encajados en casa
        ejemplo
        Team         | HomeScored | HomeConceded
        Alaves       |        1.34|        1.34|
        Real Madrid  |        2.56|        0.56|
        """
        home = self.dict_historical_data[self.country][['HomeTeam', 'HomeGoals', 'VisitGoals']] \
            .rename(columns={'HomeTeam': 'Team', 'HomeGoals': 'HomeScored', 'VisitGoals': 'HomeConceded'}) \
            .groupby(['Team'], as_index=False)[['HomeScored', 'HomeConceded']] \
            .mean()

        visit = self.dict_historical_data[self.country][['VisitTeam', 'HomeGoals', 'VisitGoals']] \
            .rename(columns={'VisitTeam': 'Team', 'HomeGoals': 'VisitConceded', 'VisitGoals': 'VisitScored'}) \
            .groupby(['Team'], as_index=False)[['VisitScored', 'VisitConceded']] \
            .mean()

        self.df_league_strength = pd.merge(home, visit, on='Team', how='left')

        # calcular la media de valores de cada una de las 4 columnas
        self.average_home_scored = home['HomeScored'].mean()  # marcados en casa
        self.average_home_conceded = home['HomeConceded'].mean()  # recibidos en casa
        self.average_visit_scored = visit['VisitScored'].mean()  # marcados como visitante
        self.average_visit_conceded = visit['VisitConceded'].mean()  # recibidos como visitante

        # dividir el valor de cada equipo entre la media de cada columna
        self.df_league_strength['HomeScored'] /= self.average_home_scored
        self.df_league_strength['HomeConceded'] /= self.average_home_conceded
        self.df_league_strength['VisitScored'] /= self.average_visit_scored
        self.df_league_strength['VisitConceded'] /= self.average_visit_conceded

        # indexar por equipo
        self.df_league_strength.set_index('Team', inplace=True)
    
    def predict_points(self, home, away):
        if home in self.df_league_strength.index and \
            away in self.df_league_strength.index:
            
            self.chart_data_home = []
            self.chart_data_visit = []

            # home_scored * away_conceded
            self.lamb_home = self.df_league_strength.at[home, 'HomeScored'] * \
                self.df_league_strength.at[away, 'VisitConceded']
            self.lamb_away = self.df_league_strength.at[away, 'VisitScored'] * \
                self.df_league_strength.at[home, 'HomeConceded']
            
            # se calcula la probabilidad de que ocurra x(0,1,2..goles) segun el valor lambda
            self.prob_home, self.prob_away, self.prob_draw = 0, 0, 0
            for x in range(0, 11):  # number of goals home team
                ph = poisson.pmf(x, self.lamb_home)
                self.chart_data_home.append(round(ph,2))

                for y in range(0, 11):  # number of goals away team
                    
                    pv = poisson.pmf(y, self.lamb_away)
                    p =  ph * pv

                    if (x == 0) :
                        self.chart_data_visit.append(round(pv,2))
                     
                    if x == y:
                        self.prob_draw += p
                    elif x > y:
                        self.prob_home += p
                    else:
                        self.prob_away += p

            points_home = 3 * self.prob_home + self.prob_draw
            points_away = 3 * self.prob_away + self.prob_draw
            
            return round(points_home,1), round(points_away,1)
        else:
            self.prob_draw=0
            self.prob_home=0
            self.prob_away=0

            return 0, 0

    def my_pronostic(self):
        """
        https://resultados.as.com/resultados/futbol/primera/clasificacion/
        """
        dict_matches_left = get_current_teams()
        dict_table = pd.DataFrame(data=dict_matches_left, columns=["Team"])
        dict_table["Points"] = 0
        dict_table["PG"] = 0
        dict_table["PP"] = 0
        dict_table["PE"] = 0
        list_points_home = []
        list_points_away = []
        for index, home in enumerate(dict_matches_left):
            for index, away in enumerate(dict_matches_left):
                if home != away:
                    points_home, points_away = self.predict_points(home, away)
                    dict_table.loc[dict_table['Team'] == home, 'Points'] += points_home
                    dict_table.loc[dict_table['Team'] == away, 'Points'] += points_away
                    
                    if(points_home == points_away):
                        dict_table.loc[dict_table['Team'] == home, 'PE'] += 1
                        dict_table.loc[dict_table['Team'] == away, 'PE'] += 1
                    
                    if(points_home > points_away):
                        dict_table.loc[dict_table['Team'] == home, 'PG'] += 1
                        dict_table.loc[dict_table['Team'] == away, 'PP'] += 1
                    
                    if(points_away > points_home):
                        dict_table.loc[dict_table['Team'] == away, 'PG'] += 1
                        dict_table.loc[dict_table['Team'] == home, 'PP'] += 1

                    # storing every match result
                    list_points_home.append(round(points_home, 1))
                    list_points_away.append(round(points_away, 1))
            
        dict_table = dict_table.sort_values('Points', ascending=False).reset_index()
        dict_table = dict_table[['Team', 'Points', "PG", "PE", "PP"]]
        dict_table.round(0)

        return dict_table

    @staticmethod
    def __filter_important_column(self, _df, _i):
        # pillar columnas importantes
        _df = _df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']]
        _df = _df.rename(columns={'FTHG': 'HomeGoals', 'FTAG': 'VisitGoals', 'AwayTeam': 'VisitTeam'})
        _df = _df.assign(Season=_i)

        return _df
