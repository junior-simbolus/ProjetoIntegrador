from flask import Flask, jsonify, request, render_template, session, redirect, flash
import fdb
from fdb import Error
import locale
import uuid
from datetime import date

from flask_cors import CORS

from flask_session import Session
from waitress import serve

user_db = "SYSDBA"
password_db = "masterkey"
name_db = "192.168.2.5/3050:C:\\Simbolus\Banco\\bSimbolus_Gestor.fdb"

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')


def create_db_connection(user_name, user_password, db_name):
   connection = None
   try:
      connection = fdb.connect(user=user_name, password=user_password, dsn=db_name, charset="WIN1252")
   except Error as err:
       print(f"Error: '{err}'")
   return connection


def read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
    except Error as err:
        return result, err
    return result, "ok"


def exec_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        msg = "OK"
    except Error as err:
        msg = err
    return msg


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = ""
Session(app)
CORS(app)


@app.route('/')
def index():
    if session.get("uid"):
       return render_template("opcoes.html", nome_cliente=session.get("nome_cliente"), idCli=session.get("idCli"),
                              sessao=session.get("uid"), Mensagem=None)
    return render_template("login.html")


@app.route('/login', methods=["POST", "GET"])
def login():
   try:
     dados = request.get_json()
     cnpj = dados['user']
     senha = dados['password']
     conexao = create_db_connection(user_db, password_db, name_db)
     sql = "select cli_senha_web, cli_razao, cli_codigo from clientes where cli_status = 0 and cli_cnpj = '"+cnpj+"'"
     cursor, msg = read_query(conexao, sql)
     conexao.close()
     if cursor:
        if cursor[0][0] != senha:
           retorno = {"mensagem": "usuário ou senha inválido", "code": 400}
        else:
           session["cnpj"] = cnpj
           session["idcli"] = cursor[0][2]
           session["nome_cliente"] = cursor[0][1]
           session["uid"] = uuid.uuid4()
           retorno = {"mensagem": "ok",
                      "idcli": cursor[0][2],
                      "nome_cliente": cursor[0][1],
                      "cnpj": cnpj,
                      "code": 200,
                      "token": session.get("uid")}
     else:
        retorno = {"mensagem": "cnpj inválido!", "code": 400}
   except Error as err:
     retorno = {"mensagem": err, "code": 400}
   return jsonify(retorno)


@app.route("/logoff/<sessao>")
def logoff(sessao):
    session["idCli"] = None
    session["cnpj"] = None
    session["nome_cliente"] = None
    session["uid"] = None
    return redirect("/")

@app.route('/login2', methods=["POST", "GET"])
def login2():
   try:
     cnpj = request.form.get('user')
     senha = request.form.get('pass')
     sql = "SELECT CLI_SENHA_WEB, CLI_RAZAO, CLI_CODIGO FROM CLIENTES WHERE CLI_STATUS = 0 AND CLI_CNPJ = '"+cnpj+"'"
     conexao = create_db_connection(user_db, password_db, name_db)
     cursor, msg = read_query(conexao, sql)
     conexao.close()
     if cursor:
        if cursor[0][0] != senha:
           flash("Usuário ou senha inválido!")
           retorno = {"mensagem": "Usuário ou senha inválido", "code": 400}
           return render_template("login.html", retorno=retorno)
        else:
           session["cnpj"] = cnpj
           session["idCli"] = cursor[0][2]
           session["nome_cliente"] = cursor[0][1]
           session["uid"] = uuid.uuid4()
           retorno = {"mensagem": "OK",
                      "idCli": cursor[0][2],
                      "nome_cliente": cursor[0][1],
                      "cnpj": cnpj,
                      "code": 200,
                      "token": session.get("uid")}
           return render_template("opcoes.html", nome_cliente=cursor[0][1], idCli=cursor[0][2], Mensagem=None,
                                  sessao=session.get("uid"), retorno=retorno)
     else:
        flash("CNPJ ou senha inválido!")
        retorno = {"mensagem": "CNPJ inválido!", "code": 400}
        return render_template("login.html", retorno=retorno)
   except Error as err:
     retorno = {"mensagem": err,
                "code": 400}
     return jsonify(retorno)


