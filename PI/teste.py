import requests
import json

dados = {
        "idCli": "6",
        "token": "74967142-f094-40d2-a440-22d5aa32903c",
        "status": "99"
        }
dados2 = {
        "user": "64064140000106",
        "password": "simbolus123"
        }

def executar():
       #r = requests.get("http://simbolussi.ddns.com.br:8088/login", json=dados2)
       #print(r.content)

       #r2 = requests.get("http://simbolussi.ddns.com.br:8088/inserir_solicitacao", json=dados)
       #print(r2.content)
    #   r2 = requests.get("http://192.168.2.190:5000/listar", json=dados)
     #  print(r2.content)
     r2 = requests.get("http://192.168.2.104:5000/listar", json=dados)
     print(r2.content)
    #1502
executar();
