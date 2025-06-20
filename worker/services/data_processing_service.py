import pandas as pd
import logging
from datetime import datetime
from models.constants import TransDetails_constants, Raw_constants, ShareProfitLoss_constants
from config import Config
from services.calculation_service import CalculationService
from services.market_data_service import MarketDataService
from services.formatting_service import FormattingService
from stock_portfolio_shared.utils.sheets import SheetsManager
from stock_portfolio_shared.utils.excel import ExcelManager

logger = logging.getLogger(__name__)

class DataProcessingService:
    """Service for data processing and transformation"""
    
    def __init__(self):
        self.config = Config()
        self.calculation_service = CalculationService()
        self.market_data_service = MarketDataService()
        self.formatting_service = FormattingService()
        self.sheets_manager = SheetsManager()
        self.excel_manager = ExcelManager()
    
    def _safe_numeric_conversion(self, data, column):
        """Safely convert column to numeric values"""
        try:
            return pd.to_numeric(data[column], errors='coerce').fillna(0)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert {column} to numeric, using 0")
            return pd.Series([0] * len(data))
    
    def process_transaction_details(self, data):
        """Process transaction details data"""
        try:
            # Ensure numeric columns are properly converted
            data[TransDetails_constants.QUANTITY] = self._safe_numeric_conversion(data, TransDetails_constants.QUANTITY)
            data[TransDetails_constants.NET_AMOUNT] = self._safe_numeric_conversion(data, TransDetails_constants.NET_AMOUNT)
            
            # Update transaction types
            data[TransDetails_constants.TRANSACTION_TYPE] = data[TransDetails_constants.QUANTITY].apply(
                lambda x: self.formatting_service._update_transaction_type(x)
            )
            
            # Sort data
            sort_list = [Raw_constants.NAME, Raw_constants.DATE, TransDetails_constants.TRANSACTION_TYPE]
            data = self.formatting_service.initialize_data(data, sort_list=sort_list)
            
            # Update intraday count
            data = self.calculation_service.update_intraday_count(data)
            
            # Calculate charges
            data[TransDetails_constants.STT] = data.apply(self.calculation_service.calculate_stt, axis=1)
            data[TransDetails_constants.SEBI_TRANSACTION_CHARGES] = data.apply(
                self.calculation_service.calculate_transaction_charges, axis=1
            )
            data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES] = abs(
                data[TransDetails_constants.NET_AMOUNT] * 0.000001
            )
            data[TransDetails_constants.BROKERAGE] = data.apply(
                self.calculation_service.calculate_brokerage, axis=1
            )
            data[TransDetails_constants.GST] = abs(
                0.18 * (data[TransDetails_constants.BROKERAGE] + 
                       data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES] + 
                       data[TransDetails_constants.SEBI_TRANSACTION_CHARGES])
            )
            data[TransDetails_constants.STAMP_DUTY] = data.apply(
                self.calculation_service.calculate_stamp_duty, axis=1
            )
            data[TransDetails_constants.DP_CHARGES] = data.apply(
                self.calculation_service.calculate_dp_charges, axis=1, args=({},)
            )
            
            # Calculate final amount
            data[TransDetails_constants.FINAL_AMOUNT] = (
                data[TransDetails_constants.NET_AMOUNT] + 
                data[TransDetails_constants.STT] + 
                data[TransDetails_constants.SEBI_TRANSACTION_CHARGES] + 
                data[TransDetails_constants.EXCHANGE_TRANSACTION_CHARGES] + 
                data[TransDetails_constants.GST] + 
                data[TransDetails_constants.STAMP_DUTY] + 
                data[TransDetails_constants.DP_CHARGES] + 
                data[TransDetails_constants.BROKERAGE]
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Error processing transaction details: {e}")
            raise
    
    def process_share_profit_loss(self, data):
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
            data = self.formatting_service.initialize_data(data, extra_cols=extra_cols)
            
            # Group by transaction type and name
            grouped_data = data.groupby([TransDetails_constants.TRANSACTION_TYPE, Raw_constants.NAME])
            
            info_map = {}
            row_data = {}
            
            # Create DataFrame with ShareProfitLoss constants
            constants_dict = {key: value for key, value in ShareProfitLoss_constants.__dict__.items() 
                            if not key.startswith('__')}
            df = pd.DataFrame(columns=list(constants_dict.values()))
            
            for (transaction_type, name), group in grouped_data:
                if name not in row_data:
                    row_data[name] = self.formatting_service.get_spl_row()
                    info_map[name] = {}
                
                # Process transactions - pass the DataFrame group directly instead of converting to list
                info_map[name][transaction_type] = group
                
                if transaction_type == self.config.SELL:
                    self._process_sell_transactions(info_map[name], row_data[name])
                else:
                    self._process_buy_transactions(info_map[name], row_data[name])
            
            # Create final DataFrame
            for share_name, share_details in row_data.items():
                # Get current stock price
                current_price = self.market_data_service.get_current_stock_price(share_name)
                
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
            
            return self.calculation_service.convert_dtypes(df)
            
        except Exception as e:
            logger.error(f"Error processing share profit loss: {e}")
            raise
    
    def _process_sell_transactions(self, transactions, row_data):
        """Process sell transactions"""
        average_sale_price = 0.0
        num_shares_sold = 0.0
        current_investment = 0.0
        
        # Process each row in the DataFrame group
        for _, transaction in transactions[self.config.SELL].iterrows():
            # Access data using proper column names
            try:
                net_amount = float(transaction[TransDetails_constants.FINAL_AMOUNT]) if transaction[TransDetails_constants.FINAL_AMOUNT] is not None else 0.0
                quantity = float(transaction[TransDetails_constants.QUANTITY]) if transaction[TransDetails_constants.QUANTITY] is not None else 0.0
            except (ValueError, TypeError):
                net_amount = 0.0
                quantity = 0.0
                logger.warning(f"Invalid transaction data: {transaction}")
            
            if num_shares_sold - quantity != 0:
                average_sale_price = (average_sale_price * num_shares_sold - net_amount) / (num_shares_sold - quantity)
            num_shares_sold -= quantity
            current_investment += net_amount
        
        if self.config.BUY in transactions:
            for _, transaction in transactions[self.config.BUY].iterrows():
                try:
                    net_amount = float(transaction[TransDetails_constants.FINAL_AMOUNT]) if transaction[TransDetails_constants.FINAL_AMOUNT] is not None else 0.0
                except (ValueError, TypeError):
                    net_amount = 0.0
                current_investment += net_amount
        
        average_cost_of_sold_shares = self.calculation_service.calculate_average_cost_of_sold_shares(transactions)
        
        row_data[ShareProfitLoss_constants.AVERAGE_SALE_PRICE] = average_sale_price
        row_data[ShareProfitLoss_constants.SHARES_SOLD] = num_shares_sold
        row_data[ShareProfitLoss_constants.AVERAGE_COST_OF_SOLD_SHARES] = average_cost_of_sold_shares
        row_data[ShareProfitLoss_constants.CURRENT_INVESTMENT] = current_investment
    
    def _process_buy_transactions(self, transactions, row_data):
        """Process buy transactions"""
        average_buy_price = 0.0
        num_shares_bought = 0
        current_investment = 0.0
        total_investment = 0.0
        
        # Process each row in the DataFrame group
        for _, transaction in transactions[self.config.BUY].iterrows():
            # Access data using proper column names
            try:
                net_amount = float(transaction[TransDetails_constants.FINAL_AMOUNT]) if transaction[TransDetails_constants.FINAL_AMOUNT] is not None else 0.0
                quantity = float(transaction[TransDetails_constants.QUANTITY]) if transaction[TransDetails_constants.QUANTITY] is not None else 0.0
            except (ValueError, TypeError):
                net_amount = 0.0
                quantity = 0.0
                logger.warning(f"Invalid transaction data: {transaction}")
            
            if num_shares_bought + quantity != 0:
                average_buy_price = (average_buy_price * num_shares_bought + net_amount) / (num_shares_bought + quantity)
            num_shares_bought += quantity
            current_investment += net_amount
            total_investment += net_amount
        
        row_data[ShareProfitLoss_constants.AVERAGE_BUY_PRICE] = average_buy_price
        row_data[ShareProfitLoss_constants.SHARES_BOUGHT] = num_shares_bought
        row_data[ShareProfitLoss_constants.TOTAL_INVESTMENT] = total_investment
        row_data[ShareProfitLoss_constants.CURRENT_INVESTMENT] = current_investment 