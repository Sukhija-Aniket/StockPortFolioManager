import pandas as pd
import os
import sys
from datetime import datetime

scripts_directory = os.path.dirname(__file__)
parent_directory = os.path.dirname(scripts_directory)
sys.path.append(parent_directory)

from pythonPackage import utils
from pythonPackage.constants import *

# Important Information
from dotenv import load_dotenv
env_file = os.path.join(parent_directory, 'secrets', '.env')
load_dotenv(env_file)

api_key_file_name = 'tradingprojects-apiKey.json'
excel_file_name = os.getenv('EXCEL_FILE_NAME')
spreadsheet_id = os.getenv('SPREADSHEET_ID')
spreadsheet_file = os.path.join(parent_directory, 'assets', excel_file_name)
credentials_file = os.path.join(parent_directory, 'secrets', api_key_file_name)

# Required Utility Functions

def script_already_executed():
    last_execution_date = os.getenv(f'LAST_EXECUTION_DATE_{typ.upper()}')
    if (last_execution_date == datetime.now().strftime(DATE_FORMAT)):
        print("The script has been already been executed today, Exiting...")
        exit()
    utils.update_env_file(f'LAST_EXECUTION_DATE_{typ.upper()}', last_execution_date, env_file)


# Functions for Handling Data

def transDetails_update_data(data):
    # Considering only IntraDay and Delivery and not FNO

    data[TransDetails_constants.TRANSACTION_TYPE] = data[TransDetails_constants.QUANTITY].apply(
        lambda x: utils.update_transaction_type(x))

    sortList = [Raw_constants.NAME, Raw_constants.DATE,
                TransDetails_constants.TRANSACTION_TYPE]
    data = utils.initialize_data(data, sortList=sortList)

    # check for Intraday Count and Delivery Count
    utils.update_intraday_count(data)

    # Calculating Additional Costs Incurred
    data[TransDetails_constants.STT] = data.apply(utils.calculate_stt, axis=1)
    data[TransDetails_constants.SEBI_TRANSACTION_CHARGES] = data.apply(
        utils.calculate_transaction_charges, axis=1)
    data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES] = abs(
        data[TransDetails_constants.NET_AMOUNT] * 0.000001)
    data[TransDetails_constants.BROKERAGE] = data.apply(
        utils.calculate_brokerage, axis=1)
    data[TransDetails_constants.GST] = abs(
        0.18 * (data[TransDetails_constants.BROKERAGE] + data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES] + data[TransDetails_constants.SEBI_TRANSACTION_CHARGES]))
    data[TransDetails_constants.STAMP_DUTY] = abs(
        0.00015 * data[TransDetails_constants.NET_AMOUNT])
    data[TransDetails_constants.STAMP_DUTY] = data.apply(
        utils.calculate_stamp_duty, axis=1)
    data[TransDetails_constants.DP_CHARGES] = data.apply(
        utils.calculate_dp_charges, axis=1, args=({},))
    data[TransDetails_constants.FINAL_AMOUNT] = data[TransDetails_constants.NET_AMOUNT] + data[TransDetails_constants.STT] + data[TransDetails_constants.SEBI_TRANSACTION_CHARGES] + \
        data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES] + data[TransDetails_constants.GST] + \
        data[TransDetails_constants.STAMP_DUTY] + \
        data[TransDetails_constants.DP_CHARGES] + \
        data[TransDetails_constants.BROKERAGE]
    return data

