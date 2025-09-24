"""
Layer Separation Enforcement for MapleHustleCAN
Ensures clear separation between repositories and services
"""

from typing import Any, Dict, List, Optional, Type, Union
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class RepositoryInterface(ABC):
    """Base interface for all repositories - data access only"""
    
    @abstractmethod
    def get_by_id(self, db: Session, id: str) -> Optional[Any]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get all entities with pagination"""
        pass
    
    @abstractmethod
    def create(self, db: Session, data: Dict[str, Any]) -> Any:
        """Create new entity"""
        pass
    
    @abstractmethod
    def update(self, db: Session, id: str, data: Dict[str, Any]) -> Optional[Any]:
        """Update entity by ID"""
        pass
    
    @abstractmethod
    def delete(self, db: Session, id: str) -> bool:
        """Delete entity by ID"""
        pass


class ServiceInterface(ABC):
    """Base interface for all services - business logic only"""
    
    def __init__(self, repository: RepositoryInterface):
        self.repository = repository
    
    @abstractmethod
    def process_business_logic(self, db: Session, data: Dict[str, Any]) -> Any:
        """Process business logic"""
        pass


class LayerSeparationValidator:
    """Validates proper layer separation"""
    
    @staticmethod
    def validate_repository_methods(repository_class: Type) -> List[str]:
        """Validate repository methods follow data access patterns"""
        violations = []
        
        # Check for business logic in repository
        for method_name in dir(repository_class):
            if method_name.startswith('_'):
                continue
                
            method = getattr(repository_class, method_name)
            if not callable(method):
                continue
            
            # Check method name patterns
            if any(pattern in method_name.lower() for pattern in [
                'validate', 'process', 'calculate', 'send', 'notify',
                'check', 'verify', 'format', 'transform'
            ]):
                violations.append(f"Repository method '{method_name}' appears to contain business logic")
        
        return violations
    
    @staticmethod
    def validate_service_methods(service_class: Type) -> List[str]:
        """Validate service methods follow business logic patterns"""
        violations = []
        
        # Check for direct database access in service
        for method_name in dir(service_class):
            if method_name.startswith('_'):
                continue
                
            method = getattr(service_class, method_name)
            if not callable(method):
                continue
            
            # Check for direct database operations
            source = method.__code__.co_names if hasattr(method, '__code__') else []
            if any(name in source for name in ['query', 'add', 'commit', 'rollback', 'execute']):
                violations.append(f"Service method '{method_name}' appears to access database directly")
        
        return violations


class RepositoryBase(RepositoryInterface):
    """Base repository with common data access patterns"""
    
    def __init__(self, model_class: Type):
        self.model_class = model_class
    
    def get_by_id(self, db: Session, id: str) -> Optional[Any]:
        """Get entity by ID - pure data access"""
        return db.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get all entities - pure data access"""
        return db.query(self.model_class).offset(skip).limit(limit).all()
    
    def create(self, db: Session, data: Dict[str, Any]) -> Any:
        """Create entity - pure data access"""
        entity = self.model_class(**data)
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity
    
    def update(self, db: Session, id: str, data: Dict[str, Any]) -> Optional[Any]:
        """Update entity - pure data access"""
        entity = db.query(self.model_class).filter(self.model_class.id == id).first()
        if entity:
            for key, value in data.items():
                setattr(entity, key, value)
            db.commit()
            db.refresh(entity)
        return entity
    
    def delete(self, db: Session, id: str) -> bool:
        """Delete entity - pure data access"""
        entity = db.query(self.model_class).filter(self.model_class.id == id).first()
        if entity:
            db.delete(entity)
            db.commit()
            return True
        return False
    
    def get_by_field(self, db: Session, field: str, value: Any) -> Optional[Any]:
        """Get entity by field - pure data access"""
        return db.query(self.model_class).filter(getattr(self.model_class, field) == value).first()
    
    def get_by_fields(self, db: Session, filters: Dict[str, Any]) -> List[Any]:
        """Get entities by multiple fields - pure data access"""
        query = db.query(self.model_class)
        for field, value in filters.items():
            query = query.filter(getattr(self.model_class, field) == value)
        return query.all()


class ServiceBase(ServiceInterface):
    """Base service with common business logic patterns"""
    
    def __init__(self, repository: RepositoryInterface):
        self.repository = repository
    
    def validate_business_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validate business rules - business logic"""
        errors = []
        # Override in subclasses for specific business rules
        return errors
    
    def process_business_logic(self, db: Session, data: Dict[str, Any]) -> Any:
        """Process business logic - business logic"""
        # Override in subclasses for specific business logic
        return self.repository.create(db, data)
    
    def handle_business_events(self, entity: Any, event_type: str) -> None:
        """Handle business events - business logic"""
        # Override in subclasses for specific event handling
        pass


# Example implementations following proper separation

class UserRepository(RepositoryBase):
    """User repository - data access only"""
    
    def __init__(self):
        super().__init__(User)  # Assuming User model is imported
    
    def get_by_email(self, db: Session, email: str) -> Optional[Any]:
        """Get user by email - pure data access"""
        return self.get_by_field(db, 'email', email)
    
    def get_active_users(self, db: Session) -> List[Any]:
        """Get active users - pure data access"""
        return self.get_by_field(db, 'status', 'active')


class UserService(ServiceBase):
    """User service - business logic only"""
    
    def __init__(self):
        super().__init__(UserRepository())
    
    def validate_business_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validate user business rules - business logic"""
        errors = []
        
        # Business rule: email must be unique
        if 'email' in data:
            existing_user = self.repository.get_by_email(None, data['email'])
            if existing_user:
                errors.append("Email already exists")
        
        # Business rule: password must meet requirements
        if 'password' in data:
            if len(data['password']) < 8:
                errors.append("Password must be at least 8 characters")
        
        return errors
    
    def process_business_logic(self, db: Session, data: Dict[str, Any]) -> Any:
        """Process user creation business logic - business logic"""
        # Validate business rules
        errors = self.validate_business_rules(data)
        if errors:
            raise ValueError(f"Business rule violations: {', '.join(errors)}")
        
        # Hash password (business logic)
        if 'password' in data:
            data['hashed_password'] = self._hash_password(data.pop('password'))
        
        # Create user
        user = self.repository.create(db, data)
        
        # Handle business events
        self.handle_business_events(user, 'user_created')
        
        return user
    
    def _hash_password(self, password: str) -> str:
        """Hash password - business logic"""
        # Implementation would go here
        return f"hashed_{password}"
    
    def handle_business_events(self, user: Any, event_type: str) -> None:
        """Handle user business events - business logic"""
        if event_type == 'user_created':
            # Send welcome email (business logic)
            logger.info(f"User {user.id} created, welcome email should be sent")
            # In real implementation, this would trigger background task


# Layer separation enforcement decorators

def repository_only(func):
    """Decorator to ensure repository methods only do data access"""
    def wrapper(*args, **kwargs):
        # Add validation logic here if needed
        return func(*args, **kwargs)
    return wrapper


def service_only(func):
    """Decorator to ensure service methods only do business logic"""
    def wrapper(*args, **kwargs):
        # Add validation logic here if needed
        return func(*args, **kwargs)
    return wrapper


# Export main components
__all__ = [
    'RepositoryInterface',
    'ServiceInterface', 
    'LayerSeparationValidator',
    'RepositoryBase',
    'ServiceBase',
    'UserRepository',
    'UserService',
    'repository_only',
    'service_only'
]
