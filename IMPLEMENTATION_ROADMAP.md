# Stevedores Dashboard 2.0 Integration Roadmap
## Fleet Management PWA Maritime Enhancement Project

**Project Overview:** Comprehensive integration of maritime stevedoring operations features from Stevedores Dashboard 2.0 into the existing Fleet Management PWA while maintaining PWA capabilities and improving architecture.

**Current Status:**
- ✅ **Working PWA Foundation**: Modern Flask architecture, offline capabilities, PWA features
- ✅ **Stable Deployment**: Running on Render.com with PostgreSQL/SQLite fallback
- ❌ **Missing Maritime Features**: Stevedoring-specific functionality needs integration

---

## PHASE 1: FOUNDATION & ANALYSIS 
**Duration: Week 1-2 (14 days)**
**Critical Path Priority: HIGH**

### 1.1 Database Architecture Enhancement (Week 1)

#### Maritime Schema Migration
**Deliverables:**
- Enhanced Ship/Vessel model with stevedoring fields
- Cargo tracking models (Automobile, Heavy Equipment)
- Team assignment models (Auto Ops, Heavy Ops, General Stevedores)
- TICO transportation management models

**Specific Tasks:**
```sql
-- New Maritime Tables
CREATE TABLE stevedoring_operations (
    id INTEGER PRIMARY KEY,
    vessel_id INTEGER REFERENCES vessels(id),
    berth_assignment VARCHAR(20),
    operation_type VARCHAR(50),
    operation_date DATE,
    shift_start TIME,
    shift_end TIME,
    break_duration INTEGER,
    target_completion DATETIME,
    status VARCHAR(20) DEFAULT 'planning'
);

CREATE TABLE cargo_discharge (
    id INTEGER PRIMARY KEY,
    operation_id INTEGER REFERENCES stevedoring_operations(id),
    total_vehicles INTEGER DEFAULT 0,
    automobiles_discharged INTEGER DEFAULT 0,
    heavy_equipment_discharged INTEGER DEFAULT 0,
    electric_vehicles INTEGER DEFAULT 0,
    static_cargo INTEGER DEFAULT 0,
    progress_percentage INTEGER DEFAULT 0
);

CREATE TABLE maritime_zones (
    id INTEGER PRIMARY KEY,
    operation_id INTEGER REFERENCES stevedoring_operations(id),
    brv_target INTEGER DEFAULT 0,
    zee_target INTEGER DEFAULT 0,
    sou_target INTEGER DEFAULT 0,
    brv_completed INTEGER DEFAULT 0,
    zee_completed INTEGER DEFAULT 0,
    sou_completed INTEGER DEFAULT 0
);

CREATE TABLE team_assignments (
    id INTEGER PRIMARY KEY,
    operation_id INTEGER REFERENCES stevedoring_operations(id),
    operation_manager VARCHAR(100),
    auto_ops_lead VARCHAR(100),
    auto_ops_assistant VARCHAR(100),
    heavy_ops_lead VARCHAR(100),
    heavy_ops_assistant VARCHAR(100),
    total_drivers INTEGER DEFAULT 0
);

CREATE TABLE tico_transport (
    id INTEGER PRIMARY KEY,
    operation_id INTEGER REFERENCES stevedoring_operations(id),
    vans_assigned INTEGER DEFAULT 0,
    station_wagons_assigned INTEGER DEFAULT 0,
    drivers_transported INTEGER DEFAULT 0
);
```

**Dependencies:** None
**Testing:** Unit tests for all new models
**Success Criteria:** Database migration completes without data loss

### 1.2 API Endpoint Development (Week 1-2)

#### Stevedoring-Specific REST APIs
**Deliverables:**
- `/api/v1/stevedoring/operations` - CRUD operations
- `/api/v1/stevedoring/wizard` - 4-step wizard data processing
- `/api/v1/stevedoring/cargo` - Discharge tracking
- `/api/v1/stevedoring/teams` - Team management
- `/api/v1/stevedoring/analytics` - Maritime KPIs

**Implementation Files:**
```python
# models/routes/stevedoring.py
stevedoring_bp = Blueprint('stevedoring', __name__)

@stevedoring_bp.route('/operations', methods=['GET', 'POST'])
@login_required
def operations():
    # Multi-ship operations management
    pass

@stevedoring_bp.route('/wizard/step/<int:step>', methods=['POST'])
@login_required
def wizard_step(step):
    # 4-step wizard processing
    pass

@stevedoring_bp.route('/cargo/<int:operation_id>/update', methods=['PUT'])
@login_required
def update_cargo_progress(operation_id):
    # Real-time cargo discharge tracking
    pass
```

**Dependencies:** Database schema completion
**Testing:** API integration tests, Postman collection
**Success Criteria:** All endpoints return valid responses

### 1.3 PWA Integration Testing (Week 2)

#### Offline Maritime Operations Support
**Deliverables:**
- Enhanced service worker for maritime data caching
- IndexedDB schema for offline stevedoring operations
- Sync conflict resolution for maritime data

**Implementation:**
```javascript
// static/js/maritime-offline.js
class MaritimeOfflineManager {
    constructor() {
        this.dbName = 'StevedoringDB';
        this.version = 1;
        this.db = null;
    }

    async init() {
        // Initialize IndexedDB for maritime operations
        const request = indexedDB.open(this.dbName, this.version);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Operations store
            const operationsStore = db.createObjectStore('operations', {
                keyPath: 'id',
                autoIncrement: true
            });
            
            // Cargo tracking store
            const cargoStore = db.createObjectStore('cargo', {
                keyPath: 'id',
                autoIncrement: true
            });
            
            // Team assignments store
            const teamStore = db.createObjectStore('teams', {
                keyPath: 'id',
                autoIncrement: true
            });
        };
    }

    async saveOperation(operation) {
        // Save operation for offline use
    }

    async syncOperations() {
        // Background sync when connection restored
    }
}
```

**Dependencies:** API endpoints completion
**Testing:** Offline functionality tests, sync testing
**Success Criteria:** PWA works fully offline with maritime data

---

## PHASE 2: CORE MARITIME FEATURES
**Duration: Week 3-5 (21 days)**
**Critical Path Priority: HIGH**

### 2.1 4-Step Wizard Implementation (Week 3)

#### Maritime Operations Setup Wizard
**Deliverables:**
- Step 1: Vessel Information (Name, Type, Shipping Line, Port, Date)
- Step 2: Cargo Configuration (Automobiles, Heavy Equipment, Zones)
- Step 3: Team Assignments (Operation Manager, Auto/Heavy Ops Leads)
- Step 4: Review & Confirmation (Summary, Auto-fill validation)

**UI Components:**
```html
<!-- templates/stevedoring/wizard.html -->
<div class="wizard-container">
    <div class="step-indicators">
        <div id="step1-indicator" class="step-indicator active">1</div>
        <div id="step2-indicator" class="step-indicator">2</div>
        <div id="step3-indicator" class="step-indicator">3</div>
        <div id="step4-indicator" class="step-indicator">4</div>
    </div>
    
    <!-- Step 1: Vessel Information -->
    <div id="step1" class="wizard-step">
        <h2>Vessel Information</h2>
        <form class="wizard-form">
            <div class="form-group">
                <label>Vessel Name</label>
                <input type="text" id="vesselName" required>
            </div>
            <div class="form-group">
                <label>Shipping Line</label>
                <select id="shippingLine" required>
                    <option value="">Select Shipping Line</option>
                    <option value="K-Line">K-Line</option>
                    <option value="Hyundai Glovis">Hyundai Glovis</option>
                    <option value="UECC">UECC</option>
                    <option value="Wallenius Wilhelmsen">Wallenius Wilhelmsen</option>
                </select>
            </div>
            <!-- Additional vessel fields -->
        </form>
    </div>
    
    <!-- Additional steps... -->
</div>
```

**JavaScript Wizard Logic:**
```javascript
// static/js/stevedoring-wizard.js
class StevedoringWizard {
    constructor() {
        this.currentStep = 1;
        this.maxSteps = 4;
        this.formData = {};
        this.autoFillEngine = new AutoFillEngine();
    }

    async nextStep() {
        if (await this.validateCurrentStep()) {
            this.saveStepData();
            this.showStep(++this.currentStep);
            
            if (this.currentStep === 4) {
                this.generateReviewSummary();
            }
        }
    }

    async validateCurrentStep() {
        // Step-specific validation logic
        switch(this.currentStep) {
            case 1: return this.validateVesselInfo();
            case 2: return this.validateCargoConfig();
            case 3: return this.validateTeamAssignments();
            default: return true;
        }
    }

    async submitWizard() {
        const response = await fetch('/api/v1/stevedoring/operations', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(this.formData)
        });
        
        if (response.ok) {
            window.location.href = '/stevedoring/operations';
        }
    }
}
```

