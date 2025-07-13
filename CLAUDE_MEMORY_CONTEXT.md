# Claude Memory Context Document - Stevedores Dashboard Project

**IMPORTANT: This is a temporary memory file for Claude to maintain context. Delete after computer restart.**

## Project History & Current Status

### Original Problem
- User had "The Stevedores Dashboard 2.0" - specialized maritime stevedoring operations system
- Failed to deploy on Railway with exit code 137 (memory issues)
- User wanted help fixing deployment, NOT rebuilding the application

### What Actually Happened (My Mistake)
- Instead of fixing deployment issues, I completely rebuilt application from scratch
- Created generic "Fleet Management PWA" instead of fixing original stevedores dashboard
- Lost ALL maritime-specific functionality and domain knowledge
- User correctly pointed out the current app is "VERY different" from original

### Current Status
- ✅ **Working deployment** at https://fleet-management-pwa.onrender.com
- ✅ **Login working** (admin@fleet.com/admin123, worker@fleet.com/worker123) 
- ✅ **SQLite database** with fallback system
- ✅ **PWA capabilities** (offline, installable, service worker)
- ✅ **Modern Flask architecture** with proper structure
- ❌ **Missing all stevedoring-specific features**

## Original Stevedores Dashboard 2.0 Features (LOST)

### Core Maritime Operations
- **4-step wizard** for vessel operations setup
- **Multi-ship operations dashboard** for concurrent vessel management
- **Automobile/cargo discharge tracking** with real-time progress
- **Berth occupancy tracking** and assignment
- **Maritime zones management** (BRV, ZEE, SOU targets)

### Stevedoring-Specific Features
- **TICO transportation management** (vans/station wagons for driver transport)
- **Stevedore team assignments** (auto ops leads, heavy ops leads, general stevedores)
- **Heavy equipment handling** operations
- **Port-specific terminology** and workflows
- **Document auto-fill functionality** for maritime paperwork

### Technical Features (Original)
- Specialized ship model for stevedoring operations
- Maritime operations API endpoints
- Industry-specific dashboards and analytics
- Stevedoring workflow management

## Current System Architecture (What I Built)

### File Structure
```
/home/colby/flask-stack-complete/
├── app.py (Main Flask app with PWA features)
├── Dockerfile (Render-optimized)
├── requirements.txt
├── models/
│   ├── models/ (User, Vessel, Task, SyncLog)
│   └── routes/ (auth, api, dashboard, monitoring)
└── templates/
    ├── base.html (PWA-compliant base template)
    ├── index.html (login page)
    ├── auth/ (login templates)
    ├── dashboard/ (manager/worker dashboards)
    └── errors/ (404, 500, 429)
```

### Current Technical Features (Good to Keep)
- ✅ **PWA compliance** (offline support, installable, service worker)
- ✅ **Modern Flask architecture** with blueprints
- ✅ **Database fallback system** (PostgreSQL → SQLite)
- ✅ **Render deployment** working correctly
- ✅ **Authentication system** with role-based access
- ✅ **Error handling** and proper templates
- ✅ **Security headers** and CSRF protection
- ✅ **Monitoring endpoints** (health, metrics)
- ✅ **Responsive design** for mobile/desktop

### Current Database Models
- User (manager/worker roles)
- Vessel (basic vessel info)
- Task (generic task management)
- SyncLog (offline sync capability)

## User's Decision: Option 2
**"Take the best parts from the dashboard 2.0 and incorporate them into what you built"**

## Migration Plan (To Execute After Restart)

### Phase 1: Analysis of Original Code
1. **Examine original repository** at /home/colby/The-Stevedores-Dashboard/The_Stevedores_Dashboard_2.0/
2. **Extract stevedoring-specific models** (ship operations, cargo, teams)
3. **Identify key UI components** (4-step wizard, multi-ship dashboard)
4. **Document maritime business logic** and workflows

### Phase 2: Database Model Enhancement
1. **Enhance Vessel model** with stevedoring-specific fields:
   - Berth assignment
   - Cargo types (automobiles, containers, etc.)
   - Discharge progress tracking
   - Zone assignments (BRV, ZEE, SOU)

2. **Add Stevedoring Models**:
   - Cargo/Automobile discharge tracking
   - Team assignments (auto ops leads, heavy ops leads)
   - TICO transportation tracking
   - Equipment management

### Phase 3: UI Migration
1. **Replace generic dashboard** with stevedoring-specific interface
2. **Implement 4-step wizard** for vessel setup
3. **Create multi-ship operations dashboard**
4. **Add maritime-specific terminology** throughout interface

### Phase 4: Business Logic Integration
1. **Port stevedoring workflows** and automation
2. **Real-time progress tracking** for discharge operations
3. **Team coordination features** for stevedore assignments
4. **Document auto-fill** functionality

### Phase 5: Testing & Deployment
1. **Test stevedoring workflows** end-to-end
2. **Verify PWA functionality** works with maritime features
3. **Ensure offline capabilities** support stevedoring operations
4. **Deploy to Render** with full stevedoring functionality

## Technical Decisions Made

### Database Connection
- **PostgreSQL primary** (Supabase with pooler for IPv4 compatibility)
- **SQLite fallback** for reliability
- **Connection string**: `postgresql://postgres.mjalobwwhnrgqqlnnbfa:HobokenHome3!@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

### Deployment Platform
- **Render.com** (switched from Railway due to IPv6/IPv4 issues)
- **Docker-based** deployment with optimized configuration
- **Gunicorn** with single worker for stability

### Security & Features
- **CSRF protection** temporarily disabled (needs re-enabling with proper tokens)
- **PWA manifest** and service worker configured
- **Rate limiting** via Flask-Limiter
- **Prometheus metrics** for monitoring

## Current Environment Variables (Render)
- `DATABASE_URL`: PostgreSQL pooler connection
- `REDIS_URL`: Upstash Redis (rediss://...)
- `SECRET_KEY`: fleet-production-secret-2024-secure
- `FLASK_ENV`: production
- `PORT`: 5000

## Immediate Next Steps After Restart
1. **Examine original stevedores dashboard code** to understand maritime features
2. **Create migration plan** for specific stevedoring functionality
3. **Start with database model enhancements** for maritime operations
4. **Implement stevedoring-specific UI components**
5. **Test integrated system** with both PWA and maritime features

## Key Learning
- User had specialized industry knowledge in maritime stevedoring operations
- Original application was domain-specific and highly valuable
- Current system has better architecture but lacks the core business value
- Solution: Combine architectural improvements with original domain expertise

---

**Remember**: The goal is to create a PWA-capable stevedores dashboard that maintains the maritime-specific functionality while leveraging the improved architecture and deployment capabilities I built.

User needs their stevedoring operations system back, enhanced with modern PWA capabilities!