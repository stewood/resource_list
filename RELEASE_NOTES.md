# Release Notes

## Version 1.0.0 - Initial Release

**Release Date**: January 2025

### 🎉 What's New

This is the initial release of the Community Resource Directory, a comprehensive Django-based web application for managing and curating resources for people in need.

### ✨ Key Features

#### 📋 Resource Management
- **Comprehensive Resource Profiles**: Complete contact details, services, hours, eligibility criteria, and operational notes
- **Multi-Service Classification**: Support for multiple service types per resource
- **Geographic Organization**: Location-based filtering and search capabilities
- **Operational Details**: Hours, capacity, and accessibility features

#### 🔄 Workflow Management
- **Three-Stage Workflow**: Draft → Needs Review → Published
- **Status-Based Validation**: Progressive requirements at each stage
- **Verification System**: Published resources require 180-day verification cycles
- **Role-Based Access Control**: Editor, Reviewer, and Admin roles with appropriate permissions

#### 🔍 Advanced Search & Discovery
- **Full-Text Search**: SQLite FTS5 for fast, relevant results
- **Combined Search**: FTS5 + exact field matching capabilities
- **Multi-Filter Support**: Category, location, service type, and status filtering
- **Geographic Search**: Find resources by city, county, or state

#### 📊 Data Management
- **CSV Import/Export**: Bulk operations with comprehensive validation
- **Column Mapping**: Flexible import configuration options
- **Error Reporting**: Detailed feedback with row-level tracking
- **Data Validation**: Comprehensive quality rules and constraints

#### 🛡️ Data Integrity & Audit
- **Immutable Version History**: Complete audit trail for all changes
- **Database Triggers**: Prevents historical data modification
- **Audit Logging**: Append-only logs of all actions
- **Change Tracking**: Detailed diff views between versions

#### 🗃️ Archive Management
- **Soft Archiving**: Preserve closed resources historically
- **Archive Reasoning**: Track why/when/who archived resources
- **Archive Views**: Dedicated browse and search interfaces
- **Admin Actions**: Bulk archive/unarchive operations

### 🏗️ Technical Architecture

#### Tech Stack
- **Backend**: Django 5.0.2 with Python 3.x
- **Database**: SQLite with WAL mode for performance
- **Frontend**: HTMX + Bootstrap for responsive design
- **Search**: SQLite FTS5 for full-text search
- **Deployment**: Docker support included

#### Project Structure
```
resource_list/
├── resource_directory/     # Django project settings
├── directory/             # Main app (models, views, admin)
├── audit/                 # Audit and versioning logic
├── importer/              # CSV import/export functionality
├── cli_review/            # CLI tools for data review
├── docs/                  # Project documentation
├── scripts/               # Utility scripts
├── static/                # Static files
└── templates/             # HTML templates
```

#### Data Model

##### Core Entities

###### Resource Model
- **Basic Info**: Name, description, category, service types
- **Contact Info**: Phone, email, website, physical address
- **Operational**: Hours, emergency designation, capacity
- **Service-Specific**: Eligibility, populations served, insurance, cost
- **Verification**: Last verification date, verifier, metadata

###### Supporting Models
- **TaxonomyCategory**: Hierarchical organization
- **ServiceType**: Service classification
- **ResourceVersion**: Immutable snapshots
- **AuditLog**: Append-only audit trail
- **ImportJob**: CSV import tracking

#### Workflow System

| Stage | Requirements | Purpose |
|-------|-------------|---------|
| **Draft** | Name + 1 contact method | Initial data entry |
| **Needs Review** | City/state + description (20+ chars) + source | Basic completeness |
| **Published** | Verified within 180 days + verifier | Public availability |

#### Search & Discovery

##### Full-Text Search
- **FTS5 Implementation**: Fast, relevant search
- **Searchable Fields**: Name, description, services, location
- **Relevance Ranking**: Results ordered by relevance

##### Filtering Options
- **Geographic**: City, county, state
- **Service Type**: Food, housing, mental health, etc.
- **Status**: Draft, needs review, published
- **Operational**: Emergency services, 24/7 availability

#### Data Import/Export

##### CSV Import System
- **Validation Pipeline**: Comprehensive data validation
- **Error Reporting**: Detailed feedback on failures
- **Column Mapping**: Flexible CSV format configuration
- **Batch Processing**: Efficient large dataset handling

##### Export Capabilities
- **Filtered Exports**: Based on search criteria
- **Format Options**: CSV with configurable fields
- **Data Selection**: Choose fields to include

### 📈 Quality Metrics