**Dependencies:** Database schema, API endpoints
**Testing:** Form validation, wizard navigation, auto-fill accuracy
**Success Criteria:** Wizard creates complete stevedoring operation

### 2.2 Multi-Ship Operations Dashboard (Week 4)

#### Real-time Maritime Operations Hub
**Deliverables:**
- Live vessel status grid with real-time updates
- Berth occupancy visualization
- Concurrent operations management
- Performance KPIs and alerts

**Dashboard Layout:**
```html
<!-- templates/stevedoring/dashboard.html -->
<div class="operations-dashboard">
    <div class="dashboard-header">
        <h1>Stevedoring Operations Dashboard</h1>
        <div class="quick-stats">
            <div class="stat-card">
                <h3>Active Vessels</h3>
                <span id="active-vessels-count">0</span>
            </div>
            <div class="stat-card">
                <h3>Occupied Berths</h3>
                <span id="occupied-berths-count">0</span>
            </div>
            <div class="stat-card">
                <h3>Daily Discharge Rate</h3>
                <span id="daily-discharge-rate">0</span>
            </div>
        </div>
    </div>
    
    <div class="operations-grid">
        <div class="grid-header">
            <div class="col">Vessel</div>
            <div class="col">Berth</div>
            <div class="col">Operation</div>
            <div class="col">Progress</div>
            <div class="col">Team</div>
            <div class="col">ETA Completion</div>
            <div class="col">Actions</div>
        </div>
        <div id="operations-list">
            <!-- Dynamic vessel operations rows -->
        </div>
    </div>
    
    <div class="berth-visualization">
        <h2>Port Layout & Berth Status</h2>
        <div class="berth-grid">
            <!-- Interactive berth status indicators -->
        </div>
    </div>
</div>
```

**Real-time Updates:**
```javascript
// static/js/operations-dashboard.js
class OperationsDashboard {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.websocket = null;
        this.operations = new Map();
    }

    init() {
        this.loadOperations();
        this.setupWebSocket();
        this.startRefreshTimer();
    }

    async loadOperations() {
        const response = await fetch('/api/v1/stevedoring/operations/active');
        const operations = await response.json();
        this.renderOperations(operations);
    }

    setupWebSocket() {
        if ('WebSocket' in window) {
            this.websocket = new WebSocket(`ws://${window.location.host}/ws/operations`);
            this.websocket.onmessage = (event) => {
                const update = JSON.parse(event.data);
                this.handleRealTimeUpdate(update);
            };
        }
    }

    renderOperations(operations) {
        const container = document.getElementById('operations-list');
        container.innerHTML = operations.map(op => this.createOperationRow(op)).join('');
    }

    createOperationRow(operation) {
        return `
            <div class="operation-row" data-id="${operation.id}">
                <div class="col">${operation.vessel_name}</div>
                <div class="col">${operation.berth}</div>
                <div class="col">${operation.operation_type}</div>
                <div class="col">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${operation.progress}%"></div>
                        <span class="progress-text">${operation.progress}%</span>
                    </div>
                </div>
                <div class="col">${operation.operation_manager}</div>
                <div class="col">${operation.eta_completion}</div>
                <div class="col">
                    <button onclick="viewDetails(${operation.id})">Details</button>
                    <button onclick="editOperation(${operation.id})">Edit</button>
                </div>
            </div>
        `;
    }
}
```

**Dependencies:** API endpoints, wizard completion
**Testing:** Real-time updates, multi-operation handling
**Success Criteria:** Dashboard shows live maritime operations

### 2.3 Cargo Discharge Tracking (Week 5)

#### Real-time Progress Monitoring
**Deliverables:**
- Automobile discharge counter with zone breakdown
- Heavy equipment tracking
- Electric vehicle special handling
- Progress analytics and forecasting

**Tracking Interface:**
```html
<!-- templates/stevedoring/cargo-tracking.html -->
<div class="cargo-tracking">
    <div class="tracking-header">
        <h2>Cargo Discharge Progress - {{operation.vessel_name}}</h2>
        <div class="operation-status">Status: {{operation.status}}</div>
    </div>
    
    <div class="zones-breakdown">
        <div class="zone-card brv">
            <h3>BRV Zone</h3>
            <div class="zone-progress">
                <span class="completed">{{cargo.brv_completed}}</span> / 
                <span class="target">{{cargo.brv_target}}</span>
            </div>
            <div class="progress-bar">
                <div class="fill" style="width: {{(cargo.brv_completed/cargo.brv_target*100)}}%"></div>
            </div>
        </div>
        
        <div class="zone-card zee">
            <h3>ZEE Zone</h3>
            <div class="zone-progress">
                <span class="completed">{{cargo.zee_completed}}</span> / 
                <span class="target">{{cargo.zee_target}}</span>
            </div>
            <div class="progress-bar">
                <div class="fill" style="width: {{(cargo.zee_completed/cargo.zee_target*100)}}%"></div>
            </div>
        </div>
        
        <div class="zone-card sou">
            <h3>SOU Zone</h3>
            <div class="zone-progress">
                <span class="completed">{{cargo.sou_completed}}</span> / 
                <span class="target">{{cargo.sou_target}}</span>
            </div>
            <div class="progress-bar">
                <div class="fill" style="width: {{(cargo.sou_completed/cargo.sou_target*100)}}%"></div>
            </div>
        </div>
    </div>
    
    <div class="quick-update">
        <h3>Quick Progress Update</h3>
        <form id="progress-update-form">
            <div class="update-grid">
                <div class="update-field">
                    <label>BRV Discharged</label>
                    <input type="number" id="brv-update" min="0">
                    <button type="button" onclick="updateZone('brv')">Update</button>
                </div>
                <div class="update-field">
                    <label>ZEE Discharged</label>
                    <input type="number" id="zee-update" min="0">
                    <button type="button" onclick="updateZone('zee')">Update</button>
                </div>
                <div class="update-field">
                    <label>SOU Discharged</label>
                    <input type="number" id="sou-update" min="0">
                    <button type="button" onclick="updateZone('sou')">Update</button>
                </div>
            </div>
        </form>
    </div>
</div>
```

**Progress Update Logic:**
```javascript
// static/js/cargo-tracking.js
class CargoTracker {
    constructor(operationId) {
        this.operationId = operationId;
        this.updateInterval = 10000; // 10 seconds
        this.autoSaveEnabled = true;
    }