def shareProfitLoss_update_data(data):

    extraCols = [TransDetails_constants.STT, TransDetails_constants.GST, TransDetails_constants.SEBI_TRANSACTION_CHARGES,
                 TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES, TransDetails_constants.BROKERAGE, TransDetails_constants.STAMP_DUTY, TransDetails_constants.DP_CHARGES, TransDetails_constants.INTRADAY_COUNT, TransDetails_constants.STOCK_EXCHANGE]
    data = utils.initialize_data(data, extraCols=extraCols)
    grouped_data = data.groupby(
        [TransDetails_constants.TRANSACTION_TYPE, Raw_constants.NAME])

    infoMap = {}
    rowData = {}
    # Added the condition to remove key,value pairs created due to class itself.
    constants_dict = {key: value for key, value in vars(ShareProfitLoss_constants).items(
    ) if (isinstance(value, str) and not value.startswith('python'))}
    df = pd.DataFrame(columns=list(constants_dict.values()))
    for (transaction_type, name), group in grouped_data:
        if name not in rowData:
            rowData[name] = utils.get_spl_row()
            infoMap[name] = {}
        averageBuyPrice = 0
        averageSalePrice = 0
        averageCostOfSoldShares = 0
        numSharesBought = 0
        numSharesSold = 0
        totalInvestment = 0
        currentInvestment = 0

        # X --> Date, Name, Price, Quantity, Net Amount, Transaction Type, Final Amount
        infoMap[name][transaction_type] = group.values.tolist()
        if transaction_type == SELL:
            for x in infoMap[name][transaction_type]:
                averageSalePrice = (
                    averageSalePrice * numSharesSold - x[6])/(numSharesSold - x[3])
                numSharesSold -= x[3]
                currentInvestment += x[6]
            if BUY in infoMap[name]:
                for x in infoMap[name][BUY]:
                    currentInvestment += x[6]
                averageCostOfSoldShares = utils.calculate_average_cost_of_sold_shares(
                    infoMap[name])
            rowData[name][ShareProfitLoss_constants.AVERAGE_SALE_PRICE] = averageSalePrice
            rowData[name][ShareProfitLoss_constants.SHARES_SOLD] = numSharesSold
            rowData[name][ShareProfitLoss_constants.AVERAGE_COST_OF_SOLD_SHARES] = averageCostOfSoldShares
            rowData[name][ShareProfitLoss_constants.DATE] = max(
                rowData[name][ShareProfitLoss_constants.DATE], x[0])
            rowData[name][ShareProfitLoss_constants.CURRENT_INVESTMENT] = currentInvestment
        else:
            for x in infoMap[name][transaction_type]:
                averageBuyPrice = (
                    averageBuyPrice * numSharesBought + x[6])/(numSharesBought + x[3])
                numSharesBought += x[3]
                currentInvestment += x[6]
                totalInvestment += x[6]
            rowData[name][ShareProfitLoss_constants.AVERAGE_BUY_PRICE] = averageBuyPrice
            rowData[name][ShareProfitLoss_constants.SHARES_BOUGHT] = numSharesBought
            rowData[name][ShareProfitLoss_constants.DATE] = max(
                rowData[name][ShareProfitLoss_constants.DATE], x[0])
            rowData[name][ShareProfitLoss_constants.TOTAL_INVESTMENT] = totalInvestment
            rowData[name][ShareProfitLoss_constants.CURRENT_INVESTMENT] = currentInvestment

    for share_name, share_details in rowData.items():
        actualStockDetails = utils.get_prizing_details_yfinance(datetime.now(), share_name) 
        # actualStockDetails = utils.get_prizing_details_yfinance(datetime.strptime(share_details[ShareProfitLoss_constants.DATE], DATE_FORMAT), share_name)
        # actualStockDetails = utils.get_prizing_details_alphaVintage(
        #     share_name, GLOBAL_QUOTE)
        closing_price = 0
        if len(actualStockDetails) > 0:
            closing_price = actualStockDetails[3]
        new_row = pd.Series({
            ShareProfitLoss_constants.DATE: share_details[ShareProfitLoss_constants.DATE],
            ShareProfitLoss_constants.NAME: share_name,
            ShareProfitLoss_constants.AVERAGE_BUY_PRICE: share_details[ShareProfitLoss_constants.AVERAGE_BUY_PRICE],
            ShareProfitLoss_constants.AVERAGE_SALE_PRICE: share_details[ShareProfitLoss_constants.AVERAGE_SALE_PRICE],
            ShareProfitLoss_constants.AVERAGE_COST_OF_SOLD_SHARES: share_details[ShareProfitLoss_constants.AVERAGE_COST_OF_SOLD_SHARES],
            ShareProfitLoss_constants.SHARES_BOUGHT: share_details[ShareProfitLoss_constants.SHARES_BOUGHT],
            ShareProfitLoss_constants.SHARES_SOLD: share_details[ShareProfitLoss_constants.SHARES_SOLD],
            ShareProfitLoss_constants.SHARES_REMAINING: share_details[ShareProfitLoss_constants.SHARES_BOUGHT] - share_details[ShareProfitLoss_constants.SHARES_SOLD],
            ShareProfitLoss_constants.PROFIT_PER_SHARE: -(share_details[ShareProfitLoss_constants.AVERAGE_COST_OF_SOLD_SHARES] - share_details[ShareProfitLoss_constants.AVERAGE_SALE_PRICE]),
            ShareProfitLoss_constants.NET_PROFIT: -((share_details[ShareProfitLoss_constants.AVERAGE_COST_OF_SOLD_SHARES] * share_details[ShareProfitLoss_constants.SHARES_SOLD]) - (share_details[ShareProfitLoss_constants.AVERAGE_SALE_PRICE] * share_details[ShareProfitLoss_constants.SHARES_SOLD])),
            ShareProfitLoss_constants.TOTAL_INVESTMENT: share_details[ShareProfitLoss_constants.TOTAL_INVESTMENT],
            ShareProfitLoss_constants.CURRENT_INVESTMENT: share_details[ShareProfitLoss_constants.CURRENT_INVESTMENT],
            ShareProfitLoss_constants.CLOSING_PRICE: closing_price,
            ShareProfitLoss_constants.HOLDINGS: closing_price *
            (share_details[ShareProfitLoss_constants.SHARES_BOUGHT] -
             share_details[ShareProfitLoss_constants.SHARES_SOLD])
        })
        df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
    return df

