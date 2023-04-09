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

#Configurando acesso ao Telegram e Google sheets

TELEGRAM_API_KEY = os.environ["TELEGRAM_API_KEY"]
GOOGLE_SHEETS_CREDENTIALS = os.environ["GOOGLE_SHEETS_CREDENTIALS"]
with open("credenciais.json", mode="w") as arquivo:
  arquivo.write(GOOGLE_SHEETS_CREDENTIALS)
conta = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json")
api = gspread.authorize(conta)
planilha = api.open_by_key("1BTcO4G_FS1tp6_hRcPUk_4fts6ayt7Ms2cvYHsqD9nM")
sheet = planilha.worksheet("dadosrobo")

#Analisando gastos CEAP deputados Federais

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
    despesas = pd.read_csv(f, sep=';', low_memory=False)
    
#tratando dados
despesas['numMes'] = despesas['numMes'].astype(int)

#fazendo analises
gastos = despesas['vlrLiquido'].sum()

#Dataframe com gastos
gastadores = despesas.groupby(['txNomeParlamentar', 'sgUF'])['vlrLiquido'].sum()
gastadores = pd.DataFrame(gastadores)
gastadores = gastadores.reset_index()

#Quais deputados mais gastaram?
gastadores = despesas.groupby(['txNomeParlamentar', 'sgUF'])['vlrLiquido'].sum()
gastadoresBR_top10 = gastadores.nlargest(10, keep='first')
gastadoresBR_top10 = pd.DataFrame(gastadoresBR_top10)
gastadoresBR_top10 = gastadoresBR_top10.reset_index()
gastadoresBR_top10

#Deputado/a que mais gastou
maiorgastador = gastadoresBR_top10.iloc[0]['txNomeParlamentar']

#Deputado/as que menos gastaram
gastadores = despesas.groupby(['txNomeParlamentar', 'sgUF'])['vlrLiquido'].sum()
gastadores = pd.DataFrame(gastadores)
gastadores = gastadores.sort_values(by='vlrLiquido')
gastadores = gastadores.reset_index()
menorgastador = gastadores.iloc[0]['txNomeParlamentar']

#Levando dados do dataframe, pro Google sheets
sheet_gastadores = planilha.get_worksheet(1)
sheet_gastadores.update([gastadores.columns.values.tolist()] + gastadores.values.tolist())

#Qual a média de gastos por deputado/a?
mediaBr = despesas['vlrLiquido'].mean()
mediaBr = "{:.2f}".format(mediaBr)

#Média de Gastos de deputados por estado
estadosBr = despesas.groupby('sgUF')['vlrLiquido'].mean()
estadosBr.sort_values(ascending=False)
estados = pd.DataFrame(estadosBr)
estados = estados.reset_index()

#Analisando Projetos de Lei

baixar_arquivo('https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-2022.csv','proposicoesAutores-2022.csv')
proposicoes = pd.read_csv('proposicoesAutores-2022.csv',
                          sep = ';', low_memory=False)

#Quais deputados/as mais apresentaram PLs?
autores = proposicoes.groupby('nomeAutor').count()
autores = pd.DataFrame(autores)
autores = autores.sort_values(by='idProposicao', ascending = False)
autores = autores.reset_index()

#Levando dados do dataframe, pro Google sheets
sheet_autores = planilha.get_worksheet(2)
sheet_autores.update([autores.columns.values.tolist()] + autores.values.tolist())

maior_autor = autores.iloc[0]['nomeAutor']

menor_autor = autores.iloc[-1]['nomeAutor']

#Quantos projetos foram apresentados em 2022?
qtd_proposicoes = proposicoes['idProposicao'].count()

#PLs por estado
PLs_estados = proposicoes.groupby('siglaUFAutor')['idProposicao'].mean()
PLs_estados = PLs_estados.sort_values(ascending=False)
PLs_estados = pd.DataFrame(PLs_estados)
PLs_estados = PLs_estados.reset_index()

#mostrar estado que tem maior quantidade de PLs
estado_Pls = PLs_estados.iloc[0]['siglaUFAutor']

#Criando robô no Telegram***

# Criando site
  
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

@app.route("/telegram", methods=["POST"])

def telegram_bot():
  #extraindo dados para enviar mensagens
  update = request.json
  chat_id = update["message"]["chat"]["id"]
  message = update["message"]["text"]
  first_name = update["message"]["from"]["first_name"]
  sender_id = update["message"]["from"]["id"]

  # Define qual será a resposta e enviada
  sheet.update('A:C', [message])
  resultado = sheet.get('A:C')

  mensagens = ['oi', 'Oi', 'Olá', 'olá', 'ola', 'iai', 'qual é', 'e aí', "/start" ]
  if message in mensagens:
    texto_resposta = f"Olá! Seja bem-vinda(o) {first_name}! Eu sou o robô de olho na Câmara, para saber o gasto e os Projetos de Lei de um(a) deputado(a) digite seu nome." 
  elif message not in mensagens:
    for message in resultado:
      linha = sheet_gastadores.find(message).row
      valores = sheet_gastadores.row_values(linha)
      gastos = valores[2]
      texto_resposta = f'{first_name} o gasto de {message} foi igual a {gastos}'
  elif message not in mensagens:
    for message in resultado:
      linha = sheet_autores.find('message').row
      valores = sheet_autores.row_values(linha)
      PLs = valores[1]
      texto_resposta = f'{first_name} {message} apresentou {PLs} no último ano'
      
    nova_mensagem = {"chat_id": chat_id, "text": texto_resposta}
    resposta = requests.post(f"https://api.telegram.org./bot{TELEGRAM_API_KEY}/sendMessage", data=nova_mensagem)
    print(resposta.text)
    return "ok"

@app.route("/")
def hello_world():
   return "Olá, mundo!"
