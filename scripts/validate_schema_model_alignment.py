#!/usr/bin/env python3
"""
Schema-Model Alignment Validator
Ensures all Pydantic schemas align with SQLAlchemy models
"""

import sys
import inspect
from pathlib import Path
from typing import get_type_hints, get_origin, get_args
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql.sqltypes import TIMESTAMP
from pydantic import BaseModel
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_model_fields(model_class):
    """Extract field information from SQLAlchemy model"""
    fields = {}
    for attr_name in dir(model_class):
        attr = getattr(model_class, attr_name)
        if isinstance(attr, Column):
            field_info = {
                'name': attr_name,
                'type': type(attr.type),
                'nullable': attr.nullable,
                'default': attr.default,
                'primary_key': attr.primary_key,
                'foreign_key': len(attr.foreign_keys) > 0
            }
            fields[attr_name] = field_info
    return fields

def get_schema_fields(schema_class):
    """Extract field information from Pydantic schema"""
    fields = {}
    annotations = get_type_hints(schema_class)
    
    for field_name, field_info in schema_class.__fields__.items():
        field_type = annotations.get(field_name)
        fields[field_name] = {
            'name': field_name,
            'type': field_type,
            'required': field_info.is_required(),
            'default': field_info.default,
            'nullable': not field_info.is_required() and field_info.default is None
        }
    return fields

def type_matches(model_type, schema_type):
    """Check if model type matches schema type"""
    # Map SQLAlchemy types to Python types
    type_mapping = {
        String: str,
        Integer: int,
        Boolean: bool,
        DateTime: 'datetime',
        TIMESTAMP: 'datetime',
        Text: str,
        Numeric: 'Decimal',
        UUID: 'UUID',
        JSONB: dict
    }
    
    expected_python_type = type_mapping.get(model_type, str)
    
    if schema_type == expected_python_type:
        return True
    
    # Handle Optional types
    if get_origin(schema_type) is type(None) or get_origin(schema_type) is Union:
        args = get_args(schema_type)
        if len(args) == 2 and type(None) in args:
            non_none_type = args[0] if args[1] is type(None) else args[1]
            return type_matches(model_type, non_none_type)
    
    return False

def validate_schema_model_alignment():
    """Validate alignment between schemas and models"""
    print("🔍 Validating schema-model alignment...")
    
    # Import models and schemas
    try:
        from app.models import users, services, bookings, orders, payments, items, messages, notifications, provinces, reviews, subscriptions, tokens, providers, system
        from app.schemas import users as user_schemas, services as service_schemas, bookings as booking_schemas, orders as order_schemas, payments as payment_schemas, items as item_schemas, messages as message_schemas, notifications as notification_schemas, provinces as province_schemas, reviews as review_schemas, subscriptions as subscription_schemas, tokens as token_schemas, providers as provider_schemas, system as system_schemas
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        return False
    
    # Define model-schema pairs
    model_schema_pairs = [
        (users.User, user_schemas.UserResponse),
        (services.Service, service_schemas.ServiceResponse),
        (bookings.Booking, booking_schemas.BookingResponse),
        (orders.Order, order_schemas.OrderResponse),
        (payments.Payment, payment_schemas.PaymentResponse),
        (items.Item, item_schemas.ItemResponse),
        (messages.Message, message_schemas.MessageResponse),
        (notifications.Notification, notification_schemas.NotificationResponse),
        (provinces.CanadianProvince, province_schemas.ProvinceResponse),
        (reviews.Review, review_schemas.ReviewResponse),
        (subscriptions.Subscription, subscription_schemas.SubscriptionResponse),
        (tokens.RefreshToken, token_schemas.RefreshTokenResponse),
        (providers.Provider, provider_schemas.ProviderResponse),
        (system.Session, system_schemas.SessionResponse),
    ]
    
    all_valid = True
    
    for model_class, schema_class in model_schema_pairs:
        print(f"\n📋 Validating {model_class.__name__} ↔ {schema_class.__name__}")
        
        try:
            model_fields = get_model_fields(model_class)
            schema_fields = get_schema_fields(schema_class)
            
            # Check for missing fields in schema
            missing_in_schema = []
            for field_name, field_info in model_fields.items():
                if field_name not in schema_fields and not field_info['primary_key']:
                    # Skip sensitive fields that should be excluded
                    if field_name in ['hashed_password', 'password_hash', 'token', 'secret']:
                        continue
                    missing_in_schema.append(field_name)
            
            if missing_in_schema:
                print(f"  ⚠️  Missing in schema: {missing_in_schema}")
                all_valid = False
            
            # Check for extra fields in schema
            extra_in_schema = []
            for field_name in schema_fields:
                if field_name not in model_fields:
                    extra_in_schema.append(field_name)
            
            if extra_in_schema:
                print(f"  ⚠️  Extra in schema: {extra_in_schema}")
            
            # Check type alignment for common fields
            type_mismatches = []
            for field_name in model_fields:
                if field_name in schema_fields and field_name not in ['hashed_password', 'password_hash', 'token', 'secret']:
                    model_field = model_fields[field_name]
                    schema_field = schema_fields[field_name]
                    
                    if not type_matches(model_field['type'], schema_field['type']):
                        type_mismatches.append({
                            'field': field_name,
                            'model_type': model_field['type'],
                            'schema_type': schema_field['type']
                        })
            
            if type_mismatches:
                print(f"  ⚠️  Type mismatches: {type_mismatches}")
                all_valid = False
            
            # Check nullable alignment
            nullable_mismatches = []
            for field_name in model_fields:
                if field_name in schema_fields and field_name not in ['hashed_password', 'password_hash', 'token', 'secret']:
                    model_field = model_fields[field_name]
                    schema_field = schema_fields[field_name]
                    
                    if model_field['nullable'] != schema_field['nullable']:
                        nullable_mismatches.append({
                            'field': field_name,
                            'model_nullable': model_field['nullable'],
                            'schema_nullable': schema_field['nullable']
                        })
            
            if nullable_mismatches:
                print(f"  ⚠️  Nullable mismatches: {nullable_mismatches}")
                all_valid = False
            
            if not missing_in_schema and not type_mismatches and not nullable_mismatches:
                print(f"  ✅ {schema_class.__name__} aligns with {model_class.__name__}")
            
        except Exception as e:
            print(f"  ❌ Error validating {model_class.__name__}: {e}")
            all_valid = False
    
    return all_valid

def main():
    """Run schema-model alignment validation"""
    print("🚀 Starting schema-model alignment validation...")
    
    try:
        is_valid = validate_schema_model_alignment()
        
        if is_valid:
            print("\n🎉 All schemas align with models!")
            sys.exit(0)
        else:
            print("\n💥 Some schemas don't align with models!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
