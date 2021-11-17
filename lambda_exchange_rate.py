import requests
import pytz
import string
import logging
import json
from bs4 import BeautifulSoup
from datetime import date, datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Cron 0 8,15 ? * MON-FRI *
#

# Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Time
tz = pytz.timezone('America/Mexico_City')
time = datetime.now(tz)
hour = time.hour
logger.info(f'Date with TimeZone: {time}')

# Info
SENDGRID_API_KEY = "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"
TEMPLATE_ID = 'd-fcf03d892dd14632b3b08ca15b631b05'
FROM_EMAIL = 'no-reply@exire.mx'
TO_EMAILS = [('msereno@exire.mx', 'Miguel Angel Sereno'),
             ('asanchez@exire.mx', 'Angeles Sanchez'),
             ('nmartinez@exire.mx', 'Naxhely Martinez'),
             ('srojas@exire.mx', 'Saul Rojas')]
GREETING = 'Buenas tardes '
PART_OF_DAY = 'vespertino'

if hour < 12:
    GREETING = 'Buenos días '
    PART_OF_DAY = 'matutino'

# DOF https://www.dof.gob.mx/indicad ores.php
# Interbancario BBVA https://www.bbva.mx/personas/informacion-financiera-al-dia.html
# Factor EUR-USD https://www.xe.com/es/currencyconverter/convert/?Amount=1&From=EUR&To=USD

# Date
today = date.today()
day = today.strftime('%d')
month = today.strftime('%m')
year = today.strftime('%Y')


def process(event=None, context=None):
    logger.info("#####DOLLAR#####")
    html_dollar = 'https://bbv.infosel.com/bancomerindicators/indexv8.aspx'
    logger.info(f'url_dollar: {html_dollar}')
    req = requests.get(html_dollar)

    soup = BeautifulSoup(req.content, 'html.parser')

    info_dollar = soup.findAll(
        class_='table tbl-info-financiera table-striped')[1]
    row_maker = 0
    value_dollar = ''
    for row in info_dollar.find_all('tr'):
        columns = row.find_all('td')
        for column in columns:
            row_maker += 1
            if row_maker == 3:
                value_dollar = column.text.strip()

    value_dollar = value_dollar.translate(
        {ord(c): None for c in string.whitespace})
    value_dollar = value_dollar.strip('$')
    currency_dollar = u"{:.2f}".format(float(value_dollar))
    logger.info(f'value_dollar:  {currency_dollar}')

    logger.info("#####DOF#####")
    url_dof = f"http://www.dof.gob.mx/indicadores_detalle.php?cod_tipo_indicador=158&dfecha={day}%2F{month}%2F{year}&hfecha={day}%2F{month}%2F{year}"
    logger.info(f'url_dof: {url_dof}')
    req = requests.get(url_dof)
    soup = BeautifulSoup(req.content, 'html.parser')

    table_dof = soup.find(class_='Tabla_borde')
    value_dof = ''
    for r in table_dof.find_all("tr"):
        columns = r.find_all('td')
        for column in columns:
            value_dof = column.text.strip()

    if value_dof == 'Valor':
        value_dof = 0

    currency_dof = u"{:.2f}".format(float(value_dof))
    logger.info(f'value_dof: {currency_dof}')

    logger.info("#####CON#####")
    url_con = "https://www.xe.com/es/currencyconverter/convert/?Amount=1&From=EUR&To=USD"
    logger.info(f'url_con: {url_con}')
    req = requests.get(url_con)
    soup = BeautifulSoup(req.content, 'html.parser')
    info_con = soup.find(class_="result__BigRate-sc-1bsijpp-1 iGrAod")
    value_con = info_con.getText().strip(' Dólares estadounidenses')
    value_con = value_con.replace(',', '.')
    currency_con = u"{:.2f}".format(float(value_con))

    logger.info(f'value_con: {currency_con}')

    # SendGrid
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAILS)

    message.dynamic_template_data = {
        'date': date.today().strftime("%m/%d/%Y"),
        'greetings': GREETING,
        'hours': PART_OF_DAY,
        'dof': currency_dof,
        'bbva': currency_dollar,
        'factor': currency_con
    }
    message.template_id = TEMPLATE_ID

    logger.info("#####SENDGRID#####")
    logger.info(f'template_id: {TEMPLATE_ID}')
    logger.info(f'destinations: {TO_EMAILS}')

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f'status_code: {response.status_code}')
    except Exception as e:
        logger.info(f'error {e.message}')
    return {
        'statusCode': 200,
        'body': json.dumps('OK Foreing Exchange!')
    }


def lambda_handler(event=None, context=None):
    process()
