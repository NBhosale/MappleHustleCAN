# Layer Responsibilities Guide

This document clearly defines the responsibilities of each layer to prevent overlap and ensure proper separation of concerns.

## 🏗️ **Layer Responsibilities**

### **Repositories Layer (`app/repositories/`)**
**Purpose**: Data access and persistence operations only

**Responsibilities**:
- ✅ Execute database queries
- ✅ Handle CRUD operations
- ✅ Manage data relationships
- ✅ Provide data access interfaces
- ✅ Handle database-specific logic
- ✅ Manage transactions at the data level

**What Repositories SHOULD do**:
```python
# ✅ Good: Pure data access
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_data: dict) -> User:
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_services(db: Session, user_id: UUID) -> List[Service]:
    return db.query(Service).filter(Service.provider_id == user_id).all()
```

**What Repositories SHOULD NOT do**:
```python
# ❌ Bad: Business logic in repository
def create_user_with_validation(db: Session, user_data: dict) -> User:
    # This is business logic, not data access
    if not is_valid_email(user_data['email']):
        raise ValueError("Invalid email")
    # ... rest of validation logic
```

### **Services Layer (`app/services/`)**
**Purpose**: Business logic and domain operations

**Responsibilities**:
- ✅ Implement business rules
- ✅ Orchestrate complex operations
- ✅ Handle validation and business constraints
- ✅ Coordinate between repositories
- ✅ Manage business transactions
- ✅ Handle external integrations
- ✅ Process business events

**What Services SHOULD do**:
```python
# ✅ Good: Business logic
def create_user_service(db: Session, user_data: UserCreate) -> User:
    # Business validation
    if not is_valid_email(user_data.email):
        raise ValidationError("Invalid email format")
    
    # Check business rules
    existing_user = user_repo.get_by_email(db, user_data.email)
    if existing_user:
        raise BusinessError("User already exists")
    
    # Hash password (business logic)
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_data_dict = user_data.dict()
    user_data_dict['hashed_password'] = hashed_password
    user = user_repo.create(db, user_data_dict)
    
    # Send welcome email (business process)
    send_welcome_email(user.email)
    
    return user
```

**What Services SHOULD NOT do**:
```python
# ❌ Bad: Direct database access in service
def create_user_service(db: Session, user_data: UserCreate) -> User:
    # This should be in repository
    user = User(**user_data.dict())
    db.add(user)
    db.commit()
    return user
```

## 🔄 **Data Flow Pattern**

### **Correct Flow**:
```
Router → Service → Repository → Database
  ↓        ↓         ↓
Validate → Business → Data Access
  ↓        Logic      ↓
Response ← Process ← Query
```

### **Example Implementation**:

**Repository (Data Access Only)**:
```python
class UserRepository:
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def create(self, db: Session, user_data: dict) -> User:
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def get_services(self, db: Session, user_id: UUID) -> List[Service]:
        return db.query(Service).filter(Service.provider_id == user_id).all()
```

**Service (Business Logic Only)**:
```python
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def create_user(self, db: Session, user_data: UserCreate) -> User:
        # Business validation
        self._validate_user_data(user_data)
        
        # Check business rules
        existing_user = self.user_repo.get_by_email(db, user_data.email)
        if existing_user:
            raise BusinessError("User already exists")
        
        # Business processing
        hashed_password = self._hash_password(user_data.password)
        user_data_dict = user_data.dict()
        user_data_dict['hashed_password'] = hashed_password
        
        # Create user via repository
        user = self.user_repo.create(db, user_data_dict)
        
        # Business events
        self._send_welcome_email(user.email)
        
        return user
    
    def _validate_user_data(self, user_data: UserCreate):
        # Business validation logic
        pass
    
    def _hash_password(self, password: str) -> str:
        # Business logic for password hashing
        pass
    
    def _send_welcome_email(self, email: str):
        # Business process
        pass
```

**Router (HTTP Handling Only)**:
```python
@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    try:
        user = user_service.create_user(db, user_data)
        return UserResponse.from_orm(user)
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

## 🚨 **Common Anti-Patterns to Avoid**

### **Repository Anti-Patterns**:
```python
# ❌ Don't put business logic in repositories
class UserRepository:
    def create_user_with_validation(self, db: Session, user_data: dict):
        # This is business logic, not data access
        if not self._is_valid_email(user_data['email']):
            raise ValueError("Invalid email")
        # ... validation logic
```

### **Service Anti-Patterns**:
```python
# ❌ Don't access database directly in services
class UserService:
    def create_user(self, db: Session, user_data: UserCreate):
        # This should be in repository
        user = User(**user_data.dict())
        db.add(user)
        db.commit()
        return user
```

### **Router Anti-Patterns**:
```python
# ❌ Don't put business logic in routers
@router.post("/users")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # This should be in service
    if not is_valid_email(user_data.email):
        raise HTTPException(status_code=400, detail="Invalid email")
    # ... business logic
```

## 📋 **Migration Strategy**

### **Step 1: Audit Current Code**
1. Identify business logic in repositories
2. Identify data access logic in services
3. Create migration plan

### **Step 2: Refactor Repositories**
1. Remove all business logic from repositories
2. Keep only data access operations
3. Add proper error handling for data operations

### **Step 3: Refactor Services**
1. Move business logic from repositories to services
2. Ensure services only use repositories for data access
3. Add proper business validation

### **Step 4: Update Routers**
1. Ensure routers only call services
2. Remove direct database access from routers
3. Add proper HTTP error handling

## 🎯 **Benefits of Proper Separation**

### **Repositories**:
- ✅ Easy to test data access
- ✅ Reusable across services
- ✅ Simple to mock for testing
- ✅ Database-agnostic business logic

### **Services**:
- ✅ Business logic centralized
- ✅ Easy to test business rules
- ✅ Reusable across routers
- ✅ Clear business boundaries

### **Routers**:
- ✅ Focus on HTTP concerns
- ✅ Simple and clean
- ✅ Easy to test API behavior
- ✅ Consistent error handling

## 📚 **Implementation Checklist**

### **For Repositories**:
- [ ] Only contain data access methods
- [ ] No business validation logic
- [ ] No external service calls
- [ ] Proper error handling for data operations
- [ ] Clear method names (get_, create_, update_, delete_)

### **For Services**:
- [ ] Only contain business logic
- [ ] Use repositories for all data access
- [ ] Handle business validation
- [ ] Manage business transactions
- [ ] Coordinate external services

### **For Routers**:
- [ ] Only handle HTTP requests/responses
- [ ] Use services for all business operations
- [ ] Proper error handling and status codes
- [ ] Input validation using Pydantic schemas
- [ ] Consistent response format

This clear separation ensures maintainable, testable, and scalable code architecture.
