#!/usr/bin/python3

import requests
from datadog import initialize, statsd
import sys
import json
import logging

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_json(message, **kwargs):
    log_entry = {'message': message}
    log_entry.update(kwargs)
    logger.info(json.dumps(log_entry))

def datadog_send_metrics(ENV, device_name, device_id, battery_avg):
   # para o agent datadog rodando no mesmo host do script e na porta padrão
   options = {
       'statsd_host':'127.0.0.1',
       'statsd_port':8125
   }
   initialize(**options)
   # metrica chamada de dev_battery_avg
   # tags para agrupamento na metrica: env, host (device_name), device_id
   statsd.gauge('device_battery_avg', battery_avg, tags=[f"env:{ENV}", f"host:{device_name}", f"device_id:{device_id}"])


def consulta_device(ENV, AUTHTOKEN, D_I, D_F):
    # Endpoint to get the station IDs
    station_ids_url = "https://api.emeter.com.br:8443/emeter/api/v1/hidrologia/listarEstacoes"
    headers = {
        "accept": "application/json",
        "Authorization": f"{AUTHTOKEN}"
    }

    # Send GET request to retrieve the station IDs
    response = requests.get(station_ids_url, headers=headers)
    station_ids = response.json()
    # formato para datas, aqui coleta metrica de 1hora
    # data_inicial (D_I): 2024-10-28 00:00:00
    # data_final (D_F): 2024-10-28 01:00:00

    # Check if the request was successful
    if response.status_code == 200:
        # Iterate over the station IDs and fetch the battery information
        for station_id in station_ids:
            # Endpoint to get the battery information
            id_ponto = station_id['id_ponto']
            estacao_id = station_id['estacao_id']
            battery_info_url = f"https://api.emeter.com.br:8443/emeter/api/v1/hidrologia/dadosQuarterValues?site_id={id_ponto}&hydro_id={estacao_id}&data_inicial={D_I}&data_final={D_F}"
            
            # Send GET request to retrieve the battery information
            battery_response = requests.get(battery_info_url, headers=headers)
            battery_info = battery_response.json()
            battery_resume = battery_info['resumo']
            if battery_resume == {}:
                battery_avg = 0
            else:
                # Process the battery information as needed
                # ...
                # in this point we check if the key 39 exists in the response, if not we set the battery_avg to 0
                if '39' not in battery_resume:
                    battery_avg = 0
                else:
                    battery_avg = battery_resume['39']['avg']
                    log_json('Device name: %s - id: %s - battery %s' %(station_id['nome_ponto'], station_id['id_ponto'], battery_avg), battery_avg=battery_avg) 
                    datadog_send_metrics(ENV, station_id['nome_ponto'], station_id['id_ponto'], battery_avg)
    else:
        log_json("Failed to retrieve station IDs. Status code: %s" %(response.status_code))


def main():
    if len(sys.argv) < 4:
        print('Usage: main.py <ENV> <AUTHTOKEN> <DATA_INICIAL> <DATA_FINAL>')
        print('       ENV: tag para definição de environemnt no datadog')
        print('       AUTHTOKEN: tocken authentication api')
        print('       DATA_INICIAL: 2024-10-28 00:00:00')
        print('       DATA_FINAL: 2024-10-28 01:00:00')
        sys.exit(-1)
    ENV = sys.argv[1]
    AUTHTOKEN = sys.argv[2]
    DATA_INICIAL = sys.argv[3]
    DATA_FINAL = sys.argv[4]
    consulta_device(ENV, AUTHTOKEN, DATA_INICIAL, DATA_FINAL)


if __name__ == "__main__":
    main()

