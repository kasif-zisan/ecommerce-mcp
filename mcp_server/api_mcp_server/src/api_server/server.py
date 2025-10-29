"""
API MCP Server

This server provides access to current/live product data from the FakeStore API. It's designed to work in conjunction with a Database MCP server to enable 
comparative analysis between historical (6 months ago) and current inventory data.

API Source: https://fakestoreapi.com/products/
Response: Returns 20 products with current pricing and stock information

Key Feature Engineering:
    API Field: rating.count → Used as current_stock (current inventory level)
    This allows direct comparison with historical_stock from the database.

Data Mapping:
    API Response          →  Usage
    ------------------------------------------
    id                    →  Product identifier (matches DB)
    title                 →  Product name
    price                 →  Current market price
    category              →  Product category
    rating.rate           →  Current rating (0-5)
    rating.count          →  Current stock level 
    description           →  Product description
    image                 →  Product image URL

Integration Pattern:
    1. Database MCP fetches historical data (historical_stock, historical_price)
    2. This API MCP fetches current data (rating.count, price)
    3. Orchestrator LLM compares and calculates:
       - Stock depletion rate
       - Price change percentage
       - Restock cost impact
"""

import httpx
import os
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigSchema(BaseModel):
    """Configuration schema for API server authentication."""
    api_password: str = Field(
        description="Password for API access (must match API_PASS in .env file)"
    )


