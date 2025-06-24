"""
Production-ready Casio Watches E-commerce Application with:
✓ Complete product catalog with professional watch imagery
✓ Shopping cart and checkout functionality
✓ User authentication and profile management
✓ Order processing and management system
✓ Admin panel for product and inventory management
✓ Professional watch photography integration
✓ Mobile-responsive design with modern UI/UX
✓ Secure payment processing setup (Stripe integration ready)
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from nicegui import ui, app as nicegui_app
import asyncio
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import application modules
try:
    from app.core.config import settings
    from app.core.database import init_db, get_session
    from app.core.assets import CasioAssetManager
    from app.services.auth_service import AuthService
    from app.services.product_service import ProductService
    from app.services.cart_service import CartService
    from app.services.order_service import OrderService
    from app.frontend.pages.home import create_home_page
    from app.frontend.pages.products import create_products_page
    from app.frontend.pages.product_detail import create_product_detail_page
    from app.frontend.pages.cart import create_cart_page
    from app.frontend.pages.checkout import create_checkout_page
    from app.frontend.pages.auth import create_auth_page
    from app.frontend.pages.profile import create_profile_page
    from app.frontend.pages.admin import create_admin_page
    from app.frontend.components.header import create_header
    from app.frontend.components.footer import create_footer
    
    logger.info("All modules imported successfully")
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

# Global services
auth_service = AuthService()
product_service = ProductService()
cart_service = CartService()
order_service = OrderService()
asset_manager = CasioAssetManager()

# Global state
current_user = None
cart_items = []

async def startup():
    """Initialize the application on startup."""
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize sample data if needed
        await product_service.initialize_sample_data()
        logger.info("Sample data initialized")
        
        # Load CSS
        ui.add_head_html("""
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        """)
        
        # Add custom CSS
        ui.add_css("""
        :root {
            --primary-color: #1a365d;
            --secondary-color: #2d3748;
            --accent-color: #3182ce;
            --success-color: #38a169;
            --warning-color: #d69e2e;
            --error-color: #e53e3e;
            --text-primary: #2d3748;
            --text-secondary: #4a5568;
            --bg-primary: #ffffff;
            --bg-secondary: #f7fafc;
            --border-color: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --radius: 8px;
            --radius-lg: 12px;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background-color: var(--bg-primary);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }
        
        .hero-section {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 4rem 0;
            text-align: center;
        }
        
        .hero-title {
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        
        .hero-subtitle {
            font-size: 1.25rem;
            opacity: 0.9;
            margin-bottom: 2rem;
        }
        
        .btn {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: var(--radius);
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .btn-primary {
            background-color: var(--accent-color);
            color: white;
        }
        
        .btn-primary:hover {
            background-color: #2c5aa0;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background-color: transparent;
            color: var(--accent-color);
            border: 2px solid var(--accent-color);
        }
        
        .btn-secondary:hover {
            background-color: var(--accent-color);
            color: white;
        }
        
        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
            padding: 2rem 0;
        }
        
        .product-card {
            background: white;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
            overflow: hidden;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .product-card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-4px);
        }
        
        .product-image {
            width: 100%;
            height: 250px;
            object-fit: cover;
        }
        
        .product-info {
            padding: 1.5rem;
        }
        
        .product-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }
        
        .product-price {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-color);
            margin-bottom: 1rem;
        }
        
        .product-description {
            color: var(--text-secondary);
            margin-bottom: 1rem;
            line-height: 1.5;
        }
        
        .cart-badge {
            background-color: var(--error-color);
            color: white;
            border-radius: 50%;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            font-weight: bold;
            position: absolute;
            top: -8px;
            right: -8px;
        }
        
        .header {
            background: white;
            box-shadow: var(--shadow);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .nav-link {
            color: var(--text-primary);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }
        
        .nav-link:hover {
            color: var(--accent-color);
        }
        
        .footer {
            background: var(--secondary-color);
            color: white;
            padding: 3rem 0 1rem;
            margin-top: 4rem;
        }
        
        .footer-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .footer-section h3 {
            margin-bottom: 1rem;
            color: white;
        }
        
        .footer-section p, .footer-section a {
            color: #cbd5e0;
            text-decoration: none;
            line-height: 1.8;
        }
        
        .footer-section a:hover {
            color: white;
        }
        
        .footer-bottom {
            border-top: 1px solid #4a5568;
            padding-top: 1rem;
            text-align: center;
            color: #cbd5e0;
        }
        
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2rem;
            }
            
            .product-grid {
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
            }
            
            .header-content {
                flex-direction: column;
                gap: 1rem;
            }
            
            .nav-links {
                flex-wrap: wrap;
                justify-content: center;
            }
        }
        
        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--accent-color);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .alert {
            padding: 1rem;
            border-radius: var(--radius);
            margin: 1rem 0;
        }
        
        .alert-success {
            background-color: #f0fff4;
            border: 1px solid #9ae6b4;
            color: #276749;
        }
        
        .alert-error {
            background-color: #fed7d7;
            border: 1px solid #feb2b2;
            color: #c53030;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .form-input {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid var(--border-color);
            border-radius: var(--radius);
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--accent-color);
        }
        
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .modal-content {
            background: white;
            border-radius: var(--radius-lg);
            padding: 2rem;
            max-width: 500px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
        }
        """)
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

# Register startup event
nicegui_app.on_startup(startup)

# Page routes
@ui.page('/')
async def home():
    """Home page with featured Casio watches."""
    await create_home_page(product_service, asset_manager, current_user, cart_items)

@ui.page('/products')
async def products():
    """Products catalog page."""
    await create_products_page(product_service, asset_manager, current_user, cart_items)

@ui.page('/product/{product_id}')
async def product_detail(product_id: int):
    """Product detail page."""
    await create_product_detail_page(product_id, product_service, cart_service, asset_manager, current_user, cart_items)

@ui.page('/cart')
async def cart():
    """Shopping cart page."""
    await create_cart_page(cart_service, current_user, cart_items)

@ui.page('/checkout')
async def checkout():
    """Checkout page."""
    await create_checkout_page(order_service, current_user, cart_items)

@ui.page('/auth')
async def auth():
    """Authentication page (login/register)."""
    global current_user
    current_user = await create_auth_page(auth_service, current_user)

@ui.page('/profile')
async def profile():
    """User profile page."""
    await create_profile_page(auth_service, current_user)

@ui.page('/admin')
async def admin():
    """Admin panel for managing products and orders."""
    await create_admin_page(product_service, order_service, current_user)

if __name__ in {"__main__", "__mp_main__"}:
    try:
        logger.info(f"Starting Casio Watches E-commerce Application")
        logger.info(f"Server will be available at: http://{settings.host}:{settings.port}")
        
        ui.run(
            host=settings.host,
            port=settings.port,
            title="Casio Watches - Premium Timepieces",
            favicon="⌚",
            reload=settings.debug,
            show=settings.debug,
            storage_secret=settings.secret_key
        )
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        sys.exit(1)