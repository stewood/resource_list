# Staging Deployment Guide

## Overview
This guide explains how to deploy the Homeless Resource Directory application from your local development environment to the staging server on Render.

## Current Setup

### Render Infrastructure
- **Web Service**: `isaiah58-resource-directory` 
  - URL: https://isaiah58-resource-directory.onrender.com
  - Branch: `feature/spatial-service-areas`
  - Runtime: Docker
  - Plan: Free

- **Database**: `isaiah58-resource-directory-db`
  - Type: PostgreSQL 17
  - Database: `isaiah58_resources`
  - User: `isaiah58_user`

### Local Development Environment
- **Database**: PostgreSQL 16 (Docker container)
- **Django App**: Running locally
- **Settings**: `resource_directory.development_settings`

## Deployment Workflow

### 1. Prepare Your Local Environment

```bash
# Start your development environment
./scripts/start_dev.sh

# Run tests to ensure everything works
python manage.py test --settings=resource_directory.test_settings_postgresql

# Check for any uncommitted changes
git status
```

### 2. Deploy to Staging

#### Option A: Use the Deployment Script (Recommended)
```bash
# Run the automated deployment script
./scripts/deploy_to_staging.sh
```

This script will:
- ✅ Check for uncommitted changes
- ✅ Run all tests
- ✅ Validate staging configuration
- ✅ Test database connection
- ✅ Run migrations
- ✅ Collect static files
- ✅ Push to git (triggers Render deployment)

#### Option B: Manual Deployment
```bash
# 1. Test staging configuration locally
python manage.py check --settings=resource_directory.staging_settings

# 2. Test database connection
python manage.py check --database default --settings=resource_directory.staging_settings

# 3. Run migrations
python manage.py migrate --settings=resource_directory.staging_settings

# 4. Collect static files
python manage.py collectstatic --noinput --settings=resource_directory.staging_settings

# 5. Commit and push changes
git add .
git commit -m "Deploy to staging"
git push origin feature/spatial-service-areas
```

### 3. Monitor Deployment

1. **Check Render Dashboard**: https://dashboard.render.com/web/srv-d2ls9vn5r7bs73e2haeg
2. **Monitor Logs**: View build and runtime logs in the Render dashboard
3. **Test Application**: Visit https://isaiah58-resource-directory.onrender.com

## Environment Configuration

### Staging Settings
The staging environment uses `resource_directory.staging_settings.py` which:
- ✅ Uses PostgreSQL database on Render
- ✅ Disables debug mode
- ✅ Configures proper security headers
- ✅ Sets up logging for staging
- ✅ Disables GIS features (no PostGIS dependency)
- ✅ Uses environment variables for configuration

### Environment Variables (Set in Render)
```bash
DJANGO_SETTINGS_MODULE=resource_directory.staging_settings
SECRET_KEY=django-insecure-staging-key-change-me-in-production
DEBUG=0
DB_NAME=isaiah58_resources
DB_USER=isaiah58_user
DB_PASSWORD=CMXAq8v3zpy6Vwm1CIV26EKHagUDt0Nr
DB_HOST=dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com
DB_PORT=5432
GIS_ENABLED=0
```

## Data Management

### Current Data Status
- **Development**: 254 resources, 21 categories, 25 service types, 7,829 coverage areas
- **Staging**: Uses the same PostgreSQL database as development

### Data Synchronization
Since you're not concerned about preserving staging data, you can:

1. **Reset staging data** (if needed):
   ```bash
   python manage.py flush --settings=resource_directory.staging_settings
   ```

2. **Import development data to staging**:
   ```bash
   python cloud/import_json_data.py --settings=resource_directory.staging_settings
   ```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
- **Symptom**: "connection refused" or "authentication failed"
- **Solution**: Check environment variables in Render dashboard
- **Check**: Verify DB_HOST, DB_USER, DB_PASSWORD are correct

#### 2. Static Files Not Loading
- **Symptom**: CSS/JS files return 404
- **Solution**: Ensure `collectstatic` runs during deployment
- **Check**: Verify STATIC_ROOT and STATIC_URL in settings

#### 3. Migration Errors
- **Symptom**: "table already exists" or "column does not exist"
- **Solution**: Check migration history and apply missing migrations
- **Command**: `python manage.py showmigrations --settings=resource_directory.staging_settings`

#### 4. Build Failures
- **Symptom**: Docker build fails in Render
- **Solution**: Check Dockerfile and requirements.txt
- **Check**: Ensure all dependencies are in requirements.txt

### Debugging Commands

```bash
# Check staging configuration
python manage.py check --settings=resource_directory.staging_settings

# Test database connection
python manage.py dbshell --settings=resource_directory.staging_settings

# View migration status
python manage.py showmigrations --settings=resource_directory.staging_settings

# Check environment variables
python manage.py shell --settings=resource_directory.staging_settings
>>> import os
>>> print(os.environ.get('DB_HOST'))
```

## Next Steps

### Phase 4: Production Deployment
Once staging is working well:

1. **Create production environment**
   - Set up production PostgreSQL database
   - Configure production settings
   - Set up proper SSL certificates

2. **Implement CI/CD pipeline**
   - Automated testing on pull requests
   - Automated deployment to staging
   - Manual deployment to production

3. **Add monitoring and logging**
   - Application performance monitoring
   - Error tracking and alerting
   - Database performance monitoring

### Phase 5: Data Management
1. **Set up automated backups**
2. **Implement data migration scripts**
3. **Create data validation procedures**

## Files Created/Modified

### New Files
- `resource_directory/staging_settings.py` - Staging configuration
- `scripts/deploy_to_staging.sh` - Automated deployment script
- `staging.env.example` - Environment variables template
- `STAGING_DEPLOYMENT_GUIDE.md` - This guide

### Updated Files
- Render service environment variables (via API)
- Deployment configuration

## Support

- **Render Dashboard**: https://dashboard.render.com/web/srv-d2ls9vn5r7bs73e2haeg
- **Application URL**: https://isaiah58-resource-directory.onrender.com
- **Git Repository**: https://github.com/stewood/resource_list

---

**Last Updated**: 2025-01-15
**Status**: ✅ Staging environment configured and ready for deployment
