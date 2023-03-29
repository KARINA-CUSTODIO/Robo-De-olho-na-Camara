from flask import Flask
import os

import gspread
import requests
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import zipfile
import altair as alt
import plotly.express as px

TELEGRAM_API_KEY = os.environ["TELEGRAM_API_KEY"]
GOOGLE_SHEETS_CREDENTIALS = os.environ["GOOGLE_SHEETS_CREDENTIALS"]
with open("credenciais.json", mode="w") as arquivo:
  arquivo.write(GOOGLE_SHEETS_CREDENTIALS)
conta = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json")
api = gspread.authorize(conta)
planilha = api.open_by_key("1BTcO4G_FS1tp6_hRcPUk_4fts6ayt7Ms2cvYHsqD9nM")
sheet = planilha.worksheet("dadosrobo")

#Criando função que baixa arquivo
def baixar_arquivo(url, endereco):
    resposta = requests.get(url)
    if resposta.status_code == requests.codes.OK:
        with open(endereco, 'wb') as novo_arquivo:
            novo_arquivo.write(resposta.content)
        print("Donwload finalizado. Salvo em: {}".format(endereco))
    else:
        resposta.raise_for_status()
        
#baixando arquivo despesas
baixar_arquivo('https://www.camara.leg.br/cotas/Ano-2022.csv.zip','CSV')

#lendo arquivo  
with zipfile.ZipFile('CSV') as z:
  with z.open('Ano-2022.csv') as f:
    despesas = pd.read_csv(f, sep=';', skiprows = [i for i in range(1, 515) ])    
    
app = Flask(__name__)

menu = """
<a href="/">Página inicial</a> | <a href="/sobre">Sobre</a> | <a href="/gastos">Gastos</a> | <a href="/contato">Contato</a> | <a href="/telegram">Telegram</a>
<br>
"""

@app.route("/sobre")
def sobre():
  return menu + "Aqui vai o conteúdo da página Sobre"

@app.route("/contato")
def contato():
  return menu + "Aqui vai o conteúdo da página Contato"

@app.route("/Telegram")
def index():
  return menu + "Aqui vai o conteúdo da página Telegram"

@app.route("/")
def hello_world():
   return "Olá, mundo!"
