####################################################################################
## Administrator Server AI2H
##
## Born in 24/12/2019
##
## Version 0.1B
## Write and Develop by Marco Aurelio Gorgulho Drummond
## This code is property AI2H and Marco Aurelio Gorgulho Drummond
##
###################################################################################

#!/usr/bin/env python
from threading import Lock
from flask import Flask, session, request, json, make_response, jsonify
from flask_cors import CORS, cross_origin

import sys
import os
import nltk
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import random
import string # to process standard python strings
import json
import geoip2
import geoip2.database
import numpy as np
import mysql.connector
from cryptography.fernet import Fernet, MultiFernet
import smtplib
import urllib
import ftplib
import logging
import codecs
import re
import unicodedata
import sys
import uuid
import time
import logging
import ssl

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

#set the project root directory as the static folder, you can set others.
app=Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = os.urandom(24)

script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir,'ai2h_srv_admin_config.txt')
with open(file_path, 'r') as json_file:
     config = json.load(json_file)

#CORS(app)
CORS(app, resources={r"/*": {"origins": ["*", config["ai2hsrvadmin"]["cor_domain"], config["ai2hsrvadmin"]["ip"]]}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CORS_HEARDES'] = 'Access-Control-Allow-Origin = *'

#reader = geoip2.database.Reader('/home/ocram/srv_ai2h_ai/GeoLite2-City.mmdb')
reader = geoip2.database.Reader(config["ai2hsrvadmin"]["path_geodb"])

try:
    os.stat(config["logger_cfg"]["path"])
except:
    os.mkdir(config["logger_cfg"]["path"])

handler = logging.FileHandler(config["logger_cfg"]["path"] + "ai2h-server-admin.log")    # Create the file logger
app.logger.addHandler(handler)                                                           # Add it to the built-in logger
app.logger.setLevel(logging.DEBUG)                                                       # Set the log level to debug

def location(ip):
    try:
        result = reader.city(str(ip))
        app.logger.info("ai2ServerAdmin Logger")
        app.logger.info(ip)
        app.logger.info(result.city.name)
        app.logger.info(result.subdivisions.most_specific.name)
        app.logger.info(result.country.name)
    except Exception as e:
        print("type error: " + str(e))                

"""
def sendemail(s_from,s_to,subject,message):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    msg = MIMEMultipart()
    msg['From'] = 'openorange.eng@gmail.com'
    msg['To'] = 'openorange.eng@gmail.com'
    msg['Subject'] = 'DEBUG ATIVADO'
    msg.attach(MIMEText(message))

    mailserver = smtplib.SMTP('smtp.gmail.com', 587)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    
    mailserver.sendmail('openorange.eng@gmail.com', 'openorange.eng@gmail.com', msg.as_string())
    mailserver.quit()
"""

def sendemail(s_to,message,country):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    print("****************************************************************************************************")
    msg = MIMEMultipart()
    print(config["email_cfg"]["from"])
    msg['From'] = config["email_cfg"]["from"]
    print(s_to)
    msg['To'] = s_to

    if (country=='en'):
        msg['Subject'] = 'Your registration was successful!'
    if (country=='es'):
        msg['Subject'] = '¡Su registro se realizó correctamente!'
    if (country=='pt'):
        msg['Subject'] = 'Seu cadastro foi realizado com sucesso!'
    print(message)
    
    msg.attach(MIMEText(message))
    print("PASSO-01")

    mailserver = smtplib.SMTP(config["email_cfg"]["smtpcfg"], int(config["email_cfg"]["smtport"]))
    # identify ourselves to smtp gmail client
    print("PASSO-02")
    mailserver.ehlo()
    # secure our email with tls encryption
    print("PASSO-03")
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    print("PASSO-04")
    print(config["email_cfg"]["login"])
    print(config["email_cfg"]["pwd"])
    
    print("PASSO-05")
    mailserver.sendmail(config["email_cfg"]["from"], s_to, msg.as_string())
    print("PASSO-06")
    mailserver.quit()


####################################################  DATABASE TOOLS ###############################################################
def connecttomariadb():
    print("user="+ config["mariadb"]["user"] + "  password=" + config["mariadb"]["pwd"] + "  ip=" + config["mariadb"]["ip"] )
    cnx = mysql.connector.connect(user=config["mariadb"]["user"], password=config["mariadb"]["pwd"],
                                  host=config["mariadb"]["ip"], port=config["mariadb"]["port"],
                                  database=config["mariadb"]["database"])
    cursor = cnx.cursor()
    return cnx, cursor

def select(sql):
    """logging.info("select")"""
    res = None
    cnx, cursor = connecttomariadb()
    logging.info(sql)
    cursor.execute(sql)
    for r in cursor: res = r[0]
    cursor.close()
    cnx.close()
    return res

#******************************************************************************************************************************************

@app.route('/login_customer', methods=['POST', 'GET'])
def login_customer():
    logging.info("/login_customer")    
    location(request.remote_addr)

    res=""
    tolkenID = ""
    company_name = ""
    resposible_name = ""
    password = ""
    customer_lvl = ""
    coutry = ""

    email = request.form.get('email')
    pwd = request.form.get('password')

    cnx, cursor = connecttomariadb()
    sSQL = "SELECT tolken_id,company_name,responsible_name,responsible_email,password,customer_level,country FROM " + config["mariadb"]["database"] + "." + "register WHERE responsible_email='" + email + "' AND password=SHA1('" + pwd + "');" 

    try:
        rows_count = cursor.execute(sSQL)
        if rows_count == None:
           res=erro_login("pt")                            
        
        for r in cursor:
            tolkenID = r[0]
            company_name = r[1]
            resposible_name = r[2]            
            print(tolkenID)
            print(company_name)
            print(resposible_name)
            print(r[3])
            print(r[4])
            res="200 OK\n"
    except mysql.connector.Error as err:  
        logging.debug(err)
    finally:
        cursor.close()
        cnx.close()

    return res

################################################################# REGISTRO DE CLIENTES ####################################################################################################
@app.route('/customer_reg', methods=['POST', 'GET'])
def customer_reg():
    logging.info("/customer_reg")    
    location(request.remote_addr)
  
    id    = str(uuid.uuid4())
    cia   = request.form.get('empresa')
    usr   = request.form.get('usuario')
    email = request.form.get('email')
    pwd   = request.form.get('password')
    lvl   = request.form.get('level')
    lang  = request.form.get('lang')
    term  = request.form.get('Contrato')

    cnx,cursor = connecttomariadb()
    sSQL = ("INSERT INTO " + config["mariadb"]["database"] + "." + "register"
            "( tolken_id,company_name,responsible_name,responsible_email,password,customer_level,country,acept_termuser )"
            " VALUES('" + id + "','" + cia + "','" + usr + "','" + email + "',SHA1('" + pwd + "'),'" + lvl + "','" + lang + "','" + term + "')")

    try:
        cursor.execute(sSQL)
        cnx.commit()
    except mysql.connector.Error as err:
        logging.debug(err)
    finally:
        cursor.close()
        cnx.close()

    #sendemail(email,lang,"Teste.")

    return ai2hhtml("pt")


def painel_ai2hadmin(lang):
    shtml  = '<!doctype html>'
    shtml += '<html lang="pt-br">' 

def erro_login(lang):
    resp  = '<!doctype html>'
    resp += '<html lang="pt-br">'
    resp += '<script type="text/javascript"> alert("Login ou Senha Inválido!\\nFavor tentar novamente.") </script>'
    resp += '<meta http-equiv="Refresh" content="5; url=http://ai2h.ddns.net:8181/pt/login.html" />'
    resp += '</html>'
    return resp

def ai2hhtml(lang):
    resp  = '<!doctype html>'
    resp += '<html lang="pt-br">'
    resp += '<script type="text/javascript"> alert("Seu Cadastro foi realizado com sucesso!\\nVeja sua caixa de email para mais informações.") </script>'
    resp += '<meta http-equiv="Refresh" content="5; url=http://ai2h.ddns.net:8181/pt/login.html" />'
    resp += '</html>'
    return resp

#**********************************************************************************************************************************
if __name__ == '__main__':
    print('Start AI2H Server Admin')
    print('Copyright (c) 2019 by AI2H - Artificial Inteligence Interface Human')
    print('AI2H_SRV_ADMIN - Write and Developed by Marco Aurelio Gorgulho Drummond')
    #print("user="+ config["mariadb"]["user"] + "  password=" + config["mariadb"]["pwd"] + "  ip=" + config["mariadb"]["ip"] )

    usehttps = int(config["usehttps"]["https"])
    if usehttps == 1:
        print("Start AI2H Server Admin using https")
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(config["usehttps"]["context_load_verify_locations"])
        context.load_cert_chain(config["usehttps"]["context_load_cert_chain_crt"],config["usehttps"]["/etc/apache2/certs/2019/srvai2h.ai2h.net/srvai2h.ai2h.net.key"])
        app.run(debug=config["ai2hsrvadmin"]["debug"],ssl_context=context, threaded=True)
    else:
        print('host:' + config["ai2hsrvadmin"]["ip"]+':'+str(config["ai2hsrvadmin"]["port"]))
        app.run(debug=config["ai2hsrvadmin"]["debug"], host=config["ai2hsrvadmin"]["ip"], port=config["ai2hsrvadmin"]["port"], threaded=True)