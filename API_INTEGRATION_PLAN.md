# Fleet Management PWA - Dashboard 2.0 API Integration Plan

## Executive Summary

This document outlines the comprehensive API integration plan for adding Dashboard 2.0 functionality to the Fleet Management PWA, transforming it from a generic fleet system into a specialized maritime stevedoring operations platform.

## Current System Analysis

### Existing Architecture
- **Flask Application**: Modern blueprint-based architecture with PWA capabilities
- **Database Models**: User, Vessel, Task, SyncLog with PostgreSQL/SQLite fallback
- **Authentication**: Role-based access (manager/worker) with Flask-Login
- **Offline Support**: Service worker with background sync capabilities
- **Caching**: Redis-based caching with fallback to memory

### Current API Endpoints
- `/api/tasks` - Generic task management (CRUD operations)
- `/api/vessels` - Basic vessel information
- `/api/users` - User management (managers only)
- `/api/sync` - Offline synchronization
- `/api/dashboard/stats` - Basic statistics

## 1. NEW MARITIME API ENDPOINTS

### Ship Operations API (`/api/ship-operations/`)

#### A. Vessel Operations Setup
```
POST /api/ship-operations/setup
```
**Purpose**: 4-step wizard for vessel operations setup

**Request Schema**:
```json
{
  "vessel_id": 123,
  "operation_type": "discharge", // discharge, loading, maintenance
  "step": 1, // 1-4 for wizard steps
  "step_data": {
    // Step 1: Basic Info
    "berth_assignment": "A-1",
    "eta": "2024-07-15T08:00:00Z",
    "etd": "2024-07-16T18:00:00Z",
    "cargo_manifest": {...},
    
    // Step 2: Team Assignment
    "auto_ops_lead": 456,
    "heavy_ops_lead": 789,
    "stevedore_teams": [
      {"team_id": 1, "members": [1,2,3,4], "shift": "day"}
    ],
    
    // Step 3: Equipment & Zones
    "equipment_allocation": {
      "cranes": ["crane_01", "crane_02"],
      "forklifts": ["fl_001", "fl_002"],
      "vehicles": ["van_01", "wagon_02"]
    },
    "zone_assignments": {
      "BRV": {"supervisor": 456, "workers": [1,2,3]},
      "ZEE": {"supervisor": 789, "workers": [4,5,6]},
      "SOU": {"supervisor": 321, "workers": [7,8,9]}
    },
    
    // Step 4: Safety & Documentation
    "safety_briefing_completed": true,
    "documentation": {...}
  }
}
```

**Response Schema**:
```json
{
  "operation_id": "OP-2024-001",
  "step": 1,
  "next_step": 2,
  "validation_errors": [],
  "suggested_assignments": {...},
  "estimated_completion": "2024-07-16T16:00:00Z"
}
```

#### B. Multi-Ship Dashboard Data
```
GET /api/ship-operations/dashboard
```
**Purpose**: Real-time data for concurrent vessel operations

**Query Parameters**:
- `active_only=true` - Only show active operations
- `berths=A-1,A-2,B-1` - Filter by berth assignments
- `date_range=2024-07-15,2024-07-17` - Date range filter

**Response Schema**:
```json
{
  "operations": [
    {
      "operation_id": "OP-2024-001",
      "vessel": {
        "id": 123,
        "name": "MV Atlantic Explorer",
        "imo": "IMO1234567",
        "berth": "A-1",
        "eta": "2024-07-15T08:00:00Z",
        "etd": "2024-07-16T18:00:00Z"
      },
      "status": "in_progress",
      "progress": {
        "overall_percentage": 45,
        "cargo_discharged": 120,
        "cargo_total": 267,
        "automobiles_processed": 89,
        "automobiles_total": 200
      },
      "teams": {
        "active_count": 12,
        "zones": {
          "BRV": {"status": "active", "progress": 60},
          "ZEE": {"status": "active", "progress": 30},
          "SOU": {"status": "waiting", "progress": 0}
        }
      },
      "alerts": [
        {
          "type": "equipment_issue",
          "message": "Crane 02 requires maintenance",
          "severity": "medium",
          "timestamp": "2024-07-15T14:30:00Z"
        }
      ]
    }
  ],
  "summary": {
    "total_active_operations": 3,
    "total_vessels": 5,
    "berths_occupied": 3,
    "berths_available": 2,
    "avg_operation_progress": 52
  }
}
```

### Cargo Management API (`/api/cargo/`)

