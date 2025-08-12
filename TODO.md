# Homeless Resource Directory - MVP Roadmap

## 🎯 MVP Goal
Build a small, internal-first web app to curate and maintain a high-quality directory of resources for people experiencing homelessness.

---

## 📊 Progress Overview
- **Completed**: 4/15 (27%)
- **In Progress**: 0/15 (0%)
- **Not Started**: 11/15 (73%)

---

## 🚀 Phase 1: Foundation & Core Models ✅ COMPLETED

### ✅ 1.1 Project Setup
- [x] Django 5.0.2 project structure
- [x] Virtual environment with dependencies
- [x] SQLite database configuration
- [x] Docker setup with volume mounting
- [x] Basic project documentation

### ✅ 1.2 Core Data Models
- [x] Resource model with all required fields
- [x] TaxonomyCategory model
- [x] ResourceVersion model (immutable snapshots)
- [x] AuditLog model (append-only)
- [x] Database indexes and constraints

### ✅ 1.3 Validation & Business Logic
- [x] Draft validation (name + contact method)
- [x] Review validation (city, state, description, source)
- [x] Published validation (verification within 180 days)
- [x] Data normalization (phone, state, website)

### ✅ 1.4 Admin Interface
- [x] Resource admin with proper filtering
- [x] Category admin
- [x] Version history display
- [x] Audit log interface
- [x] Status workflow management

---

## 🔄 Phase 2: Core Functionality (In Progress)

### 🔄 2.1 User Authentication & Roles
- [ ] **Priority: HIGH** - Implement Django groups for Editor/Reviewer/Admin
- [ ] **Priority: HIGH** - Create permission matrix
- [ ] **Priority: MEDIUM** - Add role-based views and forms
- [ ] **Priority: LOW** - User profile management

**Acceptance Criteria:**
- Users can be assigned to Editor, Reviewer, or Admin groups
- Permissions restrict actions based on role
- Admin can manage users and roles

### 🔄 2.2 Resource Workflow Views
- [ ] **Priority: HIGH** - Create resource list view with HTMX
- [ ] **Priority: HIGH** - Create resource detail/edit form
- [ ] **Priority: HIGH** - Implement status transition buttons
- [ ] **Priority: MEDIUM** - Add inline validation feedback
- [ ] **Priority: LOW** - Add confirmation dialogs for status changes

**Acceptance Criteria:**
- Users can view filtered list of resources
- Users can create/edit resources with proper validation
- Status transitions work correctly with validation
- HTMX provides smooth user experience

### 🔄 2.3 Search & Filtering
- [ ] **Priority: HIGH** - Implement FTS5 full-text search
- [ ] **Priority: HIGH** - Add filters (category, city, state, status)
- [ ] **Priority: MEDIUM** - Add sorting options
- [ ] **Priority: LOW** - Add advanced search operators

**Acceptance Criteria:**
- Search returns relevant results for common queries
- Filters work correctly and update results
- Search is fast and responsive

---

## 📋 Phase 3: Data Management

### 📋 3.1 CSV Import/Export
- [ ] **Priority: HIGH** - Create CSV import view with validation
- [ ] **Priority: HIGH** - Create CSV export functionality
- [ ] **Priority: MEDIUM** - Add column mapping for imports
- [ ] **Priority: MEDIUM** - Generate error reports for failed imports
- [ ] **Priority: LOW** - Add import templates

**Acceptance Criteria:**
- Users can upload CSV files and see validation results
- Valid rows create Draft resources
- Users can export filtered results to CSV
- Error reports show which rows failed and why

### 📋 3.2 Version History & Audit
- [ ] **Priority: MEDIUM** - Create version comparison view
- [ ] **Priority: MEDIUM** - Add diff highlighting for changes
- [ ] **Priority: LOW** - Add audit log filtering and search
- [ ] **Priority: LOW** - Add audit log export

**Acceptance Criteria:**
- Users can view version history for any resource
- Changes are clearly highlighted in diffs
- Audit logs show complete action history

---

## 🎨 Phase 4: User Interface

### 🎨 4.1 Dashboard
- [ ] **Priority: HIGH** - Create dashboard with resource counts by status
- [ ] **Priority: HIGH** - Show resources needing verification (>180 days)
- [ ] **Priority: MEDIUM** - Add recent activity feed
- [ ] **Priority: LOW** - Add charts and statistics

