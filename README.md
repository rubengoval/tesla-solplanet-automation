# app.py

import os
import time
import requests # Para fazer pedidos a APIs
from flask import Flask

# --- CONFIGURAÇÃO ---
# Deverá obter estes valores a partir das variáveis de ambiente no Render para segurança
TESLA_API_TOKEN = os.environ.get('TESLA_API_TOKEN', 'O_SEU_TOKEN_DA_TESLA_AQUI')
VIN = os.environ.get('VIN', 'O_SEU_VIN_DO_CARRO_AQUI') # Vehicle Identification Number
SOLPLANET_API_KEY = os.environ.get('SOLPLANET_API_KEY', 'A_SUA_CHAVE_API_SOLPLANET_AQUI')
SOLPLANET_INVERTER_ID = os.environ.get('SOLPLANET_INVERTER_ID', 'O_ID_DO_SEU_INVERSOR_AQUI')

# As suas regras de automação
MIN_SOLAR_PARA_INICIAR_KW = 2.0  # Iniciar a carregar acima de 2.0 kW
MIN_SOLAR_PARA_PARAR_KW = 0.5   # Parar de carregar abaixo de 0.5 kW
MAX_BATTERY_SOC = 90            # Parar de carregar quando atingir 90%

app = Flask(__name__)

# --- FUNÇÕES DE INTERAÇÃO COM APIs ---

def get_solplanet_data():
    """
    Função para obter dados do inversor Solplanet.
    Isto é um EXEMPLO. Terá de adaptar ao API real da Solplanet.
    """
    print("A obter dados da Solplanet...")
    try:
        # URL do API da Solplanet (TERÁ DE ENCONTRAR O CORRETO)
        url = f"https://api.solplanet.com/v1/inverters/{SOLPLANET_INVERTER_ID}/data"
        headers = {"Authorization": f"Bearer {SOLPLANET_API_KEY}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lança um erro se o pedido falhar
        data = response.json()
        
        # Assumindo que o API devolve a potência em Watts
        power_kw = data.get('current_power_kw', 0)
        print(f"Produção solar atual: {power_kw} kW")
        return power_kw
    except requests.exceptions.RequestException as e:
        print(f"Erro ao contactar a API da Solplanet: {e}")
        return 0 # Retorna 0 em caso de erro

def get_tesla_vehicle_data():
    """
    Obtém dados importantes do veículo Tesla.
    Esta função precisa de ser implementada com uma biblioteca Tesla ou chamadas diretas.
    """
    print("A obter dados da Tesla...")
    # Esta parte é complexa. Idealmente, usaria uma biblioteca como a "teslapy".
    # Por agora, vamos retornar dados de exemplo.
    # TODO: Implementar a chamada real à API da Tesla.
    print("AVISO: Usando dados de exemplo da Tesla.")
    example_data = {
        "is_charging": False,
        "soc": 75,
        "is_plugged_in": True,
        "is_at_home": True # Precisaria de lógica de geolocalização
    }
    return example_data

def set_tesla_charging(state: bool):
    """
    Envia comando para iniciar ou parar o carregamento.
    """
    command = "start_charge" if state else "stop_charge"
    print(f"A enviar comando para a Tesla: {command}...")
    # TODO: Implementar a chamada real à API da Tesla para enviar o comando.
    print(f"Comando '{command}' enviado com sucesso (simulação).")
    return True

# --- LÓGICA PRINCIPAL DA AUTOMAÇÃO ---

def run_automation_logic():
    print("\n--- A iniciar novo ciclo de automação ---")
    solar_power = get_solplanet_data()
    tesla_data = get_tesla_vehicle_data()

    # Condições para mais fácil leitura
    is_charging = tesla_data["is_charging"]
    can_charge = tesla_data["is_plugged_in"] and tesla_data["is_at_home"]
    battery_level = tesla_data["soc"]

    if not can_charge:
        print("Carro não está em casa ou não está ligado à corrente. A aguardar.")
        return

    # Lógica para INICIAR o carregamento
    if not is_charging and solar_power > MIN_SOLAR_PARA_INICIAR_KW and battery_level < MAX_BATTERY_SOC:
        print("CONDIÇÃO ATINGIDA: Potência solar suficiente e bateria não está cheia. A iniciar carregamento.")
        set_tesla_charging(True)
    
    # Lógica para PARAR o carregamento
    elif is_charging and (solar_power < MIN_SOLAR_PARA_PARAR_KW or battery_level >= MAX_BATTERY_SOC):
        print("CONDIÇÃO ATINGIDA: Potência solar insuficiente ou bateria cheia. A parar carregamento.")
        set_tesla_charging(False)
    
    else:
        print("Nenhuma condição atingida. O estado de carregamento permanece o mesmo.")


# --- PÁGINA WEB E EXECUÇÃO ---

@app.route('/')
def home():
    # Esta página serve apenas para o Render saber que a sua app está viva.
    return "Serviço de automação Tesla-Solplanet a correr."

def background_task():
    """ A tarefa que corre em segundo plano para sempre """
    while True:
        run_automation_logic()
        # Espera 5 minutos antes de verificar novamente
        print("A aguardar 5 minutos para o próximo ciclo...")
        time.sleep(300) 

if __name__ == '__main__':
    # Iniciar a tarefa de automação numa thread separada (para não bloquear a app web)
    import threading
    automation_thread = threading.Thread(target=background_task)
    automation_thread.daemon = True
    automation_thread.start()
    
    # Iniciar a app web (o Render precisa disto)
    # A porta é definida pelo Render através da variável de ambiente PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
