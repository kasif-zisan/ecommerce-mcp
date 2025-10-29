"""
FakeStore API to PostgreSQL Database Populator
Fetches product data from FakeStore API and populates historical inventory database
with modified prices, ratings, and stock levels to simulate 6-month-old data.
"""

import requests
import psycopg2
from psycopg2 import sql
import random
from decimal import Decimal
from typing import List, Dict
import json

# ============================================
# Configuration
# ============================================

API_URL = "https://fakestoreapi.com/products/"

# Database connection parameters
DB_CONFIG = {
    'dbname': 'products',
    'user': 'postgres',      # Change this to your PostgreSQL username
    'password': 'pwd',  # Change this to your PostgreSQL password
    'host': 'localhost',
    'port': '5432'
}

# Historical data simulation parameters
PRICE_REDUCTION_RANGE = (0.70, 0.90)   # ±30% variation
RATING_VARIATION_RANGE = (0.70, 0.90)  # ±30% variation
STOCK_INCREASE_RANGE = (1.50, 1.80)    # 50-80% higher than rating count

# ============================================
# Functions
# ============================================

def fetch_products_from_api() -> List[Dict]:
    """
    Fetch all products from FakeStore API
    
    Returns:
        List of product dictionaries
    """
    print("📡 Fetching products from FakeStore API...")
    
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes
        
        products = response.json()
        print(f"✅ Successfully fetched {len(products)} products from API")
        return products
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data from API: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON response: {e}")
        raise


def transform_product_for_database(api_product: Dict) -> Dict:
    """
    Transform API product data to database format with historical modifications
    
    Args:
        api_product: Product data from API
        
    Returns:
        Transformed product dictionary ready for database insertion
    """
    # Extract original values
    original_price = api_product['price']
    original_rating = api_product['rating']['rate']
    original_count = api_product['rating']['count']
    
    # Apply transformations for historical simulation
    historical_price = round(
        original_price * random.uniform(*PRICE_REDUCTION_RANGE), 
        2
    )
    
    historical_rating = round(
        original_rating * random.uniform(*RATING_VARIATION_RANGE), 
        2
    )
    
    # Ensure rating stays within valid range (0-5)
    historical_rating = max(0.0, min(5.0, historical_rating))
    
    # Calculate stock based on rating count (simulating full inventory 6 months ago)
    historical_stock = int(
        original_count * random.uniform(*STOCK_INCREASE_RANGE)
    )
    
    transformed_product = {
        'id': api_product['id'],
        'title': api_product['title'],
        'price': Decimal(str(historical_price)),
        'category': api_product['category'],
        'rating': Decimal(str(historical_rating)),
        'stock': historical_stock
    }
    
    # Print transformation details
    print(f"\n📦 Product ID {api_product['id']}: {api_product['title'][:50]}...")
    print(f"   💰 Price: ${original_price:.2f} → ${historical_price:.2f} ({((historical_price/original_price - 1) * 100):.1f}%)")
    print(f"   ⭐ Rating: {original_rating:.1f} → {historical_rating:.1f} ({((historical_rating/original_rating - 1) * 100):.1f}%)")
    print(f"   📊 Stock: {original_count} → {historical_stock} ({((historical_stock/original_count - 1) * 100):.1f}%)")
    
    return transformed_product


def connect_to_database() -> psycopg2.extensions.connection:
    """
    Establish connection to PostgreSQL database
    
    Returns:
        Database connection object
    """
    print("\n🔌 Connecting to PostgreSQL database...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Successfully connected to database")
        return conn
        
    except psycopg2.Error as e:
        print(f"❌ Error connecting to database: {e}")
        raise


def insert_products_to_database(conn: psycopg2.extensions.connection, 
                                products: List[Dict]) -> None:
    """
    Insert transformed products into PostgreSQL database
    
    Args:
        conn: Database connection object
        products: List of transformed product dictionaries
    """
    print("\n💾 Inserting products into database...")
    
    cursor = conn.cursor()
    
    insert_query = sql.SQL("""
        INSERT INTO products (id, title, price, category, rating, stock)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            price = EXCLUDED.price,
            category = EXCLUDED.category,
            rating = EXCLUDED.rating,
            stock = EXCLUDED.stock,
            created_at = CURRENT_TIMESTAMP
    """)
    
    inserted_count = 0
    
    try:
        for product in products:
            cursor.execute(
                insert_query,
                (
                    product['id'],
                    product['title'],
                    product['price'],
                    product['category'],
                    product['rating'],
                    product['stock']
                )
            )
            inserted_count += 1
        
        conn.commit()
        print(f"✅ Successfully inserted {inserted_count} products into database")
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Error inserting products: {e}")
        raise
    finally:
        cursor.close()

def main():
    """
    Main execution function
    """
    print("\n" + "=" * 60)
    print("🚀 FakeStore API to PostgreSQL Database Populator")
    print("=" * 60)
    
    conn = None
    
    try:
        # Step 1: Fetch products from API
        api_products = fetch_products_from_api()
        
        # Step 2: Transform products for historical database
        print("\n🔄 Transforming products for historical database...")
        transformed_products = [
            transform_product_for_database(product) 
            for product in api_products
        ]
        
        # Step 3: Connect to database
        conn = connect_to_database()
        
        # Step 4: Insert products into database
        insert_products_to_database(conn, transformed_products)
        
        print("\n✅ Database population completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1
        
    finally:
        if conn:
            conn.close()
            print("\n🔌 Database connection closed")
    
    return 0


# ============================================
# Script Entry Point
# ============================================

if __name__ == "__main__":
    exit(main())