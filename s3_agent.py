"""
S3 Browser Agent - Natural language interface to browse and manage S3 data

This agent provides tools to:
1. List S3 buckets
2. List objects in buckets
3. Get object metadata and properties
4. Search for objects by name/prefix
5. Analyze bucket contents and structure
6. Get bucket policies and configurations
"""

from strands import Agent, tool
import boto3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

def get_s3_client():
    """Get S3 client with proper credentials."""
    try:
        return boto3.client('s3')
    except Exception as e:
        raise Exception(f"Could not initialize S3 client: {e}")

def get_s3_resource():
    """Get S3 resource with proper credentials."""
    try:
        return boto3.resource('s3')
    except Exception as e:
        raise Exception(f"Could not initialize S3 resource: {e}")

@tool
def list_s3_buckets() -> str:
    """List all S3 buckets in the current AWS account.
    
    Returns:
        JSON string containing list of bucket names and creation dates
    """
    try:
        s3_client = get_s3_client()
        response = s3_client.list_buckets()
        
        buckets = []
        for bucket in response['Buckets']:
            buckets.append({
                'Name': bucket['Name'],
                'CreationDate': bucket['CreationDate'].isoformat(),
                'Region': get_bucket_region(bucket['Name'])
            })
        
        return json.dumps({
            'buckets': buckets,
            'total_count': len(buckets)
        }, indent=2)
        
    except Exception as e:
        return f"Error listing S3 buckets: {str(e)}"

def get_bucket_region(bucket_name: str) -> str:
    """Get the region of a specific bucket."""
    try:
        s3_client = get_s3_client()
        response = s3_client.get_bucket_location(Bucket=bucket_name)
        region = response.get('LocationConstraint')
        return region if region else 'us-east-1'  # Default region
    except:
        return 'unknown'

@tool
def list_bucket_objects(bucket_name: str, prefix: str = "", max_keys: int = 100) -> str:
    """List objects in a specific S3 bucket.
    
    Args:
        bucket_name: Name of the S3 bucket
        prefix: Optional prefix to filter objects (like a folder path)
        max_keys: Maximum number of objects to return (default 100)
    
    Returns:
        JSON string containing list of objects with metadata
    """
    try:
        s3_client = get_s3_client()
        
        params = {
            'Bucket': bucket_name,
            'MaxKeys': max_keys
        }
        if prefix:
            params['Prefix'] = prefix
            
        response = s3_client.list_objects_v2(**params)
        
        if 'Contents' not in response:
            return json.dumps({
                'bucket': bucket_name,
                'prefix': prefix,
                'objects': [],
                'message': 'No objects found'
            }, indent=2)
        
        objects = []
        total_size = 0
        
        for obj in response['Contents']:
            obj_info = {
                'Key': obj['Key'],
                'Size': obj['Size'],
                'SizeHuman': format_size(obj['Size']),
                'LastModified': obj['LastModified'].isoformat(),
                'StorageClass': obj.get('StorageClass', 'STANDARD')
            }
            objects.append(obj_info)
            total_size += obj['Size']
        
        return json.dumps({
            'bucket': bucket_name,
            'prefix': prefix,
            'objects': objects,
            'total_objects': len(objects),
            'total_size': total_size,
            'total_size_human': format_size(total_size),
            'is_truncated': response.get('IsTruncated', False)
        }, indent=2)
        
    except Exception as e:
        return f"Error listing objects in bucket '{bucket_name}': {str(e)}"

@tool
def get_object_metadata(bucket_name: str, object_key: str) -> str:
    """Get detailed metadata for a specific S3 object.
    
    Args:
        bucket_name: Name of the S3 bucket
        object_key: Key (path) of the object
    
    Returns:
        JSON string containing object metadata
    """
    try:
        s3_client = get_s3_client()
        response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        
        metadata = {
            'Bucket': bucket_name,
            'Key': object_key,
            'Size': response['ContentLength'],
            'SizeHuman': format_size(response['ContentLength']),
            'LastModified': response['LastModified'].isoformat(),
            'ContentType': response.get('ContentType', 'unknown'),
            'StorageClass': response.get('StorageClass', 'STANDARD'),
            'ServerSideEncryption': response.get('ServerSideEncryption'),
            'Metadata': response.get('Metadata', {}),
            'VersionId': response.get('VersionId'),
            'ETag': response.get('ETag', '').strip('"')
        }
        
        return json.dumps(metadata, indent=2)
        
    except Exception as e:
        return f"Error getting metadata for object '{object_key}' in bucket '{bucket_name}': {str(e)}"

@tool
def search_bucket_objects(bucket_name: str, search_term: str, max_results: int = 50) -> str:
    """Search for objects in a bucket by name/key containing a specific term.
    
    Args:
        bucket_name: Name of the S3 bucket
        search_term: Term to search for in object keys
        max_results: Maximum number of results to return
    
    Returns:
        JSON string containing matching objects
    """
    try:
        s3_client = get_s3_client()
        
        # Use paginator to handle large buckets
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        matching_objects = []
        search_term_lower = search_term.lower()
        
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    if search_term_lower in obj['Key'].lower():
                        matching_objects.append({
                            'Key': obj['Key'],
                            'Size': obj['Size'],
                            'SizeHuman': format_size(obj['Size']),
                            'LastModified': obj['LastModified'].isoformat(),
                            'StorageClass': obj.get('StorageClass', 'STANDARD')
                        })
                        
                        if len(matching_objects) >= max_results:
                            break
            
            if len(matching_objects) >= max_results:
                break
        
        return json.dumps({
            'bucket': bucket_name,
            'search_term': search_term,
            'matching_objects': matching_objects,
            'total_matches': len(matching_objects),
            'limited_results': len(matching_objects) >= max_results
        }, indent=2)
        
    except Exception as e:
        return f"Error searching bucket '{bucket_name}' for '{search_term}': {str(e)}"

