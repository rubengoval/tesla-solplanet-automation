# app.py (VFinal - Automação na Nuvem)

import os
import time
import requests
import json
from flask import Flask
from teslapy import Tesla, VehicleError
import threading

# --- CONFIGURAÇÃO LIDA DO RENDER ---
# Estes valores são configurados como Variáveis de Ambiente no Render
TESLA_EMAIL = os.environ.get('TESLA_EMAIL')
TESLA_CACHE_DATA = os.environ.get('TESLA_CACHE_JSON')
SOLPLANET_API_KEY = os.environ.get('SOLPLANET_API_KEY')
SOLPLANET_INVERTER_ID = os.environ.get('SOLPLANET_INVERTER_ID')

# Suas regras de automação
MIN_SOLAR_PARA_INICIAR_KW = 2.0  # Iniciar a carregar acima de 2.0 kW
MIN_SOLAR_PARA_PARAR_KW = 0.5   # Parar de carregar abaixo de 0.5 kW
MAX_BATTERY_SOC = 90            # Parar de carregar quando atingir 90%
CHECK_INTERVAL_SECONDS = 300 # Verificar a cada 5 minutos (300 segundos)

# --- INICIALIZAÇÃO DO FLASK (Para o Render) ---
app = Flask(__name__)

# --- FUNÇÕES DAS APIS ---

def get_solplanet_data():
    """Obtém dados de produção do inversor Solplanet."""
    if not SOLPLANET_API_KEY or SOLPLANET_API_KEY == 'ainda_a_esperar':
        print("AVISO: Chave da API da Solplanet não configurada. A assumir 0 kW de produção solar.")
        return 0
    
    print("A obter dados da Solplanet...")
    try:
        # NOTA: Este URL é um exemplo, precisa de ser confirmado quando tiver acesso à API
        url = f"https://cloud.solplanet.net/api/v1/inverters/{SOLPLANET_INVERTER_ID}/data" 
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
        
        # Acordar o carro de forma paciente se necessário
        if my_car['state'] != 'online':
            print(f"O veículo está '{my_car['state']}'. A tentar acordar...")
            my_car.sync_wake_up()
            print("O veículo está agora online.")
        
        # Obter os dados necessários
        my_car.get_vehicle_data()
        charge_state = my_car['charge_state']
        is_charging = charge_state['charging_state'] == 'Charging'
        battery_level = charge_state['battery_level']

        print(f"Estado atual: Bateria a {battery_level}%, Carregando: {is_charging}")

        # Obter dados da produção solar
        solar_power = get_solplanet_data()

        # Tomar a decisão
        if not is_charging and solar_power >= MIN_SOLAR_PARA_INICIAR_KW and battery_level < MAX_BATTERY_SOC:
            print(f"CONDIÇÃO ATINGIDA: Produção solar ({solar_power} kW) é suficiente. A iniciar carregamento.")
            my_car.command('CHARGE_START')
        elif is_charging and (solar_power < MIN_SOLAR_PARA_PARAR_KW or battery_level >= MAX_BATTERY_SOC):
            print(f"CONDIÇÃO ATINGIDA: Produção solar ({solar_power} kW) insuficiente ou bateria cheia. A parar carregamento.")
            my_car.command('CHARGE_STOP')
