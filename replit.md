# NovaCore Products Discord Bot

## Overview

NovaCore is a semi-automated Discord bot for managing a digital product shop. It handles product catalog management, automated checkout flows, payment processing (PayPal and cryptocurrency), staff review systems, and digital product delivery. The bot uses a role-based permission system to separate customer, staff, and owner capabilities, with comprehensive order tracking and sales analytics.

## Recent Changes

**November 2, 2025:**
- **Added Support Ticket System**: Implemented a comprehensive ticket management system with three ticket types (Product Issue, Refund Request, Others). The system includes:
  - Persistent ticket panel with interactive buttons in a designated channel
  - Modal forms for ticket creation with subject, order ID, and description fields
  - Automatic order validation: when an Order ID is provided, the bot fetches and displays order details in the ticket
  - Private ticket channels created with proper permissions (user + staff only)
  - Staff-only ticket closure with permission validation
  - Order ID required for Product Issue and Refund Request tickets, optional for Others
  - Automatic cleanup of old ticket panels on bot restart
- Separated vouch and purchase notification channels: `VOUCH_CHANNEL_ID` for customer reviews/vouches, `PUBLIC_LOG_CHANNEL_ID` for purchase notifications
- Added `/details {orderID}` command for staff to view detailed order information including status, payment proof, and timestamps
- Fixed product image URL validation to prevent invalid thumbnail URLs in product embeds

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Technology**: Discord.py 2.3+ with slash commands and UI components
- **Design Pattern**: Cog-based architecture for modular feature separation
- **Rationale**: Discord.py provides robust async support for Discord API interactions. Cogs allow clean separation of concerns between product management, order management, and UI components.

### Data Storage
- **Database**: SQLite with aiosqlite async driver
- **Schema Design**: 
  - Products table with soft deletes (is_deleted flag), categories, pricing, stock tracking, and deliverables
  - Orders table (implied from code) for transaction management
- **Rationale**: SQLite provides zero-configuration persistence suitable for Discord bots. Async operations prevent blocking the event loop during database queries.

### UI Architecture
- **Components**: Discord UI framework with Select menus, Buttons, and Modal forms
- **Key Views**:
  - `StockView`: Main product catalog interface
  - `CategorySelect`: Category browsing dropdown
  - `PaymentMethodView`: Payment selection (PayPal/Crypto)
  - `TicketPanelView`: Support ticket system with three button types
  - `TicketModal`: Dynamic form for ticket creation with conditional Order ID validation
  - `TicketControlView`: Staff controls for ticket management (close button)
  - Product selection and checkout flows
- **Rationale**: Discord's native UI components provide interactive experiences without external web interfaces, keeping everything in-platform.

### Permission System
- **Role-Based Access Control**:
  - Customer role for buyers
  - Staff roles for payment review and order management
  - Owner role for product catalog management
- **Implementation**: Environment-configured role IDs with role checking decorators
- **Rationale**: Discord's native role system provides built-in authentication and authorization without external identity management.

### Payment Processing
- **PayPal Integration**: Manual review system where customers send payment and staff verify
- **Cryptocurrency Support**: Multi-currency support (BTC, LTC, USDT, SOL, ETH) with manual verification
- **Order Flow**: 
  1. Customer selects product and quantity
  2. System generates unique order ID (NC-YYYYMMDD-XXXXXX format)
  3. Payment instructions sent to customer
  4. Staff review payment proof in dedicated channel
  5. Upon approval, deliverables sent to customer
- **Rationale**: Manual review provides fraud protection and flexibility for accepting various payment methods without automated payment gateway fees.

### Product Deliverables System
- **Format Evolution**: Migrating from comma-separated strings to JSON format with typed items
- **Structure**: Each deliverable has an item name and type (code, account, file, link, guide, support, service, warranty, key)
- **Display**: Type-based emoji mapping for visual clarity
- **Migration**: Backward compatibility maintained with format detection (JSON parse fallback to CSV parsing)
- **Rationale**: JSON format provides structured data for better extensibility and visual presentation while maintaining compatibility with existing products.

