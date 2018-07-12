import datetime
import logging
import sys
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()
FERIADOS = [
    datetime.date(2018, 7, 9),
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


@sched.scheduled_job('cron', id='job-entrada', day_of_week='mon-fri', hour='08', minute='00')
def aponta_entrada():
    if not eh_feriado():
        aponta('start')
        logging.info('>>> Entrada')


@sched.scheduled_job('cron', id='job-inicio-almoco', day_of_week='mon-fri', hour='12', minute='00')
def aponta_inicio_almoco():
    if not eh_feriado():
        aponta('finish')
        logging.info('>>> Início almoço')


@sched.scheduled_job('cron', id='job-fim-almoco', day_of_week='mon-fri', hour='13', minute='00')
def aponta_fim_almoco():
    if not eh_feriado():
        aponta('start')
        logging.info('<<< Volta do almoço')


@sched.scheduled_job('cron', id='saida', day_of_week='mon-fri', hour='17', minute='00')
def aponta_saida():
    if not eh_feriado():
        aponta('finish')
        logging.info('<<< Saída')


def aponta(entrada_ou_saida):
    headers = {'auth': os.environ['APT_AUTH'],
               'Content-Type':'application/json'}
    body = {'lat': '-23.2279589',
            'lng': '-45.8572695',
            'address': 'Av. Brg. Faria Lima, 601'}
    response = requests.post(os.environ['APT_URL'] + entrada_ou_saida, headers=headers, json=body)
    print(response.status_code)
    print(response.text)


sched.start()