@app.route('/inserir_solicitacao2/<idCli>/<origem>')
def inserir_solicitacao2(idCli, origem):
   try:
     sessao = session.get("uid")
     sql = "SELECT S.SIS_CODIGO, S.SIS_NOME FROM SISTEMAS S INNER JOIN CONTRATOS C "
     sql = sql + "ON C.SIS_CODIGO = S.SIS_CODIGO WHERE C.CLI_CODIGO = "+str(idCli)+" AND "
     sql = sql + "CTR_STATUS = 0 ORDER BY SIS_NOME"
     conexao = create_db_connection(user_db, password_db, name_db)
     sistemas_, msg = read_query(conexao, sql)
     conexao.close()
     nome_cliente = session.get("nome_cliente")

     qtde = len(sistemas_)
     nome = [0] * qtde
     codigo = [0] * qtde
     lista = {"sistemas": []}

     i = 0
     for row in sistemas_:
        nome[i] = row[1]
        codigo[i] = row[0]
        i = i+1

     for i in range(qtde):
        lista["sistemas"].append(
          {
              "nome": nome[i],
              "codigo": codigo[i]
          }
        )
     retorno = {
         "idCli": idCli,
         "nome_cliente": nome_cliente,
         "token": sessao,
         "sistemas": lista,
         "code": 200,
         "mensagem": "ok"
     }
     if str(origem) == "0":
        return render_template("solicitacao.html", idCli=idCli, nome_cliente=nome_cliente, sistemas=lista, sessao=sessao,
                            retorno=retorno)
     else:
        return jsonify(retorno)
   except Error as err:
     retorno = {"mensagem": err,
                "code": 400}
     if str(origem) == "0":
        redirect("/")
     return jsonify(retorno)



@app.route('/inclui_sol2/<idCli>/<origem>', methods=["POST"])
def inclui_sol2(idCli, origem):
   sessao = session.get("uid")
   id_sistema = request.form.get('sis')
   contato = request.form.get('contato')
   tipo = request.form.get('tipo')
   sol = request.form.get('obs')
   sol = sol.upper()
   sol1 = sol[1:255]
   sol2 = sol[256:510]
   sol3 = sol[511:765]
   try:
     sql = "SELECT CTR_CODIGO FROM CONTRATOS WHERE CLI_CODIGO = "+str(idCli)+" AND SIS_CODIGO = "+str(id_sistema)
     conexao = create_db_connection(user_db, password_db, name_db)
     contrato, msg = read_query(conexao, sql)
     conexao.close()
     ctr_codigo = contrato[0][0]
     nome_cliente = session.get("nome_cliente")
     correcao = 0
     if tipo == "CORREÇÃO":
         correcao = 1
     conexao2 = create_db_connection(user_db, password_db, name_db)
     cursor1 = conexao2.cursor()
     cursor1.callproc("SP_DESENVOLVIMENTO_WEB", (ctr_codigo, tipo, sol1, date.today(), correcao,
                     contato, -1, sol2, sol3))
     conexao2.commit()
     conexao2.close()
     retorno = {"code": 200,
                "mensagem": "ok"}
     if str(origem) == "0":
        flash("Lançamento efetuado com sucesso!")
        return render_template("opcoes.html", idCli=idCli, nome_cliente=nome_cliente, sessao=sessao)
     else:
        return jsonify(retorno)
   except Error as err:
     if str(origem) == "0":
        flash("Ocorreu um erro: "+str(err))
        redirect("/")
     else:
        return jsonify({"code": 400,
                        "mensagem": err})


