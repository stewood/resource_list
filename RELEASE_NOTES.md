# Release Notes

## Version 1.0.0 - Initial Release

**Release Date**: January 2025

### 🎉 What's New

This is the initial release of the Homeless Resource Directory, a comprehensive Django-based web application for managing and curating resources for people experiencing homelessness.

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

### 📈 Quality Metrics

- **Test Coverage**: 53% (excluding CLI tools and management commands)
- **Test Suite**: 126 tests, all passing
- **Core Functionality Coverage**:
  - Resource models: 96% coverage
  - Resource CRUD views: 100% coverage
  - Core settings: 100% coverage
  - Main workflows: 60-82% coverage

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
