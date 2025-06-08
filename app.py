# app.py (VFinal v2 - Estrutura para Gunicorn em Web Service Gratuito)

import os
import time
import requests
import json
from flask import Flask
from teslapy import Tesla, VehicleError
import threading

TESLA_EMAIL = os.environ.get('TESLA_EMAIL')
TESLA_CACHE_DATA = os.environ.get('TESLA_CACHE_JSON')
SOLPLANET_API_KEY = os.environ.get('SOLPLANET_API_KEY')
SOLPLANET_INVERTER_ID = os.environ.get('SOLPLANET_INVERTER_ID')

MIN_SOLAR_PARA_INICIAR_KW = 2.0
MIN_SOLAR_PARA_PARAR_KW = 0.5
MAX_BATTERY_SOC = 90
CHECK_INTERVAL_SECONDS = 300

app = Flask(__name__)

def get_solplanet_data():
    if not SOLPLANET_API_KEY or SOLPLANET_API_KEY == 'ainda_a_esperar':
        print("AVISO: Chave da API da Solplanet não configurada...")
        return 0
    print("A obter dados da Solplanet...")
    return 0

def run_automation_logic(tesla_client):
    print("--- A iniciar novo ciclo de automação ---")
    try:
        vehicles = tesla_client.vehicle_list()
        if not vehicles:
            print("ERRO: Nenhum veículo encontrado.")
            return
        my_car = vehicles[0]
        print(f"Veículo encontrado: {my_car['display_name']}")
        if my_car['state'] != 'online':
            print(f"O veículo está '{my_car['state']}'. A tentar acordar...")
            my_car.sync_wake_up()
            print("O veículo está agora online.")
        my_car.get_vehicle_data()
        charge_state = my_car['charge_state']
        is_charging = charge_state['charging_state'] == 'Charging'
        battery_level = charge_state['battery_level']
        print(f"Estado atual: Bateria a {battery_level}%, Carregando: {is_charging}")
        solar_power = get_solplanet_data()
        if not is_charging and solar_power >= MIN_SOLAR_PARA_INICIAR_KW and battery_level < MAX_BATTERY_SOC:
            print(f"CONDIÇÃO ATINGIDA: A iniciar carregamento.")
            my_car.command('CHARGE_START')
        elif is_charging and (solar_power < MIN_SOLAR_PARA_PARAR_KW or battery_level >= MAX_BATTERY_SOC):
            print(f"CONDIÇÃO ATINGIDA: A parar carregamento.")
            my_car.command('CHARGE_STOP')
        else:
            print("Nenhuma condição de automação atingida.")
    except Exception as e:
        print(f"Ocorreu um erro no ciclo de automação: {e}")

def background_task():
    print("A inicializar a tarefa de fundo...")
    try:
        with open('cache.json', 'w') as f:
            f.write(TESLA_CACHE_DATA)
        print("Ficheiro cache.json criado com sucesso.")
    except Exception as e:
        print(f"ERRO CRÍTICO ao criar o cache.json: {e}")
        return
    tesla_client = Tesla(TESLA_EMAIL, cache_file='cache.json')
    print("Cliente Tesla inicializado com sucesso.")
    while True:
        run_automation_logic(tesla_client)
        print(f"A aguardar {CHECK_INTERVAL_SECONDS} segundos para o próximo ciclo.")
        time.sleep(CHECK_INTERVAL_SECONDS)

@app.route('/')
def home():
    return "Serviço de automação Tesla está vivo e a correr."

if not TESLA_EMAIL or not TESLA_CACHE_DATA:
    print("ERRO CRÍTICO: Variáveis de ambiente Tesla não definidas!")
else:
    automation_thread = threading.Thread(target=background_task)
    automation_thread.daemon = True
    automation_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
