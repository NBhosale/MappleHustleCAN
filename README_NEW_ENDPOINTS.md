# 🚀 New Endpoints Documentation

## Overview
This document describes the new critical endpoints added to MapleHustleCAN API to address missing functionality for file uploads, image handling, bulk operations, and search/filtering.

## 📁 File Upload Endpoints (`/uploads`)

### Profile Image Upload
```http
POST /uploads/profile-image
Content-Type: multipart/form-data

file: (image file)
```

**Response:**
```json
{
  "message": "Profile image uploaded successfully",
  "file_path": "profiles/profile_123_abc123.jpg",
  "file_size": 1024000,
  "content_type": "image/jpeg"
}
```

### Item Images Upload
```http
POST /uploads/item-images
Content-Type: multipart/form-data

files: (multiple image files)
item_id: "uuid"
```

**Response:**
```json
{
  "message": "Successfully uploaded 2 images",
  "item_id": "uuid",
  "files": [
    {
      "filename": "item1.jpg",
      "file_path": "items/item_uuid_0_abc123.jpg",
      "file_size": 512000,
      "content_type": "image/jpeg",
      "order": 0
    }
  ]
}
```

### Message Attachments
```http
POST /uploads/message-attachments
Content-Type: multipart/form-data

files: (multiple files)
message_id: "uuid"
```

### Document Uploads
```http
POST /uploads/documents
Content-Type: multipart/form-data

file: (document file)
document_type: "certification"
```

### Bulk File Upload
```http
POST /uploads/bulk/items
Content-Type: multipart/form-data

files: (up to 50 image files)
```

## 🔍 Search & Filtering Endpoints (`/search`)

### Service Search
```http
GET /search/services?q=cleaning&service_type=house_cleaning&min_rate=20&max_rate=50&city=Toronto&province=ON&page=1&limit=20
```

**Query Parameters:**
- `q`: Search query (optional)
- `service_type`: Filter by service type (optional)
- `min_rate`/`max_rate`: Price range filters (optional)
- `city`/`province`: Location filters (optional)
- `is_featured`: Filter featured services (optional)
- `sort_by`: Sort field (default: created_at)
- `sort_order`: asc/desc (default: desc)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

### Available Services Search
```http
GET /search/services/available?date=2025-01-15&start_time=09:00&end_time=17:00&service_type=dog_walking&city=Vancouver
```

### Item Search
```http
GET /search/items?q=dog food&category_id=uuid&min_price=10&max_price=100&in_stock=true&is_featured=true
```

### Provider Search
```http
GET /search/providers?q=John&city=Montreal&province=QC&service_type=dog_sitting&min_rating=4.0
```

### Search Suggestions
```http
GET /search/suggestions?q=dog&type=all&limit=10
```

**Response:**
```json
{
  "query": "dog",
  "suggestions": [
    {"text": "Dog Walking Service", "type": "service"},
    {"text": "Dog Food Premium", "type": "item"},
    {"text": "John Smith", "type": "provider"}
  ]
}
```

### Advanced Search
```http
GET /search/advanced/services?q=cleaning&filters={"tags":["eco-friendly"],"availability_days":["monday","tuesday"]}
```

## 📦 Bulk Operations Endpoints (`/bulk`)

### Bulk Service Operations

#### Create Multiple Services
```http
POST /bulk/services
Content-Type: application/json

[
  {
    "type": "house_cleaning",
    "title": "Basic House Cleaning",
    "description": "Regular house cleaning service",
    "hourly_rate": 25.0,
    "is_featured": false
  },
  {
    "type": "dog_walking",
    "title": "Dog Walking Service",
    "description": "Professional dog walking",
    "hourly_rate": 20.0,
    "is_featured": true
  }
]
```

#### Update Multiple Services
```http
PUT /bulk/services
Content-Type: application/json

[
  {
    "id": "uuid",
    "data": {
      "title": "Updated Service",
      "hourly_rate": 30.0
    }
  }
]
```

#### Delete Multiple Services
```http
DELETE /bulk/services
Content-Type: application/json

["uuid1", "uuid2", "uuid3"]
```

### Bulk Item Operations

#### Create Multiple Items
```http
POST /bulk/items
Content-Type: application/json

[
  {
    "category_id": "uuid",
    "name": "Dog Food",
    "description": "Premium dog food",
    "price": 29.99,
    "inventory_quantity": 100
  }
]
```

#### Update Inventory Quantities
```http
PUT /bulk/items/inventory
Content-Type: application/json

[
  {"item_id": "uuid1", "quantity": 150},
  {"item_id": "uuid2", "quantity": 75}
]
```

### Bulk Availability Operations

#### Create Multiple Availability Slots
```http
POST /bulk/availability
Content-Type: application/json

[
  {
    "date": "2025-01-15",
    "start_time": "09:00",
    "end_time": "17:00",
    "status": "available"
  },
  {
    "date": "2025-01-16",
    "start_time": "09:00",
    "end_time": "17:00",
    "status": "available"
  }
]
```

### Bulk Booking Operations

#### Create Multiple Bookings
```http
POST /bulk/bookings
Content-Type: application/json

[
  {
    "provider_id": "uuid",
    "service_id": "uuid",
    "start_date": "2025-01-15",
    "end_date": "2025-01-15",
    "total_amount": 100.0,
    "status": "pending"
  }
]
```

