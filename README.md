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

# Initialize database
python manage.py migrate
python manage.py setup_wal
python manage.py createsuperuser

# Run server
python manage.py runserver
```

**Docker**: `docker-compose up --build`

## ✨ Key Features

- **📋 Resource Management**: Comprehensive profiles with contact details, services, hours, and eligibility
- **🔄 Workflow System**: Three-stage process (Draft → Review → Published) with role-based access
- **🔍 Advanced Search**: Full-text search with geographic and service type filtering
- **📊 Data Import/Export**: CSV bulk operations with validation and error reporting
- **🛡️ Audit Trail**: Immutable version history and complete change tracking
- **🗃️ Archive Management**: Soft archiving with reasoning and dedicated interfaces

## 🏗️ Tech Stack

- **Backend**: Django 5.0.2 + Python 3.x
- **Database**: SQLite with WAL mode
- **Frontend**: HTMX + Bootstrap
- **Search**: SQLite FTS5
- **Deployment**: Docker support

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
