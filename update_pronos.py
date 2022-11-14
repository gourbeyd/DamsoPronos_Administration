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

debug = False
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
				if not(debug):
					mydb.commit()
				cursor.execute("""SELECT PRONO from PRONOS where id = (%s)""", (row[0], ))
				#ici on devra choisir les gains en fonction des trucs (suffit de prendre le cote AH2 et d'appliquer poru chaque type de pari si ca passe ou pas)
				#condition sur le type de pari
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
				if not(debug):
					mydb.commit()
	
	if score != ['', '']:
		#updating csv now for teamStats
		browser = webdriver.Firefox(options=options)
		browser.get(adresse)
		element = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".stat__homeValue")))
		element = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".stat__awayValue")))
		element = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".stat__categoryName")))
		statsHome = browser.find_elements_by_class_name("stat__homeValue")
		statsAway = browser.find_elements_by_class_name("stat__awayValue")
		statsCateg = browser.find_elements_by_class_name("stat__categoryName")
		teams = browser.find_elements_by_class_name("participant__participantName")
		teams=[team.text for team in teams]
		# HPOSS, HS, HST, HFC, HCORNERS, HOFFSIDES, HTOUCHES, HSAVES, HFOULS, HYELLOW, HRED, HPASSES, HTACKLES, HATKS 
		# 	0	1	 2	  3		4			5			6		7		8		9		10		11		12		  13
		homeStatsDB = [0 for _ in range(14)]
		awayStatsDB = [0 for _ in range(14)]
		for categ, statHome, statAway in zip(statsCateg, statsHome, statsAway):
			# push them to the db
			if categ.text.startswith("Possession"):
				homeStatsDB[0]=int(statHome.text[:-1])
				awayStatsDB[0]=int(statAway.text[:-1])
			elif categ.text.startswith("Tirs au but"):
				homeStatsDB[1]=int(statHome.text)
				awayStatsDB[1]=int(statAway.text)
			elif categ.text.startswith("Tirs cadr"):
				homeStatsDB[2]=int(statHome.text)
				awayStatsDB[2]=int(statAway.text)
			elif categ.text.startswith("Coup francs"):
				homeStatsDB[3]=int(statHome.text)
				awayStatsDB[3]=int(statAway.text)
			elif categ.text.startswith("Corners"):
				homeStatsDB[4]=int(statHome.text)
				awayStatsDB[4]=int(statAway.text)
			elif categ.text.startswith("Hors-jeu"):
				homeStatsDB[5]=int(statHome.text)
				awayStatsDB[5]=int(statAway.text)
			elif categ.text.startswith("Touche"):
				homeStatsDB[6]=int(statHome.text)
				awayStatsDB[6]=int(statAway.text)
			elif categ.text.startswith("Sauvetages"):
				homeStatsDB[7]=int(statHome.text)
				awayStatsDB[7]=int(statAway.text)
			elif categ.text.startswith("Fautes"):
				homeStatsDB[8]=int(statHome.text)
				awayStatsDB[8]=int(statAway.text)
			elif categ.text.startswith("Cartons Jaunes"):
				homeStatsDB[9]=int(statHome.text)
				awayStatsDB[9]=int(statAway.text)
			elif categ.text.startswith("Cartons Rouges"):
				homeStatsDB[10]=int(statHome.text)
				awayStatsDB[10]=int(statAway.text)
			elif categ.text.startswith("Total Passes"):
				homeStatsDB[11]=int(statHome.text)
				awayStatsDB[11]=int(statAway.text)
			elif categ.text.startswith("Tacles"):
				homeStatsDB[12]=int(statHome.text)
				awayStatsDB[12]=int(statAway.text)
			elif categ.text.startswith("Attaques dange"):
				homeStatsDB[13]=int(statHome.text)
				awayStatsDB[13]=int(statAway.text)
		
		homeTeam = teams[0]
		awayTeam = teams[2]
		print(homeTeam, awayTeam)
		print(homeStatsDB, awayStatsDB)
		
		statsHome = [elem.text for elem in statsHome]
		statsAway = [elem.text for elem in statsAway]
		browser.close()
		#update matchs with stats

		# update csv stats, useful for next bets -> ok
		if not(debug):
			cursor.execute("""UPDATE MATCHS set HPOSS=%s, HSHOTS=%s, HST=%s, 
												HFC=%s, HCORNERS=%s, HOFFSIDES=%s, 
												HTOUCHES=%s, HSAVES=%s, HFOULS=%s, 
												HYELLOW=%s, HRED=%s, HPASSES=%s, 
												HTACKLES=%s, HATKS=%s,
												APOSS=%s, ASHOTS=%s, AST=%s, 
												AFC=%s, ACORNERS=%s, AOFFSIDES=%s, 
												ATOUCHES=%s, ASAVES=%s, AFOULS=%s, 
												AYELLOW=%s, ARED=%s, APASSES=%s, 
												ATACKLES=%s, AATKS=%s  WHERE id = (%s)""", (*homeStatsDB, *awayStatsDB, row[0]))
			mydb.commit()
			updateStatsCSV(homeTeam, awayTeam, int(statsHome[1]), int(statsHome[2]), int(statsAway[1]), int(statsAway[2]))

# save team stats
teamStats.to_csv("teamStats.csv", index=False)
