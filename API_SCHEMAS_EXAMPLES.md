# API Schemas and Implementation Examples

## Request/Response Schema Specifications

### 1. Ship Operations API Detailed Schemas

#### Setup Wizard - Step 1: Basic Information
```json
{
  "request": {
    "vessel_id": 123,
    "operation_type": "discharge",
    "step": 1,
    "step_data": {
      "berth_assignment": "A-1",
      "eta": "2024-07-15T08:00:00Z",
      "etd": "2024-07-16T18:00:00Z",
      "agent_details": {
        "company": "Maritime Logistics Ltd",
        "contact_person": "Jane Doe",
        "phone": "+1-555-0199",
        "email": "jane.doe@maritimelogistics.com"
      },
      "cargo_manifest": {
        "total_automobiles": 267,
        "total_containers": 45,
        "total_bulk_tons": 150,
        "special_cargo": [
          {
            "type": "hazardous",
            "description": "Paint chemicals",
            "quantity": 5,
            "handling_instructions": "Keep dry, temperature controlled"
          }
        ]
      },
      "documentation": {
        "bill_of_lading": "BOL-2024-001",
        "customs_reference": "CUST-REF-789",
        "manifest_verified": true
      }
    }
  },
  "response": {
    "operation_id": "OP-2024-001",
    "step": 1,
    "next_step": 2,
    "validation_status": "valid",
    "validation_errors": [],
    "auto_suggestions": {
      "recommended_berth": "A-1",
      "estimated_duration": "26 hours",
      "required_teams": 3,
      "equipment_needs": ["crane_01", "crane_02", "forklift_fleet"]
    },
    "wizard_progress": {
      "current_step": 1,
      "total_steps": 4,
      "completion_percentage": 25
    }
  }
}
```

#### Setup Wizard - Step 2: Team Assignment
```json
{
  "request": {
    "vessel_id": 123,
    "operation_type": "discharge", 
    "step": 2,
    "step_data": {
      "operation_supervisor": 456,
      "shift_plan": [
        {
          "shift_name": "day_shift",
          "start_time": "2024-07-15T07:00:00Z",
          "end_time": "2024-07-15T15:00:00Z",
          "teams": [
            {
              "zone": "BRV",
              "auto_ops_lead": 456,
              "team_members": [101, 102, 103, 104],
              "equipment_operators": [
                {"user_id": 105, "equipment": "forklift", "certification": "FL-ADV-2024"}
              ]
            },
            {
              "zone": "ZEE", 
              "heavy_ops_lead": 789,
              "team_members": [201, 202, 203],
              "equipment_operators": [
                {"user_id": 204, "equipment": "crane", "certification": "CR-ADV-2024"}
              ]
            }
          ]
        },
        {
          "shift_name": "night_shift",
          "start_time": "2024-07-15T23:00:00Z", 
          "end_time": "2024-07-16T07:00:00Z",
          "teams": [
            {
              "zone": "SOU",
              "auto_ops_lead": 321,
              "team_members": [301, 302, 303],
              "reduced_operations": true
            }
          ]
        }
      ],
      "break_schedule": {
        "coffee_breaks": ["10:00", "15:00"],
        "lunch_break": "12:00-12:30",
        "safety_meetings": ["07:30", "15:30"]
      }
    }
  },
  "response": {
    "operation_id": "OP-2024-001",
    "step": 2,
    "next_step": 3,
    "validation_status": "valid",
    "team_conflicts": [],
    "certification_warnings": [
      {
        "user_id": 105,
        "certification": "FL-ADV-2024",
        "expiry_date": "2024-08-15",
        "warning": "Certification expires in 31 days"
      }
    ],
    "coverage_analysis": {
      "zones_covered": ["BRV", "ZEE", "SOU"],
      "shift_coverage": "complete",
      "equipment_coverage": "adequate",
      "backup_personnel": 2
    }
  }
}
```

