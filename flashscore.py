#!/bin/env python3
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from time import sleep
from datetime import date
from datetime import datetime
import mysql.connector
import pandas as pd
import keras
import numpy as np
import conf

today = date.today().strftime("%Y-%m-%d")
mydb = mysql.connector.connect(host=conf.host, user=conf.username, password=conf.password, database="damsopronos_db")
matchs = mydb.cursor()
teamStats = pd.read_csv('teamStats.csv')

def double_chance(c1, c2):
    m1=c2/(c1+c2)
    return round(m1*c1, 2)


f1 = keras.models.load_model("models/F1.h5")
e0 = keras.models.load_model("models/E0.h5")
i1 = keras.models.load_model("models/I1.h5")
sp1 = keras.models.load_model("models/SP1.h5")
d1 = keras.models.load_model("models/D1.h5")

options = FirefoxOptions()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)
pages = []

#choose leagues
#pages.append("https://www.flashscore.fr/football/angleterre/premier-league/")
#pages.append("https://www.flashscore.fr/football/allemagne/bundesliga/")
#pages.append("https://www.flashscore.fr/football/france/ligue-1/")
#pages.append("https://www.flashscore.fr/football/espagne/laliga/")
#pages.append("https://www.flashscore.fr/football/italie/serie-a/")



# récuperer la liste des matchs
liste_url_matchs = []

debug = False
for page in pages:
    liste_matchs_ligue = []
    browser = webdriver.Firefox(options=options)
    browser.get(page)
    sleep(1)
    tab=browser.find_elements_by_class_name('event__match--scheduled')
    for elem in tab:
        liste_matchs_ligue.append(elem.get_attribute("id")[4:])#pour prendre en compte le _ ok
    if "bundesliga" in page:
        liste_url_matchs += liste_matchs_ligue[0:9] #9 matchs par journée
    else:
        liste_url_matchs += liste_matchs_ligue[0:10] #10 matchs par journée
    browser.quit()

liste_url_matchs=["tfzLo9sb"]
print(len(liste_url_matchs), " matchs this gw")


for k in range(len(liste_url_matchs)):
    # pour chacun des matchs
    print("----------------------------------------------------------------")
    page = "https://www.flashscore.fr/match/"+liste_url_matchs[k]+"/#/resume-du-match"
    browser = webdriver.Firefox(options=options)
    browser.get(page)
    #just to wait
    sleep(1)
    
    #fetch game s odds
    scraped_odds = browser.find_elements_by_class_name("oddsValue")
    cotes = []
    #todo: handle multiple bookmakers
    for element in scraped_odds[0:3]:
        cotes.append(float(element.text))
    #fetch home & away teams name
    home_team = browser.find_element_by_class_name("duelParticipant__home").text
    away_team = browser.find_element_by_class_name("duelParticipant__away").text
    #fetch gamedate
    gameDate = browser.find_element_by_class_name("duelParticipant__startTime").text
    gameHour = gameDate[-5:]
    gameDate = datetime.strptime(gameDate[0:6]+gameDate[8:10], '%d.%m.%y').strftime("%Y-%m-%d")
    #fetch goals from rankings
    page_dom = "https://www.flashscore.fr/match/"+liste_url_matchs[k]+"/#/classement/table/overall"
    browser.close()
    browser = webdriver.Firefox(options=options)
    browser.get(page_dom)
    sleep(1)

    #fetch home & way team goals
    tableau_dom = browser.find_element_by_class_name("ui-table__body").text 
    compteur = 0
    to_iter_classement = tableau_dom.splitlines()
    buts = 0
    for mot in to_iter_classement:
        if mot == home_team:
            pshg=int(to_iter_classement[compteur+5].split(sep=":")[0])
            buts += pshg
        elif mot == away_team:
            psag=int(to_iter_classement[compteur+5].split(sep=":")[0])
            buts -= psag
        compteur+=1
    browser.close()
    cotes.append(buts)

    print(home_team + " vs " + away_team)
    print(f"cotes: {cotes[0:3]} | psdg: {cotes[3]}")
    
    """
    features needed to feed the model : in a file like last year
        odds (3) + psdg -> ok at this point
        HS, HST, AS, AST (these are averages) -> need to be computed or kept in a file/df in this code
    """
    #go fetch customHS, customAS, CustomHST, CustomAST
    countHG = teamStats.loc[teamStats["Team"]== home_team]['CountHG'].values[0]
    if countHG != 0:
        customHS = teamStats.loc[teamStats["Team"]== home_team]['SumHS'].values[0]/countHG
        customHST = teamStats.loc[teamStats["Team"]== home_team]['SumHST'].values[0]/countHG
    else:
        customHS = 0
        customHST = 0
    countAG = teamStats.loc[teamStats["Team"]== away_team]['CountAG'].values[0]
    if countAG != 0:
        customAS = teamStats.loc[teamStats["Team"]== away_team]['SumAS'].values[0]/countAG
        customAST = teamStats.loc[teamStats["Team"]== away_team]['SumAST'].values[0]/countAG
    else:
        customAS = 0
        customAST = 0
    league = teamStats.loc[teamStats["Team"]==home_team]['Div'].values[0]
    print(f"HS {customHS} AS {customAS} HST {customHST} AST {customAST} league {league} gd {gameDate}")

    topredict = pd.DataFrame(np.array([[cotes[0], cotes[1], cotes[1], customHS, customAS, customHST, customAST, cotes[3]]]),
                   columns=['B365H', 'B365D', 'B365A', 'CustomHS', 'CustomAS', 'CustomHST', 'CustomAST', 'CustomPSDG'])
    #ok now we are ready to call the models based on the league
    if (league == "E0"):
        prono = e0.predict(topredict)
    elif (league=="F1"):
        prono = f1.predict(topredict)
    elif (league=="I1"):
        prono = i1.predict(topredict)
    elif (league=="SP1"):
        prono = sp1.predict(topredict)
    elif(league=="D1"):
        prono = d1.predict(topredict)
    
    if not(debug):
        #add game to matchs table
        matchs.execute("""INSERT INTO MATCHS(id, date, HomeTeam, AwayTeam, ODD_HOME, ODD_DRAW, ODD_AWAY, OD_DRAW_OR_AWAY, PSHG, PSAG, CustomHS, CustomHST, CustomAS, CustomAST, gameHour) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (liste_url_matchs[k], gameDate, home_team, away_team, cotes[0], cotes[1], cotes[2], double_chance(cotes[1], cotes[2]), int(pshg), int(psag), round(customHS, 2), round(customHST, 2), round(customAS, 2), round(customAST, 2), gameHour))

        # get argmax, percentage
        if (np.argmax(prono)==0):
            confidence = round(prono[0][0]*100)
            print(f"\t home team to win @{cotes[0]} {confidence}%")
            matchs.execute("""INSERT INTO PRONOS(id, prono, confidence) VALUES(%s, %s, %s)""", (liste_url_matchs[k], 1, confidence))

        else:
            confidence = round(prono[0][1]*100)
            print(f"\t away team or draw @{double_chance(cotes[1], cotes[2])} {confidence}%")
            matchs.execute("""INSERT INTO PRONOS(id, prono, confidence) VALUES(%s, %s, %s)""", (liste_url_matchs[k], -1, confidence))
        
        mydb.commit()

print("----------------------------------------------------------------")

    
