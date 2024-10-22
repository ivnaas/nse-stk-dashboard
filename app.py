import dash
from dash import html, dcc
import pandas as pd
from stock_data import get_stock_data
import time
import os
import logging
from datetime import datetime
import threading
import pytz
from angel import *

app = dash.Dash(__name__)
portfolio_stocks = ['SIEMENS']  # Default portfolio stock
watchlist_stocks = []  # Initialize watchlist

# Initialize a log list to store log entries
log_entries = []
global anObj
anObj = callAngelAPI()

# Function to log stock data every 5 minutes
def log_stock_data():
    while True:
        time.sleep(30)  # Sleep for 30 seconds
        for stock in portfolio_stocks:
            try:
                data = get_stock_data(stock)
                closeprice = data.indicators["close"]
                rsi15min = data.indicators["RSI"]

                st = callAngelInd(anObj, stock)
                strend_value = round(st['Supertrend_Value'], 2)
                strend_direction = st['Supertrend_Direction']

                # Create log entry with IST timestamp
                ist_timezone = pytz.timezone('Asia/Kolkata')
                timestamp = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')

                log_entry = f"{timestamp} - Stock Symbol: {stock}, Last Close Price: {str(closeprice)}, RSI_15min: {str(round(rsi15min, 2))}, STrend Value: {str(strend_value)}, STrend Direction: {strend_direction}"
                log_entries.append(log_entry)
                print(log_entry)
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
                dcc.Textarea(id='watchlist-input', value='ABB,BAJAJFIN', style={'width': '100%', 'height': 100}),
                html.Button('Update Watchlist', id='watchlist-button', n_clicks=0),
                html.Div(id='watchlist-output'),
            ], style={'width': '60%', 'display': 'inline-block'}),
        ])
    ])
])

@app.callback(
    [dash.dependencies.Output('output-container', 'children'),
     dash.dependencies.Output('log-container', 'children')],
    [dash.dependencies.Input('submit-button', 'n_clicks'),
     dash.dependencies.Input('interval-component', 'n_intervals'),
     dash.dependencies.Input('portfolio-button', 'n_clicks'),
     dash.dependencies.Input('watchlist-button', 'n_clicks')],
    [dash.dependencies.State('stock-symbol', 'value'),
     dash.dependencies.State('portfolio-input', 'value'),
     dash.dependencies.State('watchlist-input', 'value')]
)
def update_output(n_clicks, n_intervals, portfolio_clicks, watchlist_clicks, value, portfolio_input, watchlist_input):
    global portfolio_stocks, watchlist_stocks
    
    # Update portfolio and watchlist
    if portfolio_clicks > 0:
        portfolio_stocks = [stock.strip() for stock in portfolio_input.split(',') if stock.strip()]
    
    if watchlist_clicks > 0:
        watchlist_stocks = [stock.strip() for stock in watchlist_input.split(',') if stock.strip()]
    
    output = []
    log_output = [html.Li(entry) for entry in reversed(log_entries)]
    
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

    return output, log_output

if __name__ == '__main__':
    app.run_server(debug=True)
