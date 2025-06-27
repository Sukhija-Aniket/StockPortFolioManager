# Stock Portfolio Manager - User Guide

A comprehensive guide to using the Stock Portfolio Manager system for managing your stock portfolio with broker-specific calculations and Google Sheets integration.

## 🚀 Getting Started

### Prerequisites
- **Google Account**: Required for authentication and Google Sheets access
- **Web Browser**: Modern browser with JavaScript enabled
- **CSV Data**: Your stock transaction data in CSV format
- **Broker Information**: Know which broker you're using (Zerodha, Upstox, etc.)

### System Access
1. Open your web browser
2. Navigate to the Stock Portfolio Manager application
3. Click "Login with Google" to authenticate
4. Grant necessary permissions for Google Sheets access

## 📊 Understanding the System

### What the System Does
The Stock Portfolio Manager helps you:
- **Import Transaction Data**: Upload CSV files with your stock transactions
- **Calculate Broker Charges**: Apply broker-specific rates (brokerage, STT, GST, DP charges)
- **Generate Reports**: Create comprehensive profit/loss and taxation reports
- **Track Portfolio**: Monitor your portfolio performance over time
- **Export Results**: Save processed data to Google Sheets for further analysis

### Supported Brokers
The system supports major Indian brokers with configurable rates:
- **Zerodha**
- **Upstox**
- **Angel One**
- **ICICI Direct**
- **HDFC Securities**
- **Kotak Securities**
- **Axis Direct**
- **SBI Securities**
- **5Paisa**
- **Groww**

## 📁 Data Requirements

### CSV File Format
Your CSV file should contain the following columns:

| Column Name | Description | Example |
|-------------|-------------|---------|
| `Date` | Transaction date | 2024-01-15 |
| `Stock Name` | Name of the stock | RELIANCE |
| `Buy/Sell` | Transaction type | BUY or SELL |
| `Quantity` | Number of shares | 100 |
| `Price` | Transaction price | 2500.50 |
| `Net Amount` | Total transaction value | 250050.00 |
| `Exchange` | Trading exchange | NSE or BSE |

### Sample CSV Data
```csv
Date,Stock Name,Buy/Sell,Quantity,Price,Net Amount,Exchange
2024-01-15,RELIANCE,BUY,100,2500.50,250050.00,NSE
2024-01-16,TCS,SELL,50,3800.00,190000.00,NSE
2024-01-17,INFOSYS,BUY,75,1500.25,112518.75,NSE
```

### Data Validation
The system validates your data for:
- **Date Format**: Must be in YYYY-MM-DD format
- **Numeric Values**: Quantity, Price, and Net Amount must be numbers
- **Required Fields**: All columns must be present
- **Valid Transactions**: Buy/Sell must be either "BUY" or "SELL"

## 🔄 Step-by-Step Workflow

### Step 1: Create a Spreadsheet
1. **Login**: Authenticate with your Google account
2. **Select Broker**: Choose your broker from the dropdown menu
3. **Create Spreadsheet**: Click "Create New Spreadsheet"
4. **Wait for Creation**: The system will create a Google Sheet with proper structure
5. **Note the ID**: Save the spreadsheet ID for future reference

### Step 2: Upload Your Data
1. **Prepare CSV**: Ensure your CSV file is in the correct format
2. **Select File**: Click "Choose File" and select your CSV file
3. **Select Spreadsheet**: Choose the target spreadsheet from the dropdown
4. **Upload**: Click "Upload" to start the upload process
5. **Monitor Progress**: Watch the upload progress indicator

### Step 3: Process Your Data
1. **Sync Data**: Click "Sync All Data" to process all spreadsheets
2. **Wait for Processing**: The system will process your data asynchronously
3. **Check Status**: Monitor the processing status in the interface
4. **View Results**: Once complete, view results in your Google Sheet

### Step 4: Review Results
1. **Open Google Sheet**: Access your processed spreadsheet
2. **Review Calculations**: Check broker charges and profit/loss calculations
3. **Export Reports**: Download or share reports as needed
4. **Analyze Data**: Use the data for portfolio analysis and tax planning

## 📈 Understanding the Results

### Processed Data Columns
After processing, your Google Sheet will contain:

| Column | Description |
|--------|-------------|
| **Original Data** | Your uploaded transaction data |
| **Brokerage** | Broker-specific brokerage charges |
| **STT** | Securities Transaction Tax |
| **GST** | Goods and Services Tax |
| **DP Charges** | Depository Participant charges |
| **Total Charges** | Sum of all charges |
| **Net Amount** | Transaction amount after charges |
| **Profit/Loss** | Calculated profit or loss |
| **Cost Basis** | FIFO-based cost basis for sold shares |

### Calculation Methods

#### Brokerage Calculation
- **Intraday**: Rate × Transaction Value (capped at maximum amount)
- **Delivery**: Rate × Transaction Value (capped at maximum amount)

#### STT Calculation
- **Buy**: Rate × Transaction Value
- **Sell**: Rate × Transaction Value

#### GST Calculation
- Applied on brokerage and other charges
- Rate: 18% (configurable per broker)

#### DP Charges
- Applied once per stock per day
- Fixed amount per broker

