import pandas as pd
import pandas_ta as ta
import requests
import json
from SmartApi import SmartConnect
from datetime import datetime, date, timedelta
import creds as l
import math, time, os
from logzero import logger
from retrying import retry
import pyotp
import numpy as np

angelObj = None

#smartapi.angelbroking.com/docs/Historical
AB_15MIN = "FIFTEEN_MINUTE"
AB_5MIN = "FIVE_MINUTE"
AB_DAY = "ONE_DAY"

@retry(stop_max_attempt_number=3)
def initAngel():
    print("Initializing Angel API...")
    try:
        global angelObj
        angelObj = SmartConnect(api_key=l.api_key)

        totp = pyotp.TOTP(l.token).now()
        data = angelObj.generateSession(l.username, l.password, totp)

        if data['status']:
            print("Session generated successfully.")
            refreshtoken = data['data']['refreshToken']
            feedtoken = angelObj.getfeedToken()
            userprofile = angelObj.getProfile(refreshtoken)
            print(userprofile)
            return angelObj
        else:
            print("Failed to generate session:", data['message'])
            return None

    except Exception as e:
        print("Error in initialization:", e)
        time.sleep(30)
        return None

def getTokens():
    url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
    d = requests.get(url).json()
    token_df = pd.DataFrame.from_dict(d)
    token_df['expiry'] = pd.to_datetime(token_df['expiry']).apply(lambda x: x.date())
    token_df = token_df.astype({'strike': float})
    return(token_df)

def getTokenInfo (symbol,exch_seg ='NSE',instrumenttype='OPTIDX',strike_price = '',pe_ce = 'PE',expiry_day = None):
    df = getTokens()
    print("inside getTokenInfo", df)
    strike_price = strike_price*100
    if exch_seg == 'NSE':
        eq_df = df[(df['exch_seg'] == 'NSE') ]
        return eq_df[eq_df['symbol'] == symbol]
    elif exch_seg == 'NFO' and ((instrumenttype == 'FUTSTK') or (instrumenttype == 'FUTIDX')):
        return df[(df['exch_seg'] == 'NFO') & (df['instrumenttype'] == instrumenttype) & (df['name'] == symbol)].sort_values(by=['expiry'])
    elif exch_seg == 'NFO' and (instrumenttype == 'OPTSTK' or instrumenttype == 'OPTIDX'):
        return df[(df['exch_seg'] == 'NFO') & (df['expiry']==expiry_day) &  (df['instrumenttype'] == instrumenttype) & (df['name'] == symbol) & (df['strike'] == strike_price) & (df['symbol'].str.endswith(pe_ce))].sort_values(by=['expiry'])
    #expiry_day = date(2022,7,28)

def getHistoricalAPI(symbol, token, interval= 'FIVE_MINUTE'):
    to_date = datetime.now()
    from_date = to_date - timedelta(days=30)
    from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
    to_date_format = to_date.strftime("%Y-%m-%d %H:%M")
    try:
        historicParam = {
            "exchange": "NSE",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "interval": interval,
            "fromdate": from_date_format,
            "todate": to_date_format
        }
        ohlc_data = angelObj.getCandleData(historicParam)['data']

        print("OHLC Data fetched successfully.")
        history = pd.DataFrame(ohlc_data)

        history = history.rename(
            columns={0: "Datetime", 1: "Open", 2: "High", 3: "Low", 4: "Close", 5: "Volume"}
        )
        history['Datetime'] = pd.to_datetime(history['Datetime'])
        history = history.set_index('Datetime')
        return history
    except Exception as e:
        print("Error fetching OHLC data:", e)
        return None

def calculate_supertrend(ohlc_data, period=7, multiplier=3):

    """Calculate Supertrend and return the last close and its direction."""
    supertrend = ta.supertrend(ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'], period, multiplier)
    
    # Add Supertrend to the DataFrame
    ohlc_data['Supertrend'] = supertrend['SUPERT_7_3.0']
    
    # Determine Supertrend direction
    ohlc_data['Supertrend_Direction'] = np.where(ohlc_data['Supertrend'] > ohlc_data['Close'], 'Downtrend', 'Uptrend')
    
    # Get the last row
    last_row = ohlc_data.iloc[-1]
    
    return {
        'Last_Close': last_row['Close'],
        'Supertrend_Value': last_row['Supertrend'],
        'Supertrend_Direction': last_row['Supertrend_Direction']
    }

def callAngelAPI():
    angelObj = initAngel()
    return angelObj

def callAngelInd(angelObj,symbolwo_suffix):
    print ("symbol: ",symbolwo_suffix)
    if (symbolwo_suffix == 'NIFTY') or (symbolwo_suffix == 'BANKNIFTY'):
        symbol = symbolwo_suffix
    else:
        symbol = symbolwo_suffix + "-EQ"
    
    print ("symbol: ",symbol)

    if angelObj:
        # Define parameters for OHLC data
        #symbol = "TCS-EQ"  # Change to your desired symbol
        tokenInfo = getTokenInfo(symbol,'NSE')
        print("tokeinfo returned: ", tokenInfo)
        #print("token value", tokenInfo['token'])
        spot_token = tokenInfo.iloc[0]['token']
        print("spot token value: ",spot_token)
        #token = "3045"
        interval = AB_15MIN  # Define the interval
        
        # Fetch OHLC data
        ohlc_data = getHistoricalAPI(symbol, spot_token, interval)
        
        if ohlc_data is not None:
            # Calculate Supertrend
            result = calculate_supertrend(ohlc_data)

            # Print the results
            print(f"Last Close: {result['Last_Close']}")
            print(f"Supertrend Value: {result['Supertrend_Value']}")
            print(f"Supertrend Direction: {result['Supertrend_Direction']}")
        else:
            print("Failed to retrieve OHLC data.")
    
    return  {
            'Supertrend_Value': result['Supertrend_Value'],
            'Supertrend_Direction': result['Supertrend_Direction']
    }

