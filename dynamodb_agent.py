"""
DynamoDB Browser Agent - Natural language interface to browse and query DynamoDB data

This agent provides tools to:
1. List DynamoDB tables
2. Describe table structure and schema
3. Scan tables with filters
4. Query tables by partition key
5. Get specific items
6. Analyze table statistics
"""

from strands import Agent, tool
import boto3
import json
from decimal import Decimal
from typing import Dict, List, Any, Optional
import os

# Custom JSON encoder to handle DynamoDB Decimal types
class DynamoDBEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DynamoDBEncoder, self).default(obj)

# Initialize DynamoDB client
def get_dynamodb_client():
    """Get DynamoDB client with proper credentials."""
    try:
        # Try to use existing AWS credentials
        return boto3.client('dynamodb')
    except Exception as e:
        raise Exception(f"Could not initialize DynamoDB client: {e}")

def get_dynamodb_resource():
    """Get DynamoDB resource with proper credentials."""
    try:
        return boto3.resource('dynamodb')
    except Exception as e:
        raise Exception(f"Could not initialize DynamoDB resource: {e}")

@tool
def list_dynamodb_tables() -> str:
    """List all DynamoDB tables in the current AWS account/region.
    
    Returns:
        JSON string containing list of table names and basic info
    """
    try:
        client = get_dynamodb_client()
        response = client.list_tables()
        
        tables_info = []
        for table_name in response['TableNames']:
            try:
                table_desc = client.describe_table(TableName=table_name)
                table_info = {
                    'name': table_name,
                    'status': table_desc['Table']['TableStatus'],
                    'item_count': table_desc['Table'].get('ItemCount', 'Unknown'),
                    'size_bytes': table_desc['Table'].get('TableSizeBytes', 'Unknown'),
                    'created': str(table_desc['Table']['CreationDateTime']) if 'CreationDateTime' in table_desc['Table'] else 'Unknown'
                }
                tables_info.append(table_info)
            except Exception as e:
                tables_info.append({
                    'name': table_name,
                    'error': f"Could not get details: {str(e)}"
                })
        
        return json.dumps({
            'total_tables': len(response['TableNames']),
            'tables': tables_info
        }, indent=2, cls=DynamoDBEncoder)
        
    except Exception as e:
        return f"Error listing tables: {str(e)}"

@tool
def describe_dynamodb_table(table_name: str) -> str:
    """Get detailed information about a specific DynamoDB table including schema, indexes, and settings.
    
    Args:
        table_name: Name of the DynamoDB table to describe
        
    Returns:
        JSON string with detailed table information
    """
    try:
        client = get_dynamodb_client()
        response = client.describe_table(TableName=table_name)
        table = response['Table']
        
        # Extract key information
        table_info = {
            'table_name': table['TableName'],
            'status': table['TableStatus'],
            'creation_date': str(table['CreationDateTime']) if 'CreationDateTime' in table else 'Unknown',
            'item_count': table.get('ItemCount', 'Unknown'),
            'size_bytes': table.get('TableSizeBytes', 'Unknown'),
            'billing_mode': table.get('BillingModeSummary', {}).get('BillingMode', 'Unknown'),
            'key_schema': table['KeySchema'],
            'attribute_definitions': table['AttributeDefinitions'],
            'global_secondary_indexes': table.get('GlobalSecondaryIndexes', []),
            'local_secondary_indexes': table.get('LocalSecondaryIndexes', []),
            'stream_specification': table.get('StreamSpecification', {}),
            'provisioned_throughput': table.get('ProvisionedThroughput', {})
        }
        
        return json.dumps(table_info, indent=2, cls=DynamoDBEncoder)
        
    except Exception as e:
        return f"Error describing table '{table_name}': {str(e)}"

@tool
def scan_dynamodb_table(table_name: str, limit: int = 10, filter_expression: str = None) -> str:
    """Scan a DynamoDB table and return items. Use for browsing data when you don't know the partition key.
    
    Args:
        table_name: Name of the DynamoDB table to scan
        limit: Maximum number of items to return (default: 10, max: 100)
        filter_expression: Optional filter expression (e.g., "attribute_exists(email)")
        
    Returns:
        JSON string containing the scanned items
    """
    try:
        limit = min(limit, 100)  # Cap at 100 for safety
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(table_name)
        
        scan_kwargs = {
            'Limit': limit
        }
        
        if filter_expression:
            scan_kwargs['FilterExpression'] = filter_expression
        
        response = table.scan(**scan_kwargs)
        
        result = {
            'table_name': table_name,
            'count': response['Count'],
            'scanned_count': response['ScannedCount'],
            'items': response['Items'],
            'has_more': 'LastEvaluatedKey' in response
        }
        
        return json.dumps(result, indent=2, cls=DynamoDBEncoder)
        
    except Exception as e:
        return f"Error scanning table '{table_name}': {str(e)}"