#### A. Automobile/Cargo Discharge Tracking
```
POST /api/cargo/discharge/record
```
**Purpose**: Record individual cargo/automobile processing

**Request Schema**:
```json
{
  "operation_id": "OP-2024-001",
  "cargo_type": "automobile", // automobile, container, bulk
  "cargo_details": {
    "vin": "1HGBH41JXMN109186", // For automobiles
    "make": "Toyota",
    "model": "Camry",
    "year": 2024,
    "color": "blue",
    "damage_report": "none"
  },
  "processing_data": {
    "zone": "BRV",
    "processed_by": 456,
    "start_time": "2024-07-15T09:15:00Z",
    "end_time": "2024-07-15T09:18:00Z",
    "destination_lot": "LOT-A-12"
  },
  "quality_check": {
    "inspector": 789,
    "status": "approved", // approved, rejected, conditional
    "notes": "Minor paint scratch on rear bumper"
  }
}
```

#### B. Cargo Progress Summary
```
GET /api/cargo/progress/{operation_id}
```
**Response Schema**:
```json
{
  "operation_id": "OP-2024-001",
  "cargo_summary": {
    "total_units": 267,
    "processed_units": 120,
    "remaining_units": 147,
    "processing_rate": 15.5, // units per hour
    "estimated_completion": "2024-07-16T14:30:00Z"
  },
  "by_type": {
    "automobiles": {
      "total": 200,
      "processed": 89,
      "rate": 12.1
    },
    "containers": {
      "total": 45,
      "processed": 20,
      "rate": 3.2
    },
    "bulk": {
      "total": 22,
      "processed": 11,
      "rate": 0.2
    }
  },
  "by_zone": {
    "BRV": {"processed": 45, "rate": 6.1},
    "ZEE": {"processed": 32, "rate": 4.8},
    "SOU": {"processed": 43, "rate": 4.6}
  },
  "quality_metrics": {
    "approved_percentage": 96.7,
    "rejected_units": 4,
    "conditional_units": 0
  }
}
```

### Team Assignment API (`/api/teams/`)

#### A. Stevedore Team Management
```
POST /api/teams/assign
```
**Purpose**: Assign stevedore teams to operations and zones

**Request Schema**:
```json
{
  "operation_id": "OP-2024-001",
  "assignments": [
    {
      "team_type": "auto_ops_lead",
      "user_id": 456,
      "zone": "BRV",
      "shift": "day", // day, night, swing
      "start_time": "2024-07-15T07:00:00Z",
      "end_time": "2024-07-15T15:00:00Z"
    },
    {
      "team_type": "general_stevedore",
      "user_ids": [1, 2, 3, 4],
      "zone": "BRV",
      "supervisor": 456,
      "shift": "day"
    }
  ]
}
```

#### B. Team Performance Tracking
```
GET /api/teams/performance/{operation_id}
```
**Response Schema**:
```json
{
  "teams": [
    {
      "team_id": "T-BRV-001",
      "zone": "BRV",
      "supervisor": {
        "id": 456,
        "name": "John Smith",
        "role": "auto_ops_lead"
      },
      "members": [
        {"id": 1, "name": "Worker A", "hours_worked": 6.5},
        {"id": 2, "name": "Worker B", "hours_worked": 6.5}
      ],
      "performance": {
        "units_processed": 45,
        "target_rate": 8.0,
        "actual_rate": 6.9,
        "efficiency": 86.25,
        "downtime_minutes": 45
      },
      "breaks": [
        {"start": "2024-07-15T10:00:00Z", "end": "2024-07-15T10:15:00Z", "type": "coffee"},
        {"start": "2024-07-15T12:00:00Z", "end": "2024-07-15T12:30:00Z", "type": "lunch"}
      ]
    }
  ]
}
```

### Berth Management API (`/api/berths/`)

#### A. Berth Occupancy Tracking
```
GET /api/berths/occupancy
```
**Response Schema**:
```json
{
  "berths": [
    {
      "berth_id": "A-1",
      "status": "occupied", // occupied, available, maintenance
      "vessel": {
        "id": 123,
        "name": "MV Atlantic Explorer",
        "imo": "IMO1234567"
      },
      "operation_id": "OP-2024-001",
      "occupancy_start": "2024-07-15T06:00:00Z",
      "estimated_departure": "2024-07-16T18:00:00Z",
      "utilities": {
        "power": "connected",
        "water": "connected",
        "waste": "connected"
      }
    }
  ],
  "capacity": {
    "total_berths": 5,
    "occupied": 3,
    "available": 1,
    "maintenance": 1
  }
}
```

