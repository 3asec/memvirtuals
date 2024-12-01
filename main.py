from web3 import Web3
import json, os, sys, requests, time
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
print(f"Starting Sniper\nEnhanced Version")
privatekey = os.getenv("PRIVATE_KEY")
address = web3.eth.account.from_key(privatekey).address
amount = web3.to_wei(float(input("Enter Amount Virtual to Snipe: ")), 'ether')
dev_opt = input("Dev Option? (y/n): ").lower()
if dev_opt == "y":
    minbal = float(input("Min Dev Balance (USD): "))
    dev_held = float(input("Max Dev Hold Percent: "))
    skip_0_percent = input("Skip Buy If Dev Hold 0%? (y/n): ").lower()
else:
    dev_held = 100
    minbal = 0

auto_sell = input("Auto Sell? (y/n): ").lower()
if auto_sell == "y":
    cl = int(input("Cut Loss Percent: "))
    tp = int(input("Take Profit Percent: "))
    amount_percentage = amount / 100
    amount_cl = (amount_percentage * 98) - (amount_percentage * cl)
    amount_tp = (amount_percentage * tp) + amount
else:
    amount_cl = 0
    amount_tp = 0

print(f"Mempool Started From Block: {web3.eth.get_block('latest')['number']}")

contracts = web3.eth.contract(
    address='0xF66DeA7b3e897cD44A5a231c61B6B4423d613259',
    abi=abi
)

swapper = web3.eth.contract(
    address='0x08758354a72F2765FA8ba4CaC7c1dDdC88EDBdB6',
    abi=abi
)

def approve_tx(token_address_checksum):
    nonce = web3.eth.get_transaction_count(address)
    erc20 = web3.eth.contract(
        address=web3.to_checksum_address(token_address_checksum),
        abi=abi_erc
    )
    if erc20.functions.allowance(address, web3.to_checksum_address("0x08758354a72F2765FA8ba4CaC7c1dDdC88EDBdB6")).call() == 0:
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

def buy_tx(token_address_checksum):
    nonce = web3.eth.get_transaction_count(address)
    token_address = token_address_checksum.lower()
    tx = swapper.functions.mempoolBuy(
        web3.to_checksum_address(token_address),
        amount
    ).build_transaction(
        {
            "from": web3.to_checksum_address(address),
            "gasPrice": int(web3.eth.gas_price * 2),
            "chainId": 8453,
            "gas": 400000,
            "nonce": nonce
        }
    )
    signed_txns = web3.eth.account.sign_transaction(tx, private_key=privatekey)
    tx_hash = w3.eth.send_raw_transaction(signed_txns.raw_transaction)
    print("Recipt Swap >> " + web3.to_hex(tx_hash) +"\nExecuted on block: " + str(web3.eth.get_block('latest')['number']))
    web3.eth.wait_for_transaction_receipt(tx_hash)

def sell_tx(token_address_checksum):
    nonce = web3.eth.get_transaction_count(address)
    erc20 = web3.eth.contract(
        address=web3.to_checksum_address(token_address_checksum),
        abi=abi_erc
    )
    token_address = token_address_checksum.lower()
    balance = erc20.functions.balanceOf(address).call()
    tx = swapper.functions.mempoolSell(
        web3.to_checksum_address(token_address),
        balance
    ).build_transaction(
        {
            "from": web3.to_checksum_address(address),
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

def all_tx(token_address_checksum, dev, pair):
    contracts_pair = web3.eth.contract(
        address=web3.to_checksum_address(pair),
        abi=pair_abi
    )
    token_sc = web3.eth.contract(
        address=web3.to_checksum_address(token_address_checksum),
        abi=abi_erc
    )
    dev_balance = token_sc.functions.balanceOf(dev).call()
    total_supply = token_sc.functions.totalSupply().call()
    percentage_held = (dev_balance / total_supply) * 100
    print(f"Ticker: {token_sc.functions.name().call()}\nContract Address: {token_address_checksum}\nDev Hold: {percentage_held:.2f}%")
    if skip_0_percent == "y":
        if percentage_held == 0:
            print_line()
            return
    data = requests.get(f"https://relayer.host/value/{dev}").json()
    if data["usd"]:
        print(f"Dev Balance: ${data['usd']:.2f}")
    if dev_opt == "y":
        if(float(data["usd"]) <= float(minbal)):
            print("Dev Balance Too Low")
            print_line()
            return
    print(f"Token {token_address_checksum}\nPreparing to Buy")
    virtual_contract = web3.eth.contract(
        address=web3.to_checksum_address("0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"),
        abi=abi_erc
    )
    balance = virtual_contract.functions.balanceOf(address).call()
    if balance >= amount:
        if float(percentage_held) >= float(dev_held):
            print("Dev Hold Too High")
            print_line()
            return
        
        buy_tx(token_address_checksum)
    else:
        print("Not Enough Virtual Balance")
        sys.exit()
            
    if(auto_sell == "y"):
        approve_tx(token_address_checksum)
        ahaaaa, lel = contracts_pair.functions.getReserves().call()
        erc20 = web3.eth.contract(
            address=web3.to_checksum_address(token_address_checksum),
            abi=abi_erc
        )
        balance = erc20.functions.balanceOf(address).call()
        print("Waiting Balance")
        time.sleep(0.1)
        balance = erc20.functions.balanceOf(address).call()
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
            if timeout >= 300:  
                print("Timeout reached, selling...")
                break
        sell_tx(token_address_checksum)
    print_line()


def handle_event(event):
    try:
        hashnya = event["transactionHash"]
        token_address = event['args']['token']
        pair = event['args']['pair']
        receipt = web3.eth.get_transaction_receipt(hashnya)
        all_tx(token_address, receipt["from"], pair)
    except Exception as error:
        print("Error:", error)

def main():
    event_filter = contracts.events.Launched.create_filter(from_block='latest')
    while True:
        try:
            for event in event_filter.get_new_entries():
                handle_event(event)
        except Exception as e:
            print("Error fetching new entries:", e)

if __name__ == "__main__":
    approve_tx("0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b")
    main()