@tool
def query_dynamodb_table(table_name: str, partition_key: str, partition_value: str, 
                        sort_key: str = None, sort_value: str = None, limit: int = 10) -> str:
    """Query a DynamoDB table by partition key (and optionally sort key). More efficient than scanning.
    
    Args:
        table_name: Name of the DynamoDB table to query
        partition_key: Name of the partition key attribute
        partition_value: Value to search for in the partition key
        sort_key: Optional name of the sort key attribute
        sort_value: Optional value to search for in the sort key
        limit: Maximum number of items to return (default: 10)
        
    Returns:
        JSON string containing the query results
    """
    try:
        limit = min(limit, 100)  # Cap at 100 for safety
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(table_name)
        
        # Build key condition expression
        from boto3.dynamodb.conditions import Key
        key_condition = Key(partition_key).eq(partition_value)
        
        if sort_key and sort_value:
            key_condition = key_condition & Key(sort_key).eq(sort_value)
        
        response = table.query(
            KeyConditionExpression=key_condition,
            Limit=limit
        )
        
        result = {
            'table_name': table_name,
            'partition_key': partition_key,
            'partition_value': partition_value,
            'sort_key': sort_key,
            'sort_value': sort_value,
            'count': response['Count'],
            'items': response['Items'],
            'has_more': 'LastEvaluatedKey' in response
        }
        
        return json.dumps(result, indent=2, cls=DynamoDBEncoder)
        
    except Exception as e:
        return f"Error querying table '{table_name}': {str(e)}"

@tool
def get_dynamodb_item(table_name: str, key_attributes: str) -> str:
    """Get a specific item from DynamoDB by its primary key.
    
    Args:
        table_name: Name of the DynamoDB table
        key_attributes: JSON string of key attributes (e.g., '{"id": "123", "sort_key": "value"}')
        
    Returns:
        JSON string containing the item or error message
    """
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(table_name)
        
        # Parse key attributes
        key = json.loads(key_attributes)
        
        response = table.get_item(Key=key)
        
        if 'Item' in response:
            result = {
                'table_name': table_name,
                'key': key,
                'item': response['Item']
            }
        else:
            result = {
                'table_name': table_name,
                'key': key,
                'item': None,
                'message': 'Item not found'
            }
        
        return json.dumps(result, indent=2, cls=DynamoDBEncoder)
        
    except Exception as e:
        return f"Error getting item from table '{table_name}': {str(e)}"

@tool
def analyze_dynamodb_table_sample(table_name: str, sample_size: int = 20) -> str:
    """Analyze a sample of items from a DynamoDB table to understand the data structure and patterns.
    
    Args:
        table_name: Name of the DynamoDB table to analyze
        sample_size: Number of items to sample for analysis (default: 20, max: 50)
        
    Returns:
        JSON string with analysis results including common attributes, data types, and patterns
    """
    try:
        sample_size = min(sample_size, 50)  # Cap at 50 for safety
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(table_name)
        
        # Get sample items
        response = table.scan(Limit=sample_size)
        items = response['Items']
        
        if not items:
            return json.dumps({
                'table_name': table_name,
                'message': 'No items found in table'
            })
        
        # Analyze the sample
        all_attributes = set()
        attribute_types = {}
        attribute_frequency = {}
        
        for item in items:
            for attr, value in item.items():
                all_attributes.add(attr)
                
                # Count frequency
                attribute_frequency[attr] = attribute_frequency.get(attr, 0) + 1
                
                # Determine type
                value_type = type(value).__name__
                if attr not in attribute_types:
                    attribute_types[attr] = set()
                attribute_types[attr].add(value_type)
        
        # Convert sets to lists for JSON serialization
        for attr in attribute_types:
            attribute_types[attr] = list(attribute_types[attr])
        
        analysis = {
            'table_name': table_name,
            'sample_size': len(items),
            'total_attributes': len(all_attributes),
            'attributes': {
                'all_attributes': sorted(list(all_attributes)),
                'attribute_types': attribute_types,
                'attribute_frequency': attribute_frequency
            },
            'sample_items': items[:3]  # Show first 3 items as examples
        }
        
        return json.dumps(analysis, indent=2, cls=DynamoDBEncoder)
        
    except Exception as e:
        return f"Error analyzing table '{table_name}': {str(e)}"