### Transportation API (`/api/transportation/`)

#### A. TICO Vehicle Management
```
POST /api/transportation/tico/assign
```
**Purpose**: Manage vans/station wagons for driver transport

**Request Schema**:
```json
{
  "operation_id": "OP-2024-001",
  "vehicle_assignments": [
    {
      "vehicle_id": "VAN-001",
      "driver_id": 789,
      "route": "port_to_lot_A",
      "capacity": 8,
      "passengers": [
        {"driver_id": 101, "destination": "LOT-A-12"},
        {"driver_id": 102, "destination": "LOT-A-15"}
      ],
      "scheduled_departure": "2024-07-15T09:00:00Z"
    }
  ]
}
```

### Analytics API (`/api/analytics/`)

#### A. Real-time Operation Analytics
```
GET /api/analytics/realtime/{operation_id}
```
**Response Schema**:
```json
{
  "operation_id": "OP-2024-001",
  "real_time_metrics": {
    "current_processing_rate": 15.2,
    "target_processing_rate": 18.0,
    "efficiency": 84.4,
    "active_workers": 24,
    "equipment_utilization": 87.5
  },
  "predictions": {
    "estimated_completion": "2024-07-16T16:45:00Z",
    "confidence": 85,
    "potential_delays": [
      {
        "factor": "weather",
        "impact_hours": 2.5,
        "probability": 30
      }
    ]
  },
  "trends": {
    "hourly_rates": [
      {"hour": "08:00", "rate": 12.5},
      {"hour": "09:00", "rate": 15.1},
      {"hour": "10:00", "rate": 16.8}
    ]
  }
}
```

## 2. ENHANCED EXISTING ENDPOINTS

### Enhanced Vessel API

#### A. Extended Vessel Model
```
GET /api/vessels/{vessel_id}/maritime-details
```
**New fields added to vessel response**:
```json
{
  // Existing vessel fields...
  "maritime_details": {
    "berth_assignment": "A-1",
    "cargo_capacity": {
      "automobiles": 500,
      "containers_teu": 1200,
      "bulk_tons": 2500
    },
    "current_cargo": {
      "automobiles": 267,
      "containers": 45,
      "bulk_tons": 150
    },
    "operational_status": "discharging", // arriving, berthed, discharging, loading, departing
    "zone_assignments": ["BRV", "ZEE", "SOU"],
    "required_equipment": ["crane", "forklift", "reach_stacker"],
    "documentation_status": {
      "customs_cleared": true,
      "manifest_verified": true,
      "safety_approved": true
    }
  }
}
```

### Enhanced Task API

#### A. Maritime-Specific Task Types
```
POST /api/tasks
```
**New task_type values**:
- `cargo_discharge`
- `cargo_loading`
- `berth_preparation`
- `equipment_setup`
- `safety_inspection`
- `documentation_processing`
- `tico_transport`
- `zone_preparation`

**Extended task schema**:
```json
{
  // Existing task fields...
  "maritime_details": {
    "operation_id": "OP-2024-001",
    "zone": "BRV",
    "cargo_type": "automobile",
    "equipment_required": ["crane_01", "forklift_002"],
    "safety_requirements": ["hard_hat", "safety_vest", "steel_boots"],
    "tico_transport_needed": true,
    "cargo_units": 25,
    "processing_rate_target": 8.0
  }
}
```

### Enhanced User API

#### A. Maritime Roles and Certifications
```
PUT /api/users/{user_id}/maritime-profile
```
**Request Schema**:
```json
{
  "maritime_profile": {
    "primary_role": "auto_ops_lead", // auto_ops_lead, heavy_ops_lead, general_stevedore, equipment_operator
    "certifications": [
      {
        "type": "crane_operator",
        "level": "advanced",
        "expiry_date": "2025-06-15",
        "certification_number": "CO-2024-1234"
      }
    ],
    "zone_authorizations": ["BRV", "ZEE"],
    "equipment_qualifications": ["crane", "forklift", "reach_stacker"],
    "shift_preferences": ["day", "swing"],
    "emergency_contact": {
      "name": "Jane Smith",
      "phone": "+1-555-0123",
      "relationship": "spouse"
    }
  }
}
```

## 3. REAL-TIME UPDATE STRATEGY

### WebSocket Implementation

#### A. WebSocket Endpoints
```
WS /ws/operations/{operation_id}
WS /ws/dashboard/live
WS /ws/berths/status
```

