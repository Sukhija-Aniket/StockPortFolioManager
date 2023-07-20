import pandas as pd
import os
from dotenv import load_dotenv
import openpyxl
from pythonPackage import utils
import sys
from datetime import datetime

# Important Information

load_dotenv()
excel_file_name = os.getenv('EXCEL_FILE_NAME')
api_key_file_name = 'tradingprojects-apiKey.json'
credentials_file = os.path.join(os.path.dirname(__file__), api_key_file_name)
spreadsheet_id = os.getenv('SPREADSHEET_ID')
spreadsheet_file = os.path.join(os.path.dirname(__file__), excel_file_name)


# Functions for Data 

def transDetails_update_data(data):
    sortList=['Name', 'Date', 'Transaction Type']
    data = utils.initialize_data(data, sortList=sortList)
    #  Add necessary columns to data
    data['STT'] = abs(data['Net Amount'] * 0.001)
    data['Transaction Charges'] = abs(data['Net Amount'] * 0.000035)
    data['GST'] = abs(0.18 * (data['Transaction Charges']))
    data['Stamp Charges'] = abs(0.00015 * data['Net Amount'])
    data['Final Amount'] = data['Net Amount'] + data['STT'] + data['Transaction Charges'] + data['GST'] + data['Stamp Charges']
    return data

def shareProfitLoss_update_data(data):
    extraCols = ['STT', 'GST', 'Transaction Charges', 'Stamp Charges']
    data = utils.initialize_data(data, extraCols=extraCols)
    grouped_data = data.groupby(['Transaction Type', 'Name'])
    
    infoMap = {}
    rowData = {}
    df = pd.DataFrame(columns=['Date', 'Name', 'Average Buy Price', 'Average Sale Price', 'Average Cost of Sold Shares','Shares Bought', 'Shares Sold', 'Shares Remaining' ,'Profit Per Share', 'Net Profit', 'Total Investment', 'Current Investment', 'Closing Price', 'Holdings'])
    for (transaction_type, name), group in grouped_data:
        if name not in rowData:
            rowData[name] = utils.get_spl_row()
            infoMap[name] = {}
        averageBuyPrice = 0
        averageSalePrice = 0
        averageBuyPriceOfSoldShares = 0
        numSharesBought = 0
        totalInvestment = 0
        currentInvestment = 0
        numSharesSold = 0
        numShares = 0
        infoMap[name][transaction_type] = group.values.tolist()
        if transaction_type == 'SELL':
            for x in infoMap[name][transaction_type]:
                averageSalePrice = (averageSalePrice * numSharesSold - x[6])/(numSharesSold - x[3])
                numSharesSold -= x[3]
                currentInvestment += x[6]
            if 'BUY' in infoMap[name]: 
                for x in infoMap[name]['BUY']:
                    shareCnt = min(numSharesSold - numShares, x[3])
                    shareAmt = (shareCnt/x[3])*x[6]
                    averageBuyPriceOfSoldShares = (averageBuyPriceOfSoldShares * numShares + shareAmt)/(numShares + shareCnt)
                    numShares += shareCnt
                    if numShares >= numSharesSold:
                        break
                for x in infoMap[name]['BUY']:
                    currentInvestment += x[6]
            rowData[name]['averageSalePrice'] = averageSalePrice
            rowData[name]['numSharesSold'] = numSharesSold
            rowData[name]['numShares'] = numShares
            rowData[name]['averageBuyPriceOfSoldShares'] = averageBuyPriceOfSoldShares
            rowData[name]['date'] = max(rowData[name]['date'], x[0])
            rowData[name]['currentInvestment'] = currentInvestment
        else:
            for x in infoMap[name][transaction_type]:
                averageBuyPrice = (averageBuyPrice * numSharesBought + x[6])/(numSharesBought + x[3])
                numSharesBought += x[3]
                currentInvestment += x[6]
                totalInvestment += x[6]
            rowData[name]['averageBuyPrice'] = averageBuyPrice
            rowData[name]['numSharesBought'] = numSharesBought
            rowData[name]['date'] = max(rowData[name]['date'], x[0])
            rowData[name]['totalInvestment'] = totalInvestment

            
    for share_name, share_details in rowData.items():
        actualStockDetails = utils.get_prizing_details_alphaVintage(share_name,'GLOBAL_QUOTE')
        closing_price = 0
        if len(actualStockDetails) > 0:
            closing_price = actualStockDetails[3]
        new_row = pd.Series({
            'Date': share_details['date'],
            'Name': share_name,
            'Average Buy Price':share_details['averageBuyPrice'],
            'Average Sale Price': share_details['averageSalePrice'],
            'Average Cost of Sold Shares': share_details['averageBuyPriceOfSoldShares'],
            'Shares Bought': share_details['numSharesBought'],
            'Shares Sold': share_details['numSharesSold'],
            'Shares Remaining': share_details['numSharesBought'] - share_details['numSharesSold'],
            'Profit Per Share': -(share_details['averageBuyPriceOfSoldShares'] - share_details['averageSalePrice']),
            'Net Profit': -((share_details['averageBuyPriceOfSoldShares'] * share_details['numShares']) - (share_details['averageSalePrice'] * share_details['numSharesSold'])),
            'Total Investment': share_details['totalInvestment'],
            'Current Investment': share_details['currentInvestment'],
            'Closing Price': closing_price,
            'Holdings': closing_price * (share_details['numSharesBought'] - share_details['numSharesSold'])
        })
        df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
    return df

