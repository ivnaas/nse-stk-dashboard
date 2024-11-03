import dash
from dash import html, dcc, dash_table
import pandas as pd
from stock_data import get_stock_data
import time
import os
import logging
from datetime import datetime
import threading
import pytz
from angel import *
from notif import send_notif

app = dash.Dash(__name__)
portfolio_stocks = ['SIEMENS']  # Default portfolio stock
watchlist_stocks = []  # Initialize watchlist

# Initialize a log list to store log entries
log_entries = []
alerts = [] # List to store alerts

global anObj
anObj = callAngelAPI()

# Function to log stock data every 30 seconds
def log_stock_data():
    while True:
        time.sleep(30)  # Sleep for 30 seconds
        for stock in portfolio_stocks:
            try:
                data = get_stock_data(stock)
                closeprice = data.indicators["close"]
                rsi15min = round(data.indicators["RSI"],2)

                st = callAngelInd(anObj, stock)
                strend_value = round(st['Supertrend_Value'], 2)
                strend_direction = st['Supertrend_Direction']
                strend_bone_direction = st['Strend_bone_Direction']
                    
                # Create log entry with IST timestamp
                ist_timezone = pytz.timezone('Asia/Kolkata')
                timestamp = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')

                log_entry = f"{timestamp} - Stock Symbol: {stock}, Last Close Price: {str(closeprice)}, RSI_15min: {str(round(rsi15min, 2))}, STrend Value: {str(strend_value)}, STrend Direction: {strend_direction}"
                log_entries.append(log_entry)
                print(log_entry)
            except Exception as e:
                print(f"Error fetching data for {stock}: {e}")

        for stock in watchlist_stocks:
            try:
                data = get_stock_data(stock)
                closeprice = data.indicators["close"]
                rsi15min = round(data.indicators["RSI"],2)

                st = callAngelInd(anObj, stock)
                strend_value = round(st['Supertrend_Value'], 2)
                strend_direction = st['Supertrend_Direction']
                strend_bone_direction = st['Strend_bone_Direction']

                # Alert if RSI < 20 or RSI > 75
                if (rsi15min > 75 or rsi15min < 20): #>75 <20
                    send_notif(stock,"RSI",rsi15min,closeprice)

                # Alert if Super Trend direction change
                if (strend_direction=='Uptrend' and strend_bone_direction=='Downtrend'):
                    send_notif(stock,"SuperTrend Bullish",strend_value,closeprice)

                if (strend_direction=='Downtrend' and strend_bone_direction=='Uptrend'):
                    send_notif(stock,"SuperTrend Bearish",strend_value,closeprice)
                    
            except Exception as e:
                print(f"Error fetching data for {stock}: {e}")

# Start the logging thread
logging_thread = threading.Thread(target=log_stock_data, daemon=True)
logging_thread.start()

app.layout = html.Div(children=[
    dcc.Tabs([
        dcc.Tab(label='Portfolio', children=[
            html.Div(children=[
                html.H1(children='Stock Tracker'),
                dcc.Input(id='stock-symbol', value='SIEMENS', type='text'),
                html.Button('Submit', id='submit-button', n_clicks=0),
                html.Div(id='output-container'),
                html.Div(id='day-high-low'),
                dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0)  # Interval set to 30 seconds
            ], style={'width': '60%', 'display': 'inline-block'}),
            
            html.Div(children=[
                html.H2('Portfolio'),
                dcc.Textarea(id='portfolio-input', value='SIEMENS,TCS', style={'width': '100%', 'height': 100}),
                html.Button('Update Portfolio', id='portfolio-button', n_clicks=0),
            ], style={'width': '35%', 'display': 'inline-block', 'float': 'right'}),
            
            html.Div(children=[
                html.H2('Logs'),
                html.Ul(id='log-container'),
            ], style={'width': '60%', 'display': 'inline-block', 'float': 'left'})
        ]),
        
        dcc.Tab(label='Watchlist', children=[
            html.Div(children=[
                html.H2('Watchlist'),
                dcc.Textarea(id='watchlist-input', value='ABB,BAJFINANCE', style={'width': '100%', 'height': 100}),
                html.Button('Update Watchlist', id='watchlist-button', n_clicks=0),
                
                # Table for displaying watchlist data
                dash_table.DataTable(
                    id='watchlist-table',
                    columns=[
                        {'name': 'Stock Name', 'id': 'stock_name'},
                        {'name': 'Close Price', 'id': 'close_price'},
                        {'name': 'RSI Value', 'id': 'rsi_value'},
                        {'name': 'SuperTrend', 'id': 'supertrend'},
                    ],
                    data=[],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    page_size=3  # Set page size to 3 for a 3-row table
                ),
            ], style={'width': '60%', 'display': 'inline-block'}),

            html.Div(children=[
                
                # Table for displaying watchlist data
                dash_table.DataTable(
                    id='index-table',
                    columns=[
                        {'name': 'Index Name', 'id': 'index_name'},
                        {'name': 'Close Price', 'id': 'close_price'},
                        {'name': 'RSI Value', 'id': 'rsi_value'},
                        {'name': 'SuperTrend', 'id': 'supertrend'},
                    ],
                    data=[],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    page_size=3  # Set page size to 3 for a 3-row table
                ),
            ], style={'width': '60%', 'display': 'inline-block'}),

            html.Div(children=[
                html.H2('Alerts'),
                html.Ul(id='alerts-container'),
            ], style={'width': '60%', 'display': 'inline-block', 'float': 'left'})

        ])
    ])
])