#### Setup Wizard - Step 3: Equipment & Zones
```json
{
  "request": {
    "vessel_id": 123,
    "operation_type": "discharge",
    "step": 3,
    "step_data": {
      "equipment_allocation": {
        "cranes": [
          {
            "equipment_id": "crane_01",
            "zone": "BRV", 
            "operator": 204,
            "backup_operator": 205,
            "capacity": "45 tons",
            "operational_hours": "07:00-19:00"
          },
          {
            "equipment_id": "crane_02",
            "zone": "ZEE",
            "operator": 206,
            "capacity": "45 tons", 
            "operational_hours": "07:00-15:00"
          }
        ],
        "forklifts": [
          {
            "equipment_id": "fl_001",
            "zone": "BRV",
            "operator": 105,
            "capacity": "5 tons"
          },
          {
            "equipment_id": "fl_002", 
            "zone": "ZEE",
            "operator": 107,
            "capacity": "5 tons"
          }
        ],
        "tico_vehicles": [
          {
            "vehicle_id": "van_01",
            "driver": 301,
            "capacity": 8,
            "route": "port_to_lot_A"
          },
          {
            "vehicle_id": "wagon_02",
            "driver": 302,
            "capacity": 6,
            "route": "port_to_lot_B"
          }
        ]
      },
      "zone_layout": {
        "BRV": {
          "area_supervisor": 456,
          "storage_lots": ["LOT-A-01", "LOT-A-02", "LOT-A-03"],
          "processing_capacity": 100,
          "safety_equipment": ["fire_extinguisher", "first_aid", "spill_kit"]
        },
        "ZEE": {
          "area_supervisor": 789,
          "storage_lots": ["LOT-B-01", "LOT-B-02"],
          "processing_capacity": 80,
          "special_handling": "container_area"
        },
        "SOU": {
          "area_supervisor": 321,
          "storage_lots": ["LOT-C-01"],
          "processing_capacity": 60,
          "restrictions": "night_operations_limited"
        }
      }
    }
  },
  "response": {
    "operation_id": "OP-2024-001",
    "step": 3,
    "next_step": 4,
    "validation_status": "valid",
    "equipment_conflicts": [],
    "capacity_analysis": {
      "total_processing_capacity": 240,
      "required_capacity": 267,
      "capacity_shortfall": 27,
      "recommendations": [
        "Consider extending day shift by 2 hours",
        "Activate night operations in BRV zone"
      ]
    },
    "safety_compliance": {
      "equipment_inspections": "current",
      "operator_certifications": "verified",
      "zone_safety_setup": "complete"
    }
  }
}
```

#### Setup Wizard - Step 4: Safety & Documentation
```json
{
  "request": {
    "vessel_id": 123,
    "operation_type": "discharge",
    "step": 4,
    "step_data": {
      "safety_briefing": {
        "conducted_by": 456,
        "attendance": [101, 102, 103, 104, 105, 201, 202, 203, 204],
        "briefing_topics": [
          "cargo_handling_procedures",
          "equipment_safety_protocols", 
          "emergency_procedures",
          "environmental_protection"
        ],
        "completion_time": "2024-07-15T06:45:00Z"
      },
      "documentation_checklist": {
        "customs_clearance": {
          "status": "approved",
          "reference": "CUST-2024-789",
          "approved_by": "Port Authority"
        },
        "environmental_permits": {
          "status": "approved",
          "permit_number": "ENV-2024-123"
        },
        "cargo_insurance": {
          "status": "verified",
          "policy_number": "INS-2024-456"
        },
        "vessel_certificates": {
          "safety_cert": "valid_until_2025-03-15",
          "cargo_cert": "valid_until_2024-12-20"
        }
      },
      "emergency_procedures": {
        "evacuation_plan": "reviewed",
        "medical_facilities": "port_clinic_notified",
        "fire_safety": "equipment_checked",
        "spill_response": "materials_staged"
      },
      "quality_standards": {
        "damage_assessment_protocol": "enabled",
        "photo_documentation": "required",
        "inspector_assignments": [
          {"inspector": 501, "zones": ["BRV", "ZEE"]},
          {"inspector": 502, "zones": ["SOU"]}
        ]
      }
    }
  },
  "response": {
    "operation_id": "OP-2024-001",
    "step": 4,
    "operation_status": "ready_to_commence",
    "approval_status": "approved",
    "approving_manager": 456,
    "approval_timestamp": "2024-07-15T06:50:00Z",
    "operation_summary": {
      "vessel": "MV Atlantic Explorer",
      "berth": "A-1", 
      "total_cargo": 267,
      "teams_assigned": 9,
      "equipment_allocated": 6,
      "estimated_duration": "26 hours",
      "estimated_completion": "2024-07-16T16:00:00Z"
    },
    "next_steps": [
      "commence_operations",
      "begin_cargo_discharge",
      "activate_real_time_monitoring"
    ]
  }
}
```

### 2. Real-Time Progress Tracking Schemas

