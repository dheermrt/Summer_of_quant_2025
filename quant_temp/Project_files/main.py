import pandas as pd
import numpy as np
import talib as tb
import pandas_ta as ta
from backtester import BackTester


def process_data(data):
    
    data['rsi']=ta.rsi(data['close'],length=14)
    data['roc']=ta.roc(data['close'],timeperiod=14)
    data['roc_ema']=ta.ema(data['roc'],timeperiod=14)
    data['roc_std']=ta.stdev(data['roc'],timeperiod=14)

     
    return data


def strat(data):
    
    data['trade_type'] = "HOLD" 
    data['signals'] = 0
    days_low=0
    days_high=0
    position=0
    for i in range(14,len(data)):
        if (position==0):
            if(data.loc[i,'roc']>(data.loc[i,'roc_ema']+data.loc[i,'roc_std'])):
                if(data.loc[i,'rsi']<80):
                    data.loc[i,'signals']=1
                    data.loc[i,'trade_type']='LONG'
                    
                    position=1
            if(data.loc[i,'roc']<(data.loc[i,'roc_ema']-data.loc[i,'roc_std'])):
                days_low=days_low+1
                if(days_low>15 and data.loc[i,'rsi']<40):
                    data.loc[i,'signals']=1
                    data.loc[i,'trade_type']='LONG'
                    position=1
                    days_low=0
                elif(0<days_low<15):
                    data.loc[i,'signals']=-1
                    
                    data.loc[i,'trade_type']='SHORT'
                    position=-1
                    days_low=0
        elif(position==1):
            if(data.loc[i,'roc']<(data.loc[i,'roc_ema']-data.loc[i,'roc_std'])):
                days_low=days_low+1
                if(days_low>4):
                    data.loc[i,'signals']=-1
                    data.loc[i,'trade_type']='CLOSE'
                    days_low=0
                    position=0
        elif(position==-1):
            if(data.loc[i,'roc']<(data.loc[i,'roc_ema']-data.loc[i,'roc_std'])):
                days_low=days_low+1
                if(days_low>15 and data.loc[i,'rsi']<40):
                    data.loc[i,'signals']=2
                    data.loc[i,'trade_type']='REVERSE_SHORT_TO_LONG'
                    position=1
                    days_low=0
            if(data.loc[i,'roc']>data.loc[i,'roc_ema']-data.loc[i,'roc_std'] and data.loc[i,'roc']<data.loc[i,'roc_ema']+data.loc[i,'roc_std']):
                data.loc[i,'signals']=1
                data.loc[i,'trade_type']='CLOSE'
                position=0
                days_low=0
                 
                
            
 

    return data

def main():
    data = pd.read_csv("BTC_data.csv")
    processed_data = process_data(data) # process the data
    result_data = strat(processed_data) # Apply the strategy
    csv_file_path = "main.csv" 
    result_data.to_csv(csv_file_path, index=False)

    bt = BackTester("BTC", signal_data_path="main.csv", master_file_path="main.csv", compound_flag=1)
    bt.get_trades(1000)

    # print trades and their PnL
    for trade in bt.trades: 
        print(trade)
        print(trade.pnl())

    # Print results
    stats = bt.get_statistics()
    for key, val in stats.items():
        print(key, ":", val)


    #Check for lookahead bias
    print("Checking for lookahead bias...")
    lookahead_bias = False
    for i in range(len(result_data)):
        if result_data.loc[i, 'signals'] != 0:  # If there's a signal
            temp_data = data.iloc[:i+1].copy()  # Take data only up to that point
            temp_data = process_data(temp_data) # process the data
            temp_data = strat(temp_data) # Re-run strategy
            if temp_data.loc[i, 'signals'] != result_data.loc[i, 'signals']:
                print(f"Lookahead bias detected at index {i}")
                lookahead_bias = True

    if not lookahead_bias:
        print("No lookahead bias detected.")

    # Generate the PnL graph
    bt.make_trade_graph()
    bt.make_pnl_graph()
    
if __name__ == "__main__":
    main()