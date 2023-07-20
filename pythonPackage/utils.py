import pandas as pd
import openpyxl
import gspread, requests, os
import yfinance as yf
from datetime import datetime, timedelta

def read_data_from_sheets(spreadsheet, sheet_name):
    sheet = spreadsheet.worksheet(sheet_name)
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def read_data_from_excel(spreadsheet_file, sheet_name):
    df = pd.read_excel(spreadsheet_file, sheet_name=sheet_name)
    return df

def format_background_sheets(spreadsheet ,sheet, cell_range):
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

def format_background_excel(sheet, cell_range):
    for row in sheet[cell_range]:
        for cell in row:
            cell.fill = openpyxl.styles.PatternFill(fill_type=None)

def authenticate_and_get_sheets(credentials_file, spreadsheet_id):
    gc = gspread.service_account(filename=credentials_file)
    spreadsheet = gc.open_by_key(spreadsheet_id)
    return spreadsheet

def is_float(input_value):
    try:
        float(input_value)
        return True
    except ValueError:
        return False

def is_formatable(input_value):
    if isinstance(input_value,str) and input_value.isnumeric():
        return True
    return is_float(input_value)

def get_backgroundColor_formatting_request(sheet, row_number, row_data, background_color):
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

def display_and_format_sheets(sheet, data):
    headers = data.columns.tolist() 
    data = data.values.tolist() 

    sheet.update('A1', [headers])
    sheet.insert_rows(data, 2)
    
    # Add formatting to headers
    num_columns = len(headers)
    header_range = f'A1:{chr(64 + num_columns)}1'
    sheet.format(header_range, {"textFormat": {"bold": True}})

def display_and_format_excel(sheet, data):
    data = data.round(4)
    try:
        data['Date'] = data['Date'].dt.strftime('%m/%d/%Y')
    except Exception as e:
        pass
    headers = data.columns.tolist() 
    data = data.values.tolist() 
    sheet.append(headers)
    for row in data:
        sheet.append(row)
    for cell in sheet['1']:
        cell.font = openpyxl.styles.Font(bold=True)

def get_spl_row():
    context = {
        'averageSalePrice': 0,
        'averageBuyPrice': 0,
        'averageBuyPriceOfSoldShares': 0,
        'numSharesSold': 0,
        'numSharesBought': 0,
        'numShares': 0,
        'date': '01/01/2020',
        'currentInvestment': 0,
        'totalInvestment': 0,
    }
    return context

def get_prizing_details_yfinance(date, name):
    output = [0,0,0,0]
    try:
        data = yf.download(name, start=date,end=min(datetime.now(), date+timedelta(days=1)))
        output = [data['Open'].iloc[0], data['High'].iloc[0], data['Low'].iloc[0], data['Close'].iloc[0]]
        return [float(x) for x in output]
    except Exception as e:
        print("Encountered excpetion using yfinance API: ", e)
    return output

def get_prizing_details_alphaVintage(stock_name, function):
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
        data = get_prizing_details_yfinance(datetime.now() - timedelta(days=1), stock_name)
        return data
    

def initialize_data(data, extraCols=[], sortList=[]):
    if len(extraCols) > 0:
        data = data.drop(extraCols,axis=1)
    
    for header in data.columns.tolist():
        if is_formatable(data[header].iloc[0]):
            data[header] = pd.to_numeric(data[header])
    data['Date'] = pd.to_datetime(data['Date'], format='%m/%d/%Y')
    
    if len(sortList) > 0:
        data.sort_values(by=sortList, inplace=True)
    data = data.round(4)
    try:
        data['Date'] = data['Date'].dt.strftime('%m/%d/%Y')
    except Exception as e:
        pass
    return data


def initialize_sheets(spreadsheet, sheet_name):
    sheet = spreadsheet.worksheet(sheet_name)
    sheet.clear() 
    format_background_sheets(spreadsheet, sheet, 'A2:N999')    
    return sheet

def initialize_excel(spreadsheet, sheet_name):
    sheet = spreadsheet[sheet_name]
    sheet.clear()
    format_background_excel(sheet, 'A2:N999')
    return sheet

def transDetails_formatting_sheets(spreadsheet, sheet):
    worksheet_data = sheet.get_all_values()
    requests = []
    for row_number, row_data in  enumerate(worksheet_data[1:], start=2):
        transaction_type = row_data[4]
        if transaction_type == 'BUY':
            background_color = (0.8, 0.9, 1)
        else:
            background_color = (1, 0.8, 0.8)
        format_request = get_backgroundColor_formatting_request(sheet, row_number, row_data, background_color)
        requests.append(format_request)
    if len(requests) > 0:
        spreadsheet.batch_update({"requests": requests})

def transDetails_formatting_excel(sheet):
    cell_range = 'A2:N999'
    redFill = openpyxl.styles.PatternFill(start_color='FFFF0000', end_color='FFFF0000', fill_type='solid')
    blueFill = openpyxl.styles.PatternFill(start_color='FF0000FF', end_color='FF0000FF', fill_type='solid')
    for row in sheet[cell_range]:
        if row[0].value is None or row[0].value == '':
            break
        if row[4].value == 'BUY':
            for cell in row:
                cell.fill = blueFill
        elif row[4].value == 'SELL':
            for cell in row:
                cell.fill = redFill
        

def shareProfitLoss_formatting_sheets(spreadsheet, sheet):
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
            format_request = get_backgroundColor_formatting_request(sheet,row_number, row_data, background_color)
            requests.append(format_request)
    if len(requests) > 0:
        spreadsheet.batch_update({"requests": requests})
    
def shareProfitLoss_formatting_excel(sheet):
    cell_range = 'A2:N999'
    redFill = openpyxl.styles.PatternFill(start_color='FFFF0000', end_color='FFFF0000', fill_type='solid')
    blueFill = openpyxl.styles.PatternFill(start_color='FF0000FF', end_color='FF0000FF', fill_type='solid')
    for row in sheet[cell_range]:
        if row[0].value is None or row[0].value == '':
            break
        remaining_shares = int(row[7].value)
        profit = float(row[9].value)
        if remaining_shares == 0:
            if profit >= 0.0:
                for cell in row:
                    cell.fill = blueFill
            else:
                for cell in row:
                    cell.fill = redFill

def dailyProfitLoss_formatting_sheets(spreadsheet, sheet):
    worksheet_data = sheet.get_all_values()
    requests = []
    for row_number, row_data in  enumerate(worksheet_data[1:], start=2):
        if row_data[9] != "":
            if float(row_data[9]) > 0.0:
                background_color = (0.8, 0.9, 1)
            else:
                background_color = (1, 0.8, 0.8)
            format_request = get_backgroundColor_formatting_request(sheet,row_number, row_data, background_color)
            requests.append(format_request)
    if len(requests) > 0:
        spreadsheet.batch_update({"requests": requests})

def dailyProfitLoss_formatting_excel(sheet):
    cell_range = 'A2:N999'
    redFill = openpyxl.styles.PatternFill(start_color='FFFF0000', end_color='FFFF0000', fill_type='solid')
    blueFill = openpyxl.styles.PatternFill(start_color='FF0000FF', end_color='FF0000FF', fill_type='solid')
    for row in sheet[cell_range]:
        if row[0].value is None or row[0].value == '':
            break
        if row[9].value != '':
            if float(row[9].value) > 0.0:
                for cell in row:
                    cell.fill = blueFill
            else :
                for cell in row:
                    cell.fill = redFill