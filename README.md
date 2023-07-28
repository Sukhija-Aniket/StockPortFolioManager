# Stock PortFolio Manager

Stock Portfolio Manager is a Python application that allows users to manage their stock portfolio by importing data from Excel sheets or Google Sheets. The application provides real-time stock price updates, calculates total gains and losses, and generates reports for profit/loss and taxation purposes.

The Stock Portfolio Manager provides the following features:

1. Import Data: Users can choose to import stock data from local Excel sheets or Google Sheets.
2. Real-time Stock Prices: The application fetches real-time stock prices using APIs (e.g., Alpha Vantage) to keep the data up-to-date.
3. Portfolio Analytics: Calculate and display total gains, losses, and other portfolio-related metrics.
4. Profit/Loss Calculation: Automatically calculate and analyze individual stock profits and losses based on historical data.
5. Taxation Reports: Generate reports to assist with taxation calculations and record-keeping for stock trades.
6. Export Data: Users can export portfolio data to Excel or Google Sheets for further analysis or backup purposes.
7. User-friendly Interface: The application provides an intuitive and easy-to-use interface for seamless navigation.

By combining data from Excel and Google Sheets, the Stock Portfolio Manager enables users to conveniently manage their stock investments in one central place, ensuring accuracy, efficiency, and optimal portfolio performance.

Please note that this project name and description are intended for illustrative purposes only. You can modify and expand on these ideas based on your specific requirements and preferences. Good luck with your Stock Portfolio Manager project!

## Prerequisites

Before running the project, you need to have the following installed and set up:

1. Python (version 3.X.X or later)
2. pip (package installer for Python)
3. Virtual environment (optional but recommended)

## Installation

1. Clone the repository from GitHub:

```
git clone https://github.com/your-username/your-repo.git
```

2. Navigate to the project directory:

```
cd project-directory
```

3. Create a virtual environment (optional but recommended):

```
python -m venv venv
```

4. Activate the virtual environment (if you created one):

   - On Windows:

   ```
   venv\Scripts\activate
   ```

   - On macOS and Linux:

   ```
   source venv/bin/activate
   ```
5. Install project dependencies using pip:

```
pip install -r requirements.txt
```

## Configuration

To run the project, you need to set up the following configuration files:

1. `.env` file:

   Create a `.env` file in the project directory and set any environment-specific variables needed by the project. Make sure not to share sensitive information like API keys in the repository. Example `.env` content:

   ```
   STOCK_API_KEY=
   SPREADSHEET_ID=
   EXCEL_FILE_NAME=
   LAST_EXECUTION_DATE_SHEETS= <optional>
   LAST_EXECUTION_DATE_EXCEL= <optional>
   ```

   The  optional fields are required if you wish to execute the script only once per Day, in that case uncomment the line `script_already_executed()` and now your script can run at max once per day.
2. `tradingprojects-apiKey.json` file:

   To access the Google Sheets API and make changes to Google Sheets, you need to authenticate your application. Google offers two authentication methods: OAuth 2.0 and Service Accounts.

   1. OAuth 2.0:
      OAuth 2.0 is used when you want to access Google Sheets on behalf of a user. It requires user consent and provides an access token that allows your application to make requests to Google Sheets on the user's behalf.
   2. Service Accounts:
      Service Accounts are used when you want to access Google Sheets on behalf of your application, not a specific user. Service Accounts provide a JSON file containing credentials that your application uses to authenticate with the Google Sheets API.

   In this project we make use of a Service Account. Here's how you can set up a Service Account and download the required JSON file:

   1. Go to the Google API Console: [https://console.developers.google.com/](https://console.developers.google.com/)
   2. Create a new project (or use an existing one).
   3. In the project dashboard, enable the Google Sheets API.
   4. Navigate to the "Credentials" page from the left sidebar.
   5. Click on "Create credentials" and select "Service account."
   6. Fill in the necessary information for the Service Account and click "Create."
   7. On the next page, assign the "Editor" role to the Service Account (or choose a suitable role that grants access to Google Sheets).
   8. Click "Continue" and then "Done."
   9. Find the newly created Service Account in the "Credentials" list and click the "Manage service account" button.
   10. Click on "Add key" and select "Create new key."
   11. Choose the JSON key type and click "Create." This will download the JSON file containing your Service Account credentials.
   12. Save the downloaded JSON file with the name 'tradingprojects-apiKey.json' in your project directory.

   Now, your application can use the 'tradingprojects-apiKey.json' file to authenticate with the Google Sheets API and make changes to Google Sheets on behalf of the Service Account.

## Running the Project

1. Activate the virtual environment (if you created one):

   - On Windows:

      ```
      venv\Scripts\activate
      ```

   - On macOS and Linux:

      ```
      source venv/bin/activate
      ```
2. Run the Python script:

   ```
   python tradingScript.py
   ```
3. Provide the necessary Command Line Arguments:
   - The first one is absolute path of the `csv` file downloaded from Kite Zerodha
   - The second is whether you would like to choose `excel` or `sheets`. Leave empty to use default i.e. `excel`
   - If you choose `sheets`, for the third argument provide the `spreadsheet_id` for the spreadsheet you would like to use or leave empty for default spreadsheet.
   - Make sure the spreadsheet you choose is being shared with the Service Account you created.
   - If you choose `excel`, for the third argument provide the name of the excel file which you would like to use, leave empty for default excel file.
   - Make sure to place the excel file in the `assets` folder present in the project.


## Contributing

If you want to contribute to this project, follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix:

```
git checkout -b feature/your-feature-name
```

3. Make your changes and commit them:

```
git commit -m "Add your commit message here"
```

4. Push the changes to your fork:

```
git push origin feature/your-feature-name
```

5. Create a pull request on the original repository.
