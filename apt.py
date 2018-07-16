import datetime
import logging
import requests
from random import randint
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()
FERIADOS = [
    datetime.date(2018, 7, 9),
    datetime.date(2018, 7, 18),
    datetime.date(2018, 7, 19),
    datetime.date(2018, 7, 20),
    datetime.date(2018, 7, 21),
    datetime.date(2018, 7, 22),
    datetime.date(2018, 7, 23),
    datetime.date(2018, 7, 24),
    datetime.date(2018, 7, 25),
    datetime.date(2018, 7, 26),
    datetime.date(2018, 7, 27),
    datetime.date(2018, 9, 7),
    datetime.date(2018, 10, 12),
    datetime.date(2018, 11, 2),
    datetime.date(2018, 11, 15),
    datetime.date(2018, 11, 16),
    datetime.date(2018, 12, 24),
    datetime.date(2018, 12, 25),
    datetime.date(2018, 12, 26),
    datetime.date(2018, 12, 27),
    datetime.date(2018, 12, 28),
    datetime.date(2018, 12, 31),
    datetime.date(2019, 1, 1),
    datetime.date(2019, 1, 2)
]

LOCALIZACOES = [
    {
        'lat': '-23.2279589',
        'lng': '-45.8572695',
        'address': 'Av. Brg. Faria Lima, 601'
    },
    {
        'lat': '-23.21897476',
        'lng': '-45.85305484',
        'address': 'Estr. Mun. Glaudistom Pereira de Oliveira, 270'
    },
    {
        'lat': '-23.22952045',
        'lng': '-45.85532742',
        'address': 'Av. Dr. Amin Simão, 897'
    }
]

JOB_ID_ENTRADA = 'aponta_entrada'
JOB_ID_INICIO_ALMOCO = 'aponta_inicio_almoco'
JOB_ID_FIM_ALMOCO = 'aponta_fim_almoco'
JOB_ID_SAIDA = 'aponta_saida'

JOB_HORA_ENTRADA = '08'
JOB_HORA_INICIO_ALMOCO = '12'
JOB_HORA_FIM_ALMOCO = '13'
JOB_HORA_SAIDA = '17'

START = 'start'
FINISH = 'finish'
MINUTO_PADRAO = '01'

logging.getLogger('apscheduler.executors.default').propagate = False
root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


def eh_feriado():
    hoje = datetime.datetime.now().date()
    if hoje in FERIADOS:
        return True

    return False


@sched.scheduled_job('cron', id=JOB_ID_ENTRADA, day_of_week='mon-fri', hour=JOB_HORA_ENTRADA, minute=MINUTO_PADRAO)
def aponta_entrada():
    aponta(JOB_ID_ENTRADA, START, '>>> Entrada', JOB_HORA_ENTRADA)


@sched.scheduled_job('cron', id=JOB_ID_INICIO_ALMOCO, day_of_week='mon-fri', hour=JOB_HORA_INICIO_ALMOCO, minute=MINUTO_PADRAO)
def aponta_inicio_almoco():
    aponta(JOB_ID_INICIO_ALMOCO, FINISH, '>>> Início almoço', JOB_HORA_INICIO_ALMOCO)


@sched.scheduled_job('cron', id=JOB_ID_FIM_ALMOCO, day_of_week='mon-fri', hour=JOB_HORA_FIM_ALMOCO, minute=MINUTO_PADRAO)
def aponta_fim_almoco():
    aponta(JOB_ID_FIM_ALMOCO, START, '<<< Volta do almoço', JOB_HORA_FIM_ALMOCO)


@sched.scheduled_job('cron', id=JOB_ID_SAIDA, day_of_week='mon-fri', hour=JOB_HORA_SAIDA, minute=MINUTO_PADRAO)
def aponta_saida():
    aponta(JOB_ID_SAIDA, FINISH, '<<< Saída', JOB_HORA_SAIDA)


@sched.scheduled_job('cron', id='reschedule_jobs', day_of_week='mon-fri', hour='23', minute='30')
def reschedula_jobs():
    offset_dia = randint(0, 4)
    offset_almoco = randint(0, 4)

    sched.reschedule_job(JOB_ID_ENTRADA, trigger='cron', hour=JOB_HORA_ENTRADA, minute=offset_dia)
    loga_job_reschedulado(JOB_ID_ENTRADA, JOB_HORA_ENTRADA, offset_dia)

    sched.reschedule_job(JOB_ID_SAIDA, trigger='cron', hour=JOB_HORA_SAIDA, minute=offset_dia)
    loga_job_reschedulado(JOB_ID_SAIDA, JOB_HORA_SAIDA, offset_dia)

    sched.reschedule_job(JOB_ID_INICIO_ALMOCO, trigger='cron', hour=JOB_HORA_INICIO_ALMOCO, minute=offset_almoco)
    loga_job_reschedulado(JOB_ID_INICIO_ALMOCO, JOB_HORA_INICIO_ALMOCO, offset_almoco)

    sched.reschedule_job(JOB_ID_FIM_ALMOCO, trigger='cron', hour=JOB_HORA_FIM_ALMOCO, minute=offset_almoco)
    loga_job_reschedulado(JOB_ID_FIM_ALMOCO, JOB_HORA_FIM_ALMOCO, offset_almoco)


def loga_job_reschedulado(job_id, hora, minuto):
    reschedule_msg = 'Job {} reschedulado para {}:0{}'.format(job_id, hora, minuto)
    logging.info(reschedule_msg)


def aponta(job_id, entrada_ou_saida, log_msg, hora):
    if eh_feriado():
        return

    headers = {'auth': os.environ['APT_AUTH'], 'Content-Type': 'application/json'}
    body = LOCALIZACOES[randint(0, 2)]
    
    response = requests.post(os.environ['APT_URL'] + entrada_ou_saida, headers=headers, json=body)
    if response.status_code != 200:
        print('Erro ao apontar!')
        print('HTTP Status:', response.status_code)
        print('Request body:', body)
        print('Response body:', response.text)
        envia_email(headers, body, response.status_code, response.text)
    
    logging.info(log_msg)


def envia_email(request_headers, request_body, response_status_code, response_body):
    email_de = os.environ['APT_EMAIL_FROM']
    email_para = os.environ['APT_EMAIL_TO']
    msg = MIMEMultipart()
    msg['From'] = email_de
    msg['To'] = email_para
    msg['Subject'] = 'Problema no apt!'

    body = '<h3>Deu um problema no apt:</h3>' + \
           '<fieldset><legend>Request</legend>' + \
           '<b>Header<b>: {}<br><b>Body<b>: {}</fieldset><br>' + \
           '<fieldset><legend>Response</legend>' + \
           '<b>Status</b>: {}<br><b>Body</b>: {}</fieldset>'
    final_body = body.format(request_headers, request_body, response_status_code, response_body)
    print(final_body)
    msg.attach(MIMEText(final_body, 'html'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_de, os.environ['APT_EMAIL_PASS'])
    text = msg.as_string()
    server.sendmail(email_de, email_para, text)
    server.quit()


sched.start()