def dailyProfitLoss_update_data(data):
    extraCols = [TransDetails_constants.STT, TransDetails_constants.GST, TransDetails_constants.SEBI_TRANSACTION_CHARGES,
                 TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES, TransDetails_constants.BROKERAGE, TransDetails_constants.STAMP_DUTY, TransDetails_constants.DP_CHARGES, TransDetails_constants.STOCK_EXCHANGE, TransDetails_constants.INTRADAY_COUNT]
    data = utils.initialize_data(data, extraCols)
    grouped_data = data.groupby([Raw_constants.DATE, Raw_constants.NAME])

    rowData = {}
    dailySpendings = {}
    constants_dict = {key: value for key, value in vars(DailyProfitLoss_constants).items(
    ) if (isinstance(value, str) and not value.startswith('python'))}
    df = pd.DataFrame(columns=list(constants_dict.values()))
    for (date, name), group in grouped_data:
        if date not in dailySpendings:
            dailySpendings[date] = 0
        priceDetails = utils.get_prizing_details_yfinance(
            datetime.strptime(date, DATE_FORMAT), name)
        if date not in rowData:
            rowData[date] = {}
        averagePrice = 0
        quantity = 0
        amountInvested = 0
        for values in group.values.tolist():
            if quantity + values[3] == 0:
                averagePrice = 0
                quantity = 0
            else:
                averagePrice = (averagePrice * quantity +
                                values[6])/(quantity + values[3])
                quantity += values[3]
            amountInvested += values[6]
        rowData[date][name] = {
            DailyProfitLoss_constants.DATE: date,
            DailyProfitLoss_constants.NAME: name,
            DailyProfitLoss_constants.AVERAGE_PRICE: averagePrice,
            DailyProfitLoss_constants.QUANTITY: quantity,
            DailyProfitLoss_constants.AMOUNT_INVESTED: amountInvested,
            DailyProfitLoss_constants.OPENING_PRICE: priceDetails[0],
            DailyProfitLoss_constants.HIGH: priceDetails[1],
            DailyProfitLoss_constants.LOW: priceDetails[2],
            DailyProfitLoss_constants.CLOSING_PRICE: priceDetails[3],
            DailyProfitLoss_constants.VOLUME: priceDetails[4],
            DailyProfitLoss_constants.DAILY_SPENDINGS: "",
        }
        dailySpendings[date] += amountInvested
        rowData[date][DailyProfitLoss_constants.DAILY_SPENDINGS] = dailySpendings[date]

    for date, share_details in rowData.items():
        for key, value in share_details.items():
            if key == DailyProfitLoss_constants.DAILY_SPENDINGS:
                continue
            new_row = pd.Series(value)
            df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
        data_row = pd.Series({
            DailyProfitLoss_constants.DATE: date,
            DailyProfitLoss_constants.NAME: '',
            DailyProfitLoss_constants.AVERAGE_PRICE: "",
            DailyProfitLoss_constants.QUANTITY: "",
            DailyProfitLoss_constants.AMOUNT_INVESTED: "",
            DailyProfitLoss_constants.OPENING_PRICE: "",
            DailyProfitLoss_constants.HIGH: "",
            DailyProfitLoss_constants.LOW: "",
            DailyProfitLoss_constants.CLOSING_PRICE: "",
            DailyProfitLoss_constants.VOLUME: "",
            DailyProfitLoss_constants.DAILY_SPENDINGS: share_details[
                DailyProfitLoss_constants.DAILY_SPENDINGS]
        })
        df = pd.concat([df, data_row.to_frame().T], ignore_index=True)
    return df

