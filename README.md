# Homeless Resource Directory

A Django-based web application for curating and maintaining a high-quality directory of resources for people experiencing homelessness.

## Features

- **Resource Management**: Create, edit, and manage resources (shelters, food banks, legal aid, etc.)
- **Workflow Management**: Draft → Needs Review → Published status workflow
- **Version Control**: Complete audit trail with immutable version history
- **Data Validation**: Comprehensive validation rules for different status levels
- **CSV Import/Export**: Bulk import and export capabilities
- **Search & Filtering**: Full-text search and filtering by category, location, status
- **Audit Logging**: Complete audit trail of all system actions

## Tech Stack

- **Backend**: Django 5.0.2
- **Database**: SQLite with WAL mode
- **Frontend**: HTMX for dynamic interactions
- **API**: Django REST Framework (optional)
- **Deployment**: Docker with volume-mounted database

## Quick Start

### Development Setup

1. **Clone and setup virtual environment**:
   ```bash
   git clone <repository-url>
   cd rl
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Setup database with WAL mode**:
   ```bash
   python manage.py setup_wal
   ```

4. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server**:
   ```bash
   python manage.py runserver
   ```

6. **Access admin interface**:
   - URL: http://localhost:8000/admin/
   - Login with your superuser credentials

### Docker Setup

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Access the application**:
   - URL: http://localhost:8000/admin/

## Data Model

### Core Entities

- **Resource**: Main entity containing resource information
- **TaxonomyCategory**: Categories for organizing resources
- **ResourceVersion**: Immutable snapshots of resource changes
- **AuditLog**: Append-only audit trail of all actions

### Resource Status Workflow

1. **Draft**: Basic information required (name + contact method)
2. **Needs Review**: Additional validation (city, state, description, source)
3. **Published**: Requires verification within 180 days

## Validation Rules

### Draft Requirements
- Name is required
- At least one contact method (phone, email, or website)

### Review Requirements
- City and state must be present
- Description must be at least 20 characters
- Source must be specified

### Published Requirements
- Must be verified within 180 days
- Verifier must be specified

## API Endpoints (Optional)

- `GET /api/resources/` - List resources with filtering
- `POST /api/resources/` - Create new resource
- `PATCH /api/resources/{id}/` - Update resource
- `POST /api/resources/{id}/submit_review/` - Submit for review
- `POST /api/resources/{id}/publish/` - Publish resource
- `GET /api/resources/{id}/versions/` - Get version history

## File Structure

```
rl/
├── resource_directory/     # Django project settings
├── directory/             # Main app (models, views, admin)
├── audit/                 # Audit and versioning logic
├── importer/              # CSV import/export functionality
├── data/                  # SQLite database (development)
├── static/                # Static files
├── templates/             # HTML templates
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
└── README.md             # This file
```

## Development Guidelines

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Maintain test coverage above 90%
- Use Django's built-in validation and forms

## Security Considerations

- All changes are audited and versioned
- Immutable audit logs and version history
- CSRF protection enabled
- Input validation and sanitization
- Role-based access control

## Performance

- SQLite WAL mode for better concurrency
- Optimized database indexes
- Full-text search with FTS5
- Pagination for large datasets

## Contributing

1. Follow the established code style
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all migrations are backward compatible

## License

[Add your license information here]