- **Test Coverage**: 53% (excluding CLI tools and management commands)
- **Test Suite**: 126 tests, all passing
- **Core Functionality Coverage**:
  - Resource models: 96% coverage
  - Resource CRUD views: 100% coverage
  - Core settings: 100% coverage
  - Main workflows: 60-82% coverage

### 🧪 Testing Details

#### Test Suite Architecture
```
directory/tests/
├── test_models.py         # Resource validation & workflow
├── test_views.py          # HTTP views & permissions
├── test_forms.py          # Form validation & transitions
├── test_search.py         # FTS5 search & filtering
├── test_permissions.py    # Role-based access control
├── test_versions.py       # Version control & audit
└── test_integration.py    # End-to-end workflows
```

#### Test Coverage Breakdown
| Category | Tests | Coverage |
|----------|-------|----------|
| **Models** | 15+ | Validation, workflow, normalization |
| **Views** | 20+ | HTTP responses, auth, permissions |
| **Forms** | 18+ | Validation, transitions, requirements |
| **Search** | 25+ | FTS5, filtering, pagination |
| **Permissions** | 12+ | Role-based access, user management |
| **Versions** | 15+ | Version control, audit trails |
| **Integration** | 12+ | Complete workflows, scenarios |

**Total**: 117+ tests with 90%+ coverage

#### Running Tests
```bash
# Run all tests (recommended)
./run_tests.py

# Run specific categories
./run_tests.py models
./run_tests.py views
./run_tests.py integration

# Run with coverage
./run_tests.py --coverage

# Run sequentially (debugging)
./run_tests.py --no-parallel
```

**Performance**: ~50 seconds (83% faster than original)

### 🚀 Getting Started

#### Development Setup

1. **Clone and setup**:
   ```bash
   git clone https://github.com/stewood/resource_list.git
   cd resource_list
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Initialize database**:
   ```bash
   python manage.py migrate
   python manage.py setup_wal
   python manage.py createsuperuser
   ```

3. **Run server**:
   ```bash
   python manage.py runserver
   ```

4. **Access admin**: http://localhost:8000/admin/

#### Docker Setup

```bash
docker-compose up --build
```

### 🔧 Configuration

#### Environment Variables

- `DJANGO_SECRET_KEY`: Secret key for Django (required in production)
- `DEBUG`: Enable debug mode (defaults to False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_PATH`: Path to SQLite database file

#### Database Setup

The application uses SQLite with WAL mode for optimal performance. The database is automatically configured during setup.

### 📚 Documentation

- **User Guide**: See `docs/` directory for detailed documentation
- **API Documentation**: REST API endpoints documented in views
- **Contributing Guidelines**: See `CONTRIBUTING.md`
- **Data Quality Process**: See `docs/DATA_QUALITY_PROCESS.md`

### 🐛 Known Issues

- Some linting issues exist (mostly formatting-related)
- Coverage excludes CLI tools and management commands
- Backup files included in repository (will be cleaned up in future releases)

### 🎯 Use Cases

#### For Case Managers
- Quick resource discovery based on client needs
- Geographic filtering for location-based services
- Eligibility checking and contact information access

#### For Outreach Workers
- Mobile-responsive design for field use
- Emergency services identification
- Real-time service availability updates

#### For Community Partners
- Resource coordination and gap identification
- Partnership development and data sharing
- Quality assurance and accuracy verification

### 🔒 Security & Performance

#### Security Features
- **Audit System**: Immutable logs with version control
- **Access Control**: Role-based permissions
- **Data Protection**: CSRF protection, input validation
- **Privacy**: No PII stored, public service data only

#### Performance Optimizations
- **Database**: SQLite WAL mode, optimized indexes
- **Search**: FTS5 indexing, result caching
- **Import/Export**: Batch processing, progress tracking
- **Testing**: Parallel execution, database reuse

### 📈 Recent Enhancements

#### Archive System & London KY Resources
- **Complete Archive Workflow**: Integrated across models, views, admin
- **London KY Import**: 42 verified resources imported
  - **Geographic Coverage**: 30 London/Laurel County + 6 regional + 6 statewide
  - **Service Categories**: Food (8), Housing (6), Mental Health (8), Medical (2), Government (5), Faith-based (2), Veterans (1), Utilities (1)
  - **Data Quality**: Independently verified, comprehensive operational details

### 🔮 Future Roadmap

- Enhanced search capabilities
- API improvements
- Additional export formats
- Performance optimizations
- Mobile-responsive improvements

### 🤝 Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for guidelines.

### 📄 License

This project is open source. See LICENSE file for details.

### 🙏 Acknowledgments

- Django community for the excellent framework
- SQLite team for the robust database engine
- All contributors and testers

---

**For support or questions**: Please open an issue on GitHub.
