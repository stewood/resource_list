# Development Environment Quick Reference

## 🚀 **Starting Development Environment**

### **Option 1: Using the Start Script (Recommended)**
```bash
cd /home/stewood/rl
./scripts/start_dev.sh
```

### **Option 2: Manual Process**
```bash
# 1. Start PostgreSQL container
cd /home/stewood/rl
docker compose -f docker-compose.dev.yml up -d

# 2. Start Django server
source venv/bin/activate
python manage.py runserver --settings=resource_directory.development_settings
```

## 🛑 **Stopping Development Environment**

### **Option 1: Using the Stop Script (Recommended)**
```bash
cd /home/stewood/rl
./scripts/stop_dev.sh
```

### **Option 2: Manual Process**
```bash
# 1. Stop Django server (Ctrl+C in terminal)
# 2. Stop PostgreSQL container
cd /home/stewood/rl
docker compose -f docker-compose.dev.yml down
```

## 🌐 **Accessing the Application**

- **Main Application**: http://localhost:8000
- **Admin Interface**: http://localhost:8000/admin
- **Debug Toolbar**: http://localhost:8000/__debug__/

## 🔧 **Admin Credentials**

- **Username**: admin
- **Password**: admin

## 📊 **Useful Commands**

### **Database Operations**
```bash
# Run migrations
python manage.py migrate --settings=resource_directory.development_settings

# Create superuser
python manage.py createsuperuser --settings=resource_directory.development_settings

# Reset database (clears all data)
./scripts/reset_dev_environment.sh
```

### **Testing**
```bash
# Run tests
python manage.py test --settings=resource_directory.development_settings

# Run specific test
python manage.py test directory.tests.test_models --settings=resource_directory.development_settings
```

### **Docker Operations**
```bash
# Check container status
docker compose -f docker-compose.dev.yml ps

# View container logs
docker compose -f docker-compose.dev.yml logs

# Restart container
docker compose -f docker-compose.dev.yml restart
```

## 🚨 **Troubleshooting**

### **Port Already in Use**
If you get "port already in use" errors:
```bash
# Kill all Django servers
pkill -f "manage.py runserver"

# Or find and kill specific process
lsof -ti:8000 | xargs kill -9
```

### **Database Connection Issues**
```bash
# Check if PostgreSQL is running
docker compose -f docker-compose.dev.yml ps

# Restart PostgreSQL
docker compose -f docker-compose.dev.yml restart
```

### **Reset Everything**
```bash
# Complete reset (clears all data)
./scripts/reset_dev_environment.sh
```

## 📝 **Notes**

- The development environment uses PostgreSQL in Docker
- Django runs locally (not in Docker) for fast development
- Debug toolbar is enabled for development debugging
- All data is persisted in Docker volumes
- The environment matches production (PostgreSQL) but runs locally
