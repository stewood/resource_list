# Community Resource Directory

[![Test Coverage](https://img.shields.io/badge/test%20coverage-53%25-brightgreen)](https://github.com/stewood/resource_list)
[![Python](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.0.2-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue.svg)](https://www.postgresql.org/)

A comprehensive Django-based web application for managing and curating community resources for people in need. Built for case managers, outreach workers, and community partners to connect individuals with appropriate services.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Key Features](#-key-features)
- [Development Workflow](#-development-workflow)
- [Documentation](#-documentation)
- [Contributing](#-contributing)

## Overview

The Community Resource Directory is a production-ready web application that helps social service organizations manage and share information about community resources. It features a robust workflow system, advanced search capabilities, and comprehensive data management tools.

### **Current Status**
- ✅ **Staging Environment**: Successfully deployed and operational
- ✅ **Core Features**: All major functionality implemented and tested
- ✅ **Data Migration**: Complete migration from SQLite to PostgreSQL
- ✅ **Coverage Areas**: 7,829 coverage areas covering 83.5% of resources
- ✅ **Documentation**: 95% code documentation coverage

## 🚀 Quick Start

### **Prerequisites**
- Python 3.x
- Docker (for local database)
- Git

### **Local Development Setup**
```bash
# Clone the repository
git clone https://github.com/stewood/resource_list.git
cd resource_list

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development environment
./scripts/development/start_dev.sh

# Create admin user (optional)
python manage.py createsuperuser
```

### **Alternative: Docker Setup**
```bash
docker-compose up --build
```

**Access the application**: http://localhost:8000

## 📁 Project Structure

### **Core Application**
```
directory/                    # Main Django application
├── models/                   # Data models and database schema
│   ├── resource.py          # Resource model with all fields
│   ├── coverage_area.py     # Geographic coverage areas
│   ├── taxonomy.py          # Categories and service types
│   └── audit.py             # Audit trail and versioning
├── views/                    # Application views and logic
│   ├── resource_views.py    # Resource CRUD operations
│   ├── public_views.py      # Public-facing pages
│   ├── api_views.py         # REST API endpoints
│   └── workflow_views.py    # Approval workflow
├── forms/                    # Form definitions
│   ├── resource_forms.py    # Resource creation/editing
│   └── filter_forms.py      # Search and filtering
├── admin.py                  # Django admin interface
├── permissions.py            # Custom permissions
└── services/                 # Business logic services
    └── geocoding.py         # Address geocoding service
```

### **Configuration & Settings**
```
resource_directory/           # Django settings and configuration
├── settings.py              # Base settings
├── development_settings.py  # Local development settings
├── staging_settings.py      # Staging environment settings
├── production_settings.py   # Production environment settings
└── cloud_settings.py        # Cloud deployment settings
```

### **Scripts & Automation**
```
scripts/                     # Development and deployment scripts
├── development/             # Local development tools
│   ├── start_dev.sh        # Start development environment
│   └── run_tests.sh        # Run test suite
├── deployment/              # Deployment automation
│   ├── deploy_to_staging.sh # Deploy to staging
│   └── deploy_to_production.sh # Deploy to production
└── data/                    # Data management scripts
    ├── create_national_coverage.py # Create coverage areas
    └── reset_admin_password.py    # Admin utilities
```

### **Documentation**
```
docs/                        # Project documentation
├── development/             # Development guides
├── deployment/              # Deployment documentation
├── troubleshooting/         # Common issues and solutions
├── verification/            # Data verification tools
├── DATA_QUALITY_PROCESS.md  # Data management procedures
├── SERVICE_AREA_ASSIGNMENT_WORKFLOW.md # Coverage area workflow
└── GIS_DEPLOYMENT_GUIDE.md  # GIS functionality guide
```

### **Archives & Historical Data**
```
archive/                     # Historical and reference materials
├── temporary_scripts/       # One-time migration scripts
├── cloud_migrations/        # Old migration scripts
├── cli_review_tools/        # Bulk update tools
├── old_json_data/           # Historical JSON data (311 files)
└── old_csv_data/            # Historical CSV data
```

### **Templates & Static Files**
```
templates/                   # HTML templates
├── directory/               # Application templates
│   ├── resource_list.html   # Main resource listing
│   ├── resource_detail.html # Individual resource view
│   └── resource_form.html   # Resource editing form
└── base.html               # Base template

static/                      # Static assets
├── theme.css               # Main stylesheet
├── theme.js                # JavaScript functionality
└── images/                 # Images and icons
```

## ✨ Key Features

### **Resource Management**
- **Comprehensive Profiles**: Contact details, services, hours, eligibility
- **Workflow System**: Draft → Review → Published with role-based access
- **Audit Trail**: Complete version history and change tracking
- **Archive Management**: Soft archiving with reasoning

### **Search & Discovery**
- **Advanced Search**: Full-text search with geographic filtering
- **Location-Based Search**: Find resources by address or area
- **Service Type Filtering**: Filter by categories and service types
- **Coverage Area Mapping**: Geographic service area visualization

### **Data Management**
- **CSV Import/Export**: Bulk operations with validation
- **Data Quality Tools**: Automated verification and cleanup
- **Coverage Area Management**: Geographic boundary management
- **User Management**: Role-based access control

### **Technical Features**
- **Responsive Design**: Mobile-friendly interface
- **HTMX Integration**: Dynamic interactions without JavaScript
- **PostgreSQL Full-Text Search**: Fast, accurate search
- **Docker Support**: Easy development and deployment

## 🔄 Development Workflow

### **Local Development**
```bash
# Start development environment
./scripts/development/start_dev.sh

# This automatically:
# - Starts PostgreSQL database in Docker
# - Runs Django migrations
# - Starts development server at http://localhost:8000
```

### **Testing**
```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### **Staging Deployment**
```bash
# Deploy to staging (requires permission)
./scripts/deployment/deploy_to_staging.sh

# Verify at: https://isaiah58-resource-directory.onrender.com
```

### **Code Quality**
```bash
# Format code
black .
isort .

# Check code quality
flake8 .
pylint directory/
```

## 📚 Documentation

### **Essential Documentation**
- **[RELEASE_NOTES.md](RELEASE_NOTES.md)** - Complete feature documentation and changelog
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development setup and coding standards
- **[TODO.md](TODO.md)** - Current development tasks and roadmap

### **Process Documentation**
- **[docs/DATA_QUALITY_PROCESS.md](docs/DATA_QUALITY_PROCESS.md)** - Data management procedures
- **[docs/SERVICE_AREA_ASSIGNMENT_WORKFLOW.md](docs/SERVICE_AREA_ASSIGNMENT_WORKFLOW.md)** - Coverage area workflow
- **[docs/GIS_DEPLOYMENT_GUIDE.md](docs/GIS_DEPLOYMENT_GUIDE.md)** - GIS functionality guide

### **Development Guides**
- **[docs/development/](docs/development/)** - Development setup and procedures
- **[docs/deployment/](docs/deployment/)** - Deployment guides
- **[docs/troubleshooting/](docs/troubleshooting/)** - Common issues and solutions

### **API Documentation**
- **API Endpoints**: See `directory/views/api_views.py`
- **Data Models**: See `directory/models/`
- **Form Definitions**: See `directory/forms/`

## 🏗️ Tech Stack

### **Backend**
- **Framework**: Django 5.0.2
- **Language**: Python 3.x
- **Database**: PostgreSQL 16 with spatial extensions
- **Search**: PostgreSQL full-text search
- **Caching**: Django cache framework

### **Frontend**
- **Templates**: Django templates with Bootstrap 5
- **Interactions**: HTMX for dynamic functionality
- **Styling**: Bootstrap CSS framework
- **JavaScript**: Vanilla JS for enhanced interactions

### **Infrastructure**
- **Local Development**: Docker Compose
- **Staging**: Render (PostgreSQL + Web Service)
- **Version Control**: Git with automated deployment
- **Testing**: Django test framework with 53% coverage

## 📊 Project Metrics

- **Lines of Code**: 32,669 (excluding venv and archive)
- **Python Files**: 162 (excluding venv and archive)
- **Test Coverage**: 53% (126 tests, all passing)
- **Documentation Coverage**: 95% (133/140 files with docstrings)
- **Resources**: 254 community resources
- **Coverage Areas**: 7,829 geographic areas
- **Categories**: 21 service categories
- **Service Types**: 25 service types

## 🤝 Contributing

### **Development Standards**
1. **Code Style**: PEP 8 compliance with Black formatting
2. **Documentation**: Google-style docstrings for all functions
3. **Testing**: Add tests for new functionality
4. **Type Hints**: Use type annotations for all functions
5. **Git Workflow**: Feature branches with descriptive commits

### **Getting Started**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Update documentation as needed
6. Submit a pull request

### **Code Quality Tools**
```bash
# Install development tools
pip install black isort flake8 pylint coverage

# Run quality checks
black --check .
isort --check-only .
flake8 .
pylint directory/
```

## 📄 License

This project is open source. See LICENSE file for details.

---

## 🆘 Need Help?

### **Quick References**
- **API Documentation**: See `directory/views/api_views.py`
- **Data Models**: See `directory/models/`
- **Configuration**: See `resource_directory/settings.py`
- **Deployment**: See `scripts/deployment/`
- **Troubleshooting**: See `docs/troubleshooting/`

### **Common Tasks**
- **Add a new resource**: Use the admin interface or API
- **Modify search**: See `directory/forms/filter_forms.py`
- **Update coverage areas**: See `scripts/data/`
- **Deploy changes**: See `scripts/deployment/`
- **Run tests**: See `scripts/development/run_tests.sh`

### **Support**
- **Issues**: Create a GitHub issue
- **Documentation**: Check `docs/` directory
- **Release Notes**: See `RELEASE_NOTES.md` for latest changes

---

**Last Updated**: 2025-01-15  
**Version**: 1.0.0  
**Status**: Production Ready - Staging Deployed
