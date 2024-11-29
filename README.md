# Order Report Web Scraper

## Project Overview
This Scrapy spider is designed to extract order reports from a web platform, supporting date-range-based extraction and saving the data in multiple formats (JSON, Excel, CSV).

## Prerequisites
- Python 3.8+
- pip
- virtualenv

## Setup and Installation

### 1. Clone the Repository
```bash
git clone git@github.com:Speak2/shopze_admin_web_crawl.git
cd shopze_admin_web_crawl
```

### 2. Create Virtual Environment
It's recommended to use a virtual environment to manage dependencies:

#### On Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

#### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets
1. Copy the `secrets.json.example` to `secrets.json`
```bash
cp secrets.json.example secrets.json
```

2. Edit `secrets.json` with your specific credentials:
```json
{
    "email": "your_email@example.com",
    "password": "your_password",
    "login_url": "https://example.com/login",
    "base_report_url": "https://example.com/reports",
    "date_set_url": "https://example.com/set-date-range"
}
```

**IMPORTANT**: Never commit your `secrets.json` to version control. Add it to `.gitignore`.

### 5. Running the Spider

#### Basic Usage
```bash
scrapy crawl order_report
```

#### Specify Date Range (Optional)
You can specify custom date ranges when running the spider:
```bash
# Extract orders for a specific date range
scrapy crawl order_report -a from_date=2024-01-01 -a to_date=2024-12-31
```

If no dates are provided, the spider defaults to extracting orders from the last 30 days.

### 6. Output
After running the spider, three files will be generated:
- `order_report.json`: Full order details in JSON format
- `order_report.xlsx`: Order details in Excel spreadsheet
- `order_report.csv`: Order details in CSV format

## Troubleshooting

### Common Issues
1. **Login Failure**: 
   - Verify credentials in `secrets.json`
   - Check if login URL or form structure has changed
   
2. **No Orders Found**: 
   - Confirm the date range selected
   - Verify website's accessibility

### Logging
The spider uses Python's logging. Check console output for detailed information about the scraping process.

## Development Notes

### Project Structure
- `order_report.py`: Main Scrapy spider
- `settings.py`: Scrapy project configuration
- `secrets.json.example`: Template for secret configuration

### Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License
[Specify your license here]

## Disclaimer
This web scraper is for educational purposes. Always respect the website's Terms of Service and `robots.txt` guidelines.