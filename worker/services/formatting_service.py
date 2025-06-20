import pandas as pd
import numpy as np
import logging
from models.constants import Data_constants, ShareProfitLoss_constants, Taxation_constants
from config import Config

logger = logging.getLogger(__name__)

class FormattingService:
    """Service for data formatting and presentation"""
    
    def __init__(self):
        self.config = Config() 
   