#### Cargo Processing Event
```json
{
  "event_type": "cargo_processed",
  "timestamp": "2024-07-15T09:15:30Z",
  "operation_id": "OP-2024-001",
  "cargo_item": {
    "type": "automobile",
    "vin": "1HGBH41JXMN109186",
    "make": "Toyota",
    "model": "Camry",
    "year": 2024,
    "color": "blue",
    "sequence_number": 89
  },
  "processing_details": {
    "zone": "BRV",
    "processed_by": {
      "user_id": 101,
      "name": "Worker A",
      "role": "general_stevedore"
    },
    "equipment_used": "fl_001",
    "start_time": "2024-07-15T09:12:00Z",
    "end_time": "2024-07-15T09:15:30Z",
    "processing_time_seconds": 210,
    "destination_lot": "LOT-A-12"
  },
  "quality_check": {
    "inspector": {
      "user_id": 501,
      "name": "Inspector Smith"
    },
    "damage_assessment": "none",
    "photo_urls": [
      "/storage/photos/cargo_89_front.jpg",
      "/storage/photos/cargo_89_rear.jpg"
    ],
    "status": "approved",
    "notes": "Vehicle in excellent condition"
  },
  "real_time_metrics": {
    "zone_rate_current": 6.8,
    "zone_rate_target": 8.0,
    "zone_efficiency": 85.0,
    "overall_progress": 33.3
  }
}
```

#### Team Status Update
```json
{
  "event_type": "team_status_update",
  "timestamp": "2024-07-15T10:00:00Z",
  "operation_id": "OP-2024-001",
  "team": {
    "team_id": "T-BRV-001",
    "zone": "BRV",
    "supervisor": {
      "user_id": 456,
      "name": "John Smith",
      "role": "auto_ops_lead"
    }
  },
  "status_change": {
    "from": "active",
    "to": "break",
    "break_type": "coffee",
    "scheduled_duration": 15,
    "break_location": "break_area_A"
  },
  "team_members": [
    {
      "user_id": 101,
      "status": "on_break",
      "hours_worked": 2.5
    },
    {
      "user_id": 102, 
      "status": "on_break",
      "hours_worked": 2.5
    }
  ],
  "productivity_snapshot": {
    "units_processed_this_shift": 25,
    "average_processing_time": 195,
    "team_efficiency": 87.2
  }
}
```

### 3. Error Handling Examples