#### B. Message Types
```javascript
// Client subscribes to operation updates
{
  "type": "subscribe",
  "channels": ["cargo_progress", "team_updates", "equipment_alerts"]
}

// Server sends real-time updates
{
  "type": "cargo_progress_update",
  "operation_id": "OP-2024-001",
  "data": {
    "zone": "BRV",
    "units_processed": 47,
    "processing_rate": 6.2,
    "timestamp": "2024-07-15T10:15:00Z"
  }
}

{
  "type": "team_status_update",
  "operation_id": "OP-2024-001",
  "data": {
    "team_id": "T-BRV-001",
    "status": "break_started",
    "break_type": "coffee",
    "duration_minutes": 15,
    "timestamp": "2024-07-15T10:00:00Z"
  }
}

{
  "type": "equipment_alert",
  "data": {
    "equipment_id": "crane_02",
    "alert_type": "maintenance_required",
    "severity": "medium",
    "message": "Hydraulic pressure low",
    "timestamp": "2024-07-15T14:30:00Z"
  }
}
```

### Server-Sent Events (SSE) Fallback

#### A. SSE Endpoints
```
GET /api/events/operations/{operation_id}
GET /api/events/dashboard/live
```

#### B. Event Stream Format
```
event: cargo_progress
data: {"operation_id": "OP-2024-001", "units_processed": 47, "rate": 6.2}

event: team_update
data: {"team_id": "T-BRV-001", "status": "active", "zone": "BRV"}

event: berth_status
data: {"berth_id": "A-1", "status": "occupied", "vessel_id": 123}
```

## 4. OFFLINE-FIRST API DESIGN

### Background Sync Strategy

#### A. Sync Queue Management
```
POST /api/sync/queue
```
**Purpose**: Queue offline changes for background synchronization

**Request Schema**:
```json
{
  "changes": [
    {
      "id": "change_001",
      "table": "cargo_discharge",
      "action": "create",
      "local_id": "local_cargo_001",
      "timestamp": "2024-07-15T10:15:00Z",
      "data": {
        "operation_id": "OP-2024-001",
        "cargo_type": "automobile",
        "vin": "1HGBH41JXMN109186",
        "zone": "BRV",
        "processed_by": 456
      }
    }
  ]
}
```

#### B. Conflict Resolution
```
POST /api/sync/resolve-conflicts
```
**Request Schema**:
```json
{
  "conflicts": [
    {
      "local_change_id": "change_001",
      "server_version": {...},
      "local_version": {...},
      "resolution_strategy": "server_wins", // server_wins, local_wins, merge
      "merged_data": {...} // If merge strategy
    }
  ]
}
```

### Local Caching Strategy

#### A. Critical Data Caching
- **Operations Data**: Cache active operations for 5 minutes
- **Team Assignments**: Cache for 30 minutes
- **Vessel Information**: Cache for 1 hour
- **User Profiles**: Cache for 4 hours

#### B. Cache Invalidation
```
POST /api/cache/invalidate
```
**Request Schema**:
```json
{
  "cache_keys": [
    "operations:active",
    "teams:OP-2024-001",
    "vessel:123:maritime-details"
  ]
}
```

## 5. SECURITY & AUTHENTICATION

### Role-Based Access Control (RBAC)

#### A. Maritime-Specific Roles
```json
{
  "roles": {
    "port_manager": {
      "permissions": ["*"], // Full access
      "description": "Port operations manager"
    },
    "operations_supervisor": {
      "permissions": [
        "operations:read",
        "operations:create",
        "operations:update",
        "teams:assign",
        "equipment:allocate"
      ],
      "description": "Vessel operations supervisor"
    },
    "auto_ops_lead": {
      "permissions": [
        "cargo:process",
        "teams:supervise:BRV",
        "operations:read",
        "equipment:operate:automotive"
      ],
      "description": "Automobile operations team leader"
    },
    "heavy_ops_lead": {
      "permissions": [
        "cargo:process",
        "teams:supervise:heavy",
        "equipment:operate:crane",
        "equipment:operate:reach_stacker"
      ],
      "description": "Heavy equipment operations leader"
    },
    "general_stevedore": {
      "permissions": [
        "cargo:process:basic",
        "tasks:update:assigned"
      ],
      "description": "General stevedore worker"
    }
  }
}
```