    async updateZone(zone, discharged) {
        const updateData = {
            zone: zone,
            discharged: discharged,
            timestamp: new Date().toISOString()
        };

        try {
            const response = await fetch(`/api/v1/stevedoring/cargo/${this.operationId}/update`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(updateData)
            });

            if (response.ok) {
                const result = await response.json();
                this.updateProgressDisplay(result);
                this.notifyTeam(zone, discharged);
            }
        } catch (error) {
            console.error('Failed to update cargo progress:', error);
            this.showErrorMessage('Update failed. Changes saved locally.');
            this.saveOfflineUpdate(updateData);
        }
    }

    updateProgressDisplay(data) {
        // Update zone progress bars
        document.querySelector('.brv .completed').textContent = data.brv_completed;
        document.querySelector('.zee .completed').textContent = data.zee_completed;
        document.querySelector('.sou .completed').textContent = data.sou_completed;
        
        // Update progress bars
        this.updateProgressBar('.brv', data.brv_completed, data.brv_target);
        this.updateProgressBar('.zee', data.zee_completed, data.zee_target);
        this.updateProgressBar('.sou', data.sou_completed, data.sou_target);
    }

    async forecastCompletion() {
        const response = await fetch(`/api/v1/stevedoring/analytics/${this.operationId}/forecast`);
        const forecast = await response.json();
        return forecast;
    }
}
```

**Dependencies:** Dashboard completion, API endpoints
**Testing:** Progress updates, offline sync, data accuracy
**Success Criteria:** Real-time cargo tracking with zone breakdown

---

## PHASE 3: OPERATIONS & TEAM MANAGEMENT
**Duration: Week 6-8 (21 days)**
**Critical Path Priority: MEDIUM**

### 3.1 Team Assignment System (Week 6)

#### Stevedoring Crew Management
**Deliverables:**
- Operation manager assignment
- Auto operations lead/assistant tracking
- Heavy operations team management
- TICO transportation coordination

**Team Management Interface:**
```html
<!-- templates/stevedoring/team-management.html -->
<div class="team-management">
    <div class="team-header">
        <h2>Team Assignments - {{operation.vessel_name}}</h2>
        <button class="btn-primary" onclick="openTeamAssignmentModal()">Assign Team</button>
    </div>
    
    <div class="team-structure">
        <div class="management-level">
            <h3>Management</h3>
            <div class="role-card manager">
                <div class="role-title">Operation Manager</div>
                <div class="assigned-person">{{team.operation_manager or 'Unassigned'}}</div>
                <button onclick="assignRole('manager')">{{team.operation_manager and 'Change' or 'Assign'}}</button>
            </div>
        </div>
        
        <div class="operations-level">
            <h3>Operations Teams</h3>
            <div class="team-section auto-ops">
                <h4>Auto Operations</h4>
                <div class="role-card">
                    <div class="role-title">Lead</div>
                    <div class="assigned-person">{{team.auto_ops_lead or 'Unassigned'}}</div>
                    <button onclick="assignRole('auto_lead')">Assign</button>
                </div>
                <div class="role-card">
                    <div class="role-title">Assistant</div>
                    <div class="assigned-person">{{team.auto_ops_assistant or 'Unassigned'}}</div>
                    <button onclick="assignRole('auto_assistant')">Assign</button>
                </div>
            </div>
            
            <div class="team-section heavy-ops">
                <h4>Heavy Operations</h4>
                <div class="role-card">
                    <div class="role-title">Lead</div>
                    <div class="assigned-person">{{team.heavy_ops_lead or 'Unassigned'}}</div>
                    <button onclick="assignRole('heavy_lead')">Assign</button>
                </div>
                <div class="role-card">
                    <div class="role-title">Assistant</div>
                    <div class="assigned-person">{{team.heavy_ops_assistant or 'Unassigned'}}</div>
                    <button onclick="assignRole('heavy_assistant')">Assign</button>
                </div>
            </div>
        </div>
        
        <div class="drivers-section">
            <h3>Driver Management</h3>
            <div class="driver-stats">
                <div class="stat">
                    <label>Total Drivers</label>
                    <input type="number" id="total-drivers" value="{{team.total_drivers}}">
                </div>
                <div class="stat">
                    <label>TICO Vans</label>
                    <input type="number" id="tico-vans" value="{{tico.vans_assigned}}">
                </div>
                <div class="stat">
                    <label>Station Wagons</label>
                    <input type="number" id="station-wagons" value="{{tico.station_wagons_assigned}}">
                </div>
            </div>
        </div>
    </div>
</div>
```

**Team Assignment Logic:**
```javascript
// static/js/team-management.js
class TeamManager {
    constructor(operationId) {
        this.operationId = operationId;
        this.availablePersonnel = [];
        this.currentAssignments = {};
    }

    async loadAvailablePersonnel() {
        const response = await fetch('/api/v1/stevedoring/personnel/available');
        this.availablePersonnel = await response.json();
    }

    async assignRole(role, personId) {
        const assignmentData = {
            operation_id: this.operationId,
            role: role,
            person_id: personId,
            assigned_at: new Date().toISOString()
        };

        const response = await fetch('/api/v1/stevedoring/teams/assign', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(assignmentData)
        });

        if (response.ok) {
            const result = await response.json();
            this.updateTeamDisplay(result);
            this.notifyAssignment(role, personId);
        }
    }

    calculateTICORequirements(totalDrivers) {
        // TICO calculation logic
        const driversPerVan = 15;
        const driversPerWagon = 8;
        
        const recommendedVans = Math.ceil(totalDrivers * 0.7 / driversPerVan);
        const recommendedWagons = Math.ceil(totalDrivers * 0.3 / driversPerWagon);
        
        return {
            vans: recommendedVans,
            wagons: recommendedWagons
        };
    }
}
```

**Dependencies:** Database models, user management
**Testing:** Assignment validation, role conflicts
**Success Criteria:** Complete team assignment workflow

### 3.2 TICO Transportation Management (Week 7)

#### Driver Transport Coordination
**Deliverables:**
- Van and station wagon allocation
- Driver transportation scheduling
- Route optimization for personnel transport
- Real-time vehicle tracking

**TICO Management Interface:**
```html
<!-- templates/stevedoring/tico-management.html -->
<div class="tico-management">
    <div class="tico-header">
        <h2>TICO Transportation - {{operation.vessel_name}}</h2>
        <div class="transport-summary">
            <div class="summary-item">
                <span class="label">Total Drivers:</span>
                <span class="value">{{team.total_drivers}}</span>
            </div>
            <div class="summary-item">
                <span class="label">Vans Assigned:</span>
                <span class="value">{{tico.vans_assigned}}</span>
            </div>
            <div class="summary-item">
                <span class="label">Station Wagons:</span>
                <span class="value">{{tico.station_wagons_assigned}}</span>
            </div>
        </div>
    </div>
    
    <div class="vehicle-allocation">
        <h3>Vehicle Allocation</h3>
        <div class="allocation-grid">
            <div class="vehicle-type">
                <h4>TICO Vans (15 drivers each)</h4>
                <div class="vehicle-counter">
                    <button onclick="adjustVehicles('vans', -1)">-</button>
                    <span id="vans-count">{{tico.vans_assigned}}</span>
                    <button onclick="adjustVehicles('vans', 1)">+</button>
                </div>
                <div class="capacity">Capacity: <span id="vans-capacity">{{tico.vans_assigned * 15}}</span> drivers</div>
            </div>
            
            <div class="vehicle-type">
                <h4>Station Wagons (8 drivers each)</h4>
                <div class="vehicle-counter">
                    <button onclick="adjustVehicles('wagons', -1)">-</button>
                    <span id="wagons-count">{{tico.station_wagons_assigned}}</span>
                    <button onclick="adjustVehicles('wagons', 1)">+</button>
                </div>
                <div class="capacity">Capacity: <span id="wagons-capacity">{{tico.station_wagons_assigned * 8}}</span> drivers</div>
            </div>
        </div>
        
        <div class="allocation-summary">
            <div class="total-capacity">
                Total Transport Capacity: <span id="total-capacity">0</span> drivers
            </div>
            <div class="capacity-status" id="capacity-status">
                <!-- Dynamic status based on driver count vs capacity -->
            </div>
        </div>
    </div>
    
    <div class="transport-schedule">
        <h3>Transport Schedule</h3>
        <div class="schedule-grid">
            <div class="schedule-header">
                <div>Time</div>
                <div>Vehicle</div>
                <div>Route</div>
                <div>Drivers</div>
                <div>Status</div>
            </div>
            <div id="transport-schedules">
                <!-- Dynamic transport schedule rows -->
            </div>
        </div>
        <button class="btn-primary" onclick="addTransportSchedule()">Add Schedule</button>
    </div>
</div>
```

**TICO Management Logic:**
```javascript
// static/js/tico-management.js
class TICOManager {
    constructor(operationId) {
        this.operationId = operationId;
        this.vanCapacity = 15;
        this.wagonCapacity = 8;
        this.currentAllocation = {
            vans: 0,
            wagons: 0
        };
    }

    adjustVehicles(type, change) {
        const currentCount = this.currentAllocation[type];
        const newCount = Math.max(0, currentCount + change);
        
        this.currentAllocation[type] = newCount;
        this.updateDisplay();
        this.saveAllocation();
    }

    updateDisplay() {
        document.getElementById('vans-count').textContent = this.currentAllocation.vans;
        document.getElementById('wagons-count').textContent = this.currentAllocation.wagons;
        
        const vansCapacity = this.currentAllocation.vans * this.vanCapacity;
        const wagonsCapacity = this.currentAllocation.wagons * this.wagonCapacity;
        const totalCapacity = vansCapacity + wagonsCapacity;
        
        document.getElementById('vans-capacity').textContent = vansCapacity;
        document.getElementById('wagons-capacity').textContent = wagonsCapacity;
        document.getElementById('total-capacity').textContent = totalCapacity;
        
        this.updateCapacityStatus(totalCapacity);
    }

    updateCapacityStatus(totalCapacity) {
        const totalDrivers = parseInt(document.querySelector('[data-total-drivers]').textContent) || 0;
        const statusElement = document.getElementById('capacity-status');
        
        if (totalCapacity >= totalDrivers) {
            statusElement.className = 'capacity-adequate';
            statusElement.textContent = 'Adequate transport capacity';
        } else {
            statusElement.className = 'capacity-insufficient';
            statusElement.textContent = `Insufficient capacity: ${totalDrivers - totalCapacity} drivers need transport`;
        }
    }

