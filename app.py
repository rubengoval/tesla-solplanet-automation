# app.py (VFinal v2 - Estrutura Corrigida para Gunicorn)

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
MIN_SOLAR_PARA_INICIAR_KW = 2.0
MIN_SOLAR_PARA_PARAR_KW = 0.5
MAX_BATTERY_SOC = 90
CHECK_INTERVAL_SECONDS = 300

# --- INICIALIZAÇÃO DO FLASK ---
app = Flask(__name__)

# --- FUNÇÕES DAS APIS ---
def get_solplanet_data():
    """Obtém dados de produção do inversor Solplanet."""
    if not SOLPLANET_API_KEY or SOLPLANET_API_KEY == 'ainda_a_esperar':
        print("AVISO: Chave da API da Solplanet não configurada. A assumir 0 kW de produção solar.")
        return 0
    
    print("A obter dados da Solplanet...")
    try:
        url = f"https://cloud.solplanet.net/api/v1/inverters/{SOLPLANET_INVERTER_ID}/data" # Exemplo de URL
        headers = {"Authorization": f"Bearer {SOLPLANET_API_KEY}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        power_kw = data.get('current_power_kw', 0)
        print(f"Produção solar atual: {power_kw} kW")
        return power_kw
    except requests.exceptions.RequestException as e:
        print(f"Erro ao contactar a API da Solplanet: {e}")
        return 0

# --- LÓGICA PRINCIPAL DA AUTOMAÇÃO ---
def run_automation_logic(tesla_client):
    """O ciclo principal que corre para sempre."""
    print("--- A iniciar novo ciclo de automação ---")
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
        battery_level = charge_state['battery_level']

        print(f"Estado atual: Bateria a {battery_level}%, Carregando: {is_charging}")
        solar_power = get_solplanet_data()

        if not is_charging and solar_power >= MIN_SOLAR_PARA_INICIAR_KW and battery_level < MAX_BATTERY_SOC:
            print(f"CONDIÇÃO ATINGIDA: Produção solar ({solar_power} kW) é suficiente. A iniciar carregamento.")
            my_car.command('CHARGE_START')
        elif is_charging and (solar_power < MIN_SOLAR_PARA_PARAR_KW or battery_level >= MAX_BATTERY_SOC):
            print(f"CONDIÇÃO ATINGIDA: Produção solar ({solar_power} kW) insuficiente ou bateria cheia. A parar carregamento.")
            my_car.command('CHARGE_STOP')
        else:
            print("Nenhuma condição de automação atingida. A manter estado atual.")
    except VehicleError as e:
        print(f"Ocorreu um erro de comunicação com o veículo: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado no ciclo de automação: {e}")

# --- TAREFA DE FUNDO ---
def background_task():
    """Inicializa o cliente Tesla e entra no ciclo infinito."""
    print("A inicializar a tarefa de fundo...")
    try:
        with open('cache.json', 'w') as f:
            f.write(TESLA_CACHE_DATA)
        print("Ficheiro cache.json criado com sucesso a partir das variáveis de ambiente.")
    except Exception as e:
        print(f"ERRO CRÍTICO ao criar o cache.json: {e}")
        return

    tesla_client = Tesla(TESLA_EMAIL, cache_file='cache.json')
    print("Cliente Tesla inicializado com sucesso.")

    while True:
        run_automation_logic(tesla_client)
        print(f"A aguardar {CHECK_INTERVAL_SECONDS} segundos para o próximo ciclo.")
        time.sleep(CHECK_INTERVAL_SECONDS)

# --- PONTO DE ENTRADA E ARRANQUE DA AUTOMAÇÃO ---
@app.route('/')
def home():
    return "Serviço de automação Tesla está vivo e a correr."

# ESTA PARTE FOI MOVIDA PARA FORA DO "IF"
# Agora, o Gunicorn irá executar este código ao carregar o ficheiro.
if not TESLA_EMAIL or not TESLA_CACHE_DATA:
    print("ERRO CRÍTICO: As variáveis de ambiente TESLA_EMAIL ou TESLA_CACHE_JSON não estão definidas! A tarefa de automação não pode começar.")
else:
    automation_thread = threading.Thread(target=background_task)
    automation_thread.daemon = True
    automation_thread.start()

# Este bloco só é executado se corrermos o ficheiro localmente com "python app.py"
if __name__ == '__main__':
    print("A iniciar o servidor de desenvolvimento Flask (apenas para teste local).")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
