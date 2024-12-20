from web3 import Web3
import json, os, sys, time
from dotenv import load_dotenv

load_dotenv()
web3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

with open('./abi.json') as f:
    abi = json.load(f)

with open('./erc20.json') as f_erc:
    abi_erc = json.load(f_erc)

with open('./pair.json') as f_pair:
    pair_abi = json.load(f_pair)

os.system('cls' if os.name == 'nt' else 'clear')
if not web3.is_connected():
    print("Failed to Connect to Base")
    sys.exit()

print(f"Starting Auto Sell")
privatekey = os.getenv("PRIVATE_KEY")
addresss = web3.eth.account.from_key(privatekey).address
amount = web3.to_wei(float(os.getenv("AMOUNT")), 'ether')
cl = int(os.getenv("CUT_LOSS_PERCENT"))
tp = int(os.getenv("TAKE_PROFIT_PERCENT"))
amount_percentage = amount / 100
amount_cl = (amount_percentage * 95) - (amount_percentage * cl)
amount_tp = (amount_percentage * tp) + amount

contracts = web3.eth.contract(
    address='0xF66DeA7b3e897cD44A5a231c61B6B4423d613259',
    abi=abi
)

swapper = web3.eth.contract(
    address='0x08758354a72F2765FA8ba4CaC7c1dDdC88EDBdB6',
    abi=abi
)

def approve_tx(token_address_checksum):
    nonce = web3.eth.get_transaction_count(addresss)
    erc20 = web3.eth.contract(
        address=web3.to_checksum_address(token_address_checksum),
        abi=abi_erc
    )
    if erc20.functions.allowance(addresss, web3.to_checksum_address("0x08758354a72F2765FA8ba4CaC7c1dDdC88EDBdB6")).call() == 0:
        tx = {
        "to": web3.to_checksum_address(token_address_checksum),
        "gasPrice": int(web3.eth.gas_price *2),
        "nonce": nonce,
        "data": "0x095ea7b300000000000000000000000008758354a72f2765fa8ba4cac7c1dddc88edbdb6ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "chainId": 8453,
        "gas": 200000,
        }
        signed_txns = web3.eth.account.sign_transaction(tx, private_key=privatekey)
        tx_hash = w3.eth.send_raw_transaction(signed_txns.raw_transaction)
        print("Recipt Approve >> " + web3.to_hex(tx_hash) +"\nExecuted on block: " + str(web3.eth.get_block('latest')['number']))
        web3.eth.wait_for_transaction_receipt(tx_hash)
    else:
        print(f"Already Approved {token_address_checksum}")

def sell_tx(token_address_checksum):
    nonce = web3.eth.get_transaction_count(addresss)
    erc20 = web3.eth.contract(
        address=web3.to_checksum_address(token_address_checksum),
        abi=abi_erc
    )
    token_address = token_address_checksum.lower()
    balance = erc20.functions.balanceOf(addresss).call()
    tx = swapper.functions.mempoolSell(
        web3.to_checksum_address(token_address),
        balance
    ).build_transaction(
        {
            "from": web3.to_checksum_address(addresss),
            "gasPrice": int(web3.eth.gas_price * 4),
            "chainId": 8453,
            "gas": 400000,
            "nonce": nonce
        }
    )
    signed_txns = web3.eth.account.sign_transaction(tx, private_key=privatekey)
    tx_hash = w3.eth.send_raw_transaction(signed_txns.raw_transaction)
    print("Recipt Swap >> " + web3.to_hex(tx_hash) +"\nExecuted on block: " + str(web3.eth.get_block('latest')['number']))
    web3.eth.wait_for_transaction_receipt(tx_hash)

def print_line():
    width = os.get_terminal_size().columns
    print("=" * width) 

def all_tx(token_address_checksum):
    contracts_pair = web3.eth.contract(
        address=web3.to_checksum_address(contracts.functions.tokenInfo(web3.to_checksum_address(token_address_checksum)).call()[2]),
        abi=pair_abi
    )
    token_sc = web3.eth.contract(
        address=web3.to_checksum_address(token_address_checksum),
        abi=abi_erc
    )
    print(f"Ticker: {token_sc.functions.name().call()}\nContract Address: {token_address_checksum}")
    approve_tx(token_address_checksum)
    ahaaaa, lel = contracts_pair.functions.getReserves().call()
    balance = token_sc.functions.balanceOf(addresss).call()
    print(f"Token Balance: {str(web3.from_wei(balance, 'ether'))}")
    time.sleep(1)
    prices = lel / ahaaaa * balance
    timeout = 0
    while True:
        time.sleep(0.1)
        ahaaaa, lel = contracts_pair.functions.getReserves().call()
        prices = lel / ahaaaa * balance
        if prices <= int(amount_cl):
            print("Stop Loss")
            break
        if prices >= int(amount_tp):
            print("Take Profit")
            break
        print(f"Estimated Virtual : {str(web3.from_wei(prices, 'ether'))}")
        timeout += 1
        if timeout >= int(os.getenv("TIMEOUT")):  
            print("Timeout reached, selling...")
            break
    sell_tx(token_address_checksum)
    print_line()


if __name__ == "__main__":
    while True:
        approve_tx("0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b")
        token_address = input("Input Token Address: ")
        all_tx(token_address)