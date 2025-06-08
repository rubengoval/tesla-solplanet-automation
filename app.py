# app.py (VFinal v5 - Comandos de Carga Corrigidos)

import os
import time
import requests
import json
from flask import Flask
from teslapy import Tesla, VehicleError
import threading

# --- CONFIGURAÇÃO LIDA DO RENDER ---
TESLA_EMAIL = os.environ.get('TESLA_EMAIL')
TESLA_CACHE_DATA = os.environ.get('TESLA_CACHE_JSON')
SOLPLANET_API_KEY = os.environ.get('SOLPLANET_API_KEY')
SOLPLANET_INVERTER_ID = os.environ.get('SOLPLANET_INVERTER_ID')

# --- REGRAS DE AUTOMAÇÃO ---
CASA_BATERIA_MIN_PARA_PARAR = 70
CASA_BATERIA_MIN_PARA_INICIAR = 90
CARRO_BATERIA_MAX = 90
CHECK_INTERVAL_SECONDS = 300

# --- INICIALIZAÇÃO DO FLASK ---
app = Flask(__name__)

# --- FUNÇÕES DAS APIS ---
def get_house_battery_soc():
    if not SOLPLANET_API_KEY or SOLPLANET_API_KEY == 'ainda_a_esperar':
        print("AVISO: Chave da API da Solplanet não configurada. A assumir 0% de bateria da casa.")
        return 0
    
    print("A obter dados da bateria da casa via Solplanet...")
    # ... Lógica da Solplanet aqui ...
    return 0

# --- LÓGICA PRINCIPAL DA AUTOMAÇÃO ---
def run_automation_logic(tesla_client):
    print("--- A iniciar novo ciclo de automação (lógica de bateria da casa) ---")
    try:
        vehicles = tesla_client.vehicle_list()
        if not vehicles:
            print("ERRO: Nenhum veículo encontrado na conta Tesla.")
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
        car_battery_level = charge_state['battery_level']

        print(f"Estado do carro: Bateria a {car_battery_level}%, Carregando: {is_charging}")
        house_battery_soc = get_house_battery_soc()

        # MUDANÇA ABAIXO: Usar os comandos corretos da biblioteca
        if not is_charging and house_battery_soc >= CASA_BATERIA_MIN_PARA_INICIAR and car_battery_level < CARRO_BATERIA_MAX:
            print(f"CONDIÇÃO ATINGIDA: Bateria da casa ({house_battery_soc}%) está acima do limite. A enviar comando para INICIAR carregamento.")
            my_car.charge_start() # <-- CORREÇÃO
        elif is_charging and (house_battery_soc < CASA_BATERIA_MIN_PARA_PARAR or car_battery_level >= CARRO_BATERIA_MAX):
            print(f"CONDIÇÃO ATINGIDA: Bateria da casa ({house_battery_soc}%) ou do carro ({car_battery_level}%) atingiu o limite. A enviar comando para PARAR carregamento.")
            my_car.charge_stop() # <-- CORREÇÃO
        else:
            print("Nenhuma condição de automação atingida. A manter estado atual.")

    except VehicleError as e:
        print(f"Ocorreu um erro de comunicação com o veículo: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado no ciclo de automação: {e}")

# --- CÓDIGO DE ARRANQUE (igual ao anterior) ---
def background_task():
    print("A inicializar a tarefa de fundo...")
    try:
        with open('cache.json', 'w') as f: f.write(TESLA_CACHE_DATA)
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
    return "Serviço de automação Tesla (lógica de bateria da casa) está a correr."

if not TESLA_EMAIL or not TESLA_CACHE_DATA:
    print("ERRO CRÍTICO: Variáveis de ambiente Tesla não definidas!")
else:
    automation_thread = threading.Thread(target=background_task)
    automation_thread.daemon = True
    automation_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