    async saveAllocation() {
        const allocationData = {
            operation_id: this.operationId,
            vans_assigned: this.currentAllocation.vans,
            station_wagons_assigned: this.currentAllocation.wagons,
            updated_at: new Date().toISOString()
        };

        try {
            const response = await fetch(`/api/v1/stevedoring/tico/${this.operationId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(allocationData)
            });

            if (!response.ok) {
                throw new Error('Failed to save allocation');
            }
        } catch (error) {
            console.error('TICO allocation save failed:', error);
            this.showErrorMessage('Failed to save allocation. Changes stored locally.');
        }
    }

    generateOptimalAllocation(totalDrivers) {
        // Optimization algorithm for vehicle allocation
        let bestAllocation = { vans: 0, wagons: 0, efficiency: 0 };
        
        for (let vans = 0; vans <= Math.ceil(totalDrivers / this.vanCapacity); vans++) {
            for (let wagons = 0; wagons <= Math.ceil(totalDrivers / this.wagonCapacity); wagons++) {
                const capacity = (vans * this.vanCapacity) + (wagons * this.wagonCapacity);
                
                if (capacity >= totalDrivers) {
                    const efficiency = totalDrivers / capacity;
                    const cost = vans * 1.5 + wagons * 1.0; // Van cost factor
                    const score = efficiency / cost;
                    
                    if (score > bestAllocation.efficiency) {
                        bestAllocation = { vans, wagons, efficiency: score };
                    }
                }
            }
        }
        
        return bestAllocation;
    }
}
```

**Dependencies:** Team management, database updates
**Testing:** Allocation calculations, optimization algorithms
**Success Criteria:** Efficient driver transportation planning

### 3.3 Document Management & Auto-fill (Week 8)

#### Maritime Paperwork Automation
**Deliverables:**
- PDF/CSV/TXT document processing
- Auto-fill functionality for vessel information
- Document template generation
- Compliance checking

**Document Processing Interface:**
```html
<!-- templates/stevedoring/document-management.html -->
<div class="document-management">
    <div class="document-header">
        <h2>Document Management & Auto-fill</h2>
        <div class="upload-section">
            <div class="upload-zone" id="document-upload-zone">
                <div class="upload-icon">📄</div>
                <div class="upload-text">
                    <p>Drop documents here or click to upload</p>
                    <small>Supports PDF, CSV, TXT files</small>
                </div>
                <input type="file" id="document-upload" multiple accept=".pdf,.csv,.txt" hidden>
            </div>
        </div>
    </div>
    
    <div class="processing-results">
        <h3>Document Processing Results</h3>
        <div id="extraction-results">
            <!-- Dynamic extraction results -->
        </div>
    </div>
    
    <div class="auto-fill-templates">
        <h3>Document Templates</h3>
        <div class="template-grid">
            <div class="template-card">
                <h4>Bill of Lading</h4>
                <p>Generate bill of lading with extracted vessel information</p>
                <button onclick="generateTemplate('bill_of_lading')">Generate</button>
            </div>
            <div class="template-card">
                <h4>Cargo Manifest</h4>
                <p>Create cargo manifest from discharge data</p>
                <button onclick="generateTemplate('cargo_manifest')">Generate</button>
            </div>
            <div class="template-card">
                <h4>Operation Report</h4>
                <p>Comprehensive operation summary report</p>
                <button onclick="generateTemplate('operation_report')">Generate</button>
            </div>
        </div>
    </div>
</div>
```

**Document Processing Engine:**
```javascript
// static/js/document-processor.js
class DocumentProcessor {
    constructor() {
        this.supportedTypes = ['pdf', 'csv', 'txt'];
        this.extractionPatterns = {
            vesselName: /vessel\s*name[:\s]+([a-zA-Z0-9\s]+)/i,
            imoNumber: /imo[:\s]+(\d{7})/i,
            shippingLine: /shipping\s*line[:\s]+([a-zA-Z\s&]+)/i,
            totalVehicles: /total\s*vehicles[:\s]+(\d+)/i,
            automobiles: /automobiles[:\s]+(\d+)/i,
            operationDate: /operation\s*date[:\s]+(\d{4}-\d{2}-\d{2}|\d{2}\/\d{2}\/\d{4})/i
        };
    }

    async processDocument(file) {
        const fileType = file.name.split('.').pop().toLowerCase();
        
        if (!this.supportedTypes.includes(fileType)) {
            throw new Error(`Unsupported file type: ${fileType}`);
        }

        let extractedText = '';
        
        switch (fileType) {
            case 'pdf':
                extractedText = await this.processPDF(file);
                break;
            case 'csv':
                extractedText = await this.processCSV(file);
                break;
            case 'txt':
                extractedText = await this.processTXT(file);
                break;
        }

        return this.extractData(extractedText);
    }

    async processPDF(file) {
        // Use PDF.js or server-side processing
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/v1/stevedoring/documents/extract-pdf', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        return result.text;
    }

    async processCSV(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsText(file);
        });
    }

    async processTXT(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsText(file);
        });
    }

    extractData(text) {
        const extractedData = {};
        
        for (const [field, pattern] of Object.entries(this.extractionPatterns)) {
            const match = text.match(pattern);
            if (match) {
                extractedData[field] = match[1].trim();
            }
        }

        // Additional processing for specific data types
        if (extractedData.operationDate) {
            extractedData.operationDate = this.standardizeDate(extractedData.operationDate);
        }

        if (extractedData.totalVehicles) {
            extractedData.totalVehicles = parseInt(extractedData.totalVehicles);
        }

        return extractedData;
    }

    standardizeDate(dateString) {
        // Convert various date formats to YYYY-MM-DD
        const patterns = [
            /(\d{4})-(\d{2})-(\d{2})/,
            /(\d{2})\/(\d{2})\/(\d{4})/,
            /(\d{2})-(\d{2})-(\d{4})/
        ];

        for (const pattern of patterns) {
            const match = dateString.match(pattern);
            if (match) {
                if (pattern.source.includes('\\d{4}') && pattern.source.indexOf('\\d{4}') === 1) {
                    // YYYY-MM-DD format
                    return `${match[1]}-${match[2]}-${match[3]}`;
                } else {
                    // MM/DD/YYYY or similar
                    return `${match[3]}-${match[1].padStart(2, '0')}-${match[2].padStart(2, '0')}`;
                }
            }
        }

        return dateString;
    }

    async autoFillWizard(extractedData) {
        // Fill wizard fields with extracted data
        for (const [field, value] of Object.entries(extractedData)) {
            const element = document.getElementById(field);
            if (element) {
                element.value = value;
                element.dispatchEvent(new Event('change'));
            }
        }

        // Show confirmation dialog
        const confirmed = await this.showConfirmationDialog(extractedData);
        return confirmed;
    }

    showConfirmationDialog(data) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'auto-fill-confirmation';
            modal.innerHTML = `
                <div class="modal-content">
                    <h3>Confirm Auto-fill Data</h3>
                    <div class="extracted-data">
                        ${Object.entries(data).map(([key, value]) => 
                            `<div class="data-row">
                                <span class="key">${key}:</span>
                                <span class="value">${value}</span>
                            </div>`
                        ).join('')}
                    </div>
                    <div class="modal-actions">
                        <button onclick="confirmAutoFill(true)">Accept</button>
                        <button onclick="confirmAutoFill(false)">Review</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            window.confirmAutoFill = (accepted) => {
                document.body.removeChild(modal);
                resolve(accepted);
            };
        });
    }
}
```

**Dependencies:** File upload system, extraction APIs
**Testing:** Document parsing accuracy, auto-fill validation
**Success Criteria:** Accurate document data extraction and form filling

---

## PHASE 4: ADVANCED FEATURES & OPTIMIZATION
**Duration: Week 9-12 (28 days)**
**Critical Path Priority: LOW**

### 4.1 Analytics & Reporting Dashboard (Week 9-10)

#### Maritime Performance Analytics
**Deliverables:**
- KPI dashboard with maritime metrics
- Trend analysis and forecasting
- Performance comparison reports
- Export capabilities for compliance

**Analytics Dashboard:**
```html
<!-- templates/stevedoring/analytics.html -->
<div class="analytics-dashboard">
    <div class="analytics-header">
        <h1>Maritime Operations Analytics</h1>
        <div class="date-range-selector">
            <input type="date" id="start-date">
            <span>to</span>
            <input type="date" id="end-date">
            <button onclick="updateAnalytics()">Update</button>
        </div>
    </div>
    
    <div class="kpi-grid">
        <div class="kpi-card">
            <h3>Average Discharge Rate</h3>
            <div class="kpi-value" id="avg-discharge-rate">0</div>
            <div class="kpi-unit">vehicles/hour</div>
            <div class="kpi-trend" id="discharge-rate-trend">↑ 5.2%</div>
        </div>
        
        <div class="kpi-card">
            <h3>Operation Efficiency</h3>
            <div class="kpi-value" id="operation-efficiency">0</div>
            <div class="kpi-unit">%</div>
            <div class="kpi-trend" id="efficiency-trend">↑ 2.1%</div>
        </div>
        
        <div class="kpi-card">
            <h3>Berth Utilization</h3>
            <div class="kpi-value" id="berth-utilization">0</div>
            <div class="kpi-unit">%</div>
            <div class="kpi-trend" id="berth-trend">→ 0.3%</div>
        </div>
        
        <div class="kpi-card">
            <h3>Average Turnaround</h3>
            <div class="kpi-value" id="avg-turnaround">0</div>
            <div class="kpi-unit">hours</div>
            <div class="kpi-trend" id="turnaround-trend">↓ 1.8%</div>
        </div>
    </div>
    
    <div class="charts-section">
        <div class="chart-container">
            <h3>Daily Discharge Progress</h3>
            <canvas id="discharge-progress-chart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Zone Performance Comparison</h3>
            <canvas id="zone-performance-chart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Vessel Type Analysis</h3>
            <canvas id="vessel-type-chart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Monthly Trends</h3>
            <canvas id="monthly-trends-chart"></canvas>
        </div>
    </div>
    
    <div class="reports-section">
        <h3>Generate Reports</h3>
        <div class="report-options">
            <button onclick="generateReport('daily')">Daily Report</button>
            <button onclick="generateReport('weekly')">Weekly Summary</button>
            <button onclick="generateReport('monthly')">Monthly Analysis</button>
            <button onclick="generateReport('compliance')">Compliance Report</button>
        </div>
    </div>
