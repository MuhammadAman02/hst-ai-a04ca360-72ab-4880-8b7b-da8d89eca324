"""Professional visual asset management system for Casio Watches e-commerce."""

import requests
import json
from typing import Dict, List, Optional
from urllib.parse import quote
import hashlib
import logging

logger = logging.getLogger(__name__)


class CasioAssetManager:
    """Advanced professional visual asset management system for Casio watches."""
    
    # Casio-specific image categories and keywords
    CASIO_CATEGORIES = {
        "hero": {
            "keywords": ["casio", "watches", "timepiece", "luxury", "precision"],
            "style": "professional lifestyle shots"
        },
        "gshock": {
            "keywords": ["gshock", "tough", "military", "sports", "rugged"],
            "style": "action and durability focused"
        },
        "edifice": {
            "keywords": ["luxury", "chronograph", "business", "sophisticated", "steel"],
            "style": "premium business watches"
        },
        "protrek": {
            "keywords": ["outdoor", "hiking", "adventure", "compass", "altimeter"],
            "style": "outdoor adventure gear"
        },
        "babyg": {
            "keywords": ["fashion", "colorful", "women", "style", "trendy"],
            "style": "fashionable women's watches"
        },
        "classic": {
            "keywords": ["retro", "digital", "calculator", "vintage", "classic"],
            "style": "classic and vintage timepieces"
        },
        "lifestyle": {
            "keywords": ["lifestyle", "modern", "professional", "urban", "contemporary"],
            "style": "lifestyle and fashion shots"
        },
        "technology": {
            "keywords": ["technology", "innovation", "digital", "smart", "advanced"],
            "style": "technology and innovation focus"
        }
    }
    
    # Fallback images for different categories
    FALLBACK_IMAGES = {
        "hero": "https://picsum.photos/1200/600?random=1",
        "product": "https://picsum.photos/400/400?random=2",
        "category": "https://picsum.photos/300/200?random=3",
        "lifestyle": "https://picsum.photos/800/600?random=4",
        "banner": "https://picsum.photos/1000/300?random=5"
    }
    
    def __init__(self, unsplash_access_key: Optional[str] = None):
        """Initialize the asset manager with optional Unsplash API key."""
        self.unsplash_access_key = unsplash_access_key
        self.cache = {}
    
    def get_hero_images(self, count: int = 3) -> List[Dict[str, str]]:
        """Get hero banner images for the homepage."""
        images = []
        hero_keywords = self.CASIO_CATEGORIES["hero"]["keywords"]
        
        for i in range(count):
            keyword = hero_keywords[i % len(hero_keywords)]
            seed = self._generate_seed(f"hero_{keyword}_{i}")
            
            primary_url = f"https://source.unsplash.com/1200x600/?{quote(keyword)}&sig={seed}"
            fallback_url = f"https://picsum.photos/1200/600?random={seed}"
            
            images.append({
                "primary": primary_url,
                "fallback": fallback_url,
                "alt": f"Casio {keyword.title()} Collection",
                "title": f"Discover Casio {keyword.title()}",
                "description": f"Premium {keyword} timepieces for every lifestyle"
            })
        
        return images
    
    def get_category_image(self, category_name: str) -> Dict[str, str]:
        """Get image for a specific product category."""
        category_key = category_name.lower().replace("-", "").replace(" ", "")
        
        if category_key in self.CASIO_CATEGORIES:
            keywords = self.CASIO_CATEGORIES[category_key]["keywords"]
            keyword = keywords[0]  # Use primary keyword
        else:
            keyword = "watch"
        
        seed = self._generate_seed(f"category_{category_name}")
        
        return {
            "primary": f"https://source.unsplash.com/400x300/?{quote(keyword)}&sig={seed}",
            "fallback": f"https://picsum.photos/400/300?random={seed}",
            "alt": f"{category_name} Watches",
            "title": f"{category_name} Collection"
        }
    
    def get_product_images(self, product_name: str, category: str = "classic", count: int = 4) -> List[Dict[str, str]]:
        """Get multiple images for a product gallery."""
        images = []
        category_key = category.lower().replace("-", "").replace(" ", "")
        
        if category_key in self.CASIO_CATEGORIES:
            keywords = self.CASIO_CATEGORIES[category_key]["keywords"]
        else:
            keywords = ["watch", "timepiece", "casio"]
        
        for i in range(count):
            keyword = keywords[i % len(keywords)]
            seed = self._generate_seed(f"product_{product_name}_{keyword}_{i}")
            
            # Different sizes for different uses
            if i == 0:  # Main product image
                size = "500x500"
            else:  # Gallery images
                size = "400x400"
            
            images.append({
                "primary": f"https://source.unsplash.com/{size}/?{quote(keyword)}&sig={seed}",
                "fallback": f"https://picsum.photos/{size}?random={seed}",
                "alt": f"{product_name} - View {i + 1}",
                "title": f"{product_name}",
                "is_primary": i == 0
            })
        
        return images
    
    def get_lifestyle_images(self, theme: str = "professional", count: int = 6) -> List[Dict[str, str]]:
        """Get lifestyle images for marketing sections."""
        images = []
        lifestyle_themes = {
            "professional": ["business", "office", "professional", "corporate", "executive"],
            "casual": ["lifestyle", "casual", "everyday", "modern", "urban"],
            "sports": ["sports", "fitness", "active", "running", "gym"],
            "outdoor": ["outdoor", "adventure", "hiking", "nature", "exploration"]
        }
        
        keywords = lifestyle_themes.get(theme, lifestyle_themes["professional"])
        
        for i in range(count):
            keyword = keywords[i % len(keywords)]
            seed = self._generate_seed(f"lifestyle_{theme}_{keyword}_{i}")
            
            images.append({
                "primary": f"https://source.unsplash.com/600x400/?{quote(keyword)}&sig={seed}",
                "fallback": f"https://picsum.photos/600/400?random={seed}",
                "alt": f"{theme.title()} lifestyle with Casio watches",
                "title": f"{theme.title()} Collection"
            })
        
        return images
    
    def get_trust_badges(self) -> List[Dict[str, str]]:
        """Get trust and security badge images."""
        badges = [
            {
                "name": "Secure Payment",
                "icon": "fas fa-shield-alt",
                "description": "256-bit SSL encryption"
            },
            {
                "name": "Free Shipping",
                "icon": "fas fa-shipping-fast",
                "description": "On orders over $100"
            },
            {
                "name": "Warranty",
                "icon": "fas fa-certificate",
                "description": "2-year manufacturer warranty"
            },
            {
                "name": "Authentic",
                "icon": "fas fa-check-circle",
                "description": "100% genuine Casio products"
            },
            {
                "name": "Support",
                "icon": "fas fa-headset",
                "description": "24/7 customer support"
            }
        ]
        
        return badges
    
    def get_testimonial_images(self, count: int = 3) -> List[Dict[str, str]]:
        """Get customer testimonial images."""
        images = []
        
        for i in range(count):
            seed = self._generate_seed(f"testimonial_{i}")
            
            images.append({
                "primary": f"https://source.unsplash.com/150x150/?portrait,professional&sig={seed}",
                "fallback": f"https://picsum.photos/150/150?random={seed}",
                "alt": f"Customer testimonial {i + 1}",
                "name": f"Customer {i + 1}"
            })
        
        return images
    
    def _generate_seed(self, input_string: str) -> int:
        """Generate a consistent seed for image URLs."""
        return int(hashlib.md5(input_string.encode()).hexdigest()[:8], 16) % 10000
    
    def get_sample_products_data(self) -> List[Dict]:
        """Get sample product data with professional images."""
        products = [
            {
                "name": "G-Shock GA-2100-1A1",
                "model": "GA-2100-1A1",
                "category": "gshock",
                "price": 99.00,
                "original_price": 120.00,
                "description": "The iconic octagonal bezel design in a slim profile. Carbon Core Guard structure provides ultimate toughness.",
                "case_material": "Carbon / Resin",
                "band_material": "Resin",
                "water_resistance": "200M",
                "movement": "Quartz",
                "case_size": "45.4mm",
                "features": "Shock Resistant, 200M Water Resistant, LED Light, World Time, Stopwatch, Countdown Timer",
                "stock_quantity": 25,
                "is_featured": True
            },
            {
                "name": "Edifice EQB-1000D-1A",
                "model": "EQB-1000D-1A",
                "category": "edifice",
                "price": 399.00,
                "original_price": 450.00,
                "description": "Sophisticated chronograph with Bluetooth connectivity and smartphone link functionality.",
                "case_material": "Stainless Steel",
                "band_material": "Stainless Steel",
                "water_resistance": "100M",
                "movement": "Solar Powered",
                "case_size": "47.1mm",
                "features": "Bluetooth, Solar Power, Smartphone Link, World Time, Chronograph, Alarm",
                "stock_quantity": 15,
                "is_featured": True
            },
            {
                "name": "Pro Trek PRW-6900Y-1",
                "model": "PRW-6900Y-1",
                "category": "protrek",
                "price": 320.00,
                "description": "Advanced outdoor watch with Triple Sensor technology for altitude, barometric pressure, and compass readings.",
                "case_material": "Resin / Stainless Steel",
                "band_material": "Resin",
                "water_resistance": "100M",
                "movement": "Solar Powered",
                "case_size": "56.7mm",
                "features": "Triple Sensor, Solar Power, Radio Controlled, Tide Graph, Moon Data, Sunrise/Sunset",
                "stock_quantity": 20,
                "is_featured": True
            },
            {
                "name": "Baby-G BA-110-1A",
                "model": "BA-110-1A",
                "category": "babyg",
                "price": 89.00,
                "description": "Stylish and tough watch designed for active women with shock resistance and 100M water resistance.",
                "case_material": "Resin",
                "band_material": "Resin",
                "water_resistance": "100M",
                "movement": "Quartz",
                "case_size": "43.4mm",
                "features": "Shock Resistant, 100M Water Resistant, LED Light, World Time, Stopwatch, Countdown Timer",
                "stock_quantity": 30,
                "is_featured": False
            },
            {
                "name": "Classic F-91W-1",
                "model": "F-91W-1",
                "category": "classic",
                "price": 15.95,
                "description": "The legendary Casio digital watch. Simple, reliable, and iconic design that has stood the test of time.",
                "case_material": "Resin",
                "band_material": "Resin",
                "water_resistance": "30M",
                "movement": "Quartz",
                "case_size": "38.2mm",
                "features": "LED Light, Stopwatch, Alarm, Calendar, 7-year battery life",
                "stock_quantity": 100,
                "is_featured": False
            },
            {
                "name": "G-Shock DW-5600E-1V",
                "model": "DW-5600E-1V",
                "category": "gshock",
                "price": 49.00,
                "description": "The original G-Shock square design. Tough, reliable, and built to last with classic shock resistance.",
                "case_material": "Resin",
                "band_material": "Resin",
                "water_resistance": "200M",
                "movement": "Quartz",
                "case_size": "42.8mm",
                "features": "Shock Resistant, 200M Water Resistant, EL Backlight, Stopwatch, Multi-function Alarm",
                "stock_quantity": 50,
                "is_featured": False
            },
            {
                "name": "Edifice EFV-100L-1A",
                "model": "EFV-100L-1A",
                "category": "edifice",
                "price": 179.00,
                "description": "Elegant chronograph with leather band, perfect for business and formal occasions.",
                "case_material": "Stainless Steel",
                "band_material": "Leather",
                "water_resistance": "100M",
                "movement": "Quartz",
                "case_size": "44.5mm",
                "features": "Chronograph, Date Display, Luminous Hands, Screw-in Crown",
                "stock_quantity": 18,
                "is_featured": False
            },
            {
                "name": "Pro Trek PRG-330-1",
                "model": "PRG-330-1",
                "category": "protrek",
                "price": 199.00,
                "description": "Compact outdoor watch with essential sensors and solar power for extended adventures.",
                "case_material": "Resin",
                "band_material": "Resin",
                "water_resistance": "100M",
                "movement": "Solar Powered",
                "case_size": "51.6mm",
                "features": "Triple Sensor, Solar Power, Low Temperature Resistant, Duplex LCD",
                "stock_quantity": 22,
                "is_featured": False
            }
        ]
        
        # Add images to each product
        for product in products:
            product["images"] = self.get_product_images(
                product["name"], 
                product["category"], 
                count=4
            )
            product["primary_image"] = product["images"][0]["primary"]
        
        return products
    
    @staticmethod
    def generate_image_css() -> str:
        """Generate CSS for professional image handling."""
        return """
        /* Professional Image System for Casio Watches */
        .hero-image {
            width: 100%;
            height: 500px;
            object-fit: cover;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
        }
        
        .product-image {
            width: 100%;
            height: 250px;
            object-fit: cover;
            border-radius: var(--radius-md);
            transition: transform 0.3s ease;
            background: #f8f9fa;
        }
        
        .product-image:hover {
            transform: scale(1.05);
        }
        
        .product-gallery {
            display: grid;
            grid-template-columns: 1fr 100px;
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .main-product-image {
            width: 100%;
            height: 400px;
            object-fit: cover;
            border-radius: var(--radius-lg);
            border: 2px solid var(--border-color);
        }
        
        .thumbnail-images {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .thumbnail-image {
            width: 100px;
            height: 100px;
            object-fit: cover;
            border-radius: var(--radius);
            border: 2px solid transparent;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .thumbnail-image:hover,
        .thumbnail-image.active {
            border-color: var(--accent-color);
            transform: scale(1.05);
        }
        
        .category-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: var(--radius-lg);
        }
        
        .lifestyle-image {
            width: 100%;
            height: 300px;
            object-fit: cover;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
        }
        
        .testimonial-avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid white;
            box-shadow: var(--shadow);
        }
        
        .trust-badge {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: white;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            text-align: left;
        }
        
        .trust-badge i {
            font-size: 2rem;
            color: var(--accent-color);
        }
        
        .image-loading {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
        }
        
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        .image-error {
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .hero-image {
                height: 300px;
            }
            
            .product-gallery {
                grid-template-columns: 1fr;
            }
            
            .thumbnail-images {
                flex-direction: row;
                overflow-x: auto;
                padding-bottom: 0.5rem;
            }
            
            .main-product-image {
                height: 300px;
            }
        }
        """