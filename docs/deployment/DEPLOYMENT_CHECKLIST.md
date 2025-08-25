# Deployment Checklist

## ✅ Pre-Deployment Checklist

### Security
- [x] Generated secure SECRET_KEY
- [x] Created production settings with security headers
- [x] Disabled DEBUG mode
- [x] Configured HTTPS/SSL settings
- [x] Set secure cookies
- [x] Added HSTS headers

### Database
- [x] Migrated data to PostgreSQL
- [x] Updated requirements.txt with PostgreSQL dependencies
- [x] Created production database configuration
- [x] Disabled GIS for cloud deployment

### Static Files
- [x] Configured WhiteNoise for static file serving
- [x] Created build script for static file collection
- [x] Tested static file collection

### Dependencies
- [x] Updated requirements.txt for production
- [x] Added dj-database-url for database configuration
- [x] Removed heavy GIS dependencies from main requirements

## 🚀 Render Deployment Steps

### 1. Environment Variables
Set these in your Render dashboard:

```bash
DJANGO_SECRET_KEY=$0sp9q!@q-wsrryc8a2m9^!0-dwa3*m+nb0nt154$sone!k^#c
DATABASE_URL=postgresql://isaiah58_user:CMXAq8v3zpy6Vwm1CIV26EKHagUDt0Nr@dpg-d2lr5pre5dus7394h7f0-a.oregon-postgres.render.com:5432/isaiah58_resources
ALLOWED_HOSTS=your-app-name.onrender.com
DEBUG=0
```

### 2. Build Command
```bash
./build.sh
```

### 3. Start Command
```bash
gunicorn resource_directory.wsgi:application
```

### 4. Settings Module
```bash
resource_directory.production_settings
```

## 🔧 Post-Deployment Verification

### 1. Check Application Health
- [ ] Application loads without errors
- [ ] Admin interface is accessible
- [ ] Static files are served correctly
- [ ] Database connections work

### 2. Security Verification
- [ ] HTTPS redirects work
- [ ] Security headers are present
- [ ] No DEBUG information exposed
- [ ] Secure cookies are set

### 3. Functionality Testing
- [ ] User login works
- [ ] Resource listing works
- [ ] Search functionality works
- [ ] Admin operations work

## 📝 Notes

- **Development Environment**: Keep using SQLite for local development
- **GIS Features**: Disabled for cloud deployment (can be re-enabled later if needed)
- **Database**: PostgreSQL on Render with all data migrated
- **Static Files**: Served by WhiteNoise (no CDN needed for small app)

## 🆘 Troubleshooting

### Common Issues
1. **Static files not loading**: Check WhiteNoise configuration
2. **Database connection errors**: Verify DATABASE_URL format
3. **500 errors**: Check logs for specific error messages
4. **HTTPS issues**: Verify SECURE_SSL_REDIRECT settings

### Logs
- Check Render logs for detailed error information
- Django logs will show application-level errors
- Database logs available in Render dashboard