def taxation_update_data(data):
    extraCols = [TransDetails_constants.GST, TransDetails_constants.SEBI_TRANSACTION_CHARGES,
                 TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES, TransDetails_constants.BROKERAGE, TransDetails_constants.STAMP_DUTY, TransDetails_constants.DP_CHARGES, TransDetails_constants.INTRADAY_COUNT, TransDetails_constants.STOCK_EXCHANGE]
    data = utils.initialize_data(data, extraCols=extraCols)
    grouped_data = data.groupby(
        [TransDetails_constants.TRANSACTION_TYPE, Raw_constants.NAME, Raw_constants.DATE])

    infoMap = {}
    rowData = {}
    intraMap = {}
    global_buy_data = {}
    global_sell_data = {}
   
    # Added the condition to remove key,value pairs created due to class itself.
    constants_dict = {key: value for key, value in vars(Taxation_constants).items(
    ) if (isinstance(value, str) and not value.startswith('python'))}    

    df = pd.DataFrame(columns=list(constants_dict.values()))
    
    # Firstly find the intraday transactions and the profit on those transactions
    for (transaction_type, name, date), group in grouped_data:
        if name not in infoMap:
            intraMap[name] = {}
            infoMap[name] = {}
            rowData[name] = utils.get_taxation_row()
        if date not in infoMap[name]:
            infoMap[name][date] = {}
            # intraMap[name][date] = 0 # this needs to be written done, correction made.
            rowData[name][Taxation_constants.DATE] = max(rowData[name][Taxation_constants.DATE], date)
        if transaction_type not in infoMap[name][date]:
            infoMap[name][date][transaction_type] = group.values.tolist()
            # X --> Date, Name, Price, Quantity, Net Amount, Transaction Type, STT, Final Amount
            if transaction_type == BUY:
                if name not in global_buy_data:
                    global_buy_data[name] = []
                for x in infoMap[name][date][BUY]:
                    global_buy_data[name].append([x[0], x[3], x[7]])
            else:
                if name not in global_sell_data:
                    global_sell_data[name] = []
                for x in infoMap[name][date][SELL]:
                    global_sell_data[name].append([x[0], abs(x[3]), abs(x[7])])
                
        if transaction_type == SELL:
            buyData = []
            sellData = []
            
            if BUY in infoMap[name][date]:
                intraMap[name][date] = 0
                # X --> Date, Name, Price, Quantity, Net Amount, Transaction Type, STT, Final Amount
                for x in infoMap[name][date][BUY]:
                    buyData.append([x[3], x[7]])
                for x in infoMap[name][date][transaction_type]:
                    sellData.append([abs(x[3]), abs(x[7])])
            
                i,j = 0,0
                while i < len(buyData) and j < len(sellData):
                    buyCnt = buyData[i][0]
                    sellCnt = sellData[j][0]
                    if buyCnt >= sellCnt:
                        # used - (buy - sell)
                        rowData[name][Taxation_constants.INTRADAY_INCOME] -= sellCnt * (buyData[i][1]/buyCnt - sellData[j][1]/sellCnt)
                        intraMap[name][date] += sellCnt
                        buyData[i][1] = (buyData[i][0] - sellCnt) * (buyData[i][1]/buyData[i][0])
                        buyData[i][0] -= sellCnt
                        sellData[j][1] = 0
                        sellData[j][0] = 0
                        j += 1
                    else:
                        rowData[name][Taxation_constants.INTRADAY_INCOME] -= buyCnt * (buyData[i][1]/buyCnt - sellData[j][1]/sellCnt)
                        intraMap[name][date] += buyCnt
                        sellData[j][1] = (sellData[j][0] - buyCnt) * (sellData[j][1]/sellData[j][0])
                        sellData[j][0] -= buyCnt
                        buyData[i][1] = 0
                        buyData[i][0] = 0
                        i += 1
                temp = intraMap[name][date]
                intraMap[name][date] = [temp, temp]
                  
    # writing algorithm to find the STCG AND LTCG
    for name in infoMap.keys():
        # Firstly I am reducing the intraday things, 
        i,j = 0, 0
        while i < len(global_buy_data[name]):
            buyDetails = global_buy_data[name][i]
            if buyDetails[0] in intraMap[name]:
                tempval = min(buyDetails[1], intraMap[name][buyDetails[0]][0])
                buyDetails[2] = (buyDetails[1] - tempval) * (buyDetails[2]/buyDetails[1])
                buyDetails[1] -= tempval
                global_buy_data[name][i] = buyDetails
                intraMap[name][buyDetails[0]][0] -= tempval
            i += 1
        while name in global_sell_data and j < len(global_sell_data[name]):
            sellDetails = global_sell_data[name][j]
            if sellDetails[0] in intraMap[name]:
                tempval = min(sellDetails[1], intraMap[name][sellDetails[0]][1])
                sellDetails[2] = (sellDetails[1] - tempval) * (sellDetails[2]/ sellDetails[1])
                sellDetails[1] -= tempval
                global_sell_data[name][j] = sellDetails
                intraMap[name][sellDetails[0]][1] -= tempval
            j += 1
            
        # Now I will iterate again to find the LTCG and STCG for those stocks
        i,j = 0, 0
        while i < len(global_buy_data[name]) and name in global_sell_data and j < len(global_sell_data[name]):
            buyDetails = global_buy_data[name][i]
            sellDetails = global_sell_data[name][j]
            
            tempval = min(buyDetails[1], sellDetails[1])
            if tempval == 0:
                if buyDetails[1] == 0:
                    i += 1
                if sellDetails[1] == 0:
                    j += 1
                continue
            # Assumption no details are zero initially
            if utils.is_long_term(buyDetails[0], sellDetails[0]):
                # used - (buy - sell)
                rowData[name][Taxation_constants.LTCG] -= (tempval * (buyDetails[2]/buyDetails[1]) - tempval * (sellDetails[2]/sellDetails[1]))
            else:
                # used - (buy - sell)
                rowData[name][Taxation_constants.STCG] -= (tempval * (buyDetails[2]/buyDetails[1]) - tempval * (sellDetails[2]/sellDetails[1]))
            buyDetails[2] = (buyDetails[1] - tempval) * (buyDetails[2]/buyDetails[1])
            buyDetails[1] -= tempval
            global_buy_data[name][i] = buyDetails
            sellDetails[2] = (sellDetails[1] - tempval) * (sellDetails[2]/sellDetails[1])
            sellDetails[1] -= tempval
            global_sell_data[name][j] = sellDetails
            if buyDetails[1] == 0:
                i += 1
            if sellDetails[1] == 0:
                j += 1
        
        # The Assumption is that both i and j leave at the same time.
                 
    # Finally forming the answer
    for name, details in rowData.items():
        new_row = pd.Series({
            Taxation_constants.DATE: details[Taxation_constants.DATE],
            Taxation_constants.NAME: name,
            Taxation_constants.LTCG: details[Taxation_constants.LTCG],
            Taxation_constants.STCG: details[Taxation_constants.STCG],
            Taxation_constants.INTRADAY_INCOME: details[Taxation_constants.INTRADAY_INCOME],
        })
        df = pd.concat([df, new_row.to_frame().T], ignore_index=True) 
    return df    