#### B. Zone-Based Permissions
```python
# Example permission check
def check_zone_access(user, zone, operation_type):
    """Check if user has access to specific zone for operation type"""
    user_zones = user.maritime_profile.zone_authorizations
    operation_permissions = user.role.permissions
    
    required_permission = f"operations:{operation_type}:{zone}"
    
    return (zone in user_zones and 
            required_permission in operation_permissions)
```

### API Authentication

#### A. JWT Token Enhancement
```json
{
  "user_id": 456,
  "username": "john.smith",
  "role": "auto_ops_lead",
  "zones": ["BRV", "ZEE"],
  "current_operation": "OP-2024-001",
  "shift": "day",
  "equipment_certs": ["forklift", "crane_basic"],
  "exp": 1721059200
}
```

#### B. API Key for Equipment Integration
```
GET /api/equipment/crane_02/status
Authorization: Bearer <jwt_token>
X-Equipment-Key: EQUIP_KEY_CRANE_02_2024
```

## 6. PERFORMANCE OPTIMIZATION

### Caching Strategies

#### A. Multi-Level Caching
```python
# L1: In-memory cache (Redis)
# L2: Database query optimization
# L3: CDN for static assets

class CacheStrategy:
    def __init__(self):
        self.redis_ttl = {
            'operations:active': 300,      # 5 minutes
            'teams:assignments': 1800,     # 30 minutes
            'vessel:details': 3600,        # 1 hour
            'berths:occupancy': 300,       # 5 minutes
            'cargo:progress': 60,          # 1 minute
            'analytics:realtime': 30       # 30 seconds
        }
```

#### B. Cache Warming
```
POST /api/cache/warm
```
**Purpose**: Pre-populate frequently accessed data

### Query Optimization

#### A. Database Indexing Strategy
```sql
-- Operations queries
CREATE INDEX idx_operations_status_date ON ship_operations(status, created_at);
CREATE INDEX idx_cargo_operation_zone ON cargo_discharge(operation_id, zone);

-- Team performance queries  
CREATE INDEX idx_team_assignments_operation ON team_assignments(operation_id, zone);
CREATE INDEX idx_user_certifications ON user_certifications(user_id, certification_type);

-- Real-time analytics
CREATE INDEX idx_cargo_processing_time ON cargo_discharge(processed_at, operation_id);
CREATE INDEX idx_equipment_status_time ON equipment_status(timestamp, equipment_id);
```

#### B. Query Pagination
```python
# Efficient pagination for large datasets
def paginate_cargo_records(operation_id, page=1, per_page=50):
    offset = (page - 1) * per_page
    
    query = """
    SELECT * FROM cargo_discharge 
    WHERE operation_id = %s 
    ORDER BY processed_at DESC 
    LIMIT %s OFFSET %s
    """
    
    return db.execute(query, [operation_id, per_page, offset])
```

### API Response Optimization

#### A. Selective Field Loading
```
GET /api/operations/OP-2024-001?fields=progress,teams,alerts
```

#### B. Compression
```python
# Enable gzip compression for API responses
@app.after_request
def compress_response(response):
    if (response.content_length > 1000 and 
        'gzip' in request.headers.get('Accept-Encoding', '')):
        response.data = gzip.compress(response.data)
        response.headers['Content-Encoding'] = 'gzip'
    return response
```

## Error Handling & Validation

### A. Maritime-Specific Error Codes
```json
{
  "error_codes": {
    "BERTH_OCCUPIED": {
      "code": 4001,
      "message": "Berth is already occupied by another vessel",
      "category": "berth_management"
    },
    "TEAM_CAPACITY_EXCEEDED": {
      "code": 4002,
      "message": "Team assignment exceeds zone capacity",
      "category": "team_management"
    },
    "EQUIPMENT_UNAVAILABLE": {
      "code": 4003,
      "message": "Required equipment is not available",
      "category": "equipment_management"
    },
    "CARGO_MISMATCH": {
      "code": 4004,
      "message": "Cargo details do not match manifest",
      "category": "cargo_processing"
    }
  }
}
```

### B. Validation Schemas
```python
# Pydantic schemas for request validation
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

class CargoDischargeRequest(BaseModel):
    operation_id: str
    cargo_type: str
    vin: Optional[str] = None
    zone: str
    processed_by: int
    
    @validator('zone')
    def validate_zone(cls, v):
        allowed_zones = ['BRV', 'ZEE', 'SOU']
        if v not in allowed_zones:
            raise ValueError(f'Zone must be one of {allowed_zones}')
        return v
    
    @validator('vin')
    def validate_vin(cls, v, values):
        if values.get('cargo_type') == 'automobile' and not v:
            raise ValueError('VIN required for automobile cargo')
        return v
```

