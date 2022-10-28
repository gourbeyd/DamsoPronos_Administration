#!/usr/bin/env python3
import requests
import bs4
from selenium import webdriver
import mysql.connector
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import conf

teamStats = pd.read_csv('teamStats.csv')

def updateStatsCSV(homeTeam, awayTeam, HS, HST, AS, AST):
	teamStats.loc[(teamStats['Team'] == homeTeam), 'SumHS']+=HS
	teamStats.loc[(teamStats['Team'] == homeTeam), 'SumHST']+=HST
	teamStats.loc[(teamStats['Team'] == homeTeam), 'CountHG']+=1
	teamStats.loc[(teamStats['Team'] == awayTeam), 'SumAS']+=AS
	teamStats.loc[(teamStats['Team'] == awayTeam), 'SumAST']+=AST
	teamStats.loc[(teamStats['Team'] == awayTeam), 'CountAG']+=1


mydb = mysql.connector.connect(host=conf.host, user=conf.username, password=conf.password,
database="damsopronos_db")

cursor = mydb.cursor()
cursor.execute("""SELECT * FROM PRONOS WHERE RESULTAT is NULL""")
rows = cursor.fetchall()
options = FirefoxOptions()
options.add_argument("--headless")


for row in rows:	
	adresse="https://www.flashscore.fr/match/"+row[0]+"/#/resume-du-match/statistiques-du-match/0"
	r = requests.get(adresse)
	words= r.text.split()
	score = ['', '']
	for k in range(len(words)):
		if words[k].startswith("<title>"):
			score = words[k+1].split("-")
			print(adresse, score)
			if score != ['', '']:
				fthg = int(score[0])
				ftag = int(score[1])
				if fthg>ftag:
					resultat = 1
				else:
					resultat = -1
				cursor.execute("""UPDATE MATCHS set FTR=%s, FTHG=%s, FTAG=%s WHERE id = (%s)""", (resultat, fthg, ftag, row[0]))
				mydb.commit()
				cursor.execute("""SELECT PRONO from PRONOS where id = (%s)""", (row[0], ))
				if int(cursor.fetchall()[0][0]) == resultat:
					if resultat == -1:
						cursor.execute("""SELECT OD_DRAW_OR_AWAY from MATCHS where id = (%s)""", (row[0],))
						gain = float(cursor.fetchall()[0][0])-1
					else:
						cursor.execute("""select ODD_HOME from MATCHS where id=(%s)""", (row[0],))
						gain = float(cursor.fetchall()[0][0])-1
				else:
					gain = -1
				cursor.execute("""UPDATE PRONOS set resultat = %s, gain = %s WHERE id = (%s)""", (resultat, gain, row[0]))
				mydb.commit()
	
	if score != ['', '']:
		#updating csv now for teamStats
		browser = webdriver.Firefox(options=options)
		browser.get(adresse)
		element = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".stat__homeValue")))
		element = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".stat__awayValue")))
		statsHome = browser.find_elements_by_class_name("stat__homeValue")
		statsAway = browser.find_elements_by_class_name("stat__awayValue")
		teams = browser.find_elements_by_class_name("participant__participantName")
		teams=[team.text for team in teams]

		statsHome = [elem.text for elem in statsHome]
		statsAway = [elem.text for elem in statsAway]
		homeTeam = teams[0]
		awayTeam = teams[2]
		print(homeTeam, awayTeam, statsHome, statsAway)
		browser.close()
		# update csv stats, useful for next bets
		updateStatsCSV(homeTeam, awayTeam, int(statsHome[1]), int(statsHome[2]), int(statsAway[1]), int(statsAway[2]))

# save team stats
teamStats.to_csv("teamStats.csv", index=False)