# Main Program
if __name__ == "__main__":
    
    # Taking Required User Inputs
    input_file, typ = utils.get_args_and_input(sys.argv, excel_file_name, spreadsheet_id, env_file)
    input_file = utils.get_valid_path(input_file)

    '''
    Depreciated: Not allowing the script to execute twice a day, replaced by
    a better function 'data_already_exists'.
    # script_already_executed() 
    '''

    # Handling User data
    input_data = pd.read_csv(input_file)
    input_data = utils.format_input_data(input_data)
    spreadsheet, sheet_names, raw_data = utils.get_sheets_and_data(typ, credentials_file, spreadsheet_id, spreadsheet_file)
    utils.data_already_exists(raw_data, input_data) 

    
    # Preparing  data for all the sheets
    raw_data = pd.concat([raw_data, input_data], ignore_index=True)
    transDetails_data = transDetails_update_data(raw_data.copy(deep=True))
    shareProfitLoss_data = shareProfitLoss_update_data(transDetails_data.copy(deep=True))
    dailyProfitLoss_data = dailyProfitLoss_update_data(transDetails_data.copy(deep=True))
    taxation_data = taxation_update_data(transDetails_data.copy(deep=True))
    data_items = [raw_data, transDetails_data, shareProfitLoss_data, dailyProfitLoss_data, taxation_data]

    # Handling the formatting and final updation
    formatting_funcs = utils.get_formatting_funcs(typ)
    updating_func = utils.get_updating_func(typ)
    
    for i in range(len(formatting_funcs)):
        updating_func(spreadsheet, sheet_names[i], data_items[i], formatting_funcs[i])
    