**Acceptance Criteria:**
- Dashboard shows key metrics at a glance
- Users can quickly identify resources needing attention
- Interface is clean and intuitive

### 🎨 4.2 Resource Forms
- [ ] **Priority: HIGH** - Create responsive resource form
- [ ] **Priority: HIGH** - Add section-based layout (Basics, Contact, Location, etc.)
- [ ] **Priority: MEDIUM** - Add field-level validation feedback
- [ ] **Priority: LOW** - Add auto-save functionality

**Acceptance Criteria:**
- Forms are easy to use and responsive
- Validation errors are clear and helpful
- Form sections organize information logically

---

## 🔧 Phase 5: API & Integration

### 🔧 5.1 REST API (Optional)
- [ ] **Priority: LOW** - Implement resource list API
- [ ] **Priority: LOW** - Implement resource CRUD API
- [ ] **Priority: LOW** - Add API authentication
- [ ] **Priority: LOW** - Add API documentation

**Acceptance Criteria:**
- API endpoints work as specified in spec
- API is properly authenticated
- API responses are well-formatted

---

## 🚀 Phase 6: Performance & Polish

### 🚀 6.1 Performance Optimization
- [ ] **Priority: MEDIUM** - Optimize database queries
- [ ] **Priority: MEDIUM** - Add caching where appropriate
- [ ] **Priority: LOW** - Add database connection pooling
- [ ] **Priority: LOW** - Optimize static file serving

### 🚀 6.2 Security & Testing
- [ ] **Priority: HIGH** - Add comprehensive test coverage
- [ ] **Priority: HIGH** - Security audit and fixes
- [ ] **Priority: MEDIUM** - Add rate limiting
- [ ] **Priority: LOW** - Add automated security scanning

---

## 📝 Phase 7: Documentation & Deployment

### 📝 7.1 Documentation
- [ ] **Priority: MEDIUM** - User documentation
- [ ] **Priority: MEDIUM** - API documentation
- [ ] **Priority: LOW** - Developer documentation
- [ ] **Priority: LOW** - Deployment guide

### 📝 7.2 Deployment
- [ ] **Priority: HIGH** - Production Docker setup
- [ ] **Priority: HIGH** - Environment configuration
- [ ] **Priority: MEDIUM** - Backup strategy
- [ ] **Priority: LOW** - Monitoring and logging

---

## 🎯 MVP Acceptance Criteria Checklist

### Core Functionality
- [ ] Creating a Draft without `name` fails with clear error
- [ ] Submitting to **needs_review** enforces city/state, description ≥ 20 chars, source present
- [ ] Publishing requires `last_verified_at` ≤ 180 days old and `last_verified_by_id`
- [ ] Each create/update writes a `resource_version` and an `audit_log` entry
- [ ] Attempting to UPDATE/DELETE a `resource_version` or `audit_log` row fails via triggers
- [ ] FTS search returns expected results for common queries
- [ ] CSV import creates Drafts for valid rows and produces error report for invalid rows
- [ ] App runs in Docker; DB is created/used at `/data/db.sqlite3` on mounted volume

### User Experience
- [ ] Users can easily navigate between resources
- [ ] Status transitions are clear and validated
- [ ] Search and filtering work intuitively
- [ ] Forms provide helpful validation feedback
- [ ] Dashboard shows key information at a glance

---

## 📅 Timeline Estimates

- **Phase 2**: 2-3 weeks (Core functionality)
- **Phase 3**: 1-2 weeks (Data management)
- **Phase 4**: 1-2 weeks (UI polish)
- **Phase 5**: 1 week (API - optional)
- **Phase 6**: 1 week (Performance & testing)
- **Phase 7**: 1 week (Documentation & deployment)

**Total MVP Timeline**: 7-10 weeks

---

## 🔄 How to Update This TODO

1. **Mark tasks as complete**: Change `[ ]` to `[x]`
2. **Update priorities**: Adjust Priority levels as needed
3. **Add new tasks**: Insert new items in appropriate sections
4. **Update progress**: Recalculate completion percentages
5. **Add notes**: Use comments for additional context

---

## 📞 Next Actions

**Immediate Next Steps:**
1. Set up user authentication and roles
2. Create basic resource list and form views
3. Implement FTS5 search functionality
4. Add CSV import/export capabilities

**Questions to Resolve:**
- Should we implement the API in MVP or post-MVP?
- What level of test coverage is required for MVP?
- Are there any specific UI/UX requirements beyond the spec?
