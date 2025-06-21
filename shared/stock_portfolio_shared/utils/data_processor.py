"""
Data processing utilities for Stock Portfolio Manager
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from ..constants import DATE_FORMAT, DATA_TIME_FORMAT, SELL, Raw_constants, Data_constants
import os

logger = logging.getLogger(__name__)

class DataProcessor:
    """Manages data processing operations"""
    
    @staticmethod
    def replace_out_of_range_floats(obj):
        """Replace out of range floats with None"""
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
        elif isinstance(obj, list):
            return [DataProcessor.replace_out_of_range_floats(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: DataProcessor.replace_out_of_range_floats(value) for key, value in obj.items()}
        return obj
    
    @staticmethod
    def get_symbol(row):
        """Extract symbol from row data"""
        symbol = row[Data_constants.NAME]
        symbol = str(symbol).split('-')[0]
        return str(symbol)
    
    @staticmethod
    def get_data_date(date):
        """Convert date to required format"""
        date_obj = datetime.strptime(date, DATA_TIME_FORMAT)
        date_str = datetime.strftime(date_obj, DATE_FORMAT)
        return date_str
    
    @staticmethod
    def get_data_quantity(row):
        """Get data quantity from row"""
        quantity = row[Data_constants.QUANTITY]
        val = str(quantity).split('.')[0]
        if str(row[Data_constants.TYPE]).upper() == SELL:
            val = '-' + val
        return val
    
    @staticmethod
    def get_net_amount(row):
        """Calculate net amount from row"""
        val = int(row[Raw_constants.QUANTITY]) * float(row[Raw_constants.PRICE])
        return str(val)
    
    @staticmethod
    def format_add_data(input_data):
        """Format input data for processing"""
        input_data[Data_constants.QUANTITY] = input_data.apply(
            DataProcessor.get_data_quantity, axis=1)
        constants_dict = {key: value for key, value in Raw_constants.__dict__.items() if not key.startswith('__')}
        df = pd.DataFrame(columns=list(constants_dict.values()))
        
        df[Raw_constants.DATE] = input_data[Data_constants.DATE].apply(
            lambda x: DataProcessor.get_data_date(x))
        df[Raw_constants.NAME] = input_data.apply(DataProcessor.get_symbol, axis=1)
        df[Raw_constants.PRICE] = input_data[Data_constants.PRICE]
        df[Raw_constants.QUANTITY] = input_data[Data_constants.QUANTITY]
        df[Raw_constants.NET_AMOUNT] = df.apply(DataProcessor.get_net_amount, axis=1)
        df[Raw_constants.STOCK_EXCHANGE] = input_data[Data_constants.STOCK_EXCHANGE]
        return df
    
    @staticmethod
    def data_already_exists(raw_data, input_data, comparison_columns=None, return_details=False):
        """
        Generic duplicate verification logic with multiple comparison strategies
        
        Args:
            raw_data (pd.DataFrame): Existing data to check against
            input_data (pd.DataFrame): New data to check for duplicates
            comparison_columns (list): Columns to use for comparison. If None, uses all common columns
            return_details (bool): If True, returns detailed duplicate information instead of boolean
            
        Returns:
            bool or dict: True if duplicates found, False otherwise. If return_details=True, returns dict with details
        """
        try:
            # Input validation
            if raw_data.empty or input_data.empty:
                logger.info("One or both DataFrames are empty - no duplicates possible")
                return False if not return_details else {"duplicates_found": False, "reason": "empty_data"}
            
            # Reset indices for consistent comparison
            raw_data = raw_data.reset_index(drop=True)
            input_data = input_data.reset_index(drop=True)
            
            # Determine comparison columns
            if comparison_columns is None:
                # Use all common columns between the two DataFrames
                common_columns = list(set(raw_data.columns) & set(input_data.columns))
                if not common_columns:
                    logger.warning("No common columns found between raw_data and input_data")
                    return False if not return_details else {"duplicates_found": False, "reason": "no_common_columns"}
                comparison_columns = common_columns
            else:
                # Validate that specified columns exist in both DataFrames
                missing_in_raw = [col for col in comparison_columns if col not in raw_data.columns]
                missing_in_input = [col for col in comparison_columns if col not in input_data.columns]
                
                if missing_in_raw or missing_in_input:
                    logger.error(f"Comparison columns missing: {missing_in_raw} in raw_data, {missing_in_input} in input_data")
                    return False if not return_details else {"duplicates_found": False, "reason": "missing_columns"}
            
            logger.info(f"Checking for duplicates using columns: {comparison_columns}")
            
            # Create comparison DataFrames
            raw_comparison = raw_data[comparison_columns].copy()
            input_comparison = input_data[comparison_columns].copy()
            
            # Handle data type mismatches
            for col in comparison_columns:
                if raw_comparison[col].dtype != input_comparison[col].dtype:
                    # Convert to string for comparison if types don't match
                    raw_comparison[col] = raw_comparison[col].astype(str)
                    input_comparison[col] = input_comparison[col].astype(str)
                    logger.info(f"Converted column '{col}' to string for comparison")
            
            # Find duplicates
            duplicates_found = []
            duplicate_details = {
                "duplicates_found": False,
                "total_input_rows": len(input_data),
                "total_raw_rows": len(raw_data),
                "comparison_columns": comparison_columns,
                "duplicate_rows": [],
                "duplicate_count": 0,
                "match_percentage": 0.0
            }
            
            
            # Exact match strategy
            for idx, input_row in input_comparison.iterrows():
                # Check if this row exists exactly in raw_data
                matches = raw_comparison.eq(input_row).all(axis=1)
                if matches.any():
                    duplicate_rows = raw_data[matches].index.tolist()
                    duplicates_found.append({
                        "input_row_index": idx,
                        "raw_row_indices": duplicate_rows,
                        "match_type": "exact",
                        "matching_columns": comparison_columns
                    })
                    duplicate_details["duplicate_rows"].append({
                        "input_row": input_data.iloc[idx].to_dict(),
                        "raw_rows": raw_data.iloc[duplicate_rows].to_dict('records'),
                        "match_type": "exact"
                    })
            
            # Calculate overall statistics
            duplicate_details["duplicate_count"] = len(duplicates_found)
            if len(input_data) > 0:
                duplicate_details["match_percentage"] = len(duplicates_found) / len(input_data)
            
            # Determine if duplicates were found
            has_duplicates = len(duplicates_found) > 0
            duplicate_details["duplicates_found"] = has_duplicates
            
            # Log results
            if has_duplicates:
                logger.warning(f"Found {len(duplicates_found)} duplicate rows out of {len(input_data)} input rows")
                
                # Log specific duplicate details for debugging
                for dup in duplicates_found[:3]:  # Log first 3 duplicates
                    logger.debug(f"Duplicate: Input row {dup['input_row_index']} matches raw rows {dup['raw_row_indices']}")
            else:
                logger.info(f"No duplicates found")
            
            if return_details:
                return duplicate_details
            else:
                # Check if ALL input rows are duplicates
                all_rows_duplicate = has_duplicates and (len(duplicates_found) == len(input_data))
                return all_rows_duplicate
                
        except Exception as e:
            logger.error(f"Error in duplicate verification: {e}")
            if return_details:
                return {"duplicates_found": False, "error": str(e)}
            else:
                return False
    
    @staticmethod
    def find_similar_data(raw_data, input_data, similarity_threshold=0.7, comparison_columns=None):
        """
        Find similar (but not exact duplicate) data
        
        Args:
            raw_data (pd.DataFrame): Existing data
            input_data (pd.DataFrame): New data to check
            similarity_threshold (float): Minimum similarity score (0.0 to 1.0)
            comparison_columns (list): Columns to use for comparison
            
        Returns:
            dict: Similarity analysis results
        """
        return DataProcessor.data_already_exists(
            raw_data, input_data, 
            comparison_columns=comparison_columns,
            threshold_percentage=similarity_threshold,
            exact_match=False,
            return_details=True
        )
    
    @staticmethod
    def check_data_quality(raw_data, input_data):
        """
        Check data quality and potential issues
        
        Args:
            raw_data (pd.DataFrame): Existing data
            input_data (pd.DataFrame): New data
            
        Returns:
            dict: Data quality report
        """
        quality_report = {
            "raw_data_rows": len(raw_data),
            "input_data_rows": len(input_data),
            "raw_data_columns": list(raw_data.columns) if not raw_data.empty else [],
            "input_data_columns": list(input_data.columns) if not input_data.empty else [],
            "common_columns": list(set(raw_data.columns) & set(input_data.columns)) if not raw_data.empty and not input_data.empty else [],
            "missing_columns": list(set(raw_data.columns) - set(input_data.columns)) if not raw_data.empty and not input_data.empty else [],
            "extra_columns": list(set(input_data.columns) - set(raw_data.columns)) if not raw_data.empty and not input_data.empty else [],
            "data_type_mismatches": [],
            "null_values": {},
            "duplicate_check": None
        }
        
        # Check for null values
        if not input_data.empty:
            quality_report["null_values"]["input_data"] = input_data.isnull().sum().to_dict()
        if not raw_data.empty:
            quality_report["null_values"]["raw_data"] = raw_data.isnull().sum().to_dict()
        
        # Check data type mismatches in common columns
        if not raw_data.empty and not input_data.empty:
            common_cols = quality_report["common_columns"]
            for col in common_cols:
                if raw_data[col].dtype != input_data[col].dtype:
                    quality_report["data_type_mismatches"].append({
                        "column": col,
                        "raw_data_type": str(raw_data[col].dtype),
                        "input_data_type": str(input_data[col].dtype)
                    })
        
        # Run duplicate check
        quality_report["duplicate_check"] = DataProcessor.data_already_exists(
            raw_data, input_data, return_details=True
        )
        
        return quality_report
    
    @staticmethod
    def check_valid_path(path):
        """Check if path is valid"""
        if path is None or not os.path.exists(path):
            return None
        return True
    
    @staticmethod
    def get_valid_path(path):
        """Get valid path with user input if needed"""
        if path is None:
            return None
        if not os.path.exists(path):
            logger.error("The Provided Path for file downloaded from Zerodha does not exist!")
            path = input("Enter correct Absolute Path, including /home: ")
            path = DataProcessor.get_valid_path(path)   
        return path
    
    @staticmethod
    def format_data_for_display(data):
        """Format data for display purposes"""
        # This is a placeholder - implement based on specific display requirements
        return data
    
    @staticmethod
    def process_trading_data(data):
        """Process trading data for analysis"""
        # This is a placeholder - implement based on specific trading analysis requirements
        return data
    
    @staticmethod
    def validate_data(data):
        """Validate data integrity"""
        # This is a placeholder - implement based on specific validation requirements
        return True
    
    @staticmethod
    def ensure_directory_exists(directory_path):
        """Ensure directory exists, create if it doesn't"""
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return directory_path
    
    @staticmethod
    def get_file_extension(file_path):
        """Get file extension from path"""
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def is_valid_file_type(file_path, allowed_extensions):
        """Check if file type is valid"""
        extension = DataProcessor.get_file_extension(file_path)
        return extension in allowed_extensions 