def dailyProfitLoss_update_data(data):
    extraCols = ['STT', 'GST', 'Transaction Charges', 'Stamp Charges']
    data = utils.initialize_data(data, extraCols)
    grouped_data = data.groupby(['Date', 'Name'])

    rowData = {}
    dailySpendings = {}
    df = pd.DataFrame(columns=['Date', 'Name', 'Average Price', 'Quantity', 'Amount Invested', 'Opening Price','High','Low','Closing Price', 'Daily Spendings'])
    for (date, name), group in grouped_data:
        if date not in dailySpendings:
            dailySpendings[date] = 0
        print(date)
        priceDetails = utils.get_prizing_details_yfinance(datetime.strptime(date,'%m/%d/%Y'), name)
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
                averagePrice = (averagePrice * quantity + values[6])/(quantity + values[3])
                quantity += values[3]
            amountInvested += values[6]
        rowData[date][name] = {
            'Date': date,
            'Name': name,
            'Average Price': averagePrice,
            'Quantity': quantity,
            'Amount Invested': amountInvested,
            'Opening Price': priceDetails[0],
            'High': priceDetails[1],
            'Low': priceDetails[2],
            'Closing Price': priceDetails[3],
            'Daily Spendings': "",
        }
        dailySpendings[date] += amountInvested
        rowData[date]['Daily Spendings'] = dailySpendings[date]     
    

    for date, share_details in rowData.items():
        for key, value in share_details.items():
            if key == 'Daily Spendings': 
                continue
            new_row = pd.Series(value)
            df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
        data_row = pd.Series({
            'Date': date,
            'Name': '',
            'Average Price': "",
            'Quantity': "",
            'Amount Invested': "",
            'Opening Price': "",
            'High': "",
            'Low': "",
            'Closing Price': "",
            'Daily Spendings': share_details['Daily Spendings']
        })
        df = pd.concat([df, data_row.to_frame().T],ignore_index=True)
    return df


# Functions for Sheet

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


# Utility Functions

def update_env_file(key, value):
    env_file_path = os.path.join(os.path.dirname(__file__),'.env')
    
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
            print(f"{excel_file_name} is the default file, enter name below if you wish to change it, leave empty otherwise")
            value = input("Enter your choice: ")

        elif (typ == 'sheets'):
            print(f"{spreadsheet_id} is the default google sheet, enter spreadsheet_id below if you wish to change it, leave empty otherwise")
            value = input("Enter your choice: ")
            key = 'SPREADSHEET_ID'
    
    if value is not None and value != '':
        update_env_file(key, value)

    return typ

if __name__ == "__main__":

    typ = get_args_and_input()
    if typ == 'sheets':
        spreadsheet = utils.authenticate_and_get_sheets(credentials_file, spreadsheet_id)
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
    print("Transaction Details Data read successfully")

    shareProfitLoss_data = shareProfitLoss_update_data(data.copy(deep=True))
    shareProfitLoss_update_sheets(spreadsheet, sheet_names[2], shareProfitLoss_data)
    print("Share Profit updated successfully")

    dailyProfitLoss_data = dailyProfitLoss_update_data(data.copy(deep=True))
    dailyProfitLoss_update_sheets(spreadsheet, sheet_names[3], dailyProfitLoss_data)
    print("Daily Profit updated successfully")