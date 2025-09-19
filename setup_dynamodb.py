#!/usr/bin/env python3
"""
Setup script for DynamoDB conversation history table
Run this script to create the DynamoDB table manually if needed
"""

import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "chatbot-conversations")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def create_conversation_table():
    """Create DynamoDB table for conversation history"""
    try:
        print(f"Creating DynamoDB table: {DYNAMODB_TABLE_NAME}")
        print(f"AWS Region: {AWS_REGION}")
        
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        
        # Check if table already exists
        try:
            table = dynamodb.Table(DYNAMODB_TABLE_NAME)
            table.load()
            print(f"✅ Table {DYNAMODB_TABLE_NAME} already exists")
            return True
        except dynamodb.meta.client.exceptions.ResourceNotFoundException:
            pass
        
        # Create table
        table = dynamodb.create_table(
            TableName=DYNAMODB_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'session_id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'session_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand billing
        )
        
        # Wait for table to be created
        print("Waiting for table to be created...")
        table.wait_until_exists()
        print(f"✅ Table {DYNAMODB_TABLE_NAME} created successfully")
        
        # Print table info
        print(f"\nTable Details:")
        print(f"- Table Name: {DYNAMODB_TABLE_NAME}")
        print(f"- Region: {AWS_REGION}")
        print(f"- Billing Mode: Pay per request")
        print(f"- Partition Key: session_id (String)")
        print(f"- Sort Key: timestamp (String)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def test_table_access():
    """Test if we can access the table"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        
        # Try to describe the table
        response = table.describe_table()
        print(f"✅ Table access successful")
        print(f"Table Status: {response['Table']['TableStatus']}")
        print(f"Item Count: {response['Table']['ItemCount']}")
        return True
        
    except Exception as e:
        print(f"❌ Error accessing table: {e}")
        return False

if __name__ == "__main__":
    print("=== DynamoDB Setup for Chatbot Conversations ===")
    print()
    
    # Create table
    if create_conversation_table():
        print()
        # Test access
        test_table_access()
    else:
        print("Failed to create table")
