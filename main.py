import random
import time

from web3 import Web3
import json

# БРИДЖИТ ВЕСЬ БАЛАНС КОШЕЛЬКА

with open('config.json') as f:
    config = json.load(f)
with open('private_keys.txt', 'r') as keys_file:
    private_keys = keys_file.read().splitlines()

w3 = Web3(Web3.HTTPProvider('https://ethereum.publicnode.com'))
contract = w3.eth.contract(address=config['ZoraBridge']['Address'], abi=config['ZoraBridge']['ABI'])


def deposit_to_zora(private_key, bridge_all, min_eth, max_eth):
    account = w3.eth.account.from_key(private_key)

    balance = w3.eth.get_balance(account.address)
    base_fee = w3.eth.fee_history(w3.eth.get_block_number(), 'latest')['baseFeePerGas'][-1]
    priority_max = w3.to_wei(1.5, 'gwei')

    test_tx = contract.functions.depositTransaction(account.address, 100000000000, 100000, False,
                                                    b'').build_transaction({
        'from': account.address,
        'value': 100000000000,
        'nonce': w3.eth.get_transaction_count(account.address)
    })

    test_tx.update({'maxFeePerGas': base_fee + priority_max})
    test_tx.update({'maxPriorityFeePerGas': priority_max})

    gas = w3.eth.estimate_gas(test_tx)
    gas_estimate = gas * (base_fee + priority_max)

    if bridge_all:
        if balance > gas_estimate:
            value_wei = round(balance - gas_estimate * 1.20)
            value = w3.from_wei(value_wei, 'ether')
        else:
            print(f"Insufficient balance to cover gas costs. Balance: {balance}, Gas Cost: {gas_estimate}")
            return 0
    else:
        value_wei = w3.to_wei(random.uniform(min_eth, max_eth), 'ether')
        if balance > gas_estimate + value_wei:
            value = w3.from_wei(value_wei, 'ether')
        else:
            print(f"Insufficient balance to cover gas costs. Balance: {balance}, Gas Cost: {gas_estimate}")
            return 0

    tx = contract.functions.depositTransaction(account.address, value_wei, 100000, False,
                                               b'').build_transaction({
        'from': account.address,
        'value': value_wei,
        'nonce': w3.eth.get_transaction_count(account.address)
    })

    tx.update({'maxFeePerGas': base_fee + priority_max})
    tx.update({'maxPriorityFeePerGas': priority_max})
    gas_limit = round(w3.eth.estimate_gas(tx) * 1.15)
    tx.update({'gas': gas_limit})

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)

    try:
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=666)
    except ValueError or Exception:
        print("Insufficient funds for transaction.")
        print("Or it may be any other shit, check manual")
        with open('failed_transactions.txt', 'a') as f:
            f.write(f'{account.address}, transaction failed due to error\n')
        return 0

    if tx_receipt['status'] == 1:
        print(f"Transaction out of ETH was successful, value = {value}")
        print(f"Wallet {account.address}")
        print(f"Txn hash: https://etherscan.io/tx/{tx_hash.hex()}")
        with open('successful_transactions.txt', 'a') as f:
            f.write(f'{account.address}, successful transaction, Txn hash: https://etherscan.io/tx/{tx_hash.hex()}\n')
        return 1
    elif tx_receipt['status'] == 0:
        print("Transaction was unsuccessful.")
        print(f"Wallet {account.address}")
        print(f"Txn hash: https://etherscan.io/tx/{tx_hash.hex()}")
        with open('failed_transactions.txt', 'a') as f:
            f.write(f'{account.address}, transaction failed, Txn hash: https://etherscan.io/tx/{tx_hash.hex()}\n')
        return 0


bridge_all = False
min_eth = 0
max_eth = 0
min_sec = 0
max_sec = 0
input_data = input("Bridge all ETH to Zora Network ?\n1 - Yes, 2 - No\n")
if input_data == "1":
    bridge_all = True
elif input_data == "2":
    bridge_all = False

if not bridge_all:
    print("Specify the range of the ETH amount you want to transfer across the bridge.")
    min_eth = float(input("min: "))
    max_eth = float(input("max: "))

print("Specify the delay time in seconds between the execution of accounts.")
min_sec = int(input("min: "))
max_sec = int(input("max: "))

random.shuffle(private_keys)
for key in private_keys:
    try:
        deposit_to_zora(key, bridge_all, min_eth, max_eth)
    except Exception as e:
        print(e)
        deposit_to_zora(key, bridge_all, min_eth, max_eth)
    time_to_sleep = random.randint(min_sec, max_sec)
    print(f"Sleep {time_to_sleep} sec.")
    time.sleep(time_to_sleep)



