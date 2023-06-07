import requests
import pandas as pd
import re
import numpy as np
from datetime import datetime
import json
import yfinance as yf

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

from threading import Thread


def get_etf_data(ticker):
    url = f"https://www.hashdex.com.br/pt-BR/products/{ticker}/performance"

    r = requests.get(url)
    tokens = re.findall("\d+,\d+|[\d+\.]+,\d+|\d{2}\/\d{2}\/\d{4}|-\d+,\d+|-[\d+\.]+,\d+", r.text)

    for token, index in zip(tokens, range(len(tokens))):
        if "/" in token:
            first_data_index = index
            break

    tokens = tokens[first_data_index:]
    columns_name = ["date", "aum", "price", "close", "index", "premium"]
    tokens = [i.replace(".", "").replace(",", ".") for i in tokens]

    data = [tokens[i:i+len(columns_name)] for i in range(0, len(tokens) - 1, len(columns_name))]
    df = pd.DataFrame(data, columns=columns_name)

    
    for i in ["aum", "price", "close", "index", "premium"]:
        df[i] = df[i].apply(lambda x: float(x))

    df["date"] = df["date"].apply(lambda x: datetime.strptime(x, "%d/%m/%Y"))
    df = df.sort_values(by=["date"], ascending=False)
    df["ratio"] = df["index"] / df["price"]
    df["diff_premium"] = df["premium"] - df["premium"].shift(1)
    df["diff_aum"] = df["aum"].pct_change()
    df["24H_diff"] = df["close"].pct_change()

    d = {
        "name": ticker,
        "avg_ratio": np.mean(df["ratio"]),
        "avg_premium": np.mean(df["premium"]),
        "avg_diff_premium": np.mean(df["diff_premium"]),
        "avg_diff_aum": np.mean(df["diff_aum"])
    }
    df["name"] = ticker
    return df



def generate_data():
    response = {}
    
    def get_data(ticker):
        
        if ticker == "WEB311":
            url = "https://www.cfbenchmarks.com/data/indices/CFSPMWLDN_RTI_TR"
            text = requests.get(url).text
            return float(re.search('class="jsx-4214436125 stats"><span class="jsx-4214436125 price xxl">(.*)<span class="jsx-4214436125 xl', text).group(1).replace(",", ""))
            
        # hash11
        elif ticker == "HASH11":
            url = "https://www.cfbenchmarks.com/data/indices/NCI"
            text = requests.get(url).text
            return float(re.search('class="jsx-4214436125 stats"><span class="jsx-4214436125 price xxl">(.*)<span class="jsx-4214436125 xl', text).group(1).replace(",", ""))
        
        # bith11
        elif ticker == "BITH11":
            url = "https://www.cfbenchmarks.com/data/indices/NQBTC"
            text = requests.get(url).text
            return float(re.search('-->(.*)</div><div class="jsx-3311999459 change"><img src="data:image', text).group(1).split("<")[0].replace(",", ""))

        # ethe11
        elif ticker == "ETHE11":
            url = "https://www.cfbenchmarks.com/data/indices/NQETH"
            text = requests.get(url).text
            return float(re.search(r'Ether<\/div><div class="jsx-3311999459 price large">\$<!-- -->(.*)</div><div class="jsx-3311999459 change"><img src="data:image', text).group(1).split("<")[0].replace(",", ""))

        elif ticker == "usd_brl":
            stock = yf.Ticker("USDBRL=X")
            info = stock.info
            usd_brl = (info["bid"]+info["ask"]) / 2
            return usd_brl
        else:
            return None
        

    # BRL Index / fair
    ratios = {
        'BITH11': 4258.734636634171,
        'ETHE11': 341.19311084492495,
        'HASH11': 346.95267778634013,
        'WEB311': 64.53878064106745
    }
    
    assets = ["WEB311", "HASH11", "ETHE11", "BITH11"]
    
    response = {}
    threads = []
    for ticker in assets + ["usd_brl"]:
        thread = Thread(target=lambda: response.update({ticker: get_data(ticker)}))
        thread.start()
        threads.append(thread)
        
    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    usd_brl = response['usd_brl']

    res = {}
    for k in assets:
        res[k] = round(response[k] * usd_brl / ratios[k], 4)
        
    assets.remove("WEB311")
    pairs = [(a, b) for idx, a in enumerate(assets) for b in assets[idx + 1:]]
    for pair in pairs:
        res[f"{pair[0]}_{pair[1]}"] = round(res[pair[0]] / res[pair[1]], 4)
    
    # traspose dataframe
    df = pd.DataFrame([res])
    columns = df.columns
    df = df.T
    df["ticker"] = columns
    df.columns = ["value", "ticker"]
    df = df[["ticker", "value"]]
    return df.to_dict('records')


def calculculate_ratios():
    frames = [
        get_etf_data("BITH11"),
        get_etf_data("ETHE11"), 
        get_etf_data("HASH11"),
        get_etf_data("WEB311")
    ]
    df = pd.concat(frames)
    
    ratios = df[["name", "ratio", "premium"]].groupby(by="name").mean().to_dict()
    with open("params.json", "w") as file:
        json.dump(ratios, file)
    

import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.dataframe(generate_data())

st_autorefresh(interval=60*1000, limit=100000000, key="fizzbuzzcounter")


