import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple
from stock_portfolio_shared.constants.general_constants import BUY, SELL
from stock_portfolio_shared.constants.trans_details_constants import TransDetails_constants
from stock_portfolio_shared.constants.raw_constants import Raw_constants
from stock_portfolio_shared.constants.share_profit_loss_constants import ShareProfitLoss_constants
from stock_portfolio_shared.constants.daily_profit_loss_constants import DailyProfitLoss_constants
from stock_portfolio_shared.constants.taxation_constants import Taxation_constants
from stock_portfolio_shared.models.depository_participant import DepositoryParticipant
from config.config import Config
from helper.market_data_helper import MarketDataHelper
from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from stock_portfolio_shared.utils.excel_manager import ExcelManager
from stock_portfolio_shared.utils.data_processor import DataProcessor
from utils.calculation_utils import (
    calculate_exchange_transaction_charges, calculate_gst, calculate_stt, calculate_sebi_transaction_charges, calculate_brokerage,
    calculate_stamp_duty, calculate_dp_charges, calculate_average_cost_of_sold_shares,
    is_long_term, update_intraday_count, convert_dtypes, update_transaction_type,
    get_financial_year
)

from config.logging_config import setup_logging
logger = setup_logging(__name__)

class DataProcessingService:
    """Service for data processing and transformation"""
    
    def __init__(self) -> None:
        self.config = Config()
        self.market_data_helper = MarketDataHelper()
        self.sheets_manager = SheetsManager()
        self.excel_manager = ExcelManager()
    
    
    def initialize_data(self, data: pd.DataFrame, extra_cols: Optional[List[str]] = None, sort_list: Optional[List[str]] = None) -> pd.DataFrame:
        """Initialize data with extra columns and sorting"""
        try:
            if extra_cols:
                for col in extra_cols:
                    if col not in data.columns:
                        data[col] = 0
            
            if sort_list:
                data = data.sort_values(by=sort_list)
            
            return data
        except Exception as e:
            logger.error(f"Error initializing data: {e}")
            raise
    
    def process_transaction_details(self, data: pd.DataFrame, participant_name: str = "zerodha") -> pd.DataFrame:
        """Process transaction details data with participant-specific calculations"""
        try:
            # Ensure numeric columns are properly converted using DataProcessor.safe_numeric
            data[Raw_constants.QUANTITY] = data[Raw_constants.QUANTITY].apply(DataProcessor.safe_numeric)
            data[Raw_constants.NET_AMOUNT] = data[Raw_constants.NET_AMOUNT].apply(DataProcessor.safe_numeric)
            data[Raw_constants.PRICE] = data[Raw_constants.PRICE].apply(DataProcessor.safe_numeric)
            
            # Update transaction types
            data[TransDetails_constants.TRANSACTION_TYPE] = data[TransDetails_constants.QUANTITY].apply(
                lambda x: update_transaction_type(x)
            )
            
            # Sort data
            sort_list = [Raw_constants.NAME, Raw_constants.DATE, TransDetails_constants.TRANSACTION_TYPE]
            data = self.initialize_data(data, sort_list=sort_list)
            
            # Update intraday count
            data = update_intraday_count(data)
            
            # Create a shared dp_data dictionary to track DP charges per name/date combination
            dp_data: Dict[str, Dict[str, float]] = {}
            
            # Calculate charges with participant-specific rates
            data[TransDetails_constants.STT] = data.apply(
                lambda row: calculate_stt(row, participant_name), axis=1
            )
            data[TransDetails_constants.SEBI_TRANSACTION_CHARGES] = data.apply(
                lambda row: calculate_sebi_transaction_charges(row, participant_name), axis=1
            )
            data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES] = data.apply(
                lambda row: calculate_exchange_transaction_charges(row, participant_name), axis=1
            )
            data[TransDetails_constants.BROKERAGE] = data.apply(
                lambda row: calculate_brokerage(row, participant_name), axis=1
            )
            data[TransDetails_constants.STAMP_DUTY] = data.apply(
                lambda row: calculate_stamp_duty(row, participant_name), axis=1
            )
            data[TransDetails_constants.DP_CHARGES] = data.apply(
                lambda row: calculate_dp_charges(row, dp_data, participant_name), axis=1
            )
            data[TransDetails_constants.GST] = data.apply(
                lambda row: calculate_gst(row, participant_name), axis=1
            )
            
            # Calculate final amount
            data[TransDetails_constants.FINAL_AMOUNT] = (
                data[TransDetails_constants.NET_AMOUNT] + 
                data[TransDetails_constants.STT] + 
                data[TransDetails_constants.SEBI_TRANSACTION_CHARGES] + 
                data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES] + 
                data[TransDetails_constants.STAMP_DUTY] + 
                data[TransDetails_constants.DP_CHARGES] + 
                data[TransDetails_constants.BROKERAGE] +
                data[TransDetails_constants.GST]
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Error processing transaction details for {participant_name}: {e}")
            raise
        
        
    def get_spl_row(self) -> Dict[str, Union[str, float]]:
        """Get default Share Profit Loss row"""
        return {
            ShareProfitLoss_constants.DATE: self.config.DEFAULT_DATE,
            ShareProfitLoss_constants.AVERAGE_BUY_PRICE: 0.0,
            ShareProfitLoss_constants.AVERAGE_SALE_PRICE: 0.0,
            ShareProfitLoss_constants.AVERAGE_COST_OF_SOLD_SHARES: 0.0,
            ShareProfitLoss_constants.SHARES_BOUGHT: 0.0,
            ShareProfitLoss_constants.SHARES_SOLD: 0.0,
            ShareProfitLoss_constants.TOTAL_INVESTMENT: 0.0,
            ShareProfitLoss_constants.CURRENT_INVESTMENT: 0.0
        }
        
    def _get_current_price(self, share_name: str) -> float:
        """Get current stock price for a given share"""
        return self.market_data_helper.get_current_stock_price(share_name)
    
    def process_share_profit_loss(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process share profit loss data"""
        try:
            logger.info("Processing Share Profit Loss Data")
            
            # Initialize data with extra columns
            extra_cols = [
                TransDetails_constants.STT, TransDetails_constants.GST, 
                TransDetails_constants.SEBI_TRANSACTION_CHARGES,
                TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES, 
                TransDetails_constants.BROKERAGE, TransDetails_constants.STAMP_DUTY, 
                TransDetails_constants.DP_CHARGES, TransDetails_constants.INTRADAY_COUNT, 
                TransDetails_constants.STOCK_EXCHANGE
            ]
            data = self.initialize_data(data, extra_cols=extra_cols)
            
            # Group by transaction type and name
            grouped_data = data.groupby([TransDetails_constants.TRANSACTION_TYPE, Raw_constants.NAME])
            
            info_map: Dict[str, Dict[str, pd.DataFrame]] = {}
            row_data: Dict[str, Dict[str, Union[str, float]]] = {}
            
            # Create DataFrame with ShareProfitLoss constants
            constants_dict = {key: value for key, value in ShareProfitLoss_constants.__dict__.items() 
                            if not key.startswith('__')}
            df = pd.DataFrame(columns=list(constants_dict.values()))
            
            for (transaction_type, name), group in grouped_data:
                if name not in row_data:
                    row_data[name] = self.get_spl_row()
                    info_map[name] = {}
                
                # Process transactions - pass the DataFrame group directly instead of converting to list
                info_map[name][transaction_type] = group
                
                if transaction_type == self.config.SELL:
                    self._process_sell_transactions(info_map[name], row_data[name])
                else:
                    self._process_buy_transactions(info_map[name], row_data[name])
            
            # Collect all unique stock names for batch current price fetching
            stock_names = list(row_data.keys())
            logger.info(f"Batch fetching current prices for {len(stock_names)} stocks")
            batch_current_prices = self.market_data_helper.batch_get_current_prices(stock_names)
            
            # Create final DataFrame
            for share_name, share_details in row_data.items():
                # Get current stock price from batch results
                current_price = batch_current_prices.get(share_name, 0.0)
                
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
                    ShareProfitLoss_constants.CLOSING_PRICE: current_price,
                    ShareProfitLoss_constants.HOLDINGS: current_price * (share_details[ShareProfitLoss_constants.SHARES_BOUGHT] - share_details[ShareProfitLoss_constants.SHARES_SOLD])
                })
                df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
            
            return convert_dtypes(df)
            
        except Exception as e:
            logger.error(f"Error processing share profit loss: {e}")
            raise
    
    def _process_sell_transactions(self, transactions: Dict[str, pd.DataFrame], row_data: Dict[str, Union[str, float]]) -> None:
        """Process sell transactions"""
        logger.info(f"Processing sell transactions")
        average_sale_price = 0.0
        num_shares_sold = 0.0
        current_investment = 0.0
        
        # Process each row in the DataFrame group
        for _, transaction in transactions[self.config.SELL].iterrows():
            # Access data using proper column names
            try:
                net_amount = DataProcessor.safe_numeric(transaction[TransDetails_constants.FINAL_AMOUNT])
                quantity = DataProcessor.safe_numeric(transaction[TransDetails_constants.QUANTITY])
            except (ValueError, TypeError):
                net_amount = 0.0
                quantity = 0.0
                logger.warning(f"Invalid transaction data: {transaction}")
            
            if abs(num_shares_sold - quantity) >= 0.01:
                average_sale_price = (average_sale_price * num_shares_sold - net_amount) / (num_shares_sold - quantity)
            num_shares_sold -= quantity
            current_investment += net_amount
        
        if self.config.BUY in transactions:
            for _, transaction in transactions[self.config.BUY].iterrows():
                try:
                    net_amount = DataProcessor.safe_numeric(transaction[TransDetails_constants.FINAL_AMOUNT])
                except (ValueError, TypeError):
                    net_amount = 0.0
                current_investment += net_amount
        
        average_cost_of_sold_shares = calculate_average_cost_of_sold_shares(transactions)
        
        row_data[ShareProfitLoss_constants.AVERAGE_SALE_PRICE] = average_sale_price
        row_data[ShareProfitLoss_constants.SHARES_SOLD] = num_shares_sold
        row_data[ShareProfitLoss_constants.AVERAGE_COST_OF_SOLD_SHARES] = average_cost_of_sold_shares
        row_data[ShareProfitLoss_constants.CURRENT_INVESTMENT] = current_investment
    
    def _process_buy_transactions(self, transactions: Dict[str, pd.DataFrame], row_data: Dict[str, Union[str, float]]) -> None:
        """Process buy transactions"""
        logger.info(f"Processing buy transactions")
        average_buy_price = 0.0
        num_shares_bought = 0.0
        current_investment = 0.0
        total_investment = 0.0
        
        # Process each row in the DataFrame group
        for _, transaction in transactions[self.config.BUY].iterrows():
            try:
                net_amount = DataProcessor.safe_numeric(transaction[TransDetails_constants.FINAL_AMOUNT])
                quantity = DataProcessor.safe_numeric(transaction[TransDetails_constants.QUANTITY])
            except (ValueError, TypeError):
                net_amount = 0.0
                quantity = 0.0
                logger.warning(f"Invalid transaction data: {transaction}")
            
            if abs(num_shares_bought + quantity) >= 0.01:
                average_buy_price = (average_buy_price * num_shares_bought + net_amount) / (num_shares_bought + quantity)
            num_shares_bought += quantity
            current_investment += net_amount
            total_investment += net_amount
        
        row_data[ShareProfitLoss_constants.AVERAGE_BUY_PRICE] = average_buy_price
        row_data[ShareProfitLoss_constants.SHARES_BOUGHT] = num_shares_bought
        row_data[ShareProfitLoss_constants.TOTAL_INVESTMENT] = total_investment
        row_data[ShareProfitLoss_constants.CURRENT_INVESTMENT] = current_investment

    def _get_stock_price(self, date: datetime, name: str) -> List[float]:
        """Get stock price details for a given date and stock name"""
        return self.market_data_helper.get_stock_price_details(date, name)
    
    def get_market_data_cache_stats(self) -> Dict:
        """Get market data cache statistics"""
        return self.market_data_helper.get_cache_stats()
    
    def clear_market_data_cache(self) -> None:
        """Clear market data cache"""
        self.market_data_helper.clear_cache()
        logger.info("Market data cache cleared")

    def process_daily_profit_loss(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process daily profit loss data"""
        try:
            logger.info("Processing Daily Profit Loss Data")
            
            # Initialize data with extra columns
            extra_cols = [
                TransDetails_constants.STT, TransDetails_constants.GST, 
                TransDetails_constants.SEBI_TRANSACTION_CHARGES,
                TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES, 
                TransDetails_constants.BROKERAGE, TransDetails_constants.STAMP_DUTY, 
                TransDetails_constants.DP_CHARGES, TransDetails_constants.STOCK_EXCHANGE, 
                TransDetails_constants.INTRADAY_COUNT
            ]
            data = self.initialize_data(data, extra_cols=extra_cols)
            
            # Convert date for sorting
            data[Raw_constants.DATE] = pd.to_datetime(data[Raw_constants.DATE], format=self.config.DATA_TIME_FORMAT)
            grouped_data = data.groupby([Raw_constants.DATE, Raw_constants.NAME])

            row_data: Dict[str, Dict[str, Dict[str, Union[str, float]]]] = {}
            daily_spendings: Dict[str, float] = {}
            
            # Create DataFrame with DailyProfitLoss constants
            constants_dict = {key: value for key, value in DailyProfitLoss_constants.__dict__.items() 
                             if not key.startswith('__')}
            df = pd.DataFrame(columns=list(constants_dict.values()))
            
            # Collect all unique stock-date combinations for batch API calls
            stock_dates = []
            for (date, name), group in grouped_data:
                stock_dates.append((name, date))
            
            # Batch fetch all stock prices
            logger.info(f"Batch fetching prices for {len(stock_dates)} stock-date combinations")
            batch_prices = self.market_data_helper.batch_get_stock_prices(stock_dates)
            
            for (date, name), group in grouped_data:
                date_str = date.strftime(self.config.DATA_TIME_FORMAT)
                if date_str not in daily_spendings:
                    daily_spendings[date_str] = 0.0
                    row_data[date_str] = {}
                
                # Get price details from batch results
                price_details = batch_prices.get((name, date), [])
                
                average_price = 0.0
                quantity = 0.0
                amount_invested = 0.0
                
                for _, transaction in group.iterrows():
                    average_price = (average_price * quantity + transaction[TransDetails_constants.FINAL_AMOUNT]) / (quantity + abs(transaction[TransDetails_constants.QUANTITY]))
                    quantity += abs(transaction[TransDetails_constants.QUANTITY])
                    amount_invested += transaction[TransDetails_constants.FINAL_AMOUNT]
                    daily_spendings[date_str] += transaction[TransDetails_constants.FINAL_AMOUNT]
                
                # Create row data
                row_data[date_str][name] = {
                    DailyProfitLoss_constants.DATE: date_str,
                    DailyProfitLoss_constants.NAME: name,
                    DailyProfitLoss_constants.AVERAGE_PRICE: average_price,
                    DailyProfitLoss_constants.QUANTITY: quantity,
                    DailyProfitLoss_constants.AMOUNT_INVESTED: amount_invested,
                    DailyProfitLoss_constants.OPENING_PRICE: price_details[2] if len(price_details) > 2 else 0.0,
                    DailyProfitLoss_constants.HIGH: price_details[3] if len(price_details) > 3 else 0.0,
                    DailyProfitLoss_constants.LOW: price_details[4] if len(price_details) > 4 else 0.0,
                    DailyProfitLoss_constants.CLOSING_PRICE: price_details[5] if len(price_details) > 5 else 0.0,
                    DailyProfitLoss_constants.VOLUME: price_details[6] if len(price_details) > 6 else 0.0,
                    DailyProfitLoss_constants.DAILY_SPENDINGS: 0.0
                }
                
                row_data[date_str]['daily_spendings'] = daily_spendings[date_str]
            
            # Create final DataFrame
            for date, stocks in row_data.items():
                for key, value in stocks.items():
                    if key == 'daily_spendings':
                        continue
                    new_row = pd.Series(value)
                    df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
                new_row = pd.Series({
                    DailyProfitLoss_constants.DATE: date,
                    DailyProfitLoss_constants.NAME: '',
                    DailyProfitLoss_constants.AVERAGE_PRICE: 0.0,
                    DailyProfitLoss_constants.QUANTITY: 0.0,
                    DailyProfitLoss_constants.AMOUNT_INVESTED: 0.0,
                    DailyProfitLoss_constants.OPENING_PRICE: 0.0,
                    DailyProfitLoss_constants.HIGH: 0.0,
                    DailyProfitLoss_constants.LOW: 0.0,
                    DailyProfitLoss_constants.CLOSING_PRICE: 0.0,
                    DailyProfitLoss_constants.VOLUME: 0.0,
                    DailyProfitLoss_constants.DAILY_SPENDINGS: stocks['daily_spendings']
                })
                df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
            
            return convert_dtypes(df)
            
        except Exception as e:
            logger.error(f"Error processing daily profit loss: {e}")
            raise
        
    def get_taxation_row(self) -> Dict[str, float]:
        """Get default Taxation row"""
        return {
            Taxation_constants.LTCG: 0.0,
            Taxation_constants.STCG: 0.0,
            Taxation_constants.INTRADAY_INCOME: 0.0,
            Taxation_constants.TOTAL_GAINS: 0.0
        }

    def process_taxation(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process taxation data"""
        try:
            logger.info("Processing Taxation Data")
            
            # Initialize data with extra columns
            extra_cols = [
                TransDetails_constants.STT, TransDetails_constants.GST, 
                TransDetails_constants.SEBI_TRANSACTION_CHARGES,
                TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES, 
                TransDetails_constants.BROKERAGE, TransDetails_constants.STAMP_DUTY, 
                TransDetails_constants.DP_CHARGES, TransDetails_constants.STOCK_EXCHANGE, 
                TransDetails_constants.INTRADAY_COUNT
            ]
            data = self.initialize_data(data, extra_cols=extra_cols, sort_list=[Raw_constants.DATE, Raw_constants.NAME, TransDetails_constants.TRANSACTION_TYPE])
            
            # Group by transaction type, name and date
            grouped_data = data.groupby([TransDetails_constants.TRANSACTION_TYPE, Raw_constants.NAME, Raw_constants.DATE])
            
            infoMap: Dict[str, Dict[str, pd.DataFrame]] = {}
            rowData: Dict[str, Dict[str, Dict[str, float]]] = {}
            intraMap: Dict[str, Dict[str, float]] = {}
            intraMapList: Dict[str, Dict[str, List[float]]] = {}
            global_buy_data: Dict[str, List[List[Union[str, float]]]] = {}
            global_sell_data: Dict[str, List[List[Union[str, float]]]] = {}
            
            # Create DataFrame with Taxation constants
            constants_dict = {key: value for key, value in Taxation_constants.__dict__.items() 
                             if not key.startswith('__')}
            df = pd.DataFrame(columns=list(constants_dict.values()))
            
            # Firstly find the intraday transactions and the profit on those transactions
            for (transaction_type, name, date), group in grouped_data:
                if name not in infoMap:
                    infoMap[name] = {}
                    rowData[name] = {}
                    intraMap[name] = {}
                    intraMapList[name] = {}
                if date not in infoMap[name]:
                    infoMap[name][date] = {}
                if get_financial_year(date) not in rowData[name]:
                    rowData[name][get_financial_year(date)] = self.get_taxation_row()
                    # rowData[name][Taxation_constants.DATE] = max(rowData[name][Taxation_constants.DATE], date)
                if transaction_type not in infoMap[name][date]:
                    infoMap[name][date][transaction_type] = group
                    if transaction_type == BUY:
                        if name not in global_buy_data:
                            global_buy_data[name] = []
                        for _, transaction in group.iterrows():
                            global_buy_data[name].append([
                                transaction[Raw_constants.DATE], 
                                transaction[Raw_constants.QUANTITY], 
                                transaction[Raw_constants.NET_AMOUNT]
                            ])
                    else:
                        if name not in global_sell_data:
                            global_sell_data[name] = []
                        for _, transaction in group.iterrows():
                            global_sell_data[name].append([
                                transaction[Raw_constants.DATE], 
                                abs(transaction[Raw_constants.QUANTITY]), 
                                abs(transaction[Raw_constants.NET_AMOUNT])
                            ])
                
                if transaction_type == SELL:
                    buyData: List[List[float]] = []
                    sellData: List[List[float]] = []
                    
                    if BUY in infoMap[name][date]:
                        intraMap[name][date] = 0.0
                        intraMapList[name][date] = [0.0, 0.0]
                        
                        # Process buy transactions
                        for _, transaction in infoMap[name][date][BUY].iterrows():
                            buyData.append([
                                transaction[Raw_constants.QUANTITY], 
                                transaction[Raw_constants.NET_AMOUNT]
                            ])
                        
                        # Process sell transactions
                        for _, transaction in infoMap[name][date][transaction_type].iterrows():
                            sellData.append([
                                abs(transaction[Raw_constants.QUANTITY]), 
                                abs(transaction[Raw_constants.NET_AMOUNT])
                            ])
                            
                        i, j = 0, 0
                        while i < len(buyData) and j < len(sellData):
                            buyCnt = buyData[i][0]
                            sellCnt = sellData[j][0]
                            if buyCnt > sellCnt:
                                # used - (buy - sell)
                                rowData[name][get_financial_year(date)][Taxation_constants.INTRADAY_INCOME] -= sellCnt * (buyData[i][1]/buyCnt - sellData[j][1]/sellCnt)
                                intraMap[name][date] += sellCnt
                                buyData[i][1] = (buyData[i][0] - sellCnt) * (buyData[i][1]/buyData[i][0])
                                buyData[i][0] -= sellCnt
                                sellData[j][1] = 0
                                sellData[j][0] = 0
                                j += 1
                            elif sellCnt > buyCnt:
                                rowData[name][get_financial_year(date)][Taxation_constants.INTRADAY_INCOME] -= buyCnt * (buyData[i][1]/buyCnt - sellData[j][1]/sellCnt)
                                intraMap[name][date] += buyCnt
                                sellData[j][1] = (sellData[j][0] - buyCnt) * (sellData[j][1]/sellData[j][0])
                                sellData[j][0] -= buyCnt
                                buyData[i][1] = 0
                                buyData[i][0] = 0
                                i += 1
                            else:
                                rowData[name][get_financial_year(date)][Taxation_constants.INTRADAY_INCOME] -= buyCnt * (buyData[i][1]/buyCnt - sellData[j][1]/sellCnt)
                                intraMap[name][date] += buyCnt
                                sellData[j][1] = 0
                                sellData[j][0] = 0
                                buyData[i][1] = 0
                                buyData[i][0] = 0
                                i += 1
                                j += 1
                        temp = intraMap[name][date]
                        intraMapList[name][date] = [temp, temp] 
                        
            
            # Writing algorithm to find the long term and short term capital gains
            for name in infoMap.keys():
                # Firstly I am reducing the intraday things, 
                i, j = 0, 0
                while i < len(global_buy_data[name]):
                    buyDetails = global_buy_data[name][i]
                    if buyDetails[0] in intraMapList[name]:
                        tempval = min(buyDetails[1], intraMapList[name][buyDetails[0]][0])
                        buyDetails[2] = (buyDetails[1] - tempval) * (buyDetails[2]/buyDetails[1])
                        buyDetails[1] -= tempval
                        global_buy_data[name][i] = buyDetails
                        intraMapList[name][buyDetails[0]][0] -= tempval
                    i += 1
                while name in global_sell_data and j < len(global_sell_data[name]):
                    sellDetails = global_sell_data[name][j]
                    if sellDetails[0] in intraMapList[name]:
                        tempval = min(sellDetails[1], intraMapList[name][sellDetails[0]][1])
                        sellDetails[2] = (sellDetails[1] - tempval) * (sellDetails[2]/ sellDetails[1])
                        sellDetails[1] -= tempval
                        global_sell_data[name][j] = sellDetails
                        intraMapList[name][sellDetails[0]][1] -= tempval
                    j += 1
                    
                # Now I will iterate again to find the LTCG and STCG for those stocks
                i, j = 0, 0
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
                    if is_long_term(buyDetails[0], sellDetails[0]):
                        # used - (buy - sell)
                        rowData[name][get_financial_year(sellDetails[0])][Taxation_constants.LTCG] -= (tempval * (buyDetails[2]/buyDetails[1]) - tempval * (sellDetails[2]/sellDetails[1]))
                    else:
                        # used - (buy - sell)
                        rowData[name][get_financial_year(sellDetails[0])][Taxation_constants.STCG] -= (tempval * (buyDetails[2]/buyDetails[1]) - tempval * (sellDetails[2]/sellDetails[1]))
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
            
            # Finally forming the answer
            for name, fy_details in rowData.items():
                for fy, details in fy_details.items():
                    new_row = pd.Series({
                        Taxation_constants.NAME: name,
                        Taxation_constants.FINANCIAL_YEAR: fy,
                        Taxation_constants.LTCG: details[Taxation_constants.LTCG],
                        Taxation_constants.STCG: details[Taxation_constants.STCG],
                        Taxation_constants.INTRADAY_INCOME: details[Taxation_constants.INTRADAY_INCOME],
                        Taxation_constants.TOTAL_GAINS: details[Taxation_constants.LTCG] + details[Taxation_constants.STCG] + details[Taxation_constants.INTRADAY_INCOME]
                    })
                    df = pd.concat([df, new_row.to_frame().T], ignore_index=True) 
            return convert_dtypes(df) 
            
        except Exception as e:
            logger.error(f"Error processing taxation: {e}")
            raise 