@app.callback(
    [dash.dependencies.Output('output-container', 'children'),
     dash.dependencies.Output('log-container', 'children'),
     dash.dependencies.Output('watchlist-table', 'data'),
     dash.dependencies.Output('index-table', 'data'),
     dash.dependencies.Output('alerts-container', 'children'),
     ],
    [dash.dependencies.Input('submit-button', 'n_clicks'),
     dash.dependencies.Input('interval-component', 'n_intervals'),
     dash.dependencies.Input('portfolio-button', 'n_clicks'),
     dash.dependencies.Input('watchlist-button', 'n_clicks')],
    [dash.dependencies.State('stock-symbol', 'value'),
     dash.dependencies.State('portfolio-input', 'value'),
     dash.dependencies.State('watchlist-input', 'value')]
)
def update_output(n_clicks, n_intervals, portfolio_clicks, watchlist_clicks, value, portfolio_input, watchlist_input):
    global portfolio_stocks, watchlist_stocks,alerts
    
    # Update portfolio and watchlist
    if portfolio_clicks > 0:
        portfolio_stocks = [stock.strip() for stock in portfolio_input.split(',') if stock.strip()]
    
    if watchlist_clicks > 0:
        watchlist_stocks = [stock.strip() for stock in watchlist_input.split(',') if stock.strip()]
    
    output = []
    log_output = [html.Li(entry) for entry in reversed(log_entries)]
    
    # Update watchlist data
    watchlist_data = []
    for stock in watchlist_stocks:
        try:
            data = get_stock_data(stock)
            closeprice = data.indicators["close"]
            rsi15min = data.indicators["RSI"]
            st = callAngelInd(anObj, stock)
            strend_value = round(st['Supertrend_Value'], 2)
            strend_bone_direction = st['Strend_bone_Direction']
            
            # Create log entry with IST timestamp
            ist_timezone = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')

            # Alert if RSI < 15 or RSI > 75
            if (rsi15min < 20): #<20
                alerts.append(f"{timestamp} -Alert: {stock} RSI is below Threshold. RSI-Value: {rsi15min}. Closeprice: {closeprice}")

            if (rsi15min > 75 ): #>75
                alerts.append(f"{timestamp} -Alert: {stock} RSI is above Threshold. RSI-Value: {rsi15min}. Closeprice: {closeprice}")

            # Alert if Super Trend direction change
            if (strend_direction=='Uptrend' and strend_bone_direction=='Downtrend'):
                alerts.append(f"{timestamp} -Alert: {stock} SuperTrend is Bullish. SuperTrend-Value: {strend_value}. Closeprice: {closeprice}")


            if (strend_direction=='Downtrend' and strend_bone_direction=='Uptrend'):
                alerts.append(f"{timestamp} -Alert: {stock} SuperTrend is Bearish. SuperTrend-Value: {strend_value}. Closeprice: {closeprice}")


            watchlist_data.append({
                'stock_name': stock,
                'close_price': closeprice,
                'rsi_value': round(rsi15min, 2),
                'supertrend': strend_value
            })
        except Exception as e:
            print(f"Error fetching data for watchlist stock {stock}: {e}")

    #prepare alerts for display
    alert_output = [html.Div(alert) for alert in alerts]

    # Update index data
    indexlist_data = []
    index_list = ['NIFTY','BANKNIFTY']
    for index in index_list:
        try:
            data = get_stock_data(index)
            closeprice = data.indicators["close"]
            rsi15min = data.indicators["RSI"]
            #st = callAngelInd(anObj, index)
            #strend_value = round(st['Supertrend_Value'], 2)
            strend_value = 0
            indexlist_data.append({
                'index_name': index,
                'close_price': closeprice,
                'rsi_value': round(rsi15min, 2),
                'supertrend': strend_value
            })
        except Exception as e:
            print(f"Error fetching data for index list {index}: {e}")

    # Update based on the button click for stock data
    if n_clicks > 0:
        try:
            data = get_stock_data(value)
            rsi15min = data.indicators["RSI"]
            closeprice = data.indicators["close"]

            st = callAngelInd(anObj, value)
            strend_value = st['Supertrend_Value']
            strend_direction = st['Supertrend_Direction']

            output = [
                html.Li(f"Stock Symbol: {value}"),
                html.Li(f"RSI_15min: {str(round(rsi15min, 2))}"),
                html.Li(f"Last Close Price: {str(closeprice)}"),
                html.Li(f"SuperTrend Value: {str(round(strend_value, 2))}"),
                html.Li(f"SuperTrend Direction: {strend_direction}")
            ]
        except Exception as e:
            output.append(f'Error fetching data for {value}: {e}')

    return output, log_output, watchlist_data, indexlist_data,alert_output

if __name__ == '__main__':
    #send_notif('ABB',"RSI")
    app.run_server(debug=True)
