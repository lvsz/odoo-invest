import os
from itertools import chain
from urllib.parse import urlencode

import requests

from odoo.fields import Date

# ALPHA AVANTAGE
API_AV = os.getenv('API_AV')
URL_AV = 'https://www.alphavantage.co/query?'
MIC2AV = {
    'XNYS': '',
    'XNAS': '',
    'XBRU': '.BRU',
    'XPAR': '.PAR',
    'XAMS': '.AMS',
    'XETR': '.DEX',
    'XLON': '.LON',
    'XTSE': '.TRT',
    'XTSX': '.TRV',
}


def av_get(security, function='TIME_SERIES_DAILY'):
    def mapvals(date, vals):
        return {
            k.split()[-1]: float(v) if k != 'date' else v
            for k, v in chain(vals.items(), iter([('date', date)]))
        }
    qs = urlencode({
        'function': function,
        'symbol': security.ticker + MIC2AV[security.exchange_code],
        'apikey': API_AV,
    })
    res = requests.get(URL_AV + qs)
    res.raise_for_status()
    values = res.json()
    values.pop('Meta Data')
    return {
        Date.from_string(date): mapvals(date, vals)
        for date, vals in next(iter(values.values())).items()
    }


# FINANCIAL MODELING PREP
API_FMP = os.getenv('API_FMP')
URL_FMP = 'https://financialmodelingprep.com/stable'
HEADER_FMP = {
    'apikey': API_FMP,
    'User-Agent': requests.utils.default_user_agent(),
}
MIC2FMP = {
    'XNYS': 'NYSE',
    'XNAS': 'NASDAQ',
    'XNCM': 'NASDAQ',
    'XETR': 'XETRA',
    'XLON': 'LSE',
    'XSWX': 'SIX',
    'XBRU': 'BRU',
    'XPAR': 'PAR',
    'XAMS': 'AMS',
    'XOSL': 'OSL',
}


def fmp_get(security, function='historical-price-eod/full'):
    keep = {'open', 'close', 'high', 'low', 'volume'}
    qs = urlencode({
        'symbol': security.ticker,
        'exchange': MIC2FMP[security.exchange_code],
    })
    res = requests.get(
        f'{URL_FMP}/{function}?{qs}',
        headers=HEADER_FMP,
    )
    res.raise_for_status()
    return {
        Date.from_string(vals['date']): {k: v for k, v in vals.items() if k in keep}
        for vals in res.json()
    }
