# Homeless Resource Directory

[![Test Coverage](https://img.shields.io/badge/test%20coverage-53%25-brightgreen)](https://github.com/stewood/resource_list)

A Django-based web application for managing and curating resources for people experiencing homelessness. Built for case managers, outreach workers, and community partners to connect individuals with appropriate services.

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/stewood/resource_list.git
cd resource_list
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start development environment (PostgreSQL + Django)
./scripts/development/start_dev.sh

# Create superuser (optional)
python manage.py createsuperuser
```

**Alternative Docker**: `docker-compose up --build`

## 🔄 Development Workflow

This project uses a **local development → staging deployment** workflow:

### **Local Development Environment**
```bash
# Start the development environment
./scripts/development/start_dev.sh

# This will:
# - Start PostgreSQL database in Docker
# - Run Django migrations
# - Start the development server at http://localhost:8000
```

### **Staging Deployment**
```bash
# Deploy changes to staging (Render)
./scripts/deployment/deploy_to_staging.sh

# This will:
# - Run all tests
# - Validate configuration
# - Collect static files
# - Push to git and trigger Render deployment
```

### **Environment Structure**
- **Local**: Development environment with PostgreSQL (Docker)
- **Staging**: Render-hosted environment for testing
- **Production**: Future deployment target

### **Workflow Steps**
1. **Develop locally** using `./scripts/development/start_dev.sh`
2. **Test changes thoroughly** in your local environment
3. **Get user approval** before any staging deployment
4. **Deploy to staging** using `./scripts/deployment/deploy_to_staging.sh` (with permission)
5. **Verify staging** at https://isaiah58-resource-directory.onrender.com
6. **Deploy to production** (when ready, with permission)

### **Important Workflow Rules**
- **Always test in development first** - Never deploy to staging without local testing
- **Get explicit permission** - Ask for approval before staging deployments
- **Verify functionality** - Test all features, light/dark modes, and responsive design
- **Document changes** - Update documentation as needed

## ✨ Key Features

- **📋 Resource Management**: Comprehensive profiles with contact details, services, hours, and eligibility
- **🔄 Workflow System**: Three-stage process (Draft → Review → Published) with role-based access
- **🔍 Advanced Search**: Full-text search with geographic and service type filtering
- **📊 Data Import/Export**: CSV bulk operations with validation and error reporting
- **🛡️ Audit Trail**: Immutable version history and complete change tracking
- **🗃️ Archive Management**: Soft archiving with reasoning and dedicated interfaces

## 🏗️ Tech Stack

- **Backend**: Django 5.0.2 + Python 3.x
- **Database**: PostgreSQL (local Docker, staging Render)
- **Frontend**: HTMX + Bootstrap
- **Search**: PostgreSQL full-text search
- **Deployment**: Docker (local) + Render (staging)
- **Version Control**: Git with automated deployment

## 📊 Quality Metrics

- **Test Coverage**: 53% (126 tests, all passing)
- **Core Coverage**: Models (96%), CRUD views (100%), Settings (100%)
- **Performance**: ~50 second test suite execution

## 📚 Documentation

- **[Release Notes](RELEASE_NOTES.md)** - Complete feature documentation
- **[Contributing Guidelines](CONTRIBUTING.md)** - Development setup and standards
- **[Data Quality Process](docs/DATA_QUALITY_PROCESS.md)** - Data management procedures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow coding standards (PEP 8, type hints, docstrings)
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is open source. See LICENSE file for details.

---

**For detailed information**: See [RELEASE_NOTES.md](RELEASE_NOTES.md) for comprehensive documentation.