@tool
def analyze_bucket_structure(bucket_name: str, max_objects: int = 1000) -> str:
    """Analyze the structure and contents of an S3 bucket.
    
    Args:
        bucket_name: Name of the S3 bucket
        max_objects: Maximum number of objects to analyze
    
    Returns:
        JSON string containing bucket analysis
    """
    try:
        s3_client = get_s3_client()
        
        # Get bucket objects
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        objects_analyzed = 0
        total_size = 0
        file_types = {}
        folders = set()
        storage_classes = {}
        
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_analyzed += 1
                    total_size += obj['Size']
                    
                    # Analyze file extension
                    key = obj['Key']
                    if '.' in key:
                        ext = key.split('.')[-1].lower()
                        file_types[ext] = file_types.get(ext, 0) + 1
                    
                    # Analyze folder structure
                    if '/' in key:
                        folder = '/'.join(key.split('/')[:-1])
                        folders.add(folder)
                    
                    # Analyze storage classes
                    storage_class = obj.get('StorageClass', 'STANDARD')
                    storage_classes[storage_class] = storage_classes.get(storage_class, 0) + 1
                    
                    if objects_analyzed >= max_objects:
                        break
            
            if objects_analyzed >= max_objects:
                break
        
        # Sort file types by count
        top_file_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]
        
        analysis = {
            'bucket': bucket_name,
            'total_objects_analyzed': objects_analyzed,
            'total_size': total_size,
            'total_size_human': format_size(total_size),
            'unique_folders': len(folders),
            'top_file_types': [{'extension': ext, 'count': count} for ext, count in top_file_types],
            'storage_classes': storage_classes,
            'sample_folders': sorted(list(folders))[:20] if folders else []
        }
        
        return json.dumps(analysis, indent=2)
        
    except Exception as e:
        return f"Error analyzing bucket '{bucket_name}': {str(e)}"

@tool
def get_bucket_info(bucket_name: str) -> str:
    """Get detailed information about a specific S3 bucket including policies and configuration.
    
    Args:
        bucket_name: Name of the S3 bucket
    
    Returns:
        JSON string containing bucket information
    """
    try:
        s3_client = get_s3_client()
        
        bucket_info = {
            'name': bucket_name,
            'region': get_bucket_region(bucket_name)
        }
        
        # Try to get various bucket configurations
        try:
            versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
            bucket_info['versioning'] = versioning.get('Status', 'Disabled')
        except:
            bucket_info['versioning'] = 'Unknown'
        
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
            bucket_info['encryption'] = 'Enabled'
            bucket_info['encryption_details'] = encryption.get('ServerSideEncryptionConfiguration', {})
        except:
            bucket_info['encryption'] = 'Disabled or Unknown'
        
        try:
            public_access = s3_client.get_public_access_block(Bucket=bucket_name)
            bucket_info['public_access_block'] = public_access.get('PublicAccessBlockConfiguration', {})
        except:
            bucket_info['public_access_block'] = 'Not configured'
        
        return json.dumps(bucket_info, indent=2)
        
    except Exception as e:
        return f"Error getting information for bucket '{bucket_name}': {str(e)}"

def format_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def create_s3_agent():
    """Create a Strands agent specialized for S3 operations."""
    
    tools = [
        list_s3_buckets,
        list_bucket_objects,
        get_object_metadata,
        search_bucket_objects,
        analyze_bucket_structure,
        get_bucket_info
    ]
    
    system_prompt = """You are an S3 expert assistant that helps users browse, analyze, and manage their S3 buckets and objects.

You have access to the following S3 tools:
- list_s3_buckets: List all buckets in the account
- list_bucket_objects: List objects in a specific bucket (with optional prefix filtering)
- get_object_metadata: Get detailed metadata for a specific object
- search_bucket_objects: Search for objects by name/key containing specific terms
- analyze_bucket_structure: Analyze bucket contents, file types, and folder structure
- get_bucket_info: Get bucket configuration, policies, and settings

When helping users:
1. Start by listing buckets if they don't specify one
2. Use prefixes to navigate folder structures efficiently
3. Provide human-readable file sizes and dates
4. Explain storage classes and their implications
5. Help users understand bucket configurations and security settings
6. Suggest best practices for organization and cost optimization

Always explain what you're doing and why, and provide insights about storage costs, organization, and access patterns."""

    # Use default Strands Bedrock configuration
    return Agent(
        tools=tools,
        system_prompt=system_prompt
    )

def main():
    """Test the S3 agent."""
    print("S3 Browser Agent")
    print("=" * 50)
    
    try:
        agent = create_s3_agent()
        
        print("\nAgent created successfully!")
        print("You can now ask questions like:")
        print("- What S3 buckets do I have?")
        print("- Show me the contents of my-bucket")
        print("- Search for .jpg files in my-photos bucket")
        print("- Analyze the structure of my-data bucket")
        print("- What's the configuration of my-website bucket?")
        
        print("\nTesting agent...")
        
        response = agent("What S3 buckets do I have access to?")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()