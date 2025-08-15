# Homeless Resource Directory

A comprehensive Django-based web application for curating and maintaining a high-quality directory of resources for people experiencing homelessness. This system serves as a definitive reference tool for case managers, outreach workers, and community partners to connect individuals with appropriate services.

## 🎯 Mission

To provide accurate, verified, and up-to-date information about resources available to people experiencing homelessness, with a focus on the London, Kentucky area and surrounding counties. The system ensures data integrity through comprehensive validation, version control, and audit trails.

## 🚀 Quick Start

### Development Setup

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

### Docker Setup

```bash
docker-compose up --build
```

## 🌟 Key Features

### 📋 Resource Management
- **Comprehensive Profiles**: Contact details, services, hours, eligibility, operational notes
- **Multi-Service Classification**: Multiple service types per resource
- **Geographic Organization**: Location-based filtering and search
- **Operational Details**: Hours, capacity, accessibility features

### 🔄 Workflow Management
- **Three-Stage Workflow**: Draft → Needs Review → Published
- **Status-Based Validation**: Progressive requirements at each stage
- **Verification System**: Published resources require 180-day verification
- **Role-Based Access**: Editor, Reviewer, and Admin roles

### 🔍 Advanced Search & Discovery
- **Full-Text Search**: SQLite FTS5 for fast, relevant results
- **Combined Search**: FTS5 + exact field matching
- **Multi-Filter Support**: Category, location, service type, status
- **Geographic Search**: Find by city, county, or state

### 📊 Data Management
- **CSV Import/Export**: Bulk operations with validation
- **Column Mapping**: Flexible import configuration
- **Error Reporting**: Detailed feedback with row-level tracking
- **Data Validation**: Comprehensive quality rules

### 🛡️ Data Integrity & Audit
- **Immutable Version History**: Complete audit trail
- **Database Triggers**: Prevents historical data modification
- **Audit Logging**: Append-only logs of all actions
- **Change Tracking**: Detailed diff views between versions

### 🗃️ Archive Management
- **Soft Archiving**: Preserve closed resources historically
- **Archive Reasoning**: Track why/when/who archived
- **Archive Views**: Dedicated browse and search interfaces
- **Admin Actions**: Bulk archive/unarchive operations

## 🏗️ Architecture

### Tech Stack
- **Backend**: Django 5.0.2 with Python 3.x
- **Database**: SQLite with WAL mode
- **Frontend**: HTMX + Bootstrap
- **Search**: SQLite FTS5
- **Deployment**: Docker

### Project Structure
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
├── templates/             # HTML templates
└── requirements.txt       # Python dependencies
```

## 📊 Data Model

### Core Entities

#### Resource Model
- **Basic Info**: Name, description, category, service types
- **Contact Info**: Phone, email, website, physical address
- **Operational**: Hours, emergency designation, capacity
- **Service-Specific**: Eligibility, populations served, insurance, cost
- **Verification**: Last verification date, verifier, metadata

#### Supporting Models
- **TaxonomyCategory**: Hierarchical organization
- **ServiceType**: Service classification
- **ResourceVersion**: Immutable snapshots
- **AuditLog**: Append-only audit trail
- **ImportJob**: CSV import tracking

## 🔄 Workflow System

| Stage | Requirements | Purpose |
|-------|-------------|---------|
| **Draft** | Name + 1 contact method | Initial data entry |
| **Needs Review** | City/state + description (20+ chars) + source | Basic completeness |
| **Published** | Verified within 180 days + verifier | Public availability |

## 🔍 Search & Discovery

### Full-Text Search
- **FTS5 Implementation**: Fast, relevant search
- **Searchable Fields**: Name, description, services, location
- **Relevance Ranking**: Results ordered by relevance

### Filtering Options
- **Geographic**: City, county, state
- **Service Type**: Food, housing, mental health, etc.
- **Status**: Draft, needs review, published
- **Operational**: Emergency services, 24/7 availability

## 📥 Data Import/Export

### CSV Import System
- **Validation Pipeline**: Comprehensive data validation
- **Error Reporting**: Detailed feedback on failures
- **Column Mapping**: Flexible CSV format configuration
- **Batch Processing**: Efficient large dataset handling

### Export Capabilities
- **Filtered Exports**: Based on search criteria
- **Format Options**: CSV with configurable fields
- **Data Selection**: Choose fields to include

## 🧪 Testing

### Test Suite Architecture
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

### Test Coverage
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

### Running Tests

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

## 🎯 Use Cases

### For Case Managers
- Quick resource discovery based on client needs
- Geographic filtering for location-based services
- Eligibility checking and contact information access

### For Outreach Workers
- Mobile-responsive design for field use
- Emergency services identification
- Real-time service availability updates

### For Community Partners
- Resource coordination and gap identification
- Partnership development and data sharing
- Quality assurance and accuracy verification

## 🔒 Security & Performance

### Security Features
- **Audit System**: Immutable logs with version control
- **Access Control**: Role-based permissions
- **Data Protection**: CSRF protection, input validation
- **Privacy**: No PII stored, public service data only

### Performance Optimizations
- **Database**: SQLite WAL mode, optimized indexes
- **Search**: FTS5 indexing, result caching
- **Import/Export**: Batch processing, progress tracking
- **Testing**: Parallel execution, database reuse

## 📈 Recent Enhancements

### Archive System & London KY Resources
- **Complete Archive Workflow**: Integrated across models, views, admin
- **London KY Import**: 42 verified resources imported
  - **Geographic Coverage**: 30 London/Laurel County + 6 regional + 6 statewide
  - **Service Categories**: Food (8), Housing (6), Mental Health (8), Medical (2), Government (5), Faith-based (2), Veterans (1), Utilities (1)
  - **Data Quality**: Independently verified, comprehensive operational details

## 🤝 Contributing

### Quick Steps
1. Fork the repository
2. Create a feature branch
3. Follow coding standards (PEP 8, type hints, docstrings)
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines
- Maintain 90%+ test coverage
- Follow Django best practices
- Use modular test structure
- Ensure backward compatibility

## 📞 Support & Maintenance

### Regular Maintenance
- **Data Verification**: Periodic resource information verification
- **System Updates**: Security and feature updates
- **Performance Monitoring**: System performance tracking
- **Backup Management**: Database backups and recovery testing

## 📄 License

[Add your license information here]

---

## 🎉 Project Status

**MVP Status**: ✅ **COMPLETE** - All critical requirements implemented and tested!

**Current Version**: Production-ready with comprehensive feature set

**Database Status**: 361 total resources with 42 verified London KY resources

**Test Suite**: ✅ **COMPREHENSIVE** - 117+ tests with 90%+ coverage

**Code Quality**: ✅ **EXCELLENT** - Modular, maintainable structure

**Next Phase**: Production deployment and user training
