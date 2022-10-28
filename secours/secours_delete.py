
liste_url_matchs=[
"0fT14QsM",
"0KQNHUSH",
"4MOXb45q",
"6XTc56SF",
"beU6LCTh",
"bun53pcS",
"CnSucrzd",
"fNNFJjb5",
"GWOBKWra",
"IHdKpNKO",
"jwRqd2k2",
"K4V2MhEn",
"lMvXREjP",
"lpNJIADB",
"MZEWF8cU",
"QsWbNYbt",
"rDNybOKk",
"rqGSGlrO",
"StVg6nD9",
"WEyo88rc"]


for url in liste_url_matchs:
    print(f"DELETE FROM PRONOS where id='{url}';")
    print(f"DELETE FROM MATCHS where id='{url}';")

