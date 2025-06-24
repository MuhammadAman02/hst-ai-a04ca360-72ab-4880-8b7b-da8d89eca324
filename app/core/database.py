"""Database configuration and models for the Casio Watches e-commerce application."""

import asyncio
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
import os

from app.core.config import settings

# Create database directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Database setup
engine = create_engine(settings.database_url, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table for many-to-many relationship between orders and products
order_items = Table(
    'order_items',
    Base.metadata,
    Column('order_id', Integer, ForeignKey('orders.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('quantity', Integer, default=1),
    Column('price_at_time', Float)  # Store price at time of purchase
)

class User(Base):
    """User model for authentication and profile management."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")


class Category(Base):
    """Product category model."""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    image_url = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="category")


class Product(Base):
    """Product model for Casio watches."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    model = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    original_price = Column(Float)  # For showing discounts
    stock_quantity = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    # Product specifications
    case_material = Column(String(100))
    band_material = Column(String(100))
    water_resistance = Column(String(50))
    movement = Column(String(100))
    case_size = Column(String(50))
    features = Column(Text)  # JSON string of features
    
    # Images
    primary_image_url = Column(String(500))
    image_urls = Column(Text)  # JSON string of additional image URLs
    
    # SEO and metadata
    slug = Column(String(200), unique=True, index=True)
    meta_title = Column(String(200))
    meta_description = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("Order", secondary=order_items, back_populates="products")


class CartItem(Base):
    """Shopping cart item model."""
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class Order(Base):
    """Order model for purchase tracking."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Order details
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    shipping_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    
    # Status
    status = Column(String(50), default="pending")  # pending, confirmed, shipped, delivered, cancelled
    payment_status = Column(String(50), default="pending")  # pending, paid, failed, refunded
    
    # Shipping information
    shipping_name = Column(String(100))
    shipping_email = Column(String(100))
    shipping_phone = Column(String(20))
    shipping_address = Column(Text)
    shipping_city = Column(String(100))
    shipping_state = Column(String(100))
    shipping_zip = Column(String(20))
    shipping_country = Column(String(100))
    
    # Payment information
    payment_method = Column(String(50))
    payment_reference = Column(String(200))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    products = relationship("Product", secondary=order_items, back_populates="order_items")


async def init_db():
    """Initialize the database and create tables."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create default categories if they don't exist
        session = SessionLocal()
        try:
            if session.query(Category).count() == 0:
                categories = [
                    Category(
                        name="G-Shock",
                        description="Tough, durable watches built to withstand extreme conditions",
                        image_url="https://source.unsplash.com/400x300/?gshock,watch&sig=1"
                    ),
                    Category(
                        name="Edifice",
                        description="Sophisticated chronographs with advanced technology",
                        image_url="https://source.unsplash.com/400x300/?luxury,watch&sig=2"
                    ),
                    Category(
                        name="Pro Trek",
                        description="Outdoor adventure watches with advanced sensors",
                        image_url="https://source.unsplash.com/400x300/?outdoor,watch&sig=3"
                    ),
                    Category(
                        name="Baby-G",
                        description="Stylish and tough watches designed for active women",
                        image_url="https://source.unsplash.com/400x300/?fashion,watch&sig=4"
                    ),
                    Category(
                        name="Classic",
                        description="Timeless Casio digital and analog watches",
                        image_url="https://source.unsplash.com/400x300/?classic,watch&sig=5"
                    )
                ]
                
                for category in categories:
                    session.add(category)
                
                session.commit()
                print("Default categories created successfully")
        
        finally:
            session.close()
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise


def get_session() -> Session:
    """Get a database session."""
    session = SessionLocal()
    try:
        return session
    finally:
        pass  # Session will be closed by the caller


# Dependency for FastAPI (if needed)
def get_db():
    """Database dependency for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()