</div>
```

**Analytics Engine:**
```javascript
// static/js/maritime-analytics.js
class MaritimeAnalytics {
    constructor() {
        this.charts = {};
        this.kpiData = {};
        this.dateRange = {
            start: null,
            end: null
        };
    }

    async loadAnalyticsData(startDate, endDate) {
        const response = await fetch(`/api/v1/stevedoring/analytics?start=${startDate}&end=${endDate}`);
        const data = await response.json();
        
        this.kpiData = data.kpis;
        this.updateKPIDisplay();
        this.updateCharts(data.charts);
        
        return data;
    }

    updateKPIDisplay() {
        const kpis = [
            { id: 'avg-discharge-rate', value: this.kpiData.averageDischargeRate, format: 'number' },
            { id: 'operation-efficiency', value: this.kpiData.operationEfficiency, format: 'percentage' },
            { id: 'berth-utilization', value: this.kpiData.berthUtilization, format: 'percentage' },
            { id: 'avg-turnaround', value: this.kpiData.averageTurnaround, format: 'decimal' }
        ];

        kpis.forEach(kpi => {
            const element = document.getElementById(kpi.id);
            if (element) {
                let formattedValue = kpi.value;
                
                switch (kpi.format) {
                    case 'percentage':
                        formattedValue = Math.round(kpi.value * 100);
                        break;
                    case 'decimal':
                        formattedValue = kpi.value.toFixed(1);
                        break;
                    case 'number':
                        formattedValue = Math.round(kpi.value);
                        break;
                }
                
                element.textContent = formattedValue;
            }
        });
    }

    initializeCharts() {
        // Initialize Chart.js charts
        this.charts.dischargeProgress = new Chart(
            document.getElementById('discharge-progress-chart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Vehicles Discharged',
                        data: [],
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Vehicles'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        }
                    }
                }
            }
        );

        this.charts.zonePerformance = new Chart(
            document.getElementById('zone-performance-chart').getContext('2d'),
            {
                type: 'bar',
                data: {
                    labels: ['BRV', 'ZEE', 'SOU'],
                    datasets: [{
                        label: 'Efficiency %',
                        data: [],
                        backgroundColor: ['#4CAF50', '#FF9800', '#F44336']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Efficiency %'
                            }
                        }
                    }
                }
            }
        );

        // Additional chart initializations...
    }

    async generateReport(reportType) {
        const reportData = {
            type: reportType,
            dateRange: this.dateRange,
            includeCharts: true,
            format: 'pdf'
        };

        const response = await fetch('/api/v1/stevedoring/reports/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(reportData)
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `maritime-${reportType}-report-${new Date().toISOString().split('T')[0]}.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
        }
    }

    calculateKPIs(operations) {
        const kpis = {
            averageDischargeRate: 0,
            operationEfficiency: 0,
            berthUtilization: 0,
            averageTurnaround: 0
        };

        if (operations.length === 0) return kpis;

        // Calculate average discharge rate
        const totalVehicles = operations.reduce((sum, op) => sum + (op.cargo?.total_vehicles || 0), 0);
        const totalHours = operations.reduce((sum, op) => {
            const start = new Date(op.shift_start);
            const end = new Date(op.shift_end);
            return sum + ((end - start) / (1000 * 60 * 60));
        }, 0);
        
        kpis.averageDischargeRate = totalHours > 0 ? totalVehicles / totalHours : 0;

        // Calculate operation efficiency
        const completedOnTime = operations.filter(op => 
            new Date(op.actual_completion) <= new Date(op.target_completion)
        ).length;
        kpis.operationEfficiency = operations.length > 0 ? completedOnTime / operations.length : 0;

        // Calculate berth utilization
        const berthHours = operations.reduce((sum, op) => {
            const start = new Date(op.berth_arrival);
            const end = new Date(op.berth_departure);
            return sum + ((end - start) / (1000 * 60 * 60));
        }, 0);
        const availableBerthHours = this.dateRange.days * 24 * this.getAvailableBerthCount();
        kpis.berthUtilization = availableBerthHours > 0 ? berthHours / availableBerthHours : 0;

        // Calculate average turnaround time
        const turnaroundTimes = operations.map(op => {
            const arrival = new Date(op.berth_arrival);
            const departure = new Date(op.berth_departure);
            return (departure - arrival) / (1000 * 60 * 60);
        });
        kpis.averageTurnaround = turnaroundTimes.reduce((sum, time) => sum + time, 0) / turnaroundTimes.length;

        return kpis;
    }
}
```

**Dependencies:** Data collection, charting libraries
**Testing:** Report generation, data accuracy
**Success Criteria:** Comprehensive maritime analytics

### 4.2 Advanced PWA Features (Week 11)

#### Enhanced Offline Capabilities
**Deliverables:**
- Background sync for maritime data
- Push notifications for operation updates
- Advanced caching strategies
- Conflict resolution for offline edits

**Enhanced Service Worker:**
```javascript
// static/sw-enhanced.js
const CACHE_VERSION = 'v2.0.0';
const STATIC_CACHE = `stevedoring-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `stevedoring-dynamic-${CACHE_VERSION}`;
const API_CACHE = `stevedoring-api-${CACHE_VERSION}`;

const STATIC_ASSETS = [
    '/',
    '/static/css/app.css',
    '/static/js/app.js',
    '/static/js/stevedoring-wizard.js',
    '/static/js/operations-dashboard.js',
    '/static/js/cargo-tracking.js',
    '/static/js/team-management.js',
    '/static/js/maritime-analytics.js',
    '/offline'
];

const API_ENDPOINTS = [
    '/api/v1/stevedoring/operations',
    '/api/v1/stevedoring/cargo',
    '/api/v1/stevedoring/teams',
    '/api/v1/stevedoring/analytics'
];

self.addEventListener('install', event => {
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS)),
            caches.open(API_CACHE),
            caches.open(DYNAMIC_CACHE)
        ])
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName.startsWith('stevedoring-') && 
                        ![STATIC_CACHE, DYNAMIC_CACHE, API_CACHE].includes(cacheName)) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Handle API requests
    if (url.pathname.startsWith('/api/v1/stevedoring/')) {
        event.respondWith(handleAPIRequest(request));
        return;
    }

    // Handle navigation requests
    if (request.mode === 'navigate') {
        event.respondWith(handleNavigationRequest(request));
        return;
    }

    // Handle static assets
    event.respondWith(handleStaticRequest(request));
});

