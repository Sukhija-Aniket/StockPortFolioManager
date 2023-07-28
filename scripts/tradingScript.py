import pandas as pd
import os
import sys
from datetime import datetime
import openpyxl

scripts_directory = os.path.dirname(__file__)
parent_directory = os.path.dirname(scripts_directory)
sys.path.append(parent_directory)

from pythonPackage import utils
from pythonPackage.constants import *

# Important Information
from dotenv import load_dotenv
env_file = os.path.join(parent_directory, 'secrets', '.env')
load_dotenv(env_file)

spreadsheet_id = os.getenv('SPREADSHEET_ID')
excel_file_name = os.getenv('EXCEL_FILE_NAME')
spreadsheet_file = os.path.join(parent_directory, 'assets', excel_file_name)
api_key_file_name = 'tradingprojects-apiKey.json'
credentials_file = os.path.join(parent_directory, 'secrets', api_key_file_name)


# Utility Functions

def update_env_file(key, value):
    with open(env_file, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            line = f"{key}={value}\n"
        updated_lines.append(line)

    with open(env_file, 'w') as file:
        file.writelines(updated_lines)

def get_args_and_input():
    input_file = None
    key = 'EXCEL_FILE_NAME'
    if len(sys.argv) > 3:
        value = sys.argv[3]
    if len(sys.argv) > 2:
        typ = sys.argv[2].lower()
        value = ''
        if typ == 'sheets':
            key = 'SPREADSHEET_ID'
    else:
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
        else:
            input_file = input("Please enter the absolute path of the file downloaded from Zerodha: ")
        print("Please select 'excel' or 'sheets, leave empty to use excel as default")
        typ = input("Enter your choice: ")
        typ = typ.lower()
        if (typ == 'excel' or typ == ''):
            print(
                f"{excel_file_name} is the default file, enter name below if you wish to change it, leave empty otherwise")
            value = input("Enter your choice: ")

        elif (typ== 'sheets'):
            print(f"{spreadsheet_id} is the default google sheet, enter spreadsheet_id below if you wish to change it, leave empty otherwise")
            value = input("Enter your choice: ")
            key = 'SPREADSHEET_ID'

    if value is not None and value != '':
        update_env_file(key, value)

    return input_file, typ

def data_already_exists(raw_data, input_data):
    if not raw_data.empty:
        is_duplicate = raw_data[
            (raw_data[Raw_constants.DATE] == input_data[Raw_constants.DATE][0]) &
            (raw_data[Raw_constants.NAME] == input_data[Raw_constants.NAME][0])
        ].shape[0] > 0

        if is_duplicate:
            print("Orders Data Already Exists in the file, Exiting...")
            exit()

def script_already_executed():
    last_execution_date = os.getenv(f'LAST_EXECUTION_DATE_{typ.upper()}')
    if (last_execution_date == datetime.now().strftime(DATE_FORMAT)):
        print("The script has been already been executed today, Exiting...")
        exit()
    update_env_file(f'LAST_EXECUTION_DATE_{typ.upper()}', last_execution_date)

def get_sheets_and_data():
    if typ == 'sheets':
        spreadsheet = utils.authenticate_and_get_sheets(
            credentials_file, spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        sheet_names = [worksheet.title for worksheet in worksheets]
        raw_data = utils.read_data_from_sheets(spreadsheet, sheet_names[0])
    else:
        spreadsheet = openpyxl.load_workbook(spreadsheet_file)
        sheet_names = spreadsheet.sheetnames
        raw_data = utils.read_data_from_excel(spreadsheet, sheet_names[0])

    return spreadsheet, sheet_names, raw_data


# Functions for Data

def transDetails_update_data(data):
    # Ignoring BTST for Now, and considering only IntraDay and Delivery

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
    data[TransDetails_constants.GST] = abs(
        0.18 * (data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES]) + data[TransDetails_constants.SEBI_TRANSACTION_CHARGES])
    data[TransDetails_constants.STAMP_DUTY] = abs(
        0.00015 * data[TransDetails_constants.NET_AMOUNT])
    data[TransDetails_constants.STAMP_DUTY] = data.apply(
        utils.calculate_stamp_duty, axis=1)
    data[TransDetails_constants.DP_CHARGES] = data.apply(
        utils.calculate_dp_charges, axis=1, args=({},))
    data[TransDetails_constants.BROKERAGE] = data.apply(
        utils.calculate_brokerage, axis=1)
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
        totalInvestment = 0
        currentInvestment = 0
        numSharesSold = 0

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
        actualStockDetails = utils.get_prizing_details_alphaVintage(
            share_name, GLOBAL_QUOTE)
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


# Functions for Google sheets & Excel

def update_sheet(sheet_name, data, formatting_function=None):
    sheet = utils.initialize_sheets(spreadsheet, sheet_name)
    utils.display_and_format_sheets(sheet, data)
    if formatting_function is not None:
        formatting_function(spreadsheet, sheet)
    print(f"{sheet_name} updated Successfully!")

def update_excel(sheet_name, data, formatting_function=None):
    sheet = utils.initialize_excel(spreadsheet, sheet_name)
    utils.display_and_format_excel(sheet, data)
    if formatting_function is not None:
        formatting_function(spreadsheet, sheet)
    print(f"{sheet_name} updated Successfully!")


# Main Program


if __name__ == "__main__":

    # Handling User Inputs
    input_file, typ = get_args_and_input()
    input_file = utils.get_valid_path(input_file)

    # Not allowing the script to execute twice a day.
    # script_already_executed()

    # Gathering Information
    input_data = pd.read_csv(input_file)
    input_data = utils.format_input_data(input_data)
    spreadsheet, sheet_names, raw_data = get_sheets_and_data()
    
    # Checking for Existing Data
    data_already_exists(raw_data, input_data)

    # Handling the data
    raw_data = pd.concat([raw_data, input_data], ignore_index=True)
    transDetails_data = transDetails_update_data(raw_data.copy(deep=True))
    shareProfitLoss_data = shareProfitLoss_update_data(transDetails_data.copy(deep=True))
    dailyProfitLoss_data = dailyProfitLoss_update_data(transDetails_data.copy(deep=True))

    # Handling the formatting for Google  Sheets & Excel
    if typ == 'sheets':
        update_sheet(sheet_names[0], raw_data)
        update_sheet(sheet_names[1], transDetails_data, utils.transDetails_formatting_sheets)
        update_sheet(sheet_names[2], shareProfitLoss_data, utils.shareProfitLoss_formatting_sheets)
        update_sheet(sheet_names[3], dailyProfitLoss_data, utils.dailyProfitLoss_formatting_sheets)
    else:
        update_excel(sheet_names[0], raw_data)
        update_excel(sheet_names[1], transDetails_data, utils.transDetails_formatting_excel)
        update_excel(sheet_names[2], shareProfitLoss_data, utils.shareProfitLoss_formatting_excel)
        update_excel(sheet_names[3], dailyProfitLoss_data, utils.dailyProfitLoss_formatting_excel)