@app.route('/listar2/<idCli>/<sessao>/<status>/<origem>', methods=["GET"])
def listar2(idCli, sessao, status, origem):
   nome_cliente = session.get("nome_cliente")
   try:
     sql = "SELECT D.DES_CODIGO, D.CTR_CODIGO, DES_ASSUNTO, DES_DESCRICAO, DES_LANCAMENTO, "
     sql = sql + "DES_PRAZO, DES_COBRADO, DES_STATUS, DES_CORRECAO, DES_FINALIZADO, COALESCE(DES_VALOR, 0) AS "
     sql = sql + "DES_VALOR, DES_CONTATO, DES_OBS_VALOR, DES_APROVADO_CLIENTE, DES_MOTIVO FROM DESENVOLVIMENTO D "
     sql = sql + "INNER JOIN CONTRATOS CT ON CT.CTR_CODIGO = D.CTR_CODIGO "
     sql = sql + "WHERE CT.CLI_CODIGO = "+str(idCli)+" AND EXTRACT(YEAR FROM DES_LANCAMENTO) >= 2024 "
     if str(status) != "99":
        if str(status) == "11":
           sql = sql + " AND DES_STATUS IN (-1, 0) "
        elif str(status) == "4":
           sql = sql + " AND DES_STATUS = 1 AND DES_FINALIZADO = 1 "
        elif str(status) == "1":
           sql = sql + "AND DES_STATUS = 1 AND DES_FINALIZADO = 0 AND EXISTS (SELECT DF.DES_CODIGO FROM "
           sql = sql + "DESENVOLVIMENTO_FASES DF WHERE DF.DES_CODIGO = D.DES_CODIGO AND DSF_FASE = 2)"
           sql = sql + "AND NOT EXISTS (SELECT DF.DES_CODIGO FROM DESENVOLVIMENTO_FASES DF WHERE "
           sql = sql + "DF.DES_CODIGO = D.DES_CODIGO AND DSF_FASE = 3)"
        elif str(status) == "3":
           sql = sql + "AND DES_STATUS = 1 AND DES_FINALIZADO = 0 AND EXISTS (SELECT DF.DES_CODIGO FROM "
           sql = sql + "DESENVOLVIMENTO_FASES DF WHERE DF.DES_CODIGO = D.DES_CODIGO AND DSF_FASE = 3)"
        elif str(status) == "0":
           sql = sql + " AND DES_STATUS = 1 AND DES_FINALIZADO = 0"
        elif str(status) == "2":
           sql = sql + " AND DES_STATUS = 2 "
     conexao = create_db_connection(user_db, password_db, name_db)
     solicita, msg = read_query(conexao, sql)
     conexao.close()
     qtde = len(solicita)

     des_codigo = [0] * qtde
     des_assunto = [0] * qtde
     des_status = [0] * qtde
     des_lancamento = [0] * qtde
     des_valor = [0] * qtde
     des_aprovar = [0] * qtde

     lista = {"solicitacoes": []}

     conexao2 = create_db_connection(user_db, password_db, name_db)
     i = 0
     for row in solicita:
        des_codigo[i] = row[0]
        des_assunto[i] = row[2]
        des_lancamento[i] = row[4]
        des_valor[i] = locale.currency(row[10], grouping=True, symbol=True)
        des_aprovar[i] = ""
        if row[10] > 0:
            des_aprovar[i] = "Clique aqui para aprovar"
        else:
            des_valor[i] = ""
        if row[7] == -1 or row[7] == 0:
            if row[6] == 1:
                des_status[i] = "AGUARDANDO APROVACAO CLIENTE"
            else:
                des_status[i] = "AGUARDANDO ANALISE"
        elif row[7] == 1:
           if row[9] == 1:
              des_status[i] = 'FINALIZADO'
           else:
              sql2 = "SELECT COUNT(*) FROM DESENVOLVIMENTO_FASES WHERE DES_CODIGO = "+str(row[0])
              fases, msg = read_query(conexao2, sql2)
              if fases[0][0] <= 1:
                 if row[13] == 1:
                    des_status[i] = "APROVADO CLIENTE/AGUARDANDO INICIO"
                    des_aprovar[i] = ""
                 else:
                    des_status[i] = "APROVADO SIMBOLUS/AGUARDANDO INICIO"
              elif fases[0][0] == 2:
                 des_status[i] = "EM DESENVOLVIMENTO"
              elif fases[0][0] == 3:
                 des_status[i] = "EM TESTE"
        elif row[7] == 2:
            des_status[i] = "NAO APROVADO"
        i = i+1
     conexao2.close()
     for i in range(qtde):
        lista["solicitacoes"].append(
          {
              "id": des_codigo[i],
              "assunto": des_assunto[i],
              "status": des_status[i],
              "lancamento": des_lancamento[i].strftime("%d/%m/%Y"),
              "valor": des_valor[i],
              "aprovar": des_aprovar[i],
          }
        )
     retorno = {
         "code": 200,
         "mensagem": "ok",
         "idCli": idCli,
         "nome_cliente": nome_cliente,
         "token": sessao,
         "solicitacoes": lista
     }
     if str(origem) == "0":
        return render_template("listar.html", idCli=idCli, nome_cliente=nome_cliente, sessao=sessao, solicitacoes=lista)
     else:
        return jsonify(retorno)
   except Error as err:
     if str(origem) == "0":
        flash("Ocorreu um erro: "+str(err))
        redirect("/")
     else:
         return jsonify({"code": 400,
                         "mensagem": err})