## Integration with Existing Flask Blueprint Architecture

### A. New Blueprint Structure
```python
# models/routes/maritime.py
maritime_bp = Blueprint('maritime', __name__)

# Ship operations routes
@maritime_bp.route('/ship-operations/setup', methods=['POST'])
@login_required
@require_permission('operations:create')
def setup_ship_operation():
    # Implementation

# Cargo management routes  
@maritime_bp.route('/cargo/discharge/record', methods=['POST'])
@login_required
@require_permission('cargo:process')
def record_cargo_discharge():
    # Implementation

# Team management routes
@maritime_bp.route('/teams/assign', methods=['POST'])
@login_required
@require_permission('teams:assign')
def assign_teams():
    # Implementation
```

### B. Blueprint Registration
```python
# app.py
from models.routes.maritime import maritime_bp
from models.routes.websockets import websocket_bp

app.register_blueprint(maritime_bp, url_prefix='/api/maritime')
app.register_blueprint(websocket_bp, url_prefix='/ws')
```

## Support for 4-Step Wizard, Multi-Ship Dashboard, and Real-Time Tracking

### A. 4-Step Wizard State Management
```python
class OperationWizard:
    def __init__(self, operation_id):
        self.operation_id = operation_id
        self.redis_key = f"wizard:state:{operation_id}"
    
    def save_step_data(self, step, data):
        current_state = self.get_state()
        current_state[f'step_{step}'] = data
        cache_set(self.redis_key, json.dumps(current_state), timeout=3600)
    
    def validate_step(self, step, data):
        validators = {
            1: self.validate_basic_info,
            2: self.validate_team_assignment,
            3: self.validate_equipment_zones,
            4: self.validate_safety_docs
        }
        return validators[step](data)
```

### B. Multi-Ship Dashboard Data Aggregation
```python
def get_multi_ship_dashboard_data():
    """Aggregate data for multiple concurrent operations"""
    active_operations = ShipOperation.get_active_operations()
    
    dashboard_data = {
        'operations': [],
        'summary': {},
        'alerts': [],
        'berth_status': get_berth_occupancy()
    }
    
    for operation in active_operations:
        operation_data = {
            'operation_id': operation.id,
            'vessel': operation.vessel.to_dict(),
            'progress': get_operation_progress(operation.id),
            'teams': get_team_status(operation.id),
            'alerts': get_operation_alerts(operation.id)
        }
        dashboard_data['operations'].append(operation_data)
    
    return dashboard_data
```

### C. Real-Time Cargo Tracking WebSocket Handler
```python
import asyncio
from flask_socketio import SocketIO, emit, join_room

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('join_operation')
def on_join_operation(data):
    operation_id = data['operation_id']
    join_room(f"operation_{operation_id}")
    emit('joined', {'room': f"operation_{operation_id}"})

@socketio.on('cargo_processed')
def on_cargo_processed(data):
    # Update database
    record_cargo_discharge(data)
    
    # Broadcast to all clients in operation room
    operation_id = data['operation_id']
    progress_update = calculate_operation_progress(operation_id)
    
    socketio.emit('progress_update', 
                  progress_update, 
                  room=f"operation_{operation_id}")
```

## Deployment Considerations

### A. Environment Variables
```bash
# Maritime-specific configuration
MARITIME_MODE=true
DEFAULT_BERTH_COUNT=5
ZONE_TYPES=BRV,ZEE,SOU
EQUIPMENT_TYPES=crane,forklift,reach_stacker,van,wagon

# WebSocket configuration
WEBSOCKET_ENABLED=true
WEBSOCKET_PING_INTERVAL=25
WEBSOCKET_PING_TIMEOUT=60

# Real-time analytics
ANALYTICS_BATCH_SIZE=100
ANALYTICS_FLUSH_INTERVAL=30
```

### B. Docker Configuration Updates
```dockerfile
# Add WebSocket support
EXPOSE 5000 5001

# Install additional dependencies
RUN pip install flask-socketio python-socketio redis-py-cluster

# Configure for real-time operations
ENV WEBSOCKET_ENABLED=true
ENV WORKERS=1
```

This comprehensive API integration plan provides the foundation for transforming the Fleet Management PWA into a specialized maritime stevedoring operations platform while maintaining the existing architecture's strengths and PWA capabilities.