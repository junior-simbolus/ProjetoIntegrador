from flask import Flask, jsonify, request
import fdb
from fdb import Error
from flask_cors import CORS

user_db = "SYSDBA"
password_db = "masterkey"
name_db = "127.0.0.1/3050:c:\\bancos\\nutri\\MARMONTEL2.fdb"
Logado = False

def create_db_connection(user_name, user_password, db_name):
    connection = None
    try:
        connection = fdb.connect(user=user_name, password=user_password,
                                 dsn=db_name,
                                 charset="WIN1252")
    except Error as err:
        print(f"Error: '{err}'")
    return connection

def read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")

app = Flask(__name__)
CORS(app)

# Construir as funcionalidades
@app.route('/')
def homepage():
   return "API - SISTEMA ELETROTÉCNICA MARMONTEL"

@app.route('/login/<cpf>/<senha>', methods=["GET"])
def login(cpf, senha):
   conexao = create_db_connection(user_db, password_db, name_db)
   sql = "SELECT FUN_SENHA, FUN_NOME, FUN_CODIGO FROM FUNCIONARIOS WHERE FUN_SAIDA IS NULL AND FUN_CNPJ = '"+cpf+"'"
   cursor = read_query(conexao, sql)
   global Logado
   if (cursor):
      if (cursor[0][0] != senha):
         retorno = {"msg": "Senha inválida"}
      else:
         Logado = True
         retorno = {"msg": "OK", "nome":cursor[0][1], "fun_codigo":cursor[0][2]}
   else:
      retorno = {"msg":"Não existe"}
   return jsonify(retorno)

@app.route('/funcionario/<cpf>', methods=["GET"])
def funcionario(cpf):
   if Logado:
      conexao = create_db_connection(user_db, password_db, name_db)
      sql = "SELECT FUN_NOME, FUN_CODIGO FROM FUNCIONARIOS WHERE FUN_SAIDA IS NULL AND FUN_CNPJ = '"+cpf+"'"
      cursor = read_query(conexao, sql)
      if (cursor):
         retorno = {"msg": "OK", "nome":cursor[0][0], "fun_codigo":cursor[0][1]}
      else:
         retorno = {"msg":"Nada encontrado"}
   else:
      retorno = {"msg   ":"Não logado"}
   return jsonify(retorno)

@app.route('/abastecimento', methods=["POST"])
def abastecimento():
   if Logado:
      dados = request.get_json()
      pro_codigo = int(dados['pro_codigo'])
      fun_codigo = int(dados['fun_codigo'])
      try:
        conexao = create_db_connection(user_db, password_db, name_db)
        sql = "SELECT USU_CODIGO FROM USUARIO WHERE FUN_CODIGO = "+str(fun_codigo)
        usuario = read_query(conexao, sql)
        usu_codigo = usuario[0][0]
        sql = "SELECT PRO_COMPRA FROM PRODUTO WHERE PRO_CODIGO = "+str(pro_codigo)
        produto = read_query(conexao, sql)
        custo = produto[0][0]
        cursor = conexao.cursor()
        data = dados['data']
        hora = dados['hora']
        tipo = dados['tipo']
        bem_codigo = dados['bem_codigo']
        km_hora = dados['km_hora']
        local = dados['local']
        qtde = dados['qtde']
        obs = dados['obs']

        cursor.callproc("SP_ABASTECIMENTOS", (0, data, hora, tipo, bem_codigo,
                        km_hora, usu_codigo, local, pro_codigo, qtde,
                        custo, fun_codigo, obs, None, 1, None))

        conexao.commit()
        retorno = {"msg":"SEM ERRO"}
      except Error as err:
        print(err)
        retorno = {"msg":err}
   else:
      retorno = {"msg":"Não logado"}
   return jsonify(retorno)

@app.route('/combustiveis', methods=["GET"])
def combustiveis():
   conexao = create_db_connection(user_db, password_db, name_db)
   sql = "SELECT PRO_DESCRICAO, PRO_CODIGO FROM PRODUTO WHERE PRO_CODIGO IN (1588,1776)"
   produtos = read_query(conexao, sql)

   qtde = len(produtos)
   descricao = [0] * qtde
   codigo = [0] * qtde
   lista = {"produtos": []}

   i=0
   for row in produtos:
      descricao[i] = row[0]
      codigo[i] = row[1]
      i=i+1

   for i in range(qtde):
      lista["produtos"].append(
        {
            "descricao": descricao[i],
            "codigo": codigo[i]
        }
      )
   return jsonify(lista)

@app.route('/geradores', methods=["GET"])
def geradores():
   conexao = create_db_connection(user_db, password_db, name_db)
   sql = "SELECT B.BEM_CODIGO, B.BEM_DESCRICAO, G.GER_POTENCIA_MAX, G.GER_NUMERO_SERIE "
   sql = sql + "FROM BENS B INNER JOIN GERADORES G ON G.BEM_CODIGO = B.BEM_CODIGO WHERE BEM_STATUS = 0 ORDER BY BEM_DESCRICAO"
   geradores = read_query(conexao, sql)

   qtde = len(geradores)
   descricao = [0] * qtde
   codigo = [0] * qtde
   potencia = [0] * qtde
   numero_serie = [0] * qtde
   lista = {"geradores": []}

   i=0
   for row in geradores:
      descricao[i] = row[1]
      codigo[i] = row[0]
      potencia[i] = row[2]
      numero_serie[i] = row[3]
      i=i+1

   for i in range(qtde):
      lista["geradores"].append(
        {
            "descricao": descricao[i],
            "codigo": codigo[i],
            "potencia": potencia[i],
            "numero_serie": numero_serie[i]
        }
      )
   return jsonify(lista)

@app.route('/veiculos', methods=["GET"])
def veiculos():
   conexao = create_db_connection(user_db, password_db, name_db)
   sql = "SELECT B.BEM_CODIGO, B.BEM_DESCRICAO, V.VEI_PLACA "
   sql = sql + "FROM BENS B INNER JOIN VEICULOS V ON V.BEM_CODIGO = B.BEM_CODIGO WHERE BEM_STATUS = 0 ORDER BY BEM_DESCRICAO"
   veiculos = read_query(conexao, sql)

   qtde = len(veiculos)
   descricao = [0] * qtde
   codigo = [0] * qtde
   placa = [0] * qtde
   lista = {"veiculos": []}

   i=0
   for row in veiculos:
      descricao[i] = row[1]
      codigo[i] = row[0]
      placa[i] = row[2]
      i=i+1

   for i in range(qtde):
      lista["veiculos"].append(
        {
            "descricao": descricao[i],
            "codigo": codigo[i],
            "placa": placa[i]
        }
      )
   return jsonify(lista)

# Roda a nossa API
app.run(host='0.0.0.0')
