"""Order service for managing purchase orders and checkout process."""

import secrets
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.core.database import get_session, Order, Product, CartItem, User
from app.services.cart_service import CartService


class OrderService:
    """Service for managing orders and checkout process."""
    
    def __init__(self):
        self.cart_service = CartService()
    
    def _generate_order_number(self) -> str:
        """Generate unique order number."""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = secrets.token_hex(4).upper()
        return f"CW{timestamp}{random_suffix}"
    
    async def create_order_from_cart(self, user_id: int, shipping_info: Dict[str, Any], payment_method: str = "stripe") -> Dict[str, Any]:
        """Create order from user's cart."""
        session = get_session()
        try:
            # Validate cart
            cart_validation = await self.cart_service.validate_cart_for_checkout(user_id)
            if not cart_validation["valid"]:
                return {"success": False, "message": cart_validation["message"]}
            
            # Get cart summary
            cart_summary = await self.cart_service.get_cart_summary(user_id)
            if not cart_summary["items"]:
                return {"success": False, "message": "Cart is empty"}
            
            # Create order
            order_number = self._generate_order_number()
            order = Order(
                order_number=order_number,
                user_id=user_id,
                total_amount=cart_summary["total_amount"],
                tax_amount=cart_summary["tax_amount"],
                shipping_amount=cart_summary["shipping_amount"],
                discount_amount=0.0,
                status="pending",
                payment_status="pending",
                payment_method=payment_method,
                shipping_name=shipping_info.get("name", ""),
                shipping_email=shipping_info.get("email", ""),
                shipping_phone=shipping_info.get("phone", ""),
                shipping_address=shipping_info.get("address", ""),
                shipping_city=shipping_info.get("city", ""),
                shipping_state=shipping_info.get("state", ""),
                shipping_zip=shipping_info.get("zip", ""),
                shipping_country=shipping_info.get("country", "USA")
            )
            
            session.add(order)
            session.flush()  # Get order ID
            
            # Add order items and update stock
            cart_items = session.query(CartItem).filter(CartItem.user_id == user_id).all()
            
            for cart_item in cart_items:
                product = cart_item.product
                
                # Check stock one more time
                if product.stock_quantity < cart_item.quantity:
                    session.rollback()
                    return {"success": False, "message": f"Insufficient stock for {product.name}"}
                
                # Update product stock
                product.stock_quantity -= cart_item.quantity
                
                # Add to order_items table (many-to-many relationship)
                # Note: This is a simplified approach. In production, you might want a separate OrderItem table
                order.products.append(product)
            
            # Clear cart
            session.query(CartItem).filter(CartItem.user_id == user_id).delete()
            
            session.commit()
            
            return {
                "success": True,
                "message": "Order created successfully",
                "order": {
                    "id": order.id,
                    "order_number": order.order_number,
                    "total_amount": order.total_amount,
                    "status": order.status,
                    "created_at": order.created_at
                }
            }
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Order creation failed: {str(e)}"}
        finally:
            session.close()
    
    async def get_user_orders(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get orders for a specific user."""
        session = get_session()
        try:
            orders = session.query(Order).filter(Order.user_id == user_id).order_by(desc(Order.created_at)).offset(offset).limit(limit).all()
            
            result = []
            for order in orders:
                result.append({
                    "id": order.id,
                    "order_number": order.order_number,
                    "total_amount": order.total_amount,
                    "tax_amount": order.tax_amount,
                    "shipping_amount": order.shipping_amount,
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "payment_method": order.payment_method,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "shipped_at": order.shipped_at,
                    "delivered_at": order.delivered_at,
                    "item_count": len(order.products)
                })
            
            return result
            
        finally:
            session.close()
    
    async def get_order_by_id(self, order_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get order details by ID."""
        session = get_session()
        try:
            query = session.query(Order).filter(Order.id == order_id)
            if user_id:
                query = query.filter(Order.user_id == user_id)
            
            order = query.first()
            if not order:
                return None
            
            # Get order items (products)
            order_items = []
            for product in order.products:
                order_items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_model": product.model,
                    "product_image": product.primary_image_url,
                    "price": product.price,
                    "quantity": 1  # This is simplified - in production you'd store quantity in order_items table
                })
            
            return {
                "id": order.id,
                "order_number": order.order_number,
                "user_id": order.user_id,
                "total_amount": order.total_amount,
                "tax_amount": order.tax_amount,
                "shipping_amount": order.shipping_amount,
                "discount_amount": order.discount_amount,
                "status": order.status,
                "payment_status": order.payment_status,
                "payment_method": order.payment_method,
                "payment_reference": order.payment_reference,
                "shipping_info": {
                    "name": order.shipping_name,
                    "email": order.shipping_email,
                    "phone": order.shipping_phone,
                    "address": order.shipping_address,
                    "city": order.shipping_city,
                    "state": order.shipping_state,
                    "zip": order.shipping_zip,
                    "country": order.shipping_country
                },
                "items": order_items,
                "created_at": order.created_at,
                "updated_at": order.updated_at,
                "shipped_at": order.shipped_at,
                "delivered_at": order.delivered_at
            }
            
        finally:
            session.close()
    
    async def update_order_status(self, order_id: int, status: str, payment_reference: str = None) -> Dict[str, Any]:
        """Update order status."""
        session = get_session()
        try:
            order = session.query(Order).filter(Order.id == order_id).first()
            if not order:
                return {"success": False, "message": "Order not found"}
            
            valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
            if status not in valid_statuses:
                return {"success": False, "message": "Invalid status"}
            
            order.status = status
            order.updated_at = datetime.now()
            
            if payment_reference:
                order.payment_reference = payment_reference
                order.payment_status = "paid"
            
            if status == "shipped":
                order.shipped_at = datetime.now()
            elif status == "delivered":
                order.delivered_at = datetime.now()
            
            session.commit()
            
            return {"success": True, "message": f"Order status updated to {status}"}
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Status update failed: {str(e)}"}
        finally:
            session.close()
    
    async def get_all_orders(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all orders (admin only)."""
        session = get_session()
        try:
            query = session.query(Order).order_by(desc(Order.created_at))
            
            if status:
                query = query.filter(Order.status == status)
            
            orders = query.offset(offset).limit(limit).all()
            
            result = []
            for order in orders:
                # Get user info
                user = session.query(User).filter(User.id == order.user_id).first()
                
                result.append({
                    "id": order.id,
                    "order_number": order.order_number,
                    "user_id": order.user_id,
                    "user_name": user.full_name if user else "Unknown",
                    "user_email": user.email if user else "Unknown",
                    "total_amount": order.total_amount,
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "payment_method": order.payment_method,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "item_count": len(order.products)
                })
            
            return result
            
        finally:
            session.close()
    
    async def get_order_statistics(self) -> Dict[str, Any]:
        """Get order statistics for dashboard."""
        session = get_session()
        try:
            total_orders = session.query(Order).count()
            pending_orders = session.query(Order).filter(Order.status == "pending").count()
            completed_orders = session.query(Order).filter(Order.status == "delivered").count()
            
            # Calculate total revenue
            total_revenue = session.query(Order).filter(Order.payment_status == "paid").with_entities(
                func.sum(Order.total_amount)
            ).scalar() or 0
            
            # Get recent orders
            recent_orders = session.query(Order).order_by(desc(Order.created_at)).limit(5).all()
            
            return {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "completed_orders": completed_orders,
                "total_revenue": float(total_revenue),
                "recent_orders": [
                    {
                        "id": order.id,
                        "order_number": order.order_number,
                        "total_amount": order.total_amount,
                        "status": order.status,
                        "created_at": order.created_at
                    }
                    for order in recent_orders
                ]
            }
            
        finally:
            session.close()
    
    async def cancel_order(self, order_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Cancel an order and restore stock."""
        session = get_session()
        try:
            query = session.query(Order).filter(Order.id == order_id)
            if user_id:
                query = query.filter(Order.user_id == user_id)
            
            order = query.first()
            if not order:
                return {"success": False, "message": "Order not found"}
            
            if order.status in ["shipped", "delivered", "cancelled"]:
                return {"success": False, "message": "Order cannot be cancelled"}
            
            # Restore stock for all products in the order
            for product in order.products:
                product.stock_quantity += 1  # Simplified - in production, store actual quantities
            
            order.status = "cancelled"
            order.updated_at = datetime.now()
            
            session.commit()
            
            return {"success": True, "message": "Order cancelled successfully"}
            
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Cancellation failed: {str(e)}"}
        finally:
            session.close()