#### Update Booking Statuses
```http
PUT /bulk/bookings/status
Content-Type: application/json

[
  {"booking_id": "uuid1", "status": "accepted"},
  {"booking_id": "uuid2", "status": "rejected"}
]
```

### Export Operations

#### Export Services
```http
GET /bulk/export/services?format=json
```

**Supported Formats:**
- `json`: JSON format (default)
- `csv`: CSV format (planned)
- `xlsx`: Excel format (planned)

#### Export Bookings
```http
GET /bulk/export/bookings?format=json
```

## 🔧 File Management

### Delete File
```http
DELETE /uploads/files/{file_path}
```

### Get File Info
```http
GET /uploads/files/{file_path}
```

## 📊 Response Formats

### Success Response
```json
{
  "message": "Operation completed successfully",
  "data": [...],
  "total_count": 10,
  "page": 1,
  "limit": 20
}
```

### Bulk Operation Response
```json
{
  "message": "Bulk operation completed. 5 successful, 1 failed",
  "successful_items": [...],
  "failed_items": [
    {
      "index": 2,
      "error": "Validation error message",
      "data": {...}
    }
  ]
}
```

### Error Response
```json
{
  "detail": "Error message",
  "type": "validation_error",
  "field": "field_name",
  "error_code": "INVALID_VALUE"
}
```

## 🛡️ Security & Validation

### File Upload Security
- **File Type Validation**: Only allowed file types accepted
- **File Size Limits**: Configurable size limits per file type
- **Virus Scanning**: Planned for production
- **User Authorization**: Users can only access their own files

### Search Security
- **Rate Limiting**: Applied to all search endpoints
- **Input Sanitization**: All search queries are sanitized
- **SQL Injection Protection**: Parameterized queries used
- **Access Control**: Users can only search accessible data

### Bulk Operations Security
- **Batch Size Limits**: Maximum items per operation
- **User Authorization**: Users can only operate on their own data
- **Transaction Safety**: All operations are wrapped in database transactions
- **Rollback on Failure**: Failed operations are rolled back

## 🚀 Performance Considerations

### File Upload Performance
- **Chunked Uploads**: Large files uploaded in chunks
- **Async Processing**: File processing happens asynchronously
- **CDN Integration**: Files served from CDN (planned)
- **Image Optimization**: Automatic image resizing and compression

### Search Performance
- **Database Indexing**: Proper indexes on searchable fields
- **Pagination**: All search results are paginated
- **Caching**: Search results cached (planned)
- **Query Optimization**: Efficient SQL queries

### Bulk Operations Performance
- **Batch Processing**: Operations processed in batches
- **Progress Tracking**: Real-time progress updates (planned)
- **Background Jobs**: Large operations moved to background (planned)
- **Resource Management**: Memory and CPU usage optimized

## 📈 Usage Examples

### Complete Workflow Example

1. **Upload Item Images**
```bash
curl -X POST "http://localhost:8000/uploads/item-images" \
  -F "files=@item1.jpg" \
  -F "files=@item2.jpg" \
  -F "item_id=123e4567-e89b-12d3-a456-426614174000"
```

2. **Create Multiple Items**
```bash
curl -X POST "http://localhost:8000/bulk/items" \
  -H "Content-Type: application/json" \
  -d '[{"category_id":"uuid","name":"Dog Food","price":29.99,"inventory_quantity":100}]'
```

3. **Search for Items**
```bash
curl "http://localhost:8000/search/items?q=dog&in_stock=true&sort_by=price&sort_order=asc"
```

4. **Bulk Update Inventory**
```bash
curl -X PUT "http://localhost:8000/bulk/items/inventory" \
  -H "Content-Type: application/json" \
  -d '[{"item_id":"uuid1","quantity":150}]'
```

## 🔄 Integration Notes

### Frontend Integration
- **File Upload Components**: Use multipart/form-data for file uploads
- **Search Components**: Implement real-time search with debouncing
- **Bulk Operations UI**: Show progress and handle partial failures
- **Error Handling**: Display user-friendly error messages

### Mobile Integration
- **Image Compression**: Compress images before upload
- **Offline Support**: Queue operations for when online
- **Progress Indicators**: Show upload/operation progress
- **Retry Logic**: Implement retry for failed operations

### Third-Party Integration
- **CDN Integration**: Upload files directly to CDN
- **Search Services**: Integrate with Elasticsearch (planned)
- **File Processing**: Use cloud functions for image processing
- **Analytics**: Track search and usage patterns

## 🐛 Troubleshooting

### Common Issues

1. **File Upload Failures**
   - Check file size limits
   - Verify file type is allowed
   - Ensure proper authentication

2. **Search Performance Issues**
   - Add database indexes
   - Implement caching
   - Optimize queries

3. **Bulk Operation Failures**
   - Check batch size limits
   - Verify data validation
   - Review error messages

4. **Permission Errors**
   - Verify user authentication
   - Check resource ownership
   - Review access controls

### Debug Endpoints

```http
GET /debug/uploads/stats
GET /debug/search/performance
GET /debug/bulk/queue-status
```

## 📚 Additional Resources

- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [SQLAlchemy Bulk Operations](https://docs.sqlalchemy.org/en/14/orm/persistence_techniques.html#bulk-operations)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [File Upload Security Best Practices](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)