### Analytics & Reporting
- **Visualization**: Matplotlib for generating sales charts and statistics
- **Data Export**: Pandas for data analysis capabilities
- **Storage**: Generated images saved to configured LOG_DIR
- **Rationale**: Embedded analytics provide actionable insights without requiring external BI tools.

### Logging & Monitoring
- **Dual Output**: File logging (novacore.log) and stdout streaming
- **Level**: INFO level for operational visibility
- **Structure**: Timestamp, level, and message formatting
- **Rationale**: Comprehensive logging enables troubleshooting and operational monitoring in production environments.

### Configuration Management
- **Method**: Environment variables via python-dotenv
- **Validation**: Startup validation ensures all required variables are present
- **Required Variables**: 
  - Discord credentials: `DISCORD_TOKEN`
  - Channel IDs: `MAIN_CHANNEL_ID`, `STAFF_CHANNEL_ID`, `PUBLIC_LOG_CHANNEL_ID` (for purchase logs), `VOUCH_CHANNEL_ID` (for customer reviews), `TICKET_PANEL_CHANNEL_ID` (for support ticket panel)
  - Category IDs: `TICKET_CATEGORY_ID` (where ticket channels are created)
  - Role IDs: `CUSTOMER_ROLE_ID`, `STAFF_ROLE_IDS`, `OWNER_ROLE_ID`
  - Payment addresses: `PAYPAL_EMAIL`, `BTC_ADDRESS`, `LTC_ADDRESS`, `USDT_ADDRESS`, `SOL_ADDRESS`, `ETH_ADDRESS`
  - Storage: `DATABASE_PATH`, `LOG_DIR`
- **Rationale**: Environment-based configuration enables deployment flexibility and keeps secrets out of code.

### File Organization
- **Structure**:
  - `/cogs`: Feature modules (product_management, order_management, payments_management, ticket_management)
  - `/database`: Data layer with DatabaseManager abstraction
  - `/ui`: Discord UI components and views
  - `/utils`: Helper functions, validators, migration scripts
- **Rationale**: Modular organization supports maintainability and allows independent development of features.

### Support Ticket System
- **Architecture**: Cog-based ticket management with persistent UI components
- **Ticket Types**: 
  - Product Issue (requires Order ID)
  - Refund Request (requires Order ID)
  - Others (Order ID optional)
- **Workflow**:
  1. User clicks ticket type button on persistent panel
  2. Modal form opens with subject, order ID, and description fields
  3. System validates Order ID (if provided) and fetches order details from database
  4. Private ticket channel created in configured category with proper permissions
  5. Ticket embed displays all information including order status, product, and payment details
  6. Staff can close tickets using dedicated button (permission-protected)
- **Security**: Role-based access control ensures only staff members can close tickets
- **Order Integration**: Automatic lookup and display of order information when Order ID is provided, showing status, product, total, payment method, and order date
- **Rationale**: In-Discord ticket system provides seamless support experience without external tools, with automatic order context retrieval for faster issue resolution.

## External Dependencies

### Discord Platform
- **discord.py 2.3+**: Primary framework for Discord bot development
- **Requirements**: Discord bot token, server with configured channels and roles
- **Integration Points**: Slash commands, UI interactions, message sending, role management

### Database
- **aiosqlite**: Async SQLite driver
- **Database File**: Configured via DATABASE_PATH environment variable
- **Schema**: Products table with category organization and stock tracking

### Payment Services
- **PayPal**: Email-based payment collection (manual verification)
- **Cryptocurrency**: Multi-currency wallet addresses for BTC, LTC, USDT, SOL, ETH
- **Integration**: Manual verification workflow, no automated API integration

### Python Packages
- **matplotlib**: Chart generation for sales analytics
- **pandas**: Data analysis and manipulation
- **Pillow**: Image processing for proof uploads
- **aiofiles**: Async file I/O operations
- **python-dateutil**: Date/time manipulation utilities

### File System
- **LOG_DIR**: Storage for generated images and log files
- **DATABASE_PATH**: SQLite database file location
- **Requirements**: Write permissions for both directories