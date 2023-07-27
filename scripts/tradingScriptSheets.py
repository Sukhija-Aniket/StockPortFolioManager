import gspread
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import yfinance as yf

load_dotenv()
credentials_file = os.path.join(os.path.dirname(__file__),'tradingprojects-apiKey.json')
spreadsheet_id = os.getenv('SPREADSHEET_ID')

def authenticate_and_get_sheets():
    gc = gspread.service_account(filename=credentials_file)
    spreadsheet = gc.open_by_key(spreadsheet_id)
    return spreadsheet

def read_data_from_sheet(spreadsheet, sheet_name):
    sheet = spreadsheet.worksheet(sheet_name)
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def format_data(input_data):
    formatted_data = []
    for row in input_data:
        formatted_row = []
        for value in row:
            # Check if the value is a string and contains only numeric characters
            if isinstance(value, str) and value.isnumeric():
                formatted_value = int(value) if value.isdigit() else float(value)
            else:
                formatted_value = value
            formatted_row.append(formatted_value)
        formatted_data.append(formatted_row)
    return formatted_data

def isFloat(input_value):
    try:
        float_value = float(input_value)
        return True
    except ValueError:
        return False

def isFormatable(input_value):
    if isinstance(input_value,str) and input_value.isnumeric():
        return True
    return isFloat(input_value)

def isDateField(input_value):
    try:
        pd.to_datetime(input_value)
        return True
    except (ValueError, TypeError):
        return False
    except Exception as e:
        return False


def format_background(spreadsheet ,sheet, cell_range):
    requests = [{
        "updateCells": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": int(cell_range.split(':')[0][1:]) - 1,
                "endRowIndex": int(cell_range.split(':')[1][1:]),
                "startColumnIndex": ord(cell_range.split(':')[0][0].upper()) - 65,
                "endColumnIndex": ord(cell_range.split(':')[1][0].upper()) - 64,
            },
            "fields": "userEnteredFormat.backgroundColor",
        }
    }]
    spreadsheet.batch_update({"requests":requests})
    

def get_background_formatting_request(sheet, row_number, row_data, background_color):
    format_request = {
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": row_number - 1,
                "endRowIndex": row_number,
                "startColumnIndex": 0,
                "endColumnIndex": len(row_data)
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {
                        "red": background_color[0],
                        "green": background_color[1],
                        "blue": background_color[2]
                    }
                }
            },
            "fields": "userEnteredFormat.backgroundColor"
        }
    }
    return format_request

def display_and_format(sheet, data):
    data = data.round(4)
    try:
        data['Date'] = data['Date'].dt.strftime('%m/%d/%Y')
    except Exception as e:
        pass
    headers = data.columns.tolist() 
    data = data.values.tolist() 
    sheet.update('A1', [headers])
    sheet.insert_rows(data, 2)


    # Add formatting to headers
    num_columns = len(headers)
    header_range = f'A1:{chr(64 + num_columns)}1'
    sheet.format(header_range, {"textFormat": {"bold": True}})
    return sheet

def transDetailsUpdate(spreadsheet, sheet_name, data):
    sortList=['Name', 'Date', 'Transaction Type']
    sheet, data = initialize(spreadsheet, sheet_name, data, sortList=sortList)

    #  Add necessary columns to data
    data['STT'] = abs(data['Net Amount'] * 0.001)
    data['Transaction Charges'] = abs(data['Net Amount'] * 0.000035)
    data['GST'] = abs(0.18 * (data['Transaction Charges']))
    data['Stamp Charges'] = abs(0.00015 * data['Net Amount'])
    data['Final Amount'] = data['Net Amount'] + data['STT'] + data['Transaction Charges'] + data['GST'] + data['Stamp Charges']


    # display data on sheet and add formatting to headers
    sheet = display_and_format(sheet, data)

    # Add formatting to rows that have BUY/SELL Transaction Type
    worksheet_data = sheet.get_all_values()
    requests = []
    for row_number, row_data in  enumerate(worksheet_data[1:], start=2):
        transaction_type = row_data[4]
        if transaction_type == 'BUY':
            background_color = (0.8, 0.9, 1)
        else:
            background_color = (1, 0.8, 0.8)
        format_request = get_background_formatting_request(sheet, row_number, row_data, background_color)
        requests.append(format_request)
    if (len(requests)):
        spreadsheet.batch_update({"requests": requests})