async function handleAPIRequest(request) {
    const cache = await caches.open(API_CACHE);
    
    try {
        // Try network first for API requests
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful API responses
            const responseClone = networkResponse.clone();
            cache.put(request, responseClone);
        }
        
        return networkResponse;
    } catch (error) {
        // Network failed, try cache
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            // Add header to indicate cached response
            const response = cachedResponse.clone();
            response.headers.set('X-Served-By', 'ServiceWorker-Cache');
            return response;
        }
        
        // Return offline response for API
        return new Response(
            JSON.stringify({
                error: 'Offline',
                message: 'This request requires an internet connection'
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

async function handleNavigationRequest(request) {
    try {
        return await fetch(request);
    } catch (error) {
        const cache = await caches.open(STATIC_CACHE);
        return cache.match('/offline');
    }
}

async function handleStaticRequest(request) {
    const cache = await caches.open(STATIC_CACHE);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        const dynamicCache = await caches.open(DYNAMIC_CACHE);
        dynamicCache.put(request, networkResponse.clone());
        return networkResponse;
    } catch (error) {
        // Return fallback for failed requests
        return cache.match('/offline');
    }
}

// Background sync for offline data
self.addEventListener('sync', event => {
    if (event.tag === 'stevedoring-sync') {
        event.waitUntil(syncStevedoringData());
    }
});

async function syncStevedoringData() {
    // Sync offline operations data
    const db = await openIndexedDB();
    const offlineOperations = await getOfflineOperations(db);
    
    for (const operation of offlineOperations) {
        try {
            await fetch('/api/v1/stevedoring/operations/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(operation)
            });
            
            // Remove from offline storage after successful sync
            await removeOfflineOperation(db, operation.id);
        } catch (error) {
            console.error('Failed to sync operation:', operation.id, error);
        }
    }
}

// Push notifications for operation updates
self.addEventListener('push', event => {
    const data = event.data.json();
    
    const options = {
        body: data.body,
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            operationId: data.operationId,
            action: data.action
        },
        actions: [
            {
                action: 'view',
                title: 'View Operation'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.action === 'view') {
        const operationId = event.notification.data.operationId;
        event.waitUntil(
            clients.openWindow(`/stevedoring/operations/${operationId}`)
        );
    }
});
```

**Background Sync Manager:**
```javascript
// static/js/sync-manager.js
class StevedoringSyncManager {
    constructor() {
        this.dbName = 'StevedoringOfflineDB';
        this.version = 1;
        this.db = null;
        this.syncInProgress = false;
    }

    async init() {
        this.db = await this.openDatabase();
        
        // Register for background sync
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then(registration => {
                this.registration = registration;
            });
        }
        
        // Listen for online events to trigger sync
        window.addEventListener('online', () => {
            this.syncWhenOnline();
        });
    }

    async openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Operations store
                if (!db.objectStoreNames.contains('operations')) {
                    const operationsStore = db.createObjectStore('operations', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    operationsStore.createIndex('syncStatus', 'syncStatus');
                    operationsStore.createIndex('timestamp', 'timestamp');
                }
                
                // Cargo updates store
                if (!db.objectStoreNames.contains('cargo_updates')) {
                    const cargoStore = db.createObjectStore('cargo_updates', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    cargoStore.createIndex('operationId', 'operationId');
                    cargoStore.createIndex('syncStatus', 'syncStatus');
                }
                
                // Team assignments store
                if (!db.objectStoreNames.contains('team_assignments')) {
                    const teamStore = db.createObjectStore('team_assignments', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    teamStore.createIndex('operationId', 'operationId');
                    teamStore.createIndex('syncStatus', 'syncStatus');
                }
            };
        });
    }

    async saveOfflineOperation(operation) {
        const transaction = this.db.transaction(['operations'], 'readwrite');
        const store = transaction.objectStore('operations');
        
        const operationData = {
            ...operation,
            syncStatus: 'pending',
            timestamp: new Date().toISOString(),
            source: 'offline'
        };
        
        return store.add(operationData);
    }

    async saveOfflineCargoUpdate(operationId, cargoData) {
        const transaction = this.db.transaction(['cargo_updates'], 'readwrite');
        const store = transaction.objectStore('cargo_updates');
        
        const updateData = {
            operationId,
            cargoData,
            syncStatus: 'pending',
            timestamp: new Date().toISOString()
        };
        
        return store.add(updateData);
    }

    async syncWhenOnline() {
        if (this.syncInProgress || !navigator.onLine) {
            return;
        }
        
        this.syncInProgress = true;
        
        try {
            await this.syncOperations();
            await this.syncCargoUpdates();
            await this.syncTeamAssignments();
            
            this.showSyncSuccess();
        } catch (error) {
            console.error('Sync failed:', error);
            this.showSyncError();
        } finally {
            this.syncInProgress = false;
        }
    }

    async syncOperations() {
        const transaction = this.db.transaction(['operations'], 'readwrite');
        const store = transaction.objectStore('operations');
        const index = store.index('syncStatus');
        
        const pendingOperations = await this.getIndexedData(index, 'pending');
        
        for (const operation of pendingOperations) {
            try {
                const response = await fetch('/api/v1/stevedoring/operations/sync', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(operation)
                });
                
                if (response.ok) {
                    // Update sync status
                    operation.syncStatus = 'completed';
                    operation.syncedAt = new Date().toISOString();
                    store.put(operation);
                } else {
                    throw new Error(`Sync failed with status: ${response.status}`);
                }
            } catch (error) {
                console.error('Failed to sync operation:', operation.id, error);
                operation.syncStatus = 'failed';
                operation.syncError = error.message;
                store.put(operation);
            }
        }
    }

    async handleConflict(localData, serverData) {
        // Conflict resolution strategy
        const conflictResolution = {
            strategy: 'merge', // 'merge', 'local_wins', 'server_wins', 'user_choice'
            resolvedData: null
        };
        
        switch (conflictResolution.strategy) {
            case 'merge':
                conflictResolution.resolvedData = this.mergeData(localData, serverData);
                break;
            case 'local_wins':
                conflictResolution.resolvedData = localData;
                break;
            case 'server_wins':
                conflictResolution.resolvedData = serverData;
                break;
            case 'user_choice':
                conflictResolution.resolvedData = await this.showConflictDialog(localData, serverData);
                break;
        }
        
        return conflictResolution.resolvedData;
    }

    mergeData(local, server) {
        // Intelligent merge strategy for stevedoring data
        const merged = { ...server };
        
        // Merge cargo progress (take highest values)
        if (local.cargo && server.cargo) {
            merged.cargo = {
                ...server.cargo,
                brv_completed: Math.max(local.cargo.brv_completed || 0, server.cargo.brv_completed || 0),
                zee_completed: Math.max(local.cargo.zee_completed || 0, server.cargo.zee_completed || 0),
                sou_completed: Math.max(local.cargo.sou_completed || 0, server.cargo.sou_completed || 0)
            };
        }
        
        // Preserve local team assignments if server doesn't have them
        if (local.team && !server.team) {
            merged.team = local.team;
        }
        
        // Take most recent timestamp
        merged.updated_at = new Date(Math.max(
            new Date(local.updated_at || 0),
            new Date(server.updated_at || 0)
        )).toISOString();
        
        return merged;
    }

    getIndexedData(index, value) {
        return new Promise((resolve, reject) => {
            const request = index.getAll(value);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    showSyncSuccess() {
        const notification = document.createElement('div');
        notification.className = 'sync-notification success';
        notification.textContent = 'Data synchronized successfully';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showSyncError() {
        const notification = document.createElement('div');
        notification.className = 'sync-notification error';
        notification.textContent = 'Sync failed. Will retry when connection improves.';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}
```

**Dependencies:** IndexedDB setup, service worker registration
**Testing:** Offline functionality, sync accuracy, conflict resolution
**Success Criteria:** Robust offline operation with seamless sync

### 4.3 Performance Optimization & Testing (Week 12)

#### Production Readiness
**Deliverables:**
- Performance optimization
- Comprehensive testing suite
- Security hardening
- Deployment pipeline enhancement

**Performance Monitoring:**
```javascript
// static/js/performance-monitor.js
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            loadTime: 0,
            renderTime: 0,
            apiResponseTimes: {},
            memoryUsage: 0,
            cacheHitRate: 0
        };
        this.thresholds = {
            loadTime: 3000, // 3 seconds
            renderTime: 1000, // 1 second
            apiResponse: 2000, // 2 seconds
            memoryUsage: 50 * 1024 * 1024 // 50MB
        };
    }

    startMonitoring() {
        this.monitorPageLoad();
        this.monitorAPIRequests();
        this.monitorMemoryUsage();
        this.monitorCachePerformance();
    }

    monitorPageLoad() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            this.metrics.loadTime = navigation.loadEventEnd - navigation.loadEventStart;
            
            if (this.metrics.loadTime > this.thresholds.loadTime) {
                this.reportPerformanceIssue('slow_load', this.metrics.loadTime);
            }
        });
    }

    monitorAPIRequests() {
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            const startTime = performance.now();
            const response = await originalFetch(...args);
            const endTime = performance.now();
            
            const url = args[0];
            const responseTime = endTime - startTime;
            
            this.metrics.apiResponseTimes[url] = responseTime;
            
            if (responseTime > this.thresholds.apiResponse) {
                this.reportPerformanceIssue('slow_api', { url, responseTime });
            }
            
            return response;
        };
    }

    monitorMemoryUsage() {
        if ('memory' in performance) {
            setInterval(() => {
                this.metrics.memoryUsage = performance.memory.usedJSHeapSize;
                
                if (this.metrics.memoryUsage > this.thresholds.memoryUsage) {
                    this.reportPerformanceIssue('high_memory', this.metrics.memoryUsage);
                }
            }, 30000); // Check every 30 seconds
        }
    }

    async reportPerformanceIssue(type, data) {
        const report = {
            type,
            data,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        try {
            await fetch('/api/v1/monitoring/performance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(report)
            });
        } catch (error) {
            console.warn('Failed to report performance issue:', error);
        }
    }

    generatePerformanceReport() {
        return {
            ...this.metrics,
            timestamp: new Date().toISOString(),
            recommendations: this.generateRecommendations()
        };
    }

    generateRecommendations() {
        const recommendations = [];
        
        if (this.metrics.loadTime > this.thresholds.loadTime) {
            recommendations.push('Consider enabling compression and optimizing images');
        }
        
        if (Object.values(this.metrics.apiResponseTimes).some(time => time > this.thresholds.apiResponse)) {
            recommendations.push('API response times are slow - consider caching or optimization');
        }
        
        if (this.metrics.memoryUsage > this.thresholds.memoryUsage) {
            recommendations.push('High memory usage detected - check for memory leaks');
        }
        
        return recommendations;
    }
}
```

**Testing Suite Configuration:**
```python
# tests/test_stevedoring_integration.py
import pytest
import json
from datetime import datetime, timedelta
from app import app, db
from models.models.user import User
from models.models.vessel import Vessel

