# teste_final_tesla.py (v4 - Lógica para acordar o carro)
import time
from teslapy import Tesla, VehicleError

# Coloque o seu email real da conta Tesla aqui.
TESLA_EMAIL = 'rubengoval@gmail.com'

print("--- A iniciar teste final com o cache.json ---")

try:
    # Inicializar a biblioteca usando o email e o ficheiro cache.json
    tesla = Tesla(TESLA_EMAIL, cache_file='cache.json')
    
    print("1. A tentar obter a lista de veículos...")
    vehicles = tesla.vehicle_list()
    
    if not vehicles:
        raise Exception("Nenhum veículo encontrado na conta. Verifique o cache.json.")
        
    my_car = vehicles[0]
    print(f"Sucesso! Veículo encontrado: {my_car['display_name']}")
    
    # PASSO 2: ACORDAR O CARRO DE FORMA PACIENTE
    print("\n2. A verificar o estado do veículo...")
    
    if my_car['state'] != 'online':
        print(f"O veículo está '{my_car['state']}'. A tentar acordar... Isto pode demorar até 2 minutos. Por favor, aguarde.")
        my_car.sync_wake_up() # Esta função espera que o carro acorde
        print("O veículo está agora online!")
    else:
        print("O veículo já se encontra online.")

    # PASSO 3: OBTER OS DADOS
    print("\n3. A obter dados do veículo...")
    
    # Agora que o carro está acordado, este pedido deverá funcionar
    charge_state = my_car['charge_state']
    battery_level = charge_state['battery_level']
    charging_state = charge_state['charging_state']
    
    print("\n--- SUCESSO! TESTE CONCLUÍDO ---")
    print(f"Nível da Bateria: {battery_level}%")
    print(f"Estado do Carregamento: {charging_state}")
    print("-----------------------------------")
    print("A sua autenticação oficial com a Tesla está a funcionar perfeitamente!")

except VehicleError as e:
    print(f"\n--- OCORREU UM ERRO DE COMUNICAÇÃO COM O VEÍCULO ---")
    print(f"Detalhe: {e}")
    print("O carro pode não ter acordado a tempo ou estar sem ligação à internet.")

except Exception as e:
    print(f"\n--- OCORREU UM ERRO GERAL ---")
    print(f"Detalhe: {e}")
    print("Verifique se o ficheiro 'cache.json' existe e se o email no script está correto.")
