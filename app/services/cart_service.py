"""Shopping cart service for managing user cart operations."""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_session, CartItem, Product, User


class CartService:
    """Service for managing shopping cart operations."""
    
    def __init__(self):
        pass
    
    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Add item to user's cart."""
        session = get_session()
        try:
            # Check if product exists and is active
            product = session.query(Product).filter(
                and_(Product.id == product_id, Product.is_active == True)
            ).first()
            
            if not product:
                return {"success": False, "message": "Product not found"}
            
            # Check stock availability
            if product.stock_quantity < quantity:
                return {"success": False, "message": "Insufficient stock"}
            
            # Check if item already exists in cart
            existing_item = session.query(CartItem).filter(
                and_(CartItem.user_id == user_id, CartItem.product_id == product_id)
            ).first()
            
            if existing_item:
                # Update quantity
                new_quantity = existing_item.quantity + quantity
                if product.stock_quantity < new_quantity:
                    return {"success": False, "message": "Insufficient stock"}
                
                existing_item.quantity = new_quantity
            else:
                # Create new cart item
                cart_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity
                )
                session.add(cart_item)
            
            session.commit()
            return {"success": True, "message": "Item added to cart"}
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Error adding to cart: {str(e)}"}
        finally:
            session.close()
    
    async def remove_from_cart(self, user_id: int, product_id: int) -> Dict[str, Any]:
        """Remove item from user's cart."""
        session = get_session()
        try:
            cart_item = session.query(CartItem).filter(
                and_(CartItem.user_id == user_id, CartItem.product_id == product_id)
            ).first()
            
            if not cart_item:
                return {"success": False, "message": "Item not found in cart"}
            
            session.delete(cart_item)
            session.commit()
            return {"success": True, "message": "Item removed from cart"}
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Error removing from cart: {str(e)}"}
        finally:
            session.close()
    
    async def update_cart_item_quantity(self, user_id: int, product_id: int, quantity: int) -> Dict[str, Any]:
        """Update quantity of item in cart."""
        session = get_session()
        try:
            if quantity <= 0:
                return await self.remove_from_cart(user_id, product_id)
            
            cart_item = session.query(CartItem).filter(
                and_(CartItem.user_id == user_id, CartItem.product_id == product_id)
            ).first()
            
            if not cart_item:
                return {"success": False, "message": "Item not found in cart"}
            
            # Check stock availability
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product or product.stock_quantity < quantity:
                return {"success": False, "message": "Insufficient stock"}
            
            cart_item.quantity = quantity
            session.commit()
            return {"success": True, "message": "Cart updated"}
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Error updating cart: {str(e)}"}
        finally:
            session.close()
    
    async def get_cart_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all items in user's cart."""
        session = get_session()
        try:
            cart_items = session.query(CartItem).filter(CartItem.user_id == user_id).all()
            
            result = []
            for item in cart_items:
                product = item.product
                if product and product.is_active:
                    result.append({
                        'id': item.id,
                        'product_id': product.id,
                        'product_name': product.name,
                        'product_model': product.model,
                        'product_price': product.price,
                        'product_image': product.primary_image_url,
                        'quantity': item.quantity,
                        'subtotal': product.price * item.quantity,
                        'stock_available': product.stock_quantity,
                        'added_at': item.created_at
                    })
            
            return result
            
        finally:
            session.close()
    
    async def get_cart_summary(self, user_id: int) -> Dict[str, Any]:
        """Get cart summary with totals."""
        cart_items = await self.get_cart_items(user_id)
        
        total_items = sum(item['quantity'] for item in cart_items)
        subtotal = sum(item['subtotal'] for item in cart_items)
        
        # Calculate tax (8% for example)
        tax_rate = 0.08
        tax_amount = subtotal * tax_rate
        
        # Calculate shipping (free over $100)
        shipping_amount = 0.0 if subtotal >= 100 else 9.99
        
        total_amount = subtotal + tax_amount + shipping_amount
        
        return {
            'items': cart_items,
            'total_items': total_items,
            'subtotal': round(subtotal, 2),
            'tax_amount': round(tax_amount, 2),
            'shipping_amount': round(shipping_amount, 2),
            'total_amount': round(total_amount, 2),
            'free_shipping_eligible': subtotal >= 100,
            'free_shipping_remaining': max(0, 100 - subtotal) if subtotal < 100 else 0
        }
    
    async def clear_cart(self, user_id: int) -> Dict[str, Any]:
        """Clear all items from user's cart."""
        session = get_session()
        try:
            session.query(CartItem).filter(CartItem.user_id == user_id).delete()
            session.commit()
            return {"success": True, "message": "Cart cleared"}
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Error clearing cart: {str(e)}"}
        finally:
            session.close()
    
    async def get_cart_count(self, user_id: int) -> int:
        """Get total number of items in user's cart."""
        session = get_session()
        try:
            cart_items = session.query(CartItem).filter(CartItem.user_id == user_id).all()
            return sum(item.quantity for item in cart_items)
            
        finally:
            session.close()
    
    async def validate_cart_for_checkout(self, user_id: int) -> Dict[str, Any]:
        """Validate cart items before checkout."""
        session = get_session()
        try:
            cart_items = session.query(CartItem).filter(CartItem.user_id == user_id).all()
            
            if not cart_items:
                return {"valid": False, "message": "Cart is empty"}
            
            issues = []
            for item in cart_items:
                product = item.product
                if not product or not product.is_active:
                    issues.append(f"Product {item.product_id} is no longer available")
                elif product.stock_quantity < item.quantity:
                    issues.append(f"{product.name} has insufficient stock (available: {product.stock_quantity}, requested: {item.quantity})")
            
            if issues:
                return {"valid": False, "message": "Cart validation failed", "issues": issues}
            
            return {"valid": True, "message": "Cart is valid for checkout"}
            
        finally:
            session.close()