class TestStevedoringIntegration:
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                self.create_test_data()
                yield client
                db.drop_all()
    
    def create_test_data(self):
        # Create test users
        manager = User(
            email='manager@test.com',
            username='manager',
            password_hash='test_hash',
            role='manager',
            is_active=True
        )
        
        worker = User(
            email='worker@test.com',
            username='worker',
            password_hash='test_hash',
            role='worker',
            is_active=True
        )
        
        db.session.add_all([manager, worker])
        
        # Create test vessel
        vessel = Vessel(
            name='Test Vessel',
            imo_number='1234567',
            vessel_type='Car Carrier',
            flag='Test Flag',
            status='active'
        )
        
        db.session.add(vessel)
        db.session.commit()
    
    def test_wizard_flow(self, client):
        """Test complete 4-step wizard flow"""
        
        # Login as manager
        response = client.post('/auth/login', data={
            'email': 'manager@test.com',
            'password': 'test_password'
        })
        
        # Start wizard
        response = client.get('/stevedoring/wizard')
        assert response.status_code == 200
        
        # Step 1: Vessel Information
        step1_data = {
            'vesselName': 'Test Vessel',
            'shippingLine': 'K-Line',
            'vesselType': 'Car Carrier',
            'port': 'Test Port',
            'operationDate': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        }
        
        response = client.post('/api/v1/stevedoring/wizard/step/1', 
                             json=step1_data)
        assert response.status_code == 200
        
        # Step 2: Cargo Configuration
        step2_data = {
            'totalVehicles': 1000,
            'brvTarget': 400,
            'zeeTarget': 350,
            'souTarget': 250,
            'heavyEquipment': 50,
            'electricVehicles': 100
        }
        
        response = client.post('/api/v1/stevedoring/wizard/step/2', 
                             json=step2_data)
        assert response.status_code == 200
        
        # Step 3: Team Assignment
        step3_data = {
            'operationManager': 'Test Manager',
            'autoOpsLead': 'Auto Lead',
            'autoOpsAssistant': 'Auto Assistant',
            'heavyOpsLead': 'Heavy Lead',
            'heavyOpsAssistant': 'Heavy Assistant',
            'totalDrivers': 80
        }
        
        response = client.post('/api/v1/stevedoring/wizard/step/3', 
                             json=step3_data)
        assert response.status_code == 200
        
        # Step 4: Final submission
        response = client.post('/api/v1/stevedoring/wizard/submit')
        assert response.status_code == 201
        
        result = json.loads(response.data)
        assert 'operation_id' in result
    
    def test_cargo_tracking_updates(self, client):
        """Test real-time cargo tracking updates"""
        
        # Create operation first
        operation_id = self.create_test_operation(client)
        
        # Test cargo progress update
        update_data = {
            'zone': 'brv',
            'discharged': 50,
            'timestamp': datetime.now().isoformat()
        }
        
        response = client.put(f'/api/v1/stevedoring/cargo/{operation_id}/update',
                            json=update_data)
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['brv_completed'] == 50
    
    def test_team_assignment(self, client):
        """Test team assignment functionality"""
        
        operation_id = self.create_test_operation(client)
        
        assignment_data = {
            'operation_id': operation_id,
            'role': 'operation_manager',
            'person_id': 1,
            'assigned_at': datetime.now().isoformat()
        }
        
        response = client.post('/api/v1/stevedoring/teams/assign',
                             json=assignment_data)
        assert response.status_code == 200
    
    def test_analytics_generation(self, client):
        """Test analytics and KPI calculation"""
        
        # Create multiple operations for analytics
        for i in range(5):
            self.create_test_operation(client)
        
        # Request analytics
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        response = client.get(f'/api/v1/stevedoring/analytics?start={start_date}&end={end_date}')
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert 'kpis' in result
        assert 'charts' in result
    
    def test_offline_sync(self, client):
        """Test offline data synchronization"""
        
        sync_data = {
            'operations': [{
                'vesselName': 'Offline Vessel',
                'operationType': 'discharge',
                'created_offline': True,
                'timestamp': datetime.now().isoformat()
            }],
            'cargo_updates': [{
                'operation_id': 1,
                'zone': 'zee',
                'discharged': 25,
                'timestamp': datetime.now().isoformat()
            }]
        }
        
        response = client.post('/api/v1/stevedoring/operations/sync',
                             json=sync_data)
        assert response.status_code == 200
    
    def create_test_operation(self, client):
        """Helper method to create test operation"""
        
        operation_data = {
            'vesselName': 'Test Vessel',
            'operationType': 'discharge',
            'operationDate': datetime.now().strftime('%Y-%m-%d'),
            'totalVehicles': 1000,
            'brvTarget': 400,
            'zeeTarget': 350,
            'souTarget': 250
        }
        
        response = client.post('/api/v1/stevedoring/operations',
                             json=operation_data)
        result = json.loads(response.data)
        return result['operation_id']

