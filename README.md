CoinoneApi

example usage:

a = api.get_price_by_currency('AI16Z') // returns the price of AI16Z

b = api.get_balances(['KRW', 'BTC', 'AI16Z']) // returns a list of balances

d = api.get_balance_by_currency('BTC') // returns a single balance

e = api.get_nonzero_balances() // returns a list of non-zero balances

f = api.get_report(['KRW', 'BTC', 'AI16Z']) // returns a DataFrame with the report