def get_share_data():
    context = {
        'averageSalePrice': 0,
        'averageBuyPrice': 0,
        'averageBuyPriceOfSoldShares': 0,
        'numSharesSold': 0,
        'numSharesBought': 0,
        'numShares': 0,
        'date': datetime(2020,1,1),
        'currentInvestment': 0,
        'totalInvestment': 0,
    }
    return context

def get_daily_share_data():
    context = {}
    return context

def get_actual_stock_data(stock_name, function):
    STOCK_API_KEY = os.getenv('STOCK_API_KEY')
    url = f'https://www.alphavantage.co/query?function={function}&symbol={stock_name}&apikey={STOCK_API_KEY}&outputsize=full'
    output = []
    try:
        response = requests.get(url)
        data = response.json()
        if function == 'TIME_SERIES_DAILY':
            time_data = data['Time Series (Daily)']
            return time_data
        else:
            data = data['Global Quote']
            output = [data['02. open'], data['03. high'], data['04. low'], data['05. price']]
            return [float(x) for x in output]
    except Exception as e:
        print("Unable to get Share pricing details using Alpha-Vintage, Fallback to Yfinance API: ", e)
        data = get_details(datetime.now() - timedelta(days=1), stock_name)
        return data

def initialize(spreadsheet, sheet_name, data, extraCols=[], sortList=[]):
    sheet = spreadsheet.worksheet(sheet_name)
    sheet.clear() 
    format_background(spreadsheet, sheet, 'A2:N999')
    if len(extraCols) > 0:
        data = data.drop(extraCols,axis=1)
    
    for header in data.columns.tolist():
        if isFormatable(data[header].iloc[0]):
            data[header] = pd.to_numeric(data[header])
    data['Date'] = pd.to_datetime(data['Date'], format='%m/%d/%Y')
    
    if len(sortList) > 0:
        data = data.sort_values(by=sortList)
    return  sheet, data

