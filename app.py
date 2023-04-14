from flask import Flask
import os

import gspread
import requests
from flask import Flask, request
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

TELEGRAM_API_KEY = os.environ["TELEGRAM_API_KEY"]
GOOGLE_SHEETS_CREDENTIALS = os.environ["GOOGLE_SHEETS_CREDENTIALS"]
with open("credenciais.json", mode="w") as arquivo:
  arquivo.write(GOOGLE_SHEETS_CREDENTIALS)
conta = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json")
api = gspread.authorize(conta)
planilha = api.open_by_key("1BTcO4G_FS1tp6_hRcPUk_4fts6ayt7Ms2cvYHsqD9nM")
sheet = planilha.get_worksheet(3)

def projetos():
  #extraindo projetos de Lei e requerimentos
  resposta = requests.get('https://al.to.leg.br/materiasLegislativas')
  sopa = BeautifulSoup(resposta.content, 'html.parser')
  PLs = sopa.findAll('div', {'class':'row'}) 
  PL = []
  for pl in PLs:
    try:
      titulo = pl.find('h4').text
    except AttributeError:
      print(pl)
    continue
    try:
      data = pl.find('p').text.split('|')[1].split(':')[1].strip()
    except:
      print(pl) # print para vermos o que tinha na linha que deu erro
    break
    texto = pl.find_all('div', class_= 'col-12')[-1].text
    path = pl.find('a').attrs['href']
    url = f'https://al.to.leg.br{path}'
    PL.append([titulo, data, texto, url])
    return PL

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
  try:
    # extraindo dados para enviar mensagens
    update = request.json
    chat_id = update["message"]["chat"]["id"]
    message = update["message"]["text"]
    first_name = update["message"]["from"]["first_name"]
    sender_id = update["message"]["from"]["id"]
    
    # atualiza planilha com mensagens
    sheet.update('A:B', [[message]])
    resultado = sheet.get('A:B')
    mensagem = resultado[-1][-1]

    mensagens = ['oi', 'Oi', 'Olá', 'olá', 'ola', 'iai', 'qual é', 'e aí', "/start"]
    if menssagem in mensagens:
      texto_resposta = f"Olá! Seja bem-vinda(o) {first_name}! Eu sou o robô de olho na Câmara, para saber o gasto e os Projetos de Lei de um(a) deputado(a) digite seu nome."
    elif mensagem not in mensagens:
      for mensagem in resultado:
        linha = sheet_gastadores.find(mensagem).row
        valores = sheet_gastadores.row_values(linha)
        gastos = valores[2]
        linha_dois = sheet_autores.find(mensagem).row
        valores_dois = sheet_autores.row_values(linha_dois)
        PLs = valores_dois[1]
        texto_resposta = f'{first_name} {mensagem} apresentou {PLs} e gastou {gastos} no último ano'

    nova_mensagem = {"chat_id": chat_id, "text": texto_resposta}
    resposta = requests.post(f"https://api.telegram.org./bot{TELEGRAM_API_KEY}/sendMessage", data=nova_mensagem)
  
  except Exception as e:
  print(e)
  texto_resposta = "Erro ao processar a mensagem"
  nova_mensagem = {"chat_id": chat_id, "text": texto_resposta}
  resposta = requests.post(f"https://api.telegram.org./bot{TELEGRAM_API_KEY}/sendMessage", data=nova_mensagem)
  print(resultado)
  print(linha)
  print(valores)
  print(gasto)
  print(PLs)