@app.route('/carregar_sol2/<id>/<origem>', methods=["GET"])
def carregar_sol2(id, origem):
   nome_cliente = session.get("nome_cliente")
   idCli = session.get("idCli")
   sessao = session.get("uid")
   try:
     sql = "SELECT D.DES_CODIGO, D.CTR_CODIGO, DES_ASSUNTO, COALESCE(DES_DESCRICAO2, '')"
     sql = sql + "||' '||COALESCE(DES_DESCRICAO3, '')||' '||coalesce(DES_DESCRICAO4, ''), DES_LANCAMENTO, "
     sql = sql + "DES_PRAZO, DES_STATUS, DES_FINALIZADO, COALESCE(DES_VALOR, 0) AS DES_VALOR, "
     sql = sql + "DES_CONTATO, DES_OBS_VALOR, DES_MOTIVO, DES_APROVADO_CLIENTE, DES_COBRADO FROM DESENVOLVIMENTO D "
     sql = sql + "INNER JOIN CONTRATOS CT ON CT.CTR_CODIGO = D.CTR_CODIGO "
     sql = sql + "WHERE D.DES_CODIGO = "+str(id)
     conexao = create_db_connection(user_db, password_db, name_db)
     solicita, msg = read_query(conexao, sql)
     conexao.close()
     status = ""
     if solicita[0][6] == -1 or solicita[0][6] == 0:
        if solicita[0][13] == 1:
           status = "AGUARDANDO APROVACAO CLIENTE"
        else:
           status = "AGUARDANDO ANALISE"
     elif solicita[0][6] == 1:
        if solicita[0][7] == 1:
           status = 'FINALIZADO'
        else:
           sql2 = "SELECT COUNT(*) FROM DESENVOLVIMENTO_FASES WHERE DES_CODIGO = "+str(solicita[0][0])
           conexao2 = create_db_connection(user_db, password_db, name_db)
           fases, msg = read_query(conexao2, sql2)
           conexao2.close()
           if fases[0][0] <= 1:
              if solicita[0][12] == 1:
                 status = "APROVADO CLIENTE/AGUARDANDO INICIO"
              else:
                 status = "APROVADO SIMBOLUS/AGUARDANDO INICIO"
           elif fases[0][0] == 2:
              status = "EM DESENVOLVIMENTO"
           elif fases[0][0] == 3:
              status = "EM TESTE"
     elif solicita[0][6] == 2:
        status = "NAO APROVADO"
     prazo = None
     if solicita[0][5]:
        prazo = solicita[0][5].strftime("%d/%m/%Y")

     retorno = {
         "des_codigo": solicita[0][0],
         "des_assunto": solicita[0][2],
         "des_descricao": solicita[0][3],
         "des_lancamento": solicita[0][4].strftime("%d/%m/%Y"),
         "des_prazo": prazo,
         "des_valor": locale.currency(solicita[0][8], grouping=True, symbol=True),
         "des_contato": solicita[0][9],
         "des_obs_valor": solicita[0][10],
         "des_motivo": solicita[0][11],
         "des_status": status,
         "idCli": idCli,
         "sessao": sessao,
         "nome_cliente": nome_cliente,
         "code": 200,
         "mensagem": "ok"
         }
     if str(origem) == "0":
        return render_template("detalhe.html", idCli=idCli, nome_cliente=nome_cliente, sessao=sessao, retorno=retorno)
     else:
        return jsonify(retorno)
   except Error as err:
     if str(origem) == "0":
        flash("Ocorreu um erro: "+str(err))
        redirect("/")
        return False
     else:
        return jsonify({"code": 200,
                        "mensagem": err})


@app.route('/aprovar_sol2/<id>/<origem>', methods=["PUT", "GET", "POST"])
def aprovar_sol2(id, origem):
   idCli = session.get("idCli")
   sessao = session.get("uid")
   try:
     sql = "UPDATE DESENVOLVIMENTO SET DES_APROVADO_CLIENTE = 1 WHERE DES_CODIGO = "+str(id)
     conexao, msg = create_db_connection(user_db, password_db, name_db)
     exec_query(conexao, sql)
     conexao.close()
     if str(origem) == "0":
        return listar2(idCli, sessao, 0)
     else:
        return jsonify({"code": 200,
                        "mensagem": "ok"})
   except Error as err:
     if str(origem) == "0":
        flash("Ocorreu um erro: "+str(err))
        redirect("/")
     return jsonify({"mensagem": err, "code": 400})


#app.run(host='192.168.2.104')
if __name__ == "__main__":
    serve(app, host="192.168.2.104", port=5000)
    #   app.run(debug=True)
