"""Product service for managing Casio watches catalog."""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_session, Product, Category
from app.core.assets import CasioAssetManager


class ProductService:
    """Service for managing products and catalog operations."""
    
    def __init__(self):
        self.asset_manager = CasioAssetManager()
    
    async def initialize_sample_data(self):
        """Initialize sample Casio watch data."""
        session = get_session()
        try:
            # Check if products already exist
            if session.query(Product).count() > 0:
                return
            
            # Get sample products data
            sample_products = self.asset_manager.get_sample_products_data()
            
            for product_data in sample_products:
                # Get category
                category = session.query(Category).filter(
                    Category.name.ilike(f"%{product_data['category']}%")
                ).first()
                
                if not category:
                    # Create category if it doesn't exist
                    category_name = product_data['category'].title()
                    if product_data['category'] == 'gshock':
                        category_name = 'G-Shock'
                    elif product_data['category'] == 'babyg':
                        category_name = 'Baby-G'
                    elif product_data['category'] == 'protrek':
                        category_name = 'Pro Trek'
                    
                    category = Category(
                        name=category_name,
                        description=f"{category_name} collection",
                        image_url=self.asset_manager.get_category_image(category_name)["primary"]
                    )
                    session.add(category)
                    session.flush()
                
                # Create slug from name
                slug = product_data['name'].lower().replace(' ', '-').replace('/', '-')
                
                # Create product
                product = Product(
                    name=product_data['name'],
                    model=product_data['model'],
                    description=product_data['description'],
                    price=product_data['price'],
                    original_price=product_data.get('original_price'),
                    stock_quantity=product_data['stock_quantity'],
                    category_id=category.id,
                    case_material=product_data.get('case_material'),
                    band_material=product_data.get('band_material'),
                    water_resistance=product_data.get('water_resistance'),
                    movement=product_data.get('movement'),
                    case_size=product_data.get('case_size'),
                    features=product_data.get('features'),
                    primary_image_url=product_data['primary_image'],
                    image_urls=json.dumps([img['primary'] for img in product_data['images']]),
                    slug=slug,
                    meta_title=f"{product_data['name']} - Casio Watches",
                    meta_description=product_data['description'][:160],
                    is_active=True,
                    is_featured=product_data.get('is_featured', False)
                )
                
                session.add(product)
            
            session.commit()
            print("Sample products created successfully")
            
        except Exception as e:
            session.rollback()
            print(f"Error creating sample products: {e}")
            raise
        finally:
            session.close()
    
    async def get_all_products(self, 
                             category_id: Optional[int] = None,
                             search: Optional[str] = None,
                             min_price: Optional[float] = None,
                             max_price: Optional[float] = None,
                             featured_only: bool = False,
                             limit: int = 50,
                             offset: int = 0) -> List[Dict[str, Any]]:
        """Get products with filtering options."""
        session = get_session()
        try:
            query = session.query(Product).filter(Product.is_active == True)
            
            # Apply filters
            if category_id:
                query = query.filter(Product.category_id == category_id)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Product.name.ilike(search_term),
                        Product.model.ilike(search_term),
                        Product.description.ilike(search_term)
                    )
                )
            
            if min_price is not None:
                query = query.filter(Product.price >= min_price)
            
            if max_price is not None:
                query = query.filter(Product.price <= max_price)
            
            if featured_only:
                query = query.filter(Product.is_featured == True)
            
            # Apply pagination
            products = query.offset(offset).limit(limit).all()
            
            # Convert to dict format
            result = []
            for product in products:
                product_dict = {
                    'id': product.id,
                    'name': product.name,
                    'model': product.model,
                    'description': product.description,
                    'price': product.price,
                    'original_price': product.original_price,
                    'stock_quantity': product.stock_quantity,
                    'category': product.category.name if product.category else None,
                    'case_material': product.case_material,
                    'band_material': product.band_material,
                    'water_resistance': product.water_resistance,
                    'movement': product.movement,
                    'case_size': product.case_size,
                    'features': product.features,
                    'primary_image_url': product.primary_image_url,
                    'image_urls': json.loads(product.image_urls) if product.image_urls else [],
                    'slug': product.slug,
                    'is_featured': product.is_featured,
                    'created_at': product.created_at,
                    'discount_percentage': self._calculate_discount_percentage(
                        product.price, product.original_price
                    )
                }
                result.append(product_dict)
            
            return result
            
        finally:
            session.close()
    
    async def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a single product by ID."""
        session = get_session()
        try:
            product = session.query(Product).filter(
                and_(Product.id == product_id, Product.is_active == True)
            ).first()
            
            if not product:
                return None
            
            return {
                'id': product.id,
                'name': product.name,
                'model': product.model,
                'description': product.description,
                'price': product.price,
                'original_price': product.original_price,
                'stock_quantity': product.stock_quantity,
                'category': product.category.name if product.category else None,
                'category_id': product.category_id,
                'case_material': product.case_material,
                'band_material': product.band_material,
                'water_resistance': product.water_resistance,
                'movement': product.movement,
                'case_size': product.case_size,
                'features': product.features,
                'primary_image_url': product.primary_image_url,
                'image_urls': json.loads(product.image_urls) if product.image_urls else [],
                'slug': product.slug,
                'meta_title': product.meta_title,
                'meta_description': product.meta_description,
                'is_featured': product.is_featured,
                'created_at': product.created_at,
                'discount_percentage': self._calculate_discount_percentage(
                    product.price, product.original_price
                )
            }
            
        finally:
            session.close()
    
    async def get_featured_products(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Get featured products for homepage."""
        return await self.get_all_products(featured_only=True, limit=limit)
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all product categories."""
        session = get_session()
        try:
            categories = session.query(Category).all()
            
            result = []
            for category in categories:
                # Get product count for each category
                product_count = session.query(Product).filter(
                    and_(Product.category_id == category.id, Product.is_active == True)
                ).count()
                
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'image_url': category.image_url,
                    'product_count': product_count,
                    'created_at': category.created_at
                })
            
            return result
            
        finally:
            session.close()
    
    async def search_products(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search products by name, model, or description."""
        return await self.get_all_products(search=query, limit=limit)
    
    async def get_related_products(self, product_id: int, limit: int = 4) -> List[Dict[str, Any]]:
        """Get related products based on category."""
        session = get_session()
        try:
            # Get the current product's category
            current_product = session.query(Product).filter(Product.id == product_id).first()
            if not current_product:
                return []
            
            # Get other products in the same category
            related_products = session.query(Product).filter(
                and_(
                    Product.category_id == current_product.category_id,
                    Product.id != product_id,
                    Product.is_active == True
                )
            ).limit(limit).all()
            
            result = []
            for product in related_products:
                result.append({
                    'id': product.id,
                    'name': product.name,
                    'model': product.model,
                    'price': product.price,
                    'original_price': product.original_price,
                    'primary_image_url': product.primary_image_url,
                    'slug': product.slug,
                    'discount_percentage': self._calculate_discount_percentage(
                        product.price, product.original_price
                    )
                })
            
            return result
            
        finally:
            session.close()
    
    def _calculate_discount_percentage(self, current_price: float, original_price: Optional[float]) -> Optional[int]:
        """Calculate discount percentage."""
        if not original_price or original_price <= current_price:
            return None
        
        discount = ((original_price - current_price) / original_price) * 100
        return int(round(discount))
    
    async def update_stock(self, product_id: int, quantity_change: int) -> bool:
        """Update product stock quantity."""
        session = get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
            
            new_quantity = product.stock_quantity + quantity_change
            if new_quantity < 0:
                return False
            
            product.stock_quantity = new_quantity
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error updating stock: {e}")
            return False
        finally:
            session.close()
    
    async def check_stock_availability(self, product_id: int, requested_quantity: int) -> bool:
        """Check if requested quantity is available in stock."""
        session = get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
            
            return product.stock_quantity >= requested_quantity
            
        finally:
            session.close()