#### Validation Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field_errors": [
        {
          "field": "step_data.berth_assignment",
          "error": "Berth A-1 is already occupied by vessel MV Caribbean Star",
          "error_code": "BERTH_OCCUPIED"
        },
        {
          "field": "step_data.auto_ops_lead",
          "error": "User 456 is not certified for auto operations",
          "error_code": "CERTIFICATION_MISSING"
        }
      ]
    },
    "suggestions": [
      {
        "field": "berth_assignment",
        "suggested_value": "A-2",
        "reason": "Berth A-2 is available and suitable for this vessel type"
      }
    ]
  },
  "timestamp": "2024-07-15T08:30:00Z",
  "request_id": "req_789"
}
```

#### Business Logic Error Response
```json
{
  "error": {
    "code": "BUSINESS_RULE_VIOLATION",
    "message": "Operation cannot be started",
    "details": {
      "violations": [
        {
          "rule": "MINIMUM_TEAM_SIZE",
          "description": "Zone BRV requires minimum 4 team members, only 3 assigned",
          "severity": "error"
        },
        {
          "rule": "EQUIPMENT_AVAILABILITY",
          "description": "Crane crane_01 is scheduled for maintenance",
          "severity": "warning",
          "maintenance_window": "2024-07-15T14:00:00Z to 2024-07-15T16:00:00Z"
        }
      ]
    },
    "resolution_options": [
      {
        "option": "assign_additional_team_member",
        "description": "Assign one more team member to zone BRV",
        "available_workers": [106, 107, 108]
      },
      {
        "option": "reschedule_maintenance",
        "description": "Defer crane maintenance to after operation completion"
      }
    ]
  },
  "timestamp": "2024-07-15T08:35:00Z",
  "request_id": "req_790"
}
```

### 4. Offline Sync Schemas

#### Sync Queue Item
```json
{
  "sync_item": {
    "id": "sync_001",
    "table": "cargo_discharge",
    "action": "create",
    "local_id": "local_cargo_001",
    "client_timestamp": "2024-07-15T10:15:00Z",
    "retry_count": 0,
    "priority": "high",
    "data": {
      "operation_id": "OP-2024-001",
      "cargo_type": "automobile",
      "vin": "1HGBH41JXMN109186",
      "zone": "BRV",
      "processed_by": 101,
      "processing_time": 210,
      "quality_status": "approved"
    },
    "dependencies": [],
    "metadata": {
      "user_id": 101,
      "device_id": "tablet_001",
      "app_version": "2.1.0"
    }
  }
}
```

#### Conflict Resolution Response
```json
{
  "conflicts": [
    {
      "sync_item_id": "sync_001",
      "conflict_type": "concurrent_modification",
      "local_version": {
        "cargo_id": "local_cargo_001",
        "quality_status": "approved",
        "notes": "Vehicle in good condition",
        "timestamp": "2024-07-15T10:15:00Z"
      },
      "server_version": {
        "cargo_id": "CARGO-2024-089",
        "quality_status": "conditional", 
        "notes": "Minor scratch on rear bumper",
        "timestamp": "2024-07-15T10:14:30Z"
      },
      "resolution_options": [
        {
          "strategy": "merge",
          "description": "Combine notes and use most restrictive quality status",
          "result": {
            "quality_status": "conditional",
            "notes": "Vehicle in good condition. Minor scratch on rear bumper"
          }
        },
        {
          "strategy": "local_wins",
          "description": "Use local version (overwrites server changes)"
        },
        {
          "strategy": "server_wins", 
          "description": "Use server version (discards local changes)"
        }
      ],
      "auto_resolution": {
        "strategy": "merge",
        "confidence": 85,
        "reason": "Quality status conflict can be safely merged"
      }
    }
  ]
}
```

### 5. Performance Monitoring Schemas

#### Performance Metrics Response
```json
{
  "performance_metrics": {
    "operation_id": "OP-2024-001",
    "timestamp": "2024-07-15T12:00:00Z",
    "overall_performance": {
      "target_completion": "2024-07-16T16:00:00Z",
      "projected_completion": "2024-07-16T18:30:00Z",
      "delay_minutes": 150,
      "overall_efficiency": 82.5
    },
    "zone_performance": [
      {
        "zone": "BRV",
        "target_rate": 8.0,
        "actual_rate": 6.8,
        "efficiency": 85.0,
        "units_processed": 45,
        "units_remaining": 55,
        "bottlenecks": [
          {
            "type": "equipment_slow",
            "description": "Forklift fl_001 operating at 75% capacity",
            "impact": "moderate"
          }
        ]
      },
      {
        "zone": "ZEE",
        "target_rate": 6.0,
        "actual_rate": 5.2,
        "efficiency": 86.7,
        "units_processed": 32,
        "units_remaining": 23
      }
    ],
    "team_performance": [
      {
        "team_id": "T-BRV-001",
        "average_processing_time": 195,
        "target_processing_time": 180,
        "break_adherence": 95,
        "safety_incidents": 0
      }
    ],
    "equipment_utilization": [
      {
        "equipment_id": "crane_01",
        "utilization_percentage": 87.5,
        "operational_hours": 5.25,
        "maintenance_alerts": []
      },
      {
        "equipment_id": "fl_001",
        "utilization_percentage": 75.0,
        "operational_hours": 5.25,
        "maintenance_alerts": [
          {
            "type": "hydraulic_pressure_low",
            "severity": "low",
            "recommended_action": "check_fluid_levels"
          }
        ]
      }
    ]
  }
}
```

## Implementation Examples

### Flask Route Implementation Example
```python
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from marshmallow import ValidationError
from models.schemas import CargoDischargeSchema
from models.models.maritime import ShipOperation, CargoDischarge
from utils.permissions import require_permission
from utils.websockets import broadcast_cargo_update

maritime_bp = Blueprint('maritime', __name__)