#### FIFO Cost Basis
- **Buy Transactions**: Added to inventory at purchase price
- **Sell Transactions**: Matched against oldest inventory first
- **Intraday vs Delivery**: Handled separately for tax purposes

## 📊 Report Types

### 1. Transaction Summary
- **Total Buy/Sell Transactions**: Count and value of transactions
- **Total Charges**: Sum of all broker charges
- **Net Investment**: Total amount invested after charges

### 2. Profit/Loss Report
- **Realized P&L**: Profit/loss from completed transactions
- **Unrealized P&L**: Current value vs cost basis
- **Daily P&L**: Profit/loss by date

### 3. Taxation Report
- **LTCG**: Long-term capital gains (held > 1 year)
- **STCG**: Short-term capital gains (held ≤ 1 year)
- **Intraday**: Day trading profits/losses
- **Tax Liability**: Estimated tax based on current rates

### 4. Portfolio Analysis
- **Stock-wise Performance**: Individual stock P&L
- **Sector Analysis**: Performance by sector (if data available)
- **Risk Metrics**: Volatility and drawdown analysis

## 🔧 Advanced Features

### Multiple Spreadsheets
- **Create Multiple**: Create separate spreadsheets for different portfolios
- **Organize Data**: Use different sheets for different time periods or strategies
- **Compare Performance**: Analyze performance across different portfolios

### Data Validation
- **Error Checking**: System validates data before processing
- **Error Reports**: Detailed error messages for data issues
- **Data Correction**: Fix errors and re-upload corrected data

### Export Options
- **Google Sheets**: Results saved directly to Google Sheets
- **CSV Export**: Download processed data as CSV
- **PDF Reports**: Generate PDF reports for documentation

## 🐛 Troubleshooting

### Common Issues

#### 1. Upload Failures
**Problem**: CSV file upload fails
**Solutions**:
- Check file format and column names
- Ensure file size is within limits
- Verify internet connection
- Try uploading smaller files

#### 2. Processing Errors
**Problem**: Data processing fails or shows errors
**Solutions**:
- Check CSV data format
- Verify all required columns are present
- Ensure numeric values are valid
- Contact support with error details

#### 3. Authentication Issues
**Problem**: Cannot login or access Google Sheets
**Solutions**:
- Clear browser cache and cookies
- Check Google account permissions
- Ensure Google Sheets API is enabled
- Try logging out and back in

#### 4. Missing Data
**Problem**: Some transactions are missing from results
**Solutions**:
- Check CSV file for duplicate or invalid entries
- Verify date formats are correct
- Ensure all required fields are filled
- Review error logs for specific issues

### Getting Help

#### Error Messages
When you encounter errors:
1. **Note the Error**: Copy the exact error message
2. **Check Data**: Verify your CSV file format
3. **Try Again**: Attempt the operation again
4. **Contact Support**: If issues persist, contact support with details

#### Support Information
- **Error Details**: Include exact error messages
- **Data Sample**: Provide sample of your CSV data (without sensitive info)
- **Steps Taken**: Describe what you were doing when the error occurred
- **Browser Info**: Include browser type and version

## 🔒 Security and Privacy

### Data Protection
- **Secure Authentication**: Google OAuth 2.0 for secure login
- **Data Encryption**: All data transmitted over HTTPS
- **Access Control**: Only you can access your data
- **No Data Storage**: Raw data is not stored permanently

### Privacy Considerations
- **Google Sheets**: Your data is stored in your Google Sheets
- **Processing**: Data is processed temporarily for calculations
- **No Sharing**: Your data is not shared with third parties
- **Account Access**: Only basic Google Sheets access is required

## 📚 Best Practices

### Data Preparation
1. **Use Consistent Format**: Always use the same CSV format
2. **Validate Data**: Check your data before uploading
3. **Backup Data**: Keep copies of your original CSV files
4. **Regular Updates**: Upload new transactions regularly

### Portfolio Management
1. **Organize by Strategy**: Use separate spreadsheets for different strategies
2. **Track All Transactions**: Include all buys, sells, and corporate actions
3. **Review Regularly**: Check your portfolio performance regularly
4. **Tax Planning**: Use reports for tax planning and compliance

### System Usage
1. **Regular Logins**: Login regularly to maintain session
2. **Monitor Processing**: Watch for processing errors
3. **Verify Results**: Double-check calculations for important decisions
4. **Keep Updated**: Use the latest version of the system

## 🆘 Support and Resources

### Documentation
- **This User Guide**: Comprehensive usage instructions
- **API Documentation**: Technical details for developers
- **Video Tutorials**: Step-by-step video guides
- **FAQ Section**: Common questions and answers

### Contact Information
- **GitHub Issues**: Report bugs and request features
- **Email Support**: For urgent issues and account problems
- **Community Forum**: Connect with other users

### Updates and Maintenance
- **Regular Updates**: System is updated regularly with new features
- **Security Patches**: Security updates are applied automatically
- **Feature Requests**: New features based on user feedback
- **Performance Improvements**: Ongoing optimization for better performance

---

**Note**: This user guide is based on the current version of the Stock Portfolio Manager system. Features and functionality may change with updates. Always refer to the latest documentation for the most current information. 