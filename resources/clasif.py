import unidecode
class Santander():

    def __init__(self, team, pos, pts, pj, pg, pe, pp): 
        self.team = self.__normalizeTeam(team) 
        self.pos = int(pos)
        self.pts = int(pts)
        self.pj=int(pj)
        self.pg=int(pg)
        self.pe=int(pe)
        self.pp=int(pp)

    def __normalizeTeam(self, team):
        nTeam =""

        # replace
        nTeam = team.replace('\n\t\t', '')
        nTeam = nTeam.strip()

        return unidecode.unidecode(nTeam.upper())

    def isTeam(self, team):
        nTeam = self.__normalizeTeam(team)

        #ñapa
        if nTeam == 'ATH MADRID': nTeam = 'ATL MADRID'
        if nTeam == 'ATH BILBAO': nTeam = 'ATHLETIC CLUB'
        if nTeam == 'ESPANOL'   : nTeam = 'ESPANYOL'
        
        if self.team == nTeam:
            return True
        elif nTeam in self.team:
            return True
        else:
            return False 
