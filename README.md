# NovaCore Products Discord Bot

A semi-automated shop system Discord bot for managing product sales, handling payments, and tracking orders.

## Features

- Product catalog with categories
- Automated checkout flow
- PayPal and Cryptocurrency payment support
- Staff payment review system
- Delivery system for digital products
- Sales statistics and charts
- Stock management
- Role-based permissions

## Requirements

- Python 3.8 or higher
- discord.py 2.3+
- Additional packages listed in `requirements.txt`

## Installation

1. Clone the repository
2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure the environment variables:

## Environment Variables

Required variables:
- `DISCORD_TOKEN`: Your Discord bot token
- `MAIN_CHANNEL_ID`: Channel ID for the stock panel
- `STAFF_CHANNEL_ID`: Channel ID for staff payment review
- `PUBLIC_LOG_CHANNEL_ID`: Channel ID for public purchase logs
- `CUSTOMER_ROLE_ID`: Role ID for customers
- `STAFF_ROLE_IDS`: Comma-separated role IDs for staff
- `PAYPAL_EMAIL`: PayPal email for payments
- `DATABASE_PATH`: Path to SQLite database file
- `LOG_DIR`: Directory for logs and generated images

Optional variables:
- `PRODUCT_CATEGORY_ID`: Category for product channels
- `BTC_ADDRESS`: Bitcoin wallet address
- `LTC_ADDRESS`: Litecoin wallet address
- `USDT_ADDRESS`: USDT wallet address (TRC20)
- `SOL_ADDRESS`: Solana wallet address
- `ETH_ADDRESS`: Ethereum wallet address

## Usage

1. Set up the environment variables
2. Run the bot:
```bash
python bot.py
```

## Admin Commands

- `/addstock` - Add or update a product
- `/removestock` - Remove a product
- `/setstock` - Set product stock amount
- `/stats` - View sales statistics
- `/listproducts` - List all products

## Security Considerations

- All sensitive data is stored in environment variables
- Staff-only commands are protected by role checks
- Database uses transactions to prevent race conditions
- Payment proofs are reviewed manually by staff
- Rate limits on admin commands

## License

© NovaCore - All Rights Reserved