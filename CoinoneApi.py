'''
example usage:
a = api.get_price_by_currency('AI16Z') // returns the price of AI16Z
b = api.get_balances(['KRW', 'BTC', 'AI16Z']) // returns a list of balances
d = api.get_balance_by_currency('BTC') // returns a single balance
e = api.get_nonzero_balances() // returns a list of non-zero balances
f = api.get_report(['KRW', 'BTC', 'AI16Z']) // returns a DataFrame with the report

.env 파일 생성해서 아래와 같이 키 정보 등록해놔야 함
COINONE_ACCESS_KEY = "111111111111"
COINONE_SECRET_KEY = "1111111111111"

'''

import os
import hmac
import json
import uuid
import base64
import hashlib
import requests
import pprint as pp
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

class CoinoneAPI:
    BASE_URL = "https://api.coinone.co.kr/"

    def __init__(self, access_token, secret_key):
        self.access_token = access_token
        self.secret_key = bytes(secret_key, 'utf-8')

    def _get_encoded_payload(self, payload):
        payload['nonce'] = str(uuid.uuid4())
        encoded_json = base64.b64encode(json.dumps(payload).encode('utf-8'))
        return encoded_json

    def _get_signature(self, encoded_payload):
        signature = hmac.new(self.secret_key, encoded_payload, hashlib.sha512)
        return signature.hexdigest()

    def _post_request(self, endpoint, payload):
        url = f"{self.BASE_URL}{endpoint}"
        encoded_payload = self._get_encoded_payload(payload)
        headers = {
            'Content-type': 'application/json',
            'X-COINONE-PAYLOAD': encoded_payload,
            'X-COINONE-SIGNATURE': self._get_signature(encoded_payload),
        }
        response = requests.post(url, headers=headers)
        return response.json()

    def get_balances(self, currencies):
        response = self._post_request("/v2.1/account/balance", {
            'access_token': self.access_token,
            'currencies': currencies
        })
        
        if response.get("result") != "success":
            return []
        
        return [
            {
                "currency": balance["currency"],
                "balance": float(balance["available"]) + float(balance["limit"])
            }
            for balance in response.get("balances", [])
        ]
    
    def get_balance_by_currency(self, currency):
        response = self._post_request("/v2.1/account/balance", {
            'access_token': self.access_token,
            'currencies': [currency]
        })
        
        if response.get("result") != "success":
            return None
        
        balance_data = next((balance for balance in response.get("balances", []) if balance["currency"] == currency), None)
        if balance_data:
            return {
                "currency": balance_data["currency"],
                "balance": float(balance_data["available"]) + float(balance_data["limit"])
            }
        return None
    
    def get_nonzero_balances(self):
        response = self._post_request("/v2.1/account/balance/all", {
            'access_token': self.access_token
        })
        
        if response.get("result") != "success":
            return []
        
        return [
            {
                "currency": balance["currency"],
                "balance": float(balance["available"]) + float(balance["limit"])
            }
            for balance in response.get("balances", [])
            if float(balance["available"]) + float(balance["limit"]) > 0
        ]

    def get_price_by_currency(self, coin: str):
        if coin.lower() == 'krw':
            return 1.0

        def _make_request(url: str):
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                return f"Error: {str(e)}"

        url = f'https://api.coinone.co.kr/ticker/?currency={coin}'
        data = _make_request(url)

        if data.get("errorCode") == "0":
            try:
                return float(data.get("last", 0))
            except (ValueError, TypeError):
                return f"Error: Invalid Coinone price data.."
        return f"Error: Invalid Coinone price data"

    def get_report(self, currencies):
        # Get balances for the requested currencies
        balances = self.get_balances(currencies)
        report_data = []

        # Get price for each currency and calculate the total value
        for balance in balances:
            currency = balance["currency"]
            balance_amount = balance["balance"]
            price = self.get_price_by_currency(currency)

            # Skip currencies with invalid price data
            if isinstance(price, str) and "Error" in price:
                continue

            total_value = price * balance_amount
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Append the data for the report
            report_data.append({
                "currency": currency,
                "balance": balance_amount,
                "price": price,
                "total": total_value,
                "date": current_time
            })

        # Create DataFrame and return
        df = pd.DataFrame(report_data)
        return df
    
load_dotenv()

# Usage example
if __name__ == "__main__":

    ACCESS_KEY = os.getenv("COINONE_ACCESS_KEY")
    SECRET_KEY = os.getenv("COINONE_SECRET_KEY")

    api = CoinoneAPI(ACCESS_KEY, SECRET_KEY)

    coin_price = api.get_price_by_currency('AI16Z')
    pp.pprint(coin_price)
    
    btc_balance = api.get_balance_by_currency('AI16Z')
    pp.pprint(btc_balance)
    
    balances = api.get_balances(['KRW', 'BTC', 'SOL', 'ETH', 'USDC', 'AI16Z'])
    pp.pprint(balances)

    nonzero_balances = api.get_nonzero_balances()
    pp.pprint(nonzero_balances)

    nonezero_currencies = [item['currency'] for item in nonzero_balances]
    print("잔액있는 코인들: ",nonezero_currencies)

    report_df = api.get_report(nonezero_currencies)
    print(report_df)


# end of code
