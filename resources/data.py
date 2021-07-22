import pandas as pd
from pandas.core.frame import DataFrame
from scipy.stats import poisson
import datetime
import glob
import os


def get_current_teams(country='SP1'):
    df = pd.read_csv("http://www.football-data.co.uk/mmz4281/2021/" + country +".csv")
    return df['HomeTeam'].unique()


class League():

    def __init__(self, country='SP1'):
        self.country = country
        self.dict_historical_data = {}
        self.df_league_strength = DataFrame

        frames = []

        current_year = (datetime.datetime.now()).year
        index_year = int(str(current_year)[2:4])

        # leer desde historico csv
        path = os.getcwd()
        for i in range(index_year - 5, index_year):
            df = pd.read_csv(os.path.join(path + "/resources/files/" + str(i - 1) + str(i) + "_" + country + ".csv"))
            frames.append(self.__filter_importan_column(self, df, i))

        # leer liga actual desde url
        df = pd.read_csv(
            "http://www.football-data.co.uk/mmz4281/" + str(index_year - 1) + str(index_year) + "/" + country + ".csv")
        frames.append(self.__filter_importan_column(self, df, index_year))

        self.dict_historical_data[country] = pd.concat(frames)

    def get_table_result(self, home, visit):
        return self.dict_historical_data[self.country][
            (self.dict_historical_data[self.country]['HomeTeam'] == home) &
            (self.dict_historical_data[self.country]['VisitTeam'] == visit)] \
                .rename(columns=
                {
                    'Date': 'Fecha Partido',
                    'HomeTeam': 'Local',
                    'VisitTeam': 'Visitante',
                    'HomeGoals': 'Goles Local',
                    'VisitGoals': 'Goles Visitantes',
                    'Season': 'Temporada'
                })

    def calculate_strength(self):
        # se suman todos los goles metidos jugando en casa y encajados (ultimos 5 años)
        # por cada equipo se hace la media de sus goles metidos y encajados en casa
        # ejemplo
        # Team         | HomeScored | HomeConceded
        # Alaves       |        1.34|        1.34|
        # Real Madrid  |        2.56|        0.56|
        home = self.dict_historical_data[self.country][['HomeTeam', 'HomeGoals', 'VisitGoals']] \
            .rename(columns={'HomeTeam': 'Team', 'HomeGoals': 'HomeScored', 'VisitGoals': 'HomeConceded'}) \
            .groupby(['Team'], as_index=False)[['HomeScored', 'HomeConceded']] \
            .mean()

        # se suman todos los goles metidos jugando fuera y encajados (ultimos 5 años)
        # por cada equipo se hace la media de sus goles metidos y encajados como visitante
        visit = self.dict_historical_data[self.country][['VisitTeam', 'HomeGoals', 'VisitGoals']] \
            .rename(columns={'VisitTeam': 'Team', 'HomeGoals': 'VisitConceded', 'VisitGoals': 'VisitScored'}) \
            .groupby(['Team'], as_index=False)[['VisitScored', 'VisitConceded']] \
            .mean()

        self.df_league_strength = pd.merge(home, visit, on='Team')

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

                    #storing every match result
                    list_points_home.append(round(points_home, 1))
                    list_points_away.append(round(points_away, 1))
            
        dict_table = dict_table.sort_values('Points', ascending=False).reset_index()
        dict_table = dict_table[['Team', 'Points', "PG", "PE", "PP"]]
        dict_table.round(0)

        return dict_table

    @staticmethod
    def __filter_importan_column(self, _df, _i):
        # pillar columnas importantes
        _df = _df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']]
        _df = _df.rename(columns={'FTHG': 'HomeGoals', 'FTAG': 'VisitGoals', 'AwayTeam': 'VisitTeam'})
        _df = _df.assign(Season=_i)

        return _df
