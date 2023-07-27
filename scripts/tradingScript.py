import pandas as pd
import os
import sys
from datetime import datetime
import openpyxl

scripts_directory = os.path.dirname(__file__)
parent_directory = os.path.dirname(scripts_directory)
sys.path.append(parent_directory)

from pythonPackage.constants import *
from pythonPackage import utils


# Important Information
from dotenv import load_dotenv
env_file = os.path.join(parent_directory, 'secrets', '.env')
load_dotenv(env_file)

spreadsheet_id = os.getenv('SPREADSHEET_ID')
excel_file_name = os.getenv('EXCEL_FILE_NAME')
spreadsheet_file = os.path.join(parent_directory, 'secrets', excel_file_name)
api_key_file_name = 'tradingprojects-apiKey.json'
credentials_file = os.path.join(parent_directory, 'secrets', api_key_file_name)


# Utility Functions

def update_env_file(key, value):
    env_file_path = os.path.join(parent_directory, '.env')

    with open(env_file_path, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            line = f"{key}={value}\n"
        updated_lines.append(line)

    with open(env_file_path, 'w') as file:
        file.writelines(updated_lines)


def get_args_and_input():
    key = 'EXCEL_FILE_NAME'
    if len(sys.argv) > 2:
        value = sys.argv[2]
    if len(sys.argv) > 1:
        typ = sys.argv[1]
        value = ''
        if typ == 'sheets':
            key = 'SPREADSHEET_ID'

    else:
        print("Please select 'excel' or 'sheets, leave empty to use excel as default")
        typ = input("Enter your choice: ")
        if (typ == 'excel' or typ == ''):
            print(
                f"{excel_file_name} is the default file, enter name below if you wish to change it, leave empty otherwise")
            value = input("Enter your choice: ")

        elif (typ == 'sheets'):
            print(f"{spreadsheet_id} is the default google sheet, enter spreadsheet_id below if you wish to change it, leave empty otherwise")
            value = input("Enter your choice: ")
            key = 'SPREADSHEET_ID'

    if value is not None and value != '':
        update_env_file(key, value)

    return typ


def update_transaction_type(x):
    if x[0] != '-':
        return BUY
    return SELL


def update_intraday_count(data):
    infoMap = {}
    rowData = {}
    sumData = {}
    grouped_data = data.groupby(
        [Raw_constants.NAME, TransDetails_constants.TRANSACTION_TYPE, Raw_constants.DATE])
    for (name, transaction_type, date), group in grouped_data:
        if name not in infoMap:
            infoMap[name] = {}
            rowData[name] = {}
            sumData[name] = {}
        if date not in infoMap[name]:
            infoMap[name][date] = {}
            rowData[name][date] = []
            sumData[name][date] = 0
        if transaction_type not in infoMap[name][date]:
            infoMap[name][date][transaction_type] = group.values.tolist()

        if transaction_type == SELL:
            buyCnt = 0

            if BUY in infoMap[name][date]:
                for x in infoMap[name][date][BUY]:
                    buyCnt += abs(x[3])
            for x in infoMap[name][date][transaction_type]:
                sellCnt = min(abs(x[3]), buyCnt)
                buyCnt -= sellCnt
                rowData[name][date].append(sellCnt)
                sumData[name][date] += sellCnt

    data[TransDetails_constants.INTRADAY_COUNT] = data.apply(
        calculate_intra_sell_count, axis=1, args=(rowData,))
    data[TransDetails_constants.INTRADAY_COUNT] = data.apply(
        calculate_intra_buy_count, axis=1, args=(sumData,))


def calculate_intra_sell_count(row, rowData):
    name = row[Raw_constants.NAME]
    date = row[Raw_constants.DATE]
    transaction_type = row[TransDetails_constants.TRANSACTION_TYPE]

    if transaction_type == BUY:
        return 0

    if name not in rowData or date not in rowData[name]:
        return 0

    if len(rowData[name][date]) > 0:
        intraCount = rowData[name][date][0]
        rowData[name][date].pop(0)
        return intraCount


def calculate_intra_buy_count(row, sumData):
    name = row[Raw_constants.NAME]
    date = row[Raw_constants.DATE]
    transaction_type = row[TransDetails_constants.TRANSACTION_TYPE]

    if name not in sumData or date not in sumData[name]:
        return 0

    if transaction_type == SELL:
        return row[TransDetails_constants.INTRADAY_COUNT]

    intraCount = min(sumData[name][date], row[Raw_constants.QUANTITY])
    sumData[name][date] -= intraCount
    return intraCount


def calculate_stt(row):
    intraDay_charges, delivery_charges = 0, 0
    delivery_charges = (abs(row[Raw_constants.QUANTITY]) -
                        row[TransDetails_constants.INTRADAY_COUNT]) * 0.001 * row[Raw_constants.PRICE]
    if row[TransDetails_constants.TRANSACTION_TYPE] == SELL:
        intraDay_charges = row[TransDetails_constants.INTRADAY_COUNT] * \
            0.00025 * row[Raw_constants.PRICE]
    return intraDay_charges + delivery_charges


def calculate_transaction_charges(row):
    if row[Raw_constants.STOCK_EXCHANGE] == BSE:
        return abs(row[Raw_constants.NET_AMOUNT]) * 0.0000375
    return abs(row[Raw_constants.NET_AMOUNT]) * 0.0000335

def calculate_stamp_duty(row):
    if row[TransDetails_constants.TRANSACTION_TYPE] == SELL:
        return 0
    
    intraDay_charges, delivery_charges = 0, 0
    delivery_charges = (abs(row[Raw_constants.QUANTITY]) -
                        row[TransDetails_constants.INTRADAY_COUNT]) * 0.00015 * row[Raw_constants.PRICE]
    intraDay_charges = row[TransDetails_constants.INTRADAY_COUNT] * \
        0.00003 * row[Raw_constants.PRICE]
    return intraDay_charges + delivery_charges


def calculate_dp_charges(row, dp_data):
    name = row[Raw_constants.NAME]
    date = row[Raw_constants.DATE]
    if row[TransDetails_constants.TRANSACTION_TYPE] == SELL and abs(row[Raw_constants.QUANTITY]) > row[TransDetails_constants.INTRADAY_COUNT]:
        if name not in dp_data:
            dp_data[name] = {}
        if date not in dp_data[name]:
            dp_data[name][date] = True
            return 15.93
    return 0


def calculate_brokerage(row):
    if row[TransDetails_constants.TRANSACTION_TYPE] == SELL and row[TransDetails_constants.INTRADAY_COUNT] > 0:
        return min(((row[TransDetails_constants.NET_AMOUNT] * row[TransDetails_constants.INTRADAY_COUNT])/row[TransDetails_constants.QUANTITY]) * 0.0003, 20)
    # val = min(data[TransDetails_constants.NET_AMOUNT] * 0.0003, 20)
    return 0

def compare_dates(d1, d2):
    dt1 = datetime.strptime(d1, DATE_FORMAT)
    dt2 = datetime.strptime(d2, DATE_FORMAT)

    if dt1 == dt2:
        return 0
    elif dt1 > dt2:
        return 1

    return -1

def calculate_average_cost_of_sold_shares(infoMap):
    sold_list = infoMap[SELL]
    buy_list = infoMap[BUY]

    j = 0
    price = 0
    intraCount = 0
    delCount = 0
    counter = 0

    # Calculating for IntraDay Orders
    for i in range(0, len(sold_list)):
        sold_list[i][3] = abs(sold_list[i][3])
        sold_list[i][6] = abs(sold_list[i][6])
        if j >= len(buy_list):
            break
        if compare_dates(buy_list[j][0], sold_list[i][0]) == 0:
            if buy_list[j][3] < sold_list[i][3]:
                intraCount += buy_list[j][3]
                sold_list[i][3] -= buy_list[j][3]
                price += buy_list[j][6]
                buy_list[j][3] = 0
                buy_list[j][6] = 0
                j += 1
                i -= 1
            elif buy_list[j][3] > sold_list[i][3]:
                price += ((buy_list[j][6] * sold_list[i][3])/buy_list[j][3])
                buy_list[j][6] -= ((buy_list[j][6] *
                                    sold_list[i][3])/buy_list[j][3])
                buy_list[j][3] -= sold_list[i][3]
                intraCount += sold_list[i][3]
                sold_list[i][3] = 0
            else:
                intraCount += sold_list[i][3]
                sold_list[i][3] = 0
                price += buy_list[j][6]
                buy_list[j][3] = 0
                buy_list[j][6] = 0
                j += 1
        elif compare_dates(buy_list[j][0], sold_list[i][0]) < 0:
            i -= 1
            j += 1

    # Calculating for Delivery Orders
    for x in sold_list:
        delCount += x[3]
    for x in buy_list:
        if x[3] <= (delCount - counter):
            price += x[6]
            counter += x[3]
        else:
            price += (x[6] * (delCount - counter))/x[3]
            counter = delCount
    counter += intraCount

    return price/counter


# Functions for Data

def transDetails_update_data(data):
    # Ignoring BTST for Now, and considering only IntraDay and Delivery

    data[TransDetails_constants.TRANSACTION_TYPE] = data[TransDetails_constants.QUANTITY].apply(
        lambda x: update_transaction_type(x))

    sortList = [Raw_constants.NAME, Raw_constants.DATE,
                TransDetails_constants.TRANSACTION_TYPE]
    data = utils.initialize_data(data, sortList=sortList)

    # check for Intraday Count and Delivery Count
    update_intraday_count(data)

    # Calculating Additional Costs Incurred
    data[TransDetails_constants.STT] = data.apply(calculate_stt, axis=1)
    data[TransDetails_constants.SEBI_TRANSACTION_CHARGES] = data.apply(
        calculate_transaction_charges, axis=1)
    data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES] = abs(
        data[TransDetails_constants.NET_AMOUNT] * 0.000001)
    data[TransDetails_constants.GST] = abs(
        0.18 * (data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES]) + data[TransDetails_constants.SEBI_TRANSACTION_CHARGES])
    data[TransDetails_constants.STAMP_DUTY] = abs(
        0.00015 * data[TransDetails_constants.NET_AMOUNT])
    data[TransDetails_constants.STAMP_DUTY] = data.apply(calculate_stamp_duty, axis=1)
    data[TransDetails_constants.DP_CHARGES] = data.apply(
        calculate_dp_charges, axis=1, args=({},))
    data[TransDetails_constants.BROKERAGE] = data.apply(
        calculate_brokerage, axis=1)
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
                averageCostOfSoldShares = calculate_average_cost_of_sold_shares(
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


# Functions for Google Sheets

def transDetails_update_sheets(spreadsheet, sheet_name, data):
    sheet = utils.initialize_sheets(spreadsheet, sheet_name)
    utils.display_and_format_sheets(sheet, data)
    utils.transDetails_formatting_sheets(spreadsheet, sheet)


def shareProfitLoss_update_sheets(spreadsheet, sheet_name, data):
    sheet = utils.initialize_sheets(spreadsheet, sheet_name)
    utils.display_and_format_sheets(sheet, data)
    utils.shareProfitLoss_formatting_sheets(spreadsheet, sheet)


def dailyProfitLoss_update_sheets(spreadsheet, sheet_name, data):
    sheet = utils.initialize_sheets(spreadsheet, sheet_name)
    utils.display_and_format_sheets(sheet, data)
    utils.dailyProfitLoss_formatting_sheets(spreadsheet, sheet)


# Functions for Excel

def transDetails_update_excel(spreadsheet, sheet_name, data):
    sheet = utils.initialize_excel(spreadsheet, sheet_name)
    utils.display_and_format_excel(sheet, data)
    utils.transDetails_formatting_excel(sheet)


def shareProfitLoss_update_excel(spreadsheet, sheet_name, data):
    sheet = utils.initialize_excel(spreadsheet, sheet_name)
    utils.display_and_format_excel(sheet, data)
    utils.shareProfitLoss_formatting_excel(sheet)


def dailyProfitLoss_update_excel(spreadsheet, sheet_name, data):
    sheet = utils.initialize_excel(spreadsheet, sheet_name)
    utils.display_and_format_excel(sheet, data)
    utils.dailyProfitLoss_formatting_excel(sheet)


# Main Program

if __name__ == "__main__":

    typ = get_args_and_input()
    if typ == 'sheets':
        spreadsheet = utils.authenticate_and_get_sheets(
            credentials_file, spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        sheet_names = [worksheet.title for worksheet in worksheets]
    else:
        spreadsheet = openpyxl.load_workbook(spreadsheet_file)
        sheet_names = spreadsheet.sheetnames

    input_data = utils.read_data_from_sheets(spreadsheet, sheet_names[0])
    print("Raw Input Data read successfully")

    transDetails_data = transDetails_update_data(input_data.copy(deep=True))

    transDetails_update_sheets(spreadsheet, sheet_names[1], transDetails_data)
    print("Transaction Details updated successfully")

    data = utils.read_data_from_sheets(spreadsheet, sheet_names[1])
    print("Transaction Details Data read successfully\n\n")

    shareProfitLoss_data = shareProfitLoss_update_data(data.copy(deep=True))
    shareProfitLoss_update_sheets(
        spreadsheet, sheet_names[2], shareProfitLoss_data)
    print("Share Profit updated successfully")

    dailyProfitLoss_data = dailyProfitLoss_update_data(data.copy(deep=True))
    dailyProfitLoss_update_sheets(
        spreadsheet, sheet_names[3], dailyProfitLoss_data)
    print("Daily Profit updated successfully")
