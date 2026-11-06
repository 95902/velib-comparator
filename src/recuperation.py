from operator import index
import requests
import pandas as pd


URL_VELIB = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/exports/json"

def telecharger_velib():
    reponse = requests.get(URL_VELIB,timeout=30)
    reponse.raise_for_status()

    donnees = reponse.json()
    df = pd.DataFrame(donnees)

    df.to_csv("data/brut/velib.csv",index=False)
    return df

if __name__ == "__main__":
    df = telecharger_velib()
    print("Nombre de stations :",len(df))
    print(df.head())

