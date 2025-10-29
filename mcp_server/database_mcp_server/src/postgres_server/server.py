"""
PostgreSQL MCP Server

This server provides read-only access to a PostgreSQL database containing historical product inventory data from 6 months ago (snapshot date: 2024-04-27).
It's designed to work in conjunction with an API MCP server to enable comparative analysis between historical and current data.

Database Schema:
    products table:
        - id: Product identifier (matches with API product IDs)
        - title: Product name
        - price: Historical price from 6 months ago
        - category: Product category
        - rating: Historical rating (0-5)
        - stock: Historical stock level from 6 months ago
        - last_updated: Date of the snapshot (2024-04-27)
        - created_at: Record creation timestamp

API Integration Note:
    The API MCP server returns current data with structure:
        - id, title, category (direct match)
        - price: Current market price
        - rating.rate: Current rating
        - rating.count: Current stock level (feature engineered from rating count)
    
    This allows easy comparison: historical stock vs rating.count for depletion analysis

Use Cases:
- Historical inventory level analysis
- Price change tracking over time
- Stock depletion rate calculations
- Comparative restocking cost analysis
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field
import re
from datetime import datetime


class ConfigSchema(BaseModel):
    """Configuration schema for database connection parameters."""
    db_host: str = Field(description="PostgreSQL database host")
    db_port: int = Field(default=5432, description="PostgreSQL database port")
    db_username: str = Field(description="PostgreSQL database username")
    db_password: str = Field(description="PostgreSQL database password")
    db_name: str = Field(description="PostgreSQL database name")


class DatabaseService:
    """
    Service class to handle all database operations with safety validations.
    
    This service enforces read-only access and implements query timeouts
    to ensure safe database operations.
    """
    
    # Dangerous SQL keywords that should be blocked for read-only operations
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'TRUNCATE', 'INSERT', 'UPDATE', 
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE'
    ]
    
    QUERY_TIMEOUT = 60  # 60 seconds timeout for long queries
    
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        """
        Initialize database service with connection parameters.
        
        Args:
            host: Database host address
            port: Database port number
            username: Database username
            password: Database password
            database: Database name
        """
        self.connection_params = {
            'host': host,
            'port': port,
            'user': username,
            'password': password,
            'database': database
        }
    
    def _get_connection(self):
        """
        Create a new database connection with timeout settings.
        
        Returns:
            psycopg2 connection object
            
        Raises:
            ConnectionError: If connection fails
        """
        try:
            conn = psycopg2.connect(**self.connection_params)
            # Set statement timeout to prevent long-running queries
            cursor = conn.cursor()
            cursor.execute(f"SET statement_timeout = {self.QUERY_TIMEOUT * 1000}")  # milliseconds
            cursor.close()
            return conn
        except psycopg2.Error as e:
            raise ConnectionError(f"Failed to connect to database: {str(e)}")
    
    def _validate_query(self, query: str) -> tuple[bool, str]:
        """
        Validate that the query is safe to execute (SELECT only).
        
        This prevents any data modification operations and ensures
        only read operations are performed.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Remove comments and normalize whitespace
        query_upper = re.sub(r'--.*$', '', query, flags=re.MULTILINE).upper()
        query_upper = re.sub(r'/\*.*?\*/', '', query_upper, flags=re.DOTALL)
        query_upper = ' '.join(query_upper.split())
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            if re.search(r'\b' + keyword + r'\b', query_upper):
                return False, f"Query contains forbidden keyword: {keyword}"
        
        # Ensure query starts with SELECT
        if not query_upper.strip().startswith('SELECT'):
            return False, "Only SELECT queries are allowed"
        
        return True, ""
    
    def execute_query(self, query: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a SELECT query and return results.
        
        This is the core query execution method with built-in safety checks
        and error handling.
        
        Args:
            query: SQL SELECT query to execute
            limit: Optional row limit (default: None for no limit)
            
        Returns:
            Dictionary containing:
                - success: Boolean indicating query success
                - row_count: Number of rows returned
                - data: List of result rows as dictionaries
                - message: Success/error message
        """
        # Validate query
        is_valid, error_msg = self._validate_query(query)
        if not is_valid:
            return {"error": error_msg, "success": False}
        
        # Add LIMIT clause if specified and not already present
        if limit and 'LIMIT' not in query.upper():
            query = query.rstrip(';') + f' LIMIT {limit}'
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries for JSON serialization
            results = [dict(row) for row in rows]
            
            return {
                "success": True,
                "row_count": len(results),
                "data": results,
                "message": f"Query executed successfully. Returned {len(results)} row(s)."
            }
        
        except psycopg2.errors.QueryCanceled:
            return {
                "error": f"Query timeout: execution exceeded {self.QUERY_TIMEOUT} seconds",
                "success": False
            }
        except psycopg2.Error as e:
            return {"error": f"Database error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}
        finally:
            if conn:
                conn.close()
    
    def get_table_data(
        self, 
        table_name: str, 
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get data from a specific table with flexible filtering options.
        
        This is a high-level method for retrieving table data without
        writing raw SQL queries. Ideal for common data retrieval patterns.
        
        Args:
            table_name: Name of the table to query
            columns: List of column names to retrieve (None = all columns)
            where_clause: WHERE condition without the 'WHERE' keyword
                         Example: "price > 100 AND category = 'electronics'"
            order_by: ORDER BY clause without the 'ORDER BY' keyword
                     Example: "price DESC, title ASC"
            limit: Maximum number of rows to return (default: 100)
            
        Returns:
            Dictionary containing query results or error
            
        Example:
            get_table_data(
                "products",
                columns=["id", "title", "price", "stock"],
                where_clause="category = 'electronics' AND stock < 50",
                order_by="stock ASC",
                limit=20
            )
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build column list
            if columns:
                column_list = ', '.join([sql.Identifier(col).as_string(conn) for col in columns])
            else:
                column_list = '*'
            
            # Build query
            query_parts = [f"SELECT {column_list} FROM {sql.Identifier(table_name).as_string(conn)}"]
            
            if where_clause:
                query_parts.append(f"WHERE {where_clause}")
            
            if order_by:
                query_parts.append(f"ORDER BY {order_by}")
            
            query_parts.append(f"LIMIT {limit}")
            
            query = ' '.join(query_parts)
            
            # Execute query
            cursor.execute(query)
            rows = cursor.fetchall()
            
            results = [dict(row) for row in rows]
            
            return {
                "success": True,
                "table_name": table_name,
                "row_count": len(results),
                "data": results,
                "message": f"Retrieved {len(results)} row(s) from {table_name}"
            }
        
        except psycopg2.Error as e:
            return {"error": f"Database error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}
        finally:
            if conn:
                conn.close()
    
    def get_historical_inventory(
        self,
        product_ids: Optional[List[int]] = None,
        category: Optional[str] = None,
        min_stock: Optional[int] = None,
        max_stock: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        order_by: str = "stock ASC",
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get historical inventory data with flexible filtering.
        
        This specialized method is designed for inventory analysis use cases,
        providing easy access to historical stock and pricing data from 6 months ago.
        
        Args:
            product_ids: List of specific product IDs to retrieve
            category: Filter by product category
            min_stock: Minimum historical stock level filter
            max_stock: Maximum historical stock level filter
            min_price: Minimum historical price filter
            max_price: Maximum historical price filter
            order_by: Sort order (default: "stock ASC" for lowest stock first)
                     Options: "stock ASC/DESC", "price ASC/DESC", "rating ASC/DESC"
            limit: Maximum number of rows to return (default: 100)
            
        Returns:
            Dictionary containing:
                - success: Boolean
                - row_count: Number of products returned
                - data: List of product records with historical data
                - summary: Aggregate statistics about the results
                - snapshot_date: Date when this historical data was captured
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build WHERE conditions
            conditions = []
            params = []
            
            if product_ids:
                conditions.append(f"id = ANY(%s)")
                params.append(product_ids)
            
            if category:
                conditions.append("category = %s")
                params.append(category)
            
            if min_stock is not None:
                conditions.append("stock >= %s")
                params.append(min_stock)
            
            if max_stock is not None:
                conditions.append("stock <= %s")
                params.append(max_stock)
            
            if min_price is not None:
                conditions.append("price >= %s")
                params.append(min_price)
            
            if max_price is not None:
                conditions.append("price <= %s")
                params.append(max_price)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Main query to get historical inventory data
            query = f"""
                SELECT 
                    id,
                    title,
                    price as historical_price,
                    category,
                    rating as historical_rating,
                    stock as historical_stock,
                    last_updated as snapshot_date
                FROM products
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT %s
            """
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            
            # Calculate summary statistics
            summary = {
                "total_products": len(results),
                "avg_historical_stock": 0,
                "avg_historical_price": 0,
                "min_historical_stock": 0,
                "max_historical_stock": 0,
                "total_historical_inventory_value": 0
            }
            
            if results:
                stocks = [float(r.get('historical_stock', 0) or 0) for r in results]
                prices = [float(r.get('historical_price', 0) or 0) for r in results]
                
                summary["avg_historical_stock"] = round(sum(stocks) / len(stocks), 2)
                summary["avg_historical_price"] = round(sum(prices) / len(prices), 2)
                summary["min_historical_stock"] = int(min(stocks))
                summary["max_historical_stock"] = int(max(stocks))
                summary["total_historical_inventory_value"] = round(
                    sum((r.get('historical_stock', 0) or 0) * (r.get('historical_price', 0) or 0) for r in results),
                    2
                )
            
            return {
                "success": True,
                "row_count": len(results),
                "data": results,
                "summary": summary,
                "snapshot_date": "2024-04-27",
                "message": f"Retrieved {len(results)} historical inventory record(s) from snapshot date 2024-04-27"
            }
        
        except psycopg2.Error as e:
            return {"error": f"Database error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}
        finally:
            if conn:
                conn.close()
    
    def get_products_by_ids(self, product_ids: List[int]) -> Dict[str, Any]:
        """
        Get historical data for specific product IDs.
        
        Optimized method for retrieving multiple products by their IDs,
        which is the primary key for matching with API data.
        
        Args:
            product_ids: List of product IDs to retrieve
            
        Returns:
            Dictionary containing historical product data keyed by product ID
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    id,
                    title,
                    price as historical_price,
                    category,
                    rating as historical_rating,
                    stock as historical_stock,
                    last_updated as snapshot_date
                FROM products
                WHERE id = ANY(%s)
                ORDER BY id
            """
            
            cursor.execute(query, (product_ids,))
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            
            # Create a lookup dictionary for easy access by ID
            products_by_id = {row['id']: row for row in results}
            
            # Identify missing IDs
            found_ids = set(products_by_id.keys())
            missing_ids = set(product_ids) - found_ids
            
            return {
                "success": True,
                "row_count": len(results),
                "data": results,
                "products_by_id": products_by_id,
                "found_ids": list(found_ids),
                "missing_ids": list(missing_ids),
                "snapshot_date": "2024-04-27",
                "message": f"Retrieved {len(results)} of {len(product_ids)} requested products"
            }
        
        except psycopg2.Error as e:
            return {"error": f"Database error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}
        finally:
            if conn:
                conn.close()
    
    def get_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed schema information for a specific table.
        
        Useful for understanding table structure before querying.
        
        Args:
            table_name: Name of the table to inspect
            
        Returns:
            Dictionary containing:
                - columns: Detailed column information
                - primary_keys: List of primary key columns
                - foreign_keys: Foreign key relationships
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get column information
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            if not columns:
                return {"error": f"Table '{table_name}' not found", "success": False}
            
            # Get primary key information
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary
            """, (table_name,))
            
            primary_keys = [row['attname'] for row in cursor.fetchall()]
            
            # Get foreign key information
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s
            """, (table_name,))
            
            foreign_keys = [dict(row) for row in cursor.fetchall()]
            
            # Format column information
            column_info = []
            for col in columns:
                col_dict = dict(col)
                col_dict['is_primary_key'] = col['column_name'] in primary_keys
                col_dict['is_nullable'] = col['is_nullable'] == 'YES'
                column_info.append(col_dict)
            
            return {
                "success": True,
                "table_name": table_name,
                "columns": column_info,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys
            }
        
        except psycopg2.Error as e:
            return {"error": f"Database error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}
        finally:
            if conn:
                conn.close()
    
    def list_tables(self) -> Dict[str, Any]:
        """
        List all tables in the database with row counts.
        
        Returns:
            Dictionary containing list of tables with metadata
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all tables in public schema
            cursor.execute("""
                SELECT 
                    table_name,
                    table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            # Get row counts for each table
            table_info = []
            for table in tables:
                table_name = table['table_name']
                try:
                    cursor.execute(sql.SQL("SELECT COUNT(*) as row_count FROM {}").format(
                        sql.Identifier(table_name)
                    ))
                    row_count = cursor.fetchone()['row_count']
                except:
                    row_count = None
                
                table_info.append({
                    "table_name": table_name,
                    "table_type": table['table_type'],
                    "row_count": row_count
                })
            
            return {
                "success": True,
                "table_count": len(table_info),
                "tables": table_info
            }
        
        except psycopg2.Error as e:
            return {"error": f"Database error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}
        finally:
            if conn:
                conn.close()


@smithery.server(config_schema=ConfigSchema)
def create_server():
    """
    Create and return a FastMCP server instance for PostgreSQL operations.
    
    This server provides tools for accessing historical inventory data
    from a PostgreSQL database (snapshot from 2024-04-27), designed to work 
    alongside an API MCP server for comparative analysis.
    """
    
    server = FastMCP(name="PostgreSQL Historical Inventory Server")
    
    def get_database_service(ctx: Context) -> DatabaseService:
        """
        Helper to get DatabaseService instance with credentials from context.
        
        Args:
            ctx: MCP context containing session configuration
            
        Returns:
            Configured DatabaseService instance
            
        Raises:
            ValueError: If required credentials are missing
        """
        if not ctx or not hasattr(ctx, 'session_config') or not ctx.session_config:
            raise ValueError("Session context is required")
        
        config = ctx.session_config
        
        if not all([config.db_host, config.db_username, config.db_password, config.db_name]):
            raise ValueError(
                "Database credentials are required. Please provide host, username, password, and database name."
            )
        
        return DatabaseService(
            host=config.db_host,
            port=config.db_port,
            username=config.db_username,
            password=config.db_password,
            database=config.db_name
        )

    @server.tool()
    def get_historical_inventory(
        product_ids: Optional[List[int]] = None,
        category: Optional[str] = None,
        min_stock: Optional[int] = None,
        max_stock: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        order_by: str = "stock ASC",
        limit: int = 100,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Retrieve historical inventory data from 6 months ago (snapshot: 2024-04-27) with flexible filtering.
        
        This tool provides historical stock levels and pricing data that MUST be compared with current API data to calculate:
        1. Stock Depletion Rate: (historical_stock - current_stock) / historical_stock × 100%
        2. Price Change Impact: (current_price - historical_price) / historical_price × 100%
        3. Restock Cost Difference: (current_price - historical_price) × restock_quantity
        
        
        CRITICAL: The API returns current stock as "rating.count" - this is feature engineering to fit the API structure. Always compare historical_stock with rating.count!
        
        Args:
            product_ids: Filter by specific product IDs. Useful when you already know which
                        products to analyze (e.g., from API response).
                        Example: [1, 2, 5, 10] - get historical data for these products
                        
            category: Filter by product category. Available categories from API:
                     "electronics", "jewelery", "men's clothing", "women's clothing"
                     Example: "electronics" - analyze all electronics
                     
            min_stock: Minimum historical stock level. Use to find products that had
                      healthy stock 6 months ago (to compare current depletion).
                      Example: 100 - products with 100+ units historically
                      
            max_stock: Maximum historical stock level. Use to find products that were
                      already low in stock historically (chronic low stock issues).
                      Example: 50 - products with ≤50 units 6 months ago
                      
            min_price: Minimum historical price filter (in USD).
                      Example: 100.0 - products priced $100+ historically
                      
            max_price: Maximum historical price filter (in USD).
                      Example: 500.0 - products priced ≤$500 historically
                      
            order_by: Sort order for results. Options:
                     - "stock ASC" (default) - lowest stock first (critical items)
                     - "stock DESC" - highest stock first
                     - "price ASC" - cheapest first
                     - "price DESC" - most expensive first
                     - "rating ASC" - lowest rated first
                     - "rating DESC" - highest rated first
                     
            limit: Maximum number of products to return. Default 100.
                  Increase for comprehensive analysis (max practical: 1000)
        
        Returns:
            Dictionary with:
                success: Boolean - operation status
                row_count: Integer - number of products returned
                snapshot_date: String - "2024-04-27" (when historical data was captured)
                data: List of product dictionaries, each containing:
                    {
                        "id": 1,                              # Match with API id
                        "title": "Product Name",              # Match with API title
                        "historical_price": 109.95,           # Compare with API price
                        "category": "men's clothing",         # Match with API category
                        "historical_rating": 3.9,             # Compare with API rating.rate
                        "historical_stock": 120,              # Compare with API rating.count ⚠️
                        "snapshot_date": "2024-04-27"         # Reference date
                    }
                summary: Aggregate statistics:
                    {
                        "total_products": 20,
                        "avg_historical_stock": 156.5,
                        "avg_historical_price": 234.67,
                        "min_historical_stock": 51,
                        "max_historical_stock": 437,
                        "total_historical_inventory_value": 73234.50
                    }
        
        COMMON PATTERNS:
        
        1. Find critically depleted products across all categories:
           get_historical_inventory(max_stock=80, limit=50, order_by="stock ASC")
           → Returns products that were already low 6 months ago
        
        2. Analyze specific category for restocking:
           get_historical_inventory(category="electronics", limit=100)
           → Get all electronics historical data for category-wide analysis
        
        3. Compare specific products (after getting API data):
           get_historical_inventory(product_ids=[1, 5, 10, 15, 20])
           → Get historical data for specific products to compare with current
        
        4. Find high-value inventory items:
           get_historical_inventory(min_price=200, order_by="price DESC", limit=30)
           → Expensive items where price changes have major budget impact
        
        5. Products with healthy historical stock (to measure depletion):
           get_historical_inventory(min_stock=150, limit=100)
           → Items that had good stock - if current is low, indicates high demand
        
        IMPORTANT NOTES:
        - Historical data is from 2024-04-27 (approximately 6 months ago)
        - Stock values are point-in-time snapshots, not averages
        - Always pair with current API data for meaningful analysis
        - "historical_stock" from DB compares to "rating.count" from API
        - Price comparisons show market price changes over 6 months
        - Use product ID as the join key between historical and current data
        """
        try:
            db_service = get_database_service(ctx)
            return db_service.get_historical_inventory(
                product_ids=product_ids,
                category=category,
                min_stock=min_stock,
                max_stock=max_stock,
                min_price=min_price,
                max_price=max_price,
                order_by=order_by,
                limit=limit
            )
        except ValueError as e:
            return {"error": str(e), "success": False}
        except Exception as e:
            return {"error": f"Failed to retrieve historical inventory: {str(e)}", "success": False}

    @server.tool()
    def get_products_by_ids(
        product_ids: List[int],
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Get historical data for specific product IDs - optimized for API data comparison.
        
        ⚡ FAST LOOKUP TOOL - Use this when you have product IDs from the API and need
        to quickly fetch their historical data for comparison.
        
        This tool is optimized for the common pattern:
        1. Get current products from API MCP
        2. Extract product IDs from API response
        3. Use this tool to get historical data for those exact products
        4. Compare historical vs current for analysis
        
        Args:
            product_ids: List of product IDs to retrieve historical data for.
                        These IDs should match the "id" field from API responses.
                        Example: [1, 2, 3, 4, 5, 10, 15, 20]
                        
        Returns:
            Dictionary with:
                success: Boolean - operation status
                row_count: Integer - number of products found
                snapshot_date: "2024-04-27" - historical data date
                found_ids: List of IDs that were found in database
                missing_ids: List of IDs that were NOT found (may be new products)
                data: List of product dictionaries (same structure as get_historical_inventory)
                products_by_id: Dictionary keyed by product ID for O(1) lookup
                    {
                        1: {"id": 1, "title": "...", "historical_price": 109.95, ...},
                        2: {"id": 2, "title": "...", "historical_price": 22.30, ...}
                    }
        """
        try:
            db_service = get_database_service(ctx)
            return db_service.get_products_by_ids(product_ids)
        except ValueError as e:
            return {"error": str(e), "success": False}
        except Exception as e:
            return {"error": f"Failed to get products by IDs: {str(e)}", "success": False}

    @server.tool()
    def get_table_data(
        table_name: str,
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: int = 100,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Get data from any table with flexible filtering - GENERAL PURPOSE TOOL.
        
        Use this when you need more control than specialized tools provide, or when
        working with tables other than products.
        
        For the products table, prefer get_historical_inventory() which provides
        better field naming and summary statistics.
        
        Args:
            table_name: Name of table to query. Use "products" for main inventory data.
            columns: Specific columns to retrieve. 
                    Products table columns: id, title, price, category, rating, stock, 
                                          last_updated, created_at
                    Example: ["id", "title", "price", "stock"]
            where_clause: SQL WHERE condition (without 'WHERE' keyword).
                         Example: "stock < 50 AND category = 'electronics'"
            order_by: SQL ORDER BY clause (without 'ORDER BY' keyword).
                     Example: "stock ASC, price DESC"
            limit: Max rows to return (default: 100)
        
        Returns:
            Dictionary with success, row_count, table_name, data
        
        Example:
            get_table_data(
                "products",
                columns=["id", "title", "stock"],
                where_clause="stock < 30",
                order_by="stock ASC",
                limit=20
            )
        """
        try:
            db_service = get_database_service(ctx)
            return db_service.get_table_data(
                table_name=table_name,
                columns=columns,
                where_clause=where_clause,
                order_by=order_by,
                limit=limit
            )
        except ValueError as e:
            return {"error": str(e), "success": False}
        except Exception as e:
            return {"error": f"Failed to get table data: {str(e)}", "success": False}

    @server.tool()
    def execute_query(
        query: str, 
        limit: Optional[int] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Execute a custom SELECT query - ADVANCED TOOL for complex analysis.
        
        Use this when you need:
        - Aggregate functions (COUNT, SUM, AVG, MIN, MAX)
        - GROUP BY for category-level or statistical analysis
        - Complex calculations or CASE statements
        - Subqueries
        
        SAFETY: Only SELECT queries allowed. INSERT/UPDATE/DELETE/DROP blocked.
        TIMEOUT: Queries automatically canceled after 60 seconds.
        
        Args:
            query: PostgreSQL SELECT query
            limit: Optional row limit (auto-added if not in query)
        
        Returns:
            Dictionary with success, row_count, data, message
        
        """
        try:
            db_service = get_database_service(ctx)
            return db_service.execute_query(query=query, limit=limit)
        except ValueError as e:
            return {"error": str(e), "success": False}
        except Exception as e:
            return {"error": f"Failed to execute query: {str(e)}", "success": False}

    @server.tool()
    def get_schema(table_name: str, ctx: Context = None) -> Dict[str, Any]:
        """
        Get detailed schema information for a table.
        
        Use this to understand table structure before querying.
        
        Products table schema:
            - id: INTEGER PRIMARY KEY
            - title: VARCHAR(500) - Product name
            - price: DECIMAL(10,2) - Price in USD
            - category: VARCHAR(100) - Product category
            - rating: DECIMAL(3,2) - Rating 0-5
            - stock: INTEGER - Stock quantity (non-negative)
            - last_updated: DATE - Snapshot date (2024-04-27)
            - created_at: TIMESTAMP - Record creation time
        
        Args:
            table_name: Table name to inspect (e.g., "products")
        
        Returns:
            Dictionary with columns, primary_keys, foreign_keys, data types
        """
        try:
            db_service = get_database_service(ctx)
            return db_service.get_schema(table_name)
        except ValueError as e:
            return {"error": str(e), "success": False}
        except Exception as e:
            return {"error": f"Failed to get schema: {str(e)}", "success": False}

    @server.tool()
    def list_tables(ctx: Context = None) -> Dict[str, Any]:
        """
        List all tables in the database with row counts.
        
        Use this first to discover available tables. Primary table is "products"
        which contains the historical inventory data from 2024-04-27.
        
        Returns:
            Dictionary with table_count and tables list (name, type, row_count)
        """
        try:
            db_service = get_database_service(ctx)
            return db_service.list_tables()
        except ValueError as e:
            return {"error": str(e), "success": False}
        except Exception as e:
            return {"error": f"Failed to list tables: {str(e)}", "success": False}

    return server