class APIService:
    """
    Service class to handle all FakeStore API operations.
    
    This service manages HTTP requests to the FakeStore API and handles
    response parsing, error handling, and data transformation.
    """
    
    # FakeStore API configuration
    BASE_URL = "https://fakestoreapi.com"
    PRODUCTS_ENDPOINT = "/products"
    REQUEST_TIMEOUT = 30  # 30 seconds timeout
    
    def __init__(self):
        """Initialize the API service with HTTP client."""
        self.client = httpx.Client(timeout=self.REQUEST_TIMEOUT)
    
    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make HTTP GET request to the API.
        
        Args:
            endpoint: API endpoint path (e.g., "/products")
            
        Returns:
            Dictionary containing response data or error
            
        Raises:
            Exception: If request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.client.get(url)
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes
            return response.json()
        
        except httpx.TimeoutException:
            raise Exception(f"Request timeout: API did not respond within {self.REQUEST_TIMEOUT} seconds")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {str(e)}")
        except httpx.RequestError as e:
            raise Exception(f"Request error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
    
    def get_all_products(self) -> Dict[str, Any]:
        """
        Fetch all products from the FakeStore API.
        
        The API returns 20 products with complete information including
        current pricing and stock levels (via rating.count).
        
        Returns:
            Dictionary containing:
                - success: Boolean indicating operation status
                - product_count: Number of products returned
                - data: List of product dictionaries with current data
                - summary: Aggregate statistics about current inventory
                
        Product Structure:
            Each product contains:
            - id: Product identifier
            - title: Product name
            - price: Current market price (USD)
            - description: Product description
            - category: Product category
            - image: Product image URL
            - rating: {
                rate: Current rating (0-5),
                count: Current stock level 
              }
        """
        try:
            products = self._make_request(self.PRODUCTS_ENDPOINT)
            
            # Validate response
            if not isinstance(products, list):
                return {
                    "error": "Invalid API response: expected list of products",
                    "success": False
                }
            
            # Calculate summary statistics
            summary = self._calculate_summary(products)
            
            return {
                "success": True,
                "product_count": len(products),
                "data": products,
                "summary": summary,
                "message": f"Successfully fetched {len(products)} products from FakeStore API"
            }
        
        except Exception as e:
            return {
                "error": f"Failed to fetch products: {str(e)}",
                "success": False
            }
    
    def _calculate_summary(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate statistics from product data.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Dictionary with summary statistics
        """
        if not products:
            return {
                "total_products": 0,
                "avg_current_price": 0,
                "avg_current_stock": 0,
                "min_current_stock": 0,
                "max_current_stock": 0,
                "avg_current_rating": 0,
                "total_current_inventory_value": 0,
                "categories": []
            }
        
        # Extract values
        prices = [float(p.get('price', 0)) for p in products]
        stocks = [int(p.get('rating', {}).get('count', 0)) for p in products]
        ratings = [float(p.get('rating', {}).get('rate', 0)) for p in products]
        categories = list(set(p.get('category', 'unknown') for p in products))
        
        # Calculate inventory value
        total_value = sum(
            float(p.get('price', 0)) * int(p.get('rating', {}).get('count', 0))
            for p in products
        )
        
        return {
            "total_products": len(products),
            "avg_current_price": round(sum(prices) / len(prices), 2),
            "avg_current_stock": round(sum(stocks) / len(stocks), 2),
            "min_current_stock": min(stocks),
            "max_current_stock": max(stocks),
            "avg_current_rating": round(sum(ratings) / len(ratings), 2),
            "total_current_inventory_value": round(total_value, 2),
            "categories": sorted(categories),
            "category_count": len(categories)
        }
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


def verify_password(provided_password: str) -> bool:
    """
    Verify the provided password against the environment variable.
    
    Args:
        provided_password: Password provided by user at session time
        
    Returns:
        Boolean indicating if password is correct
    """
    expected_password = os.getenv("API_PASS")
    
    if not expected_password:
        raise ValueError(
            "API_PASS not found in environment variables. "
            "Please ensure .env file exists with API_PASS=your_password"
        )
    
    return provided_password == expected_password


@smithery.server(config_schema=ConfigSchema)
def create_server():
    """
    Create and return a FastMCP server instance for FakeStore API operations.
    
    This server provides tools for accessing current product inventory data
    from the FakeStore API, designed to work alongside a Database MCP server
    for historical-current comparative analysis.
    
    Authentication:
        - Requires password at session initialization
        - Password must match API_PASS in .env file
        - If password is incorrect, all tool calls will fail with auth error
    """
    
    server = FastMCP(name="FakeStore API Current Inventory Server")
    
    # Store API service instance
    api_service = APIService()
    
    def verify_session_auth(ctx: Context) -> None:
        """
        Verify that the session is authenticated with correct password.
        
        Args:
            ctx: MCP context containing session configuration
            
        Raises:
            ValueError: If authentication fails
        """
        if not ctx or not hasattr(ctx, 'session_config') or not ctx.session_config:
            raise ValueError("Session context is required")
        
        config = ctx.session_config
        
        if not config.api_password:
            raise ValueError("API password is required for authentication")
        
        # Verify password
        if not verify_password(config.api_password):
            raise ValueError(
                "Authentication failed: Invalid password. "
                "Please provide the correct API password."
            )

    @server.tool()
    def get_all_products(ctx: Context = None) -> Dict[str, Any]:
        """
        Fetch all current products from the FakeStore API.
        
        PRIMARY TOOL for getting current/live inventory data 
        
        This tool retrieves 20 products from the FakeStore API with their current
        pricing and stock information. The data should be compared with historical
        data from the Database MCP server to calculate:
        
        1. Stock Depletion Rate: How much inventory has been sold/depleted
        2. Price Changes: How market prices have changed over 6 months
        3. Restock Cost Impact: Budget impact due to price changes
        
        CRITICAL FIELD MAPPING:
        
        API Field              →  Interpretation           →  Compare With (DB)
        -------------------------------------------------------------------------
        id                     →  Product ID               →  id
        title                  →  Product name             →  title
        price                  →  Current market price     →  historical_price
        category               →  Product category         →  category
        rating.rate            →  Current rating           →  historical_rating
        rating.count           →  Current stock level ⭐   →  historical_stock
        
        FEATURE ENGINEERING:
        The API doesn't have a dedicated "stock" field. We use rating.count as 
        the current stock level. This is the KEY field for inventory depletion analysis.
        
        Returns:
            Dictionary containing:
                success: Boolean - operation status
                product_count: Integer - number of products (typically 20)
                data: List of product dictionaries, each containing:
                    {
                        "id": 1,
                        "title": "Fjallraven - Foldsack No. 1 Backpack...",
                        "price": 109.95,                    # Current price
                        "description": "Your perfect pack...",
                        "category": "men's clothing",
                        "image": "https://...",
                        "rating": {
                            "rate": 3.9,                    # Current rating
                            "count": 120                    # Current stock ⭐
                        }
                    }
                summary: Aggregate statistics about current inventory:
                    {
                        "total_products": 20,
                        "avg_current_price": 124.50,
                        "avg_current_stock": 156.3,
                        "min_current_stock": 51,
                        "max_current_stock": 679,
                        "avg_current_rating": 3.85,
                        "total_current_inventory_value": 38924.50,
                        "categories": ["electronics", "jewelery", ...],
                        "category_count": 4
                    }
                message: Success message
        
        
        LLM performs comparative analysis
        ------------------------------------------
        For each product (matched by ID):
            
            # Calculate stock depletion
            depletion_rate = (
                (historical_stock - current_stock) / historical_stock * 100
            )
            
            # Calculate price change
            price_change_pct = (
                (current_price - historical_price) / historical_price * 100
            )
            
            # Determine restock need
            if depletion_rate > 70%:
                status = "CRITICAL - Immediate restocking required"
            elif depletion_rate > 50%:
                status = "WARNING - Restocking recommended"
            else:
                status = "OK - Stock levels healthy"
            
            # Calculate restock cost impact
            units_to_restock = historical_stock - current_stock
            old_cost = units_to_restock * historical_price
            new_cost = units_to_restock * current_price
            cost_increase = new_cost - old_cost
        
        Step 4: Generate actionable report
        -----------------------------------
        Present findings with:
        - Products ranked by depletion rate (most critical first)
        - Price change impact on restock budget
        - Total additional budget needed due to price increases
        - Recommended immediate actions
        """
        try:
            # Verify authentication
            verify_session_auth(ctx)
            
            # Fetch products from API
            return api_service.get_all_products()
        
        except ValueError as e:
            return {
                "error": str(e),
                "success": False
            }
        except Exception as e:
            return {
                "error": f"Failed to fetch products: {str(e)}",
                "success": False
            }

    return server