def shareProfitLossUpdate(spreadsheet, sheet_name, data):
    
    extraCols = ['STT', 'GST', 'Transaction Charges', 'Stamp Charges']
    sheet, data = initialize(spreadsheet, sheet_name, data, extraCols)
    grouped_data = data.groupby(['Transaction Type', 'Name'])
    infoMap = {}
    rowData = {}
    df = pd.DataFrame(columns=['Date', 'Name', 'Average Buy Price', 'Average Sale Price', 'Average Cost of Sold Shares','Shares Bought', 'Shares Sold', 'Shares Remaining' ,'Profit Per Share', 'Net Profit', 'Total Investment', 'Current Investment', 'Closing Price', 'Holdings'])
    for (transaction_type, name), group in grouped_data:
        if name not in rowData:
            rowData[name] = get_share_data()
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
            rowData[name]['currentInvestment'] = currentInvestment

            
    for share_name, share_details in rowData.items():
        actualStockDetails = get_actual_stock_data(share_name,'GLOBAL_QUOTE')
        closing_price = 0
        if len(actualStockDetails) > 0:
            closing_price = actualStockDetails[3]
        # 'Date', 'Name', 'Average Buy Price', 'Average Sale Price', 'Average Cost of Sold Shares',
        # 'Shares Bought', 'Shares Sold', 'Shares Remaining' ,'Profit Per Share', 'Net Profit'
        new_row = pd.Series({
            'Date': share_details['date'].strftime('%m/%d/%Y'),
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

    # Now I will paste this data and do coloring as well when shares remaining is 0
    display_and_format(sheet, df)
    

    # Add formatting to headers
    
    # Add formatting for some  other purpose
    # Add formatting to rows that have BUY/SELL Transaction Type
    worksheet_data = sheet.get_all_values()
    requests = []
    for row_number, row_data in  enumerate(worksheet_data[1:], start=2):
        remaining_shares = int(row_data[7])
        profit = float(row_data[9])
        if remaining_shares == 0:
            if profit > 0:
                background_color = (0.8, 0.9, 1)
            else:
                background_color = (1, 0.8, 0.8)
            format_request = get_background_formatting_request(sheet,row_number, row_data, background_color)
            requests.append(format_request)
    if len(requests) > 0:
        spreadsheet.batch_update({"requests": requests})

def get_details(date, name):
    output = [0,0,0,0]
    try:
        data = yf.download(name, start=date,end=min(datetime.now(), date+timedelta(days=1)))
        output = [data['Open'].iloc[0], data['High'].iloc[0], data['Low'].iloc[0], data['Close'].iloc[0]]
        return [float(x) for x in output]
    except Exception as e:
        print("Encountered excpetion using yfinance API: ", e)
    return output

def dailyProfitLossUpdate(spreadsheet, sheet_name, data): 
    # For that Particular Day all shares bought on that day,
    # For that Particular Day all shares sold on that day,
    # Additional IntraDay Charge
    # Amount Invested is the total amount spend today --> in negative when selling shares + intraday cost 
    # date, name, average price ,num shares bought/sold, Intraday Cost, Amount Invested, opening price, high, low, closing price, daily Total Spendings

    extraCols = ['STT', 'GST', 'Transaction Charges', 'Stamp Charges']
    sheet, data = initialize(spreadsheet, sheet_name, data, extraCols)
    grouped_data = data.groupby(['Date', 'Name'])


    rowData = {}
    dailySpendings = {}
    df = pd.DataFrame(columns=['Date', 'Name', 'Average Price', 'Quantity', 'Amount Invested', 'Opening Price','High','Low','Closing Price', 'Daily Spendings'])
    for (date, name), group in grouped_data:
        if date not in dailySpendings:
            dailySpendings[date] = 0
        priceDetails = get_details(date, name)
        if date not in rowData:
            rowData[date] = get_daily_share_data()
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
            'Date': date.strftime('%m/%d/%Y'),
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
            'Date': date.strftime('%m/%d/%Y'),
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
    
    # Now I will paste this data and do coloring as well when shares remaining is 0
    display_and_format(sheet, df)

    # Add formatting to rows that have dailySpendings > 0
    worksheet_data = sheet.get_all_values()
    requests = []
    for row_number, row_data in  enumerate(worksheet_data[1:], start=2):
        if row_data[9] != "":
            background_color = (0.8, 0.9, 1)
            format_request = get_background_formatting_request(sheet,row_number, row_data, background_color)
            requests.append(format_request)
    if (len(requests)):
        spreadsheet.batch_update({"requests": requests})

if __name__ == "__main__":
    spreadsheet = authenticate_and_get_sheets()
    worksheets = spreadsheet.worksheets()
    sheet_names = [worksheet.title for worksheet in worksheets]
    input_data = read_data_from_sheet(spreadsheet, sheet_names[0])
    print("Raw Input Data read successfully")
    transDetailsUpdate(spreadsheet, sheet_names[1], input_data.copy(deep=True))
    print("Transaction Details updated successfully")
    data = read_data_from_sheet(spreadsheet, sheet_names[1])
    print("Transaction Details Data read successfully")
    shareProfitLossUpdate(spreadsheet, sheet_names[2], data.copy(deep=True))
    print("Share Profit updated successfully")
    dailyProfitLossUpdate(spreadsheet, sheet_names[3], data.copy(deep=True))
    print("Daily Profit updated successfully")