# Performance Tests
class TestPerformance:
    
    def test_api_response_times(self, client):
        """Test API response time performance"""
        import time
        
        endpoints = [
            '/api/v1/stevedoring/operations',
            '/api/v1/stevedoring/analytics',
            '/api/v1/stevedoring/teams'
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to ms
            assert response_time < 2000, f"{endpoint} took {response_time}ms"
    
    def test_database_query_performance(self):
        """Test database query performance"""
        from sqlalchemy import text
        import time
        
        with app.app_context():
            start_time = time.time()
            
            # Test complex query performance
            result = db.session.execute(text("""
                SELECT v.name, so.operation_type, so.status,
                       cd.automobiles_discharged, cd.progress_percentage
                FROM vessels v
                JOIN stevedoring_operations so ON v.id = so.vessel_id
                JOIN cargo_discharge cd ON so.id = cd.operation_id
                WHERE so.operation_date >= :start_date
                ORDER BY so.operation_date DESC
                LIMIT 100
            """), {
                'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            })
            
            results = result.fetchall()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            assert query_time < 1000, f"Database query took {query_time}ms"

# Security Tests
class TestSecurity:
    
    def test_authentication_required(self, client):
        """Test that protected endpoints require authentication"""
        
        protected_endpoints = [
            '/stevedoring/wizard',
            '/stevedoring/operations',
            '/api/v1/stevedoring/operations'
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 302], f"{endpoint} should require authentication"
    
    def test_sql_injection_protection(self, client):
        """Test SQL injection protection"""
        
        # Login first
        client.post('/auth/login', data={
            'email': 'manager@test.com',
            'password': 'test_password'
        })
        
        # Try SQL injection
        malicious_input = "'; DROP TABLE vessels; --"
        
        response = client.get(f'/api/v1/stevedoring/operations?search={malicious_input}')
        
        # Should not return 500 error (indicating SQL injection worked)
        assert response.status_code != 500
    
    def test_xss_protection(self, client):
        """Test XSS protection"""
        
        client.post('/auth/login', data={
            'email': 'manager@test.com',
            'password': 'test_password'
        })
        
        xss_payload = "<script>alert('xss')</script>"
        
        response = client.post('/api/v1/stevedoring/operations', json={
            'vesselName': xss_payload,
            'operationType': 'discharge'
        })
        
        # Check that script tags are escaped in response
        if response.status_code == 200:
            assert '<script>' not in response.get_data(as_text=True)
```

**Dependencies:** All previous phases
**Testing:** Comprehensive test suite execution
**Success Criteria:** Production-ready system with performance benchmarks

---

## GANTT CHART TIMELINE

```
STEVEDORES DASHBOARD 2.0 INTEGRATION - 12 WEEK TIMELINE

Week 1  |████████████| Database Schema Migration & API Development
Week 2  |████████████| PWA Integration Testing & Offline Setup
Week 3  |████████████| 4-Step Wizard Implementation
Week 4  |████████████| Multi-Ship Operations Dashboard
Week 5  |████████████| Cargo Discharge Tracking System
Week 6  |████████████| Team Assignment System
Week 7  |████████████| TICO Transportation Management
Week 8  |████████████| Document Management & Auto-fill
Week 9  |████████████| Analytics & Reporting Dashboard (Part 1)
Week 10 |████████████| Analytics & Reporting Dashboard (Part 2)
Week 11 |████████████| Advanced PWA Features & Offline Sync
Week 12 |████████████| Performance Optimization & Testing

CRITICAL PATH DEPENDENCIES:
Week 1-2: Foundation (CRITICAL) → Week 3-5: Core Features (CRITICAL) → Week 6-8: Operations (MEDIUM) → Week 9-12: Advanced (LOW)

PARALLEL WORK OPPORTUNITIES:
- UI development can parallel API development within each phase
- Testing can be ongoing throughout each phase
- Documentation can be parallel to implementation
```

---

## RESOURCE ALLOCATION

### Development Focus Areas

**Database/Backend (40% effort):**
- Schema design and migration
- API endpoint development
- Business logic implementation
- Data validation and security

**Frontend/UI (35% effort):**
- Maritime-specific UI components
- Wizard implementation
- Dashboard development
- PWA enhancement

**Testing/QA (15% effort):**
- Unit testing
- Integration testing
- Performance testing
- Security testing

**DevOps/Deployment (10% effort):**
- CI/CD pipeline
- Monitoring setup
- Performance optimization
- Security hardening

### Skill Requirements

**Required Skills:**
- Flask/Python backend development
- PostgreSQL database design
- JavaScript/PWA development
- Maritime domain knowledge
- RESTful API design

**Nice-to-Have:**
- Chart.js/D3.js for analytics
- WebSocket implementation
- Docker containerization
- Redis caching

---

## MILESTONE DEFINITIONS

### Phase 1 Milestones (Week 1-2)
**M1.1:** Database schema migration complete with all maritime tables
**M1.2:** Core API endpoints functional with proper authentication
**M1.3:** PWA features maintained with maritime data caching

### Phase 2 Milestones (Week 3-5)
**M2.1:** 4-step wizard creates complete stevedoring operations
**M2.2:** Multi-ship dashboard shows real-time operations
**M2.3:** Cargo tracking updates in real-time with zone breakdown

### Phase 3 Milestones (Week 6-8)
**M3.1:** Complete team assignment workflow functional
**M3.2:** TICO transportation optimization working
**M3.3:** Document auto-fill extracts and populates wizard data

### Phase 4 Milestones (Week 9-12)
**M4.1:** Analytics dashboard generates maritime KPIs
**M4.2:** Enhanced offline capabilities with conflict resolution
**M4.3:** Production deployment with performance benchmarks

### Success Criteria for Each Milestone
- **Functional Requirements:** All specified features working as designed
- **Performance:** API responses < 2s, page load < 3s
- **Reliability:** 99.9% uptime, proper error handling
- **Security:** Authentication, input validation, SQL injection protection
- **PWA Compliance:** Offline functionality, installable, service worker

---

## RISK MANAGEMENT

### HIGH RISK - CRITICAL PATH BLOCKERS

**R1: Database Migration Complexity**
- **Risk:** Complex maritime data relationships cause migration issues
- **Mitigation:** Incremental migration with rollback plan
- **Contingency:** Hybrid approach with gradual data model transition

**R2: PWA Offline Sync Conflicts**
- **Risk:** Maritime data conflicts during offline/online sync
- **Contingency:** Simplified conflict resolution with manual review
- **Alternative:** Server-side conflict resolution with user notifications

**R3: Performance with Large Datasets**
- **Risk:** Maritime operations generate large amounts of data
- **Mitigation:** Database indexing, pagination, caching strategies
- **Contingency:** Data archiving and performance optimization

### MEDIUM RISK - FEATURE DELIVERY

**R4: Maritime Domain Complexity**
- **Risk:** Incomplete understanding of stevedoring operations
- **Mitigation:** Domain expert consultation, iterative development
- **Contingency:** Simplified initial version with enhancement iterations

**R5: Integration Testing Complexity**
- **Risk:** Complex interactions between maritime features
- **Mitigation:** Comprehensive test suite, staged testing
- **Contingency:** Phased rollout with feature flags

### LOW RISK - ENHANCEMENT FEATURES

**R6: Advanced Analytics Complexity**
- **Risk:** Complex KPI calculations and reporting
- **Mitigation:** Start with basic metrics, enhance iteratively
- **Contingency:** Third-party analytics integration

**R7: Document Processing Accuracy**
- **Risk:** Auto-fill extraction accuracy varies by document type
- **Mitigation:** Multiple extraction strategies, user validation
- **Contingency:** Manual data entry with template assistance

### Contingency Plans

**Plan A: Aggressive Timeline (12 weeks)**
- Full implementation as specified
- All features delivered on schedule
- Comprehensive testing and optimization

**Plan B: Conservative Timeline (16 weeks)**
- Core maritime features prioritized
- Advanced features deferred to phase 2
- Focus on stability and PWA compliance

**Plan C: Minimal Viable Product (8 weeks)**
- Essential stevedoring features only
- Basic wizard and cargo tracking
- Enhanced features in future iterations

---

## DEPLOYMENT CHECKPOINTS

### Weekly Deployment Schedule

**Week 1-2:** Development environment setup with maritime models
**Week 3-4:** Staging deployment with wizard and dashboard
**Week 5-6:** Beta testing with maritime operations team
**Week 7-8:** User acceptance testing and feedback integration
**Week 9-10:** Pre-production deployment with analytics
**Week 11-12:** Production deployment with monitoring

### Quality Gates

**Gate 1 (Week 2):** Database migration successful, APIs functional
**Gate 2 (Week 5):** Core maritime features working, PWA compliant
**Gate 3 (Week 8):** Operations management complete, user tested
**Gate 4 (Week 12):** Production ready, performance validated

### Rollback Strategy

- **Database:** Automated backup before each migration
- **Application:** Blue-green deployment with instant rollback
- **Features:** Feature flags for selective rollback
- **Data:** Point-in-time recovery for data corruption

---

## CONCLUSION

This comprehensive roadmap provides a structured approach to integrating Stevedores Dashboard 2.0 features into the Fleet Management PWA. The 12-week timeline balances thoroughness with practicality, ensuring maritime-specific functionality while maintaining the robust PWA foundation.

**Key Success Factors:**
1. **Phased Approach:** Critical path prioritization ensures core functionality first
2. **Maritime Focus:** Domain-specific features address real stevedoring operations
3. **PWA Preservation:** Offline capabilities maintained throughout integration
4. **Risk Management:** Comprehensive contingency planning for common blockers
5. **Quality Assurance:** Testing integrated throughout development cycle

The roadmap accounts for the complexity of maritime operations while leveraging the existing PWA infrastructure to deliver a production-ready stevedoring dashboard that exceeds the capabilities of the original system.