@tool
def search_dynamodb_table(table_name: str, search_term: str, limit: int = 10) -> str:
    """Search for items in a DynamoDB table that contain a specific term in any string attribute.
    
    Args:
        table_name: Name of the DynamoDB table to search
        search_term: Term to search for in string attributes
        limit: Maximum number of items to return (default: 10)
        
    Returns:
        JSON string containing matching items
    """
    try:
        limit = min(limit, 100)  # Cap at 100 for safety
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(table_name)
        
        # Scan with a filter to find items containing the search term
        from boto3.dynamodb.conditions import Attr
        
        response = table.scan(
            Limit=limit * 5,  # Scan more items since we're filtering
            FilterExpression=Attr('data').contains(search_term) |
                           Attr('name').contains(search_term) |
                           Attr('title').contains(search_term) |
                           Attr('description').contains(search_term) |
                           Attr('content').contains(search_term)
        )
        
        # Take only the requested number of results
        items = response['Items'][:limit]
        
        result = {
            'table_name': table_name,
            'search_term': search_term,
            'count': len(items),
            'scanned_count': response['ScannedCount'],
            'items': items
        }
        
        return json.dumps(result, indent=2, cls=DynamoDBEncoder)
        
    except Exception as e:
        return f"Error searching table '{table_name}' for '{search_term}': {str(e)}"

def create_dynamodb_agent():
    """Create a Strands agent specialized for DynamoDB operations."""
    
    tools = [
        list_dynamodb_tables,
        describe_dynamodb_table,
        scan_dynamodb_table,
        query_dynamodb_table,
        get_dynamodb_item,
        analyze_dynamodb_table_sample,
        search_dynamodb_table
    ]
    
    system_prompt = """You are a DynamoDB expert assistant that helps users browse, query, and analyze their DynamoDB data.

You have access to the following DynamoDB tools:
- list_dynamodb_tables: List all tables in the account
- describe_dynamodb_table: Get detailed table schema and configuration
- scan_dynamodb_table: Browse table data (use when you don't know the partition key)
- query_dynamodb_table: Query by partition key (more efficient than scanning)
- get_dynamodb_item: Get a specific item by primary key
- analyze_dynamodb_table_sample: Analyze table structure and data patterns
- search_dynamodb_table: Search for items containing specific text

When helping users:
1. Start by listing tables if they don't specify one
2. Describe the table structure before querying to understand the schema
3. Use query operations when possible (more efficient than scans)
4. Explain the data structure and suggest better ways to access the data
5. Be helpful in interpreting the results and suggesting next steps

Always explain what you're doing and why, and provide insights about the data structure and access patterns."""

    # Use default Strands Bedrock configuration - let it pick the best available model
    return Agent(
        tools=tools,
        system_prompt=system_prompt
    )

def main():
    """Test the DynamoDB agent."""
    print("DynamoDB Browser Agent")
    print("=" * 50)
    
    try:
        agent = create_dynamodb_agent()
        
        print("\nAgent created successfully!")
        print("You can now ask questions like:")
        print("- 'What DynamoDB tables do I have?'")
        print("- 'Show me the structure of the users table'")
        print("- 'Get me 5 items from the products table'")
        print("- 'Query the orders table for user_id = 12345'")
        print("- 'Search for items containing the word email'")
        print("- 'Analyze the data structure of my logs table'")
        
        # Test with a simple question
        print("\n" + "=" * 50)
        print("Testing agent...")
        
        response = agent("What DynamoDB tables do I have access to?")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error creating agent: {e}")
        print("\nMake sure you have:")
        print("1. AWS credentials configured (aws configure)")
        print("2. DynamoDB permissions in your AWS account")
        print("3. Strands agents SDK installed")

if __name__ == "__main__":
    main()