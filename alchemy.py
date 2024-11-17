from web3 import Web3
import json
import os
from dotenv import load_dotenv

# Carrega as configurações do arquivo .env
load_dotenv()

PRIVATE_RPC = os.getenv("PRIVATE_RPC")
ALCHEMY_RPC = os.getenv("ALCHEMY_RPC")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

# ABI do contrato
CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "target", "type": "address"},
            {"indexed": False, "name": "data", "type": "bytes"},
        ],
        "name": "DataReceived",
        "type": "event",
    },
    {
        "inputs": [
            {"name": "target", "type": "address"},
            {"name": "data", "type": "bytes"},
        ],
        "name": "receiveData",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
        ],
        "name": "forwardETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
]

# Inicializa o Web3
private_web3 = Web3(Web3.HTTPProvider(PRIVATE_RPC))
alchemy_web3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC))

if not private_web3.isConnected():
    print("Erro: Não foi possível conectar ao RPC privado.")
    exit()

if not alchemy_web3.isConnected():
    print("Erro: Não foi possível conectar ao Alchemy RPC.")
    exit()

print("Conexão bem-sucedida com ambos os RPCs.")

# Conecta ao contrato inteligente
contract = private_web3.eth.contract(address=Web3.toChecksumAddress(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

# Conecta à carteira do proprietário
account = private_web3.eth.account.from_key(PRIVATE_KEY)
owner_address = account.address


def handle_event(event):
    """
    Manipula eventos emitidos pelo contrato e redireciona a chamada para o Alchemy.
    """
    print(f"Evento capturado: {event}")

    from_address = event["args"]["from"]
    target_address = event["args"]["target"]
    data = event["args"]["data"]

    print(f"Redirecionando dados de {from_address} para {target_address} via Alchemy.")

    # Conexão ao contrato via Alchemy
    alchemy_contract = alchemy_web3.eth.contract(address=Web3.toChecksumAddress(target_address), abi=CONTRACT_ABI)

    # Envia a transação usando o Alchemy
    try:
        tx = alchemy_contract.functions.receiveData(target_address, data).buildTransaction({
            "chainId": alchemy_web3.eth.chain_id,
            "gas": 3000000,
            "gasPrice": alchemy_web3.toWei("20", "gwei"),
            "nonce": alchemy_web3.eth.getTransactionCount(owner_address),
        })

        signed_tx = alchemy_web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = alchemy_web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transação enviada para o Alchemy. Hash: {tx_hash.hex()}")
    except Exception as e:
        print(f"Erro ao redirecionar dados para o Alchemy: {str(e)}")


def log_loop(event_filter, poll_interval):
    """
    Loop para monitorar eventos no contrato.
    """
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        private_web3.middleware_onion.sleep(poll_interval)


# Configura um filtro para o evento `DataReceived`
event_filter = contract.events.DataReceived.createFilter(fromBlock="latest")

print("Monitorando eventos do contrato...")
log_loop(event_filter, 2)
