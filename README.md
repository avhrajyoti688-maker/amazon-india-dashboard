# Amazon India Sales Dashboard

An interactive dashboard built with Python and Streamlit for **Sapphire IQ**. It turns 10,000 Amazon India orders (Jan 2024 to Aug 2026) into one easy-to-read page for management.

## What the dashboard shows

1. **Overall Sales & Profit:** Total sales, profit, orders, units sold, average order value, profit margin, and a monthly trend chart.
2. **Category & Product Performance:** Sales and profit by category, units sold by category, and the top 10 products.
3. **Order Status & Revenue Loss:** Delivered, shipped, returned and cancelled orders, return and cancellation rates, and revenue lost by category.
4. **Payment, Fulfilment & Geography:** Sales and profit by payment method and fulfilment method, plus state-wise sales, profit and orders.

**Sidebar filters:** date range, category and state. Every number and chart updates when a filter changes.

## Key findings

- Total sales of about ₹15.58 Cr and profit of about ₹3.32 Cr (21.3% margin)
- Electronics & Mobiles makes up about 79% of sales
- About 10% of sales value is lost to returns and cancellations
- UPI is the leading payment method and Amazon FBA the leading fulfilment channel
- Maharashtra, Karnataka and Delhi together bring in about 49% of sales

## Project files

| File | Purpose |
|---|---|
| `app.py` | The dashboard |
| `Amazon_Sales_Data_India.xlsx` | The dataset (10,000 orders, 13 columns) |
| `requirements.txt` | Python libraries needed |
| `universal_dashboard.py` | Optional version that works with other CSV/Excel files |

## How to run

1. Install Python 3.9 or newer.
2. Put all the files in one folder.
3. Open a terminal in that folder and install the libraries:
```
   pip install -r requirements.txt
```
4. Start the dashboard:
```
   py -m streamlit run app.py
```
   (on Mac/Linux: `python -m streamlit run app.py`)
5. Open `http://localhost:8501` in your browser.

## Tech stack

Python, Streamlit, Pandas, Plotly, OpenPyXL

## Notes on the data

- Total Sales includes returned and cancelled orders. Revenue lost is shown separately in Section 3.
- Returned and cancelled orders have zero profit in the dataset.
- The dataset contains 10 states, so "Top 10 States" shows all of them.

## Author

Avhrajyoti Sengupta, AI/ML Intern, Sapphire IQ