@maritime_bp.route('/cargo/discharge/record', methods=['POST'])
@login_required
@require_permission('cargo:process')
def record_cargo_discharge():
    """Record cargo discharge with real-time updates"""
    try:
        # Validate request data
        schema = CargoDischargeSchema()
        data = schema.load(request.json)
        
        # Check operation exists and is active
        operation = ShipOperation.query.get(data['operation_id'])
        if not operation or operation.status != 'active':
            return jsonify({
                'error': {
                    'code': 'OPERATION_NOT_ACTIVE',
                    'message': 'Operation is not currently active'
                }
            }), 400
        
        # Verify user has access to the zone
        if not current_user.has_zone_access(data['zone']):
            return jsonify({
                'error': {
                    'code': 'ZONE_ACCESS_DENIED',
                    'message': f'User does not have access to zone {data["zone"]}'
                }
            }), 403
        
        # Create cargo discharge record
        cargo_discharge = CargoDischarge(
            operation_id=data['operation_id'],
            cargo_type=data['cargo_type'],
            vin=data.get('vin'),
            zone=data['zone'],
            processed_by=current_user.id,
            processing_start=data['processing_start'],
            processing_end=data['processing_end'],
            destination_lot=data['destination_lot'],
            quality_status=data.get('quality_status', 'pending'),
            notes=data.get('notes', '')
        )
        
        db.session.add(cargo_discharge)
        db.session.commit()
        
        # Calculate updated progress
        progress = operation.calculate_progress()
        
        # Broadcast real-time update
        broadcast_cargo_update({
            'operation_id': operation.id,
            'cargo_processed': cargo_discharge.to_dict(),
            'progress_update': progress,
            'zone': data['zone'],
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'message': 'Cargo discharge recorded successfully',
            'cargo_id': cargo_discharge.id,
            'operation_progress': progress
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Request validation failed',
                'details': e.messages
            }
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to record cargo discharge'
            }
        }), 500
```

### WebSocket Event Handler Example
```python
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
import json

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('join_operation')
def handle_join_operation(data):
    """Join operation room for real-time updates"""
    operation_id = data.get('operation_id')
    
    # Verify user has access to operation
    operation = ShipOperation.query.get(operation_id)
    if not operation or not current_user.can_access_operation(operation):
        emit('error', {'message': 'Access denied to operation'})
        return
    
    room = f"operation_{operation_id}"
    join_room(room)
    
    # Send current operation status
    current_status = {
        'operation_id': operation_id,
        'status': operation.status,
        'progress': operation.calculate_progress(),
        'active_teams': operation.get_active_teams(),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    emit('operation_status', current_status)
    emit('joined_room', {'room': room})

@socketio.on('cargo_progress_update')
def handle_cargo_progress(data):
    """Handle real-time cargo progress updates"""
    operation_id = data.get('operation_id')
    room = f"operation_{operation_id}"
    
    # Broadcast to all users in the operation room
    emit('progress_update', {
        'operation_id': operation_id,
        'zone': data.get('zone'),
        'units_processed': data.get('units_processed'),
        'processing_rate': data.get('processing_rate'),
        'timestamp': datetime.utcnow().isoformat()
    }, room=room)
```

### Caching Implementation Example
```python
import redis
import json
from functools import wraps
from datetime import timedelta

class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl_config = {
            'operations:active': 300,      # 5 minutes
            'teams:performance': 180,      # 3 minutes
            'cargo:progress': 60,          # 1 minute
            'vessel:details': 3600,        # 1 hour
        }
    
    def cache_key(self, prefix, *args):
        """Generate cache key"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"
    
    def get_cached(self, key):
        """Get cached value"""
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None
    
    def set_cached(self, key, value, ttl=None):
        """Set cached value"""
        try:
            if ttl is None:
                # Determine TTL from key prefix
                prefix = key.split(':')[0]
                ttl = self.ttl_config.get(prefix, 300)
            
            self.redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception:
            return False
    
    def invalidate_pattern(self, pattern):
        """Invalidate cache keys matching pattern"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception:
            return False

def cached_response(cache_prefix, ttl=None):
    """Decorator for caching API responses"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Generate cache key from function args
            cache_key = f"{cache_prefix}:{':'.join(str(arg) for arg in args)}"
            
            # Try to get from cache
            cached_result = cache_manager.get_cached(cache_key)
            if cached_result:
                return jsonify(cached_result)
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            if result.status_code == 200:
                cache_manager.set_cached(cache_key, result.json, ttl)
            
            return result
        return decorated
    return decorator

# Usage example
@maritime_bp.route('/operations/<operation_id>/progress')
@login_required
@cached_response('operation:progress', ttl=60)
def get_operation_progress(operation_id):
    """Get operation progress with caching"""
    operation = ShipOperation.query.get_or_404(operation_id)
    progress_data = operation.calculate_detailed_progress()
    return jsonify(progress_data)
```

This supplementary document provides detailed schemas and implementation examples that complement the main API integration plan, offering practical guidance for implementing the maritime stevedoring operations API.