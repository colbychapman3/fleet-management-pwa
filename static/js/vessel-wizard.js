/**
 * Vessel Operations Wizard
 * 4-step maritime workflow with offline capability and auto-save
 */

class VesselOperationsWizard {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            autoSave: true,
            autoSaveInterval: 30000, // 30 seconds
            offline: true,
            ...options
        };
        
        this.currentStep = 1;
        this.totalSteps = 4;
        this.data = {
            vessel: {},
            cargo: {},
            team: {},
            review: {}
        };
        
        this.autoSaveTimer = null;
        this.validationErrors = {};
        this.isSubmitting = false;
        
        // Cached reference data
        this.teamData = null;
        this.berthData = null;
        this.zoneData = null;
        
        this.init();
    }

    async init() {
        try {
            // Initialize offline database if enabled
            if (this.options.offline && window.fleetApp?.offlineDB) {
                this.offlineDB = window.fleetApp.offlineDB;
                await this.loadSavedData();
            }
            
            // Load reference data
            await this.loadReferenceData();
            
            this.render();
            this.setupEventListeners();
            this.startAutoSave();
            
            console.log('Vessel Operations Wizard initialized');
        } catch (error) {
            console.error('Failed to initialize wizard:', error);
            this.showError('Failed to initialize wizard');
        }
    }

    async loadReferenceData() {
        try {
            // Try to load from cache first
            if (this.offlineDB) {
                this.teamData = await this.offlineDB.getTeamData();
                this.berthData = await this.offlineDB.getBerthData();
                this.zoneData = await this.offlineDB.getCargoZoneData();
            }

            // Load fresh data from API if online
            if (navigator.onLine) {
                await Promise.all([
                    this.loadTeamData(),
                    this.loadBerthData(),
                    this.loadZoneData()
                ]);
            }
        } catch (error) {
            console.warn('Failed to load some reference data:', error);
            // Continue with cached or mock data
        }
    }

    async loadTeamData() {
        try {
            const response = await fetch('/api/maritime/ship-operations/wizard/teams', {
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                this.teamData = await response.json();
                
                // Cache the data
                if (this.offlineDB) {
                    await this.offlineDB.saveTeamData(this.teamData);
                }
            }
        } catch (error) {
            console.warn('Failed to load team data:', error);
        }
    }

    async loadBerthData() {
        try {
            const response = await fetch('/api/maritime/ship-operations/wizard/berths', {
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                this.berthData = await response.json();
                
                // Cache the data
                if (this.offlineDB) {
                    await this.offlineDB.saveBerthData(this.berthData);
                }
            }
        } catch (error) {
            console.warn('Failed to load berth data:', error);
        }
    }

    async loadZoneData() {
        try {
            const response = await fetch('/api/maritime/ship-operations/wizard/cargo-zones', {
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                this.zoneData = await response.json();
                
                // Cache the data
                if (this.offlineDB) {
                    await this.offlineDB.saveCargoZoneData(this.zoneData);
                }
            }
        } catch (error) {
            console.warn('Failed to load zone data:', error);
        }
    }

    render() {
        if (!this.container) {
            throw new Error('Wizard container not found');
        }

        this.container.innerHTML = `
            <div class="vessel-wizard">
                <div class="wizard-header">
                    <h2 class="wizard-title">Vessel Operations Setup</h2>
                    ${this.renderProgressIndicator()}
                </div>
                
                <div class="wizard-content">
                    ${this.renderCurrentStep()}
                </div>
                
                <div class="wizard-footer">
                    ${this.renderNavigation()}
                    ${this.renderAutoSaveStatus()}
                </div>
            </div>
        `;
    }

    renderProgressIndicator() {
        const steps = [
            { number: 1, title: 'Vessel Info', icon: '🚢' },
            { number: 2, title: 'Cargo Config', icon: '📦' },
            { number: 3, title: 'Team Assign', icon: '👥' },
            { number: 4, title: 'Review', icon: '✅' }
        ];

        return `
            <div class="progress-indicator">
                ${steps.map(step => `
                    <div class="progress-step ${step.number <= this.currentStep ? 'active' : ''} ${step.number < this.currentStep ? 'completed' : ''}">
                        <div class="step-icon">${step.icon}</div>
                        <div class="step-number">${step.number}</div>
                        <div class="step-title">${step.title}</div>
                    </div>
                `).join('')}
                
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${((this.currentStep - 1) / (this.totalSteps - 1)) * 100}%"></div>
                </div>
            </div>
        `;
    }

    renderCurrentStep() {
        switch (this.currentStep) {
            case 1:
                return this.renderVesselInformationStep();
            case 2:
                return this.renderCargoConfigurationStep();
            case 3:
                return this.renderTeamAssignmentStep();
            case 4:
                return this.renderReviewStep();
            default:
                return '<div class="error">Invalid step</div>';
        }
    }

    renderVesselInformationStep() {
        return `
            <div class="wizard-step" data-step="1">
                <div class="step-header">
                    <h3>Vessel Information</h3>
                    <p>Enter basic vessel details and berth assignment</p>
                </div>
                
                <div class="step-form">
                    <div class="row">
                        <div class="col-6">
                            <div class="form-group">
                                <label class="form-label" for="vessel-name">Vessel Name *</label>
                                <input type="text" 
                                       id="vessel-name" 
                                       class="form-control" 
                                       value="${this.data.vessel.name || ''}"
                                       placeholder="Enter vessel name"
                                       required>
                                <div class="field-error" id="vessel-name-error"></div>
                            </div>
                        </div>
                        
                        <div class="col-6">
                            <div class="form-group">
                                <label class="form-label" for="vessel-type">Vessel Type *</label>
                                <select id="vessel-type" class="form-control" required>
                                    <option value="">Select vessel type</option>
                                    <option value="cargo" ${this.data.vessel.type === 'cargo' ? 'selected' : ''}>Cargo Ship</option>
                                    <option value="container" ${this.data.vessel.type === 'container' ? 'selected' : ''}>Container Ship</option>
                                    <option value="roro" ${this.data.vessel.type === 'roro' ? 'selected' : ''}>RoRo Ship</option>
                                    <option value="bulk" ${this.data.vessel.type === 'bulk' ? 'selected' : ''}>Bulk Carrier</option>
                                    <option value="tanker" ${this.data.vessel.type === 'tanker' ? 'selected' : ''}>Tanker</option>
                                </select>
                                <div class="field-error" id="vessel-type-error"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-6">
                            <div class="form-group">
                                <label class="form-label" for="shipping-line">Shipping Line *</label>
                                <input type="text" 
                                       id="shipping-line" 
                                       class="form-control" 
                                       value="${this.data.vessel.shippingLine || ''}"
                                       placeholder="Enter shipping line"
                                       required>
                                <div class="field-error" id="shipping-line-error"></div>
                            </div>
                        </div>
                        
                        <div class="col-6">
                            <div class="form-group">
                                <label class="form-label" for="berth-assignment">Berth Assignment *</label>
                                <select id="berth-assignment" class="form-control" required>
                                    <option value="">Select berth</option>
                                    <option value="berth-1" ${this.data.vessel.berth === 'berth-1' ? 'selected' : ''}>Berth 1</option>
                                    <option value="berth-2" ${this.data.vessel.berth === 'berth-2' ? 'selected' : ''}>Berth 2</option>
                                    <option value="berth-3" ${this.data.vessel.berth === 'berth-3' ? 'selected' : ''}>Berth 3</option>
                                    <option value="berth-4" ${this.data.vessel.berth === 'berth-4' ? 'selected' : ''}>Berth 4</option>
                                    <option value="berth-5" ${this.data.vessel.berth === 'berth-5' ? 'selected' : ''}>Berth 5</option>
                                </select>
                                <div class="field-error" id="berth-assignment-error"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-6">
                            <div class="form-group">
                                <label class="form-label" for="arrival-date">Expected Arrival</label>
                                <input type="datetime-local" 
                                       id="arrival-date" 
                                       class="form-control" 
                                       value="${this.data.vessel.arrivalDate || ''}">
                            </div>
                        </div>
                        
                        <div class="col-6">
                            <div class="form-group">
                                <label class="form-label" for="departure-date">Expected Departure</label>
                                <input type="datetime-local" 
                                       id="departure-date" 
                                       class="form-control" 
                                       value="${this.data.vessel.departureDate || ''}">
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="vessel-notes">Additional Notes</label>
                        <textarea id="vessel-notes" 
                                  class="form-control" 
                                  rows="3" 
                                  placeholder="Any additional vessel information">${this.data.vessel.notes || ''}</textarea>
                    </div>
                </div>
            </div>
        `;
    }

    renderCargoConfigurationStep() {
        return `
            <div class="wizard-step" data-step="2">
                <div class="step-header">
                    <h3>Cargo Configuration</h3>
                    <p>Configure automobile counts and zone assignments</p>
                </div>
                
                <div class="step-form">
                    <div class="cargo-summary">
                        <h4>Cargo Summary</h4>
                        <div class="summary-cards">
                            <div class="summary-card">
                                <div class="card-icon">🚗</div>
                                <div class="card-content">
                                    <div class="card-number" id="total-vehicles">${this.getTotalVehicles()}</div>
                                    <div class="card-label">Total Vehicles</div>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="card-icon">📦</div>
                                <div class="card-content">
                                    <div class="card-number" id="active-zones">${this.getActiveZones()}</div>
                                    <div class="card-label">Active Zones</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="zone-configuration">
                        <h4>Zone Assignments</h4>
                        
                        <div class="zone-section">
                            <div class="zone-header">
                                <h5>BRV Zone (Bremerhaven)</h5>
                                <div class="zone-toggle">
                                    <input type="checkbox" 
                                           id="brv-enabled" 
                                           class="zone-checkbox"
                                           ${this.data.cargo.brv?.enabled ? 'checked' : ''}>
                                    <label for="brv-enabled">Enable Zone</label>
                                </div>
                            </div>
                            
                            <div class="zone-content ${this.data.cargo.brv?.enabled ? '' : 'disabled'}">
                                <div class="row">
                                    <div class="col-4">
                                        <div class="form-group">
                                            <label class="form-label" for="brv-cars">Cars</label>
                                            <input type="number" 
                                                   id="brv-cars" 
                                                   class="form-control vehicle-count" 
                                                   min="0" 
                                                   value="${this.data.cargo.brv?.cars || 0}">
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="form-group">
                                            <label class="form-label" for="brv-trucks">Trucks</label>
                                            <input type="number" 
                                                   id="brv-trucks" 
                                                   class="form-control vehicle-count" 
                                                   min="0" 
                                                   value="${this.data.cargo.brv?.trucks || 0}">
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="form-group">
                                            <label class="form-label" for="brv-special">Special Vehicles</label>
                                            <input type="number" 
                                                   id="brv-special" 
                                                   class="form-control vehicle-count" 
                                                   min="0" 
                                                   value="${this.data.cargo.brv?.special || 0}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="zone-section">
                            <div class="zone-header">
                                <h5>ZEE Zone (Zeebrugge)</h5>
                                <div class="zone-toggle">
                                    <input type="checkbox" 
                                           id="zee-enabled" 
                                           class="zone-checkbox"
                                           ${this.data.cargo.zee?.enabled ? 'checked' : ''}>
                                    <label for="zee-enabled">Enable Zone</label>
                                </div>
                            </div>
                            
                            <div class="zone-content ${this.data.cargo.zee?.enabled ? '' : 'disabled'}">
                                <div class="row">
                                    <div class="col-4">
                                        <div class="form-group">
                                            <label class="form-label" for="zee-cars">Cars</label>
                                            <input type="number" 
                                                   id="zee-cars" 
                                                   class="form-control vehicle-count" 
                                                   min="0" 
                                                   value="${this.data.cargo.zee?.cars || 0}">
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="form-group">
                                            <label class="form-label" for="zee-trucks">Trucks</label>
                                            <input type="number" 
                                                   id="zee-trucks" 
                                                   class="form-control vehicle-count" 
                                                   min="0" 
                                                   value="${this.data.cargo.zee?.trucks || 0}">
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="form-group">
                                            <label class="form-label" for="zee-special">Special Vehicles</label>
                                            <input type="number" 
                                                   id="zee-special" 
                                                   class="form-control vehicle-count" 
                                                   min="0" 
                                                   value="${this.data.cargo.zee?.special || 0}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="zone-section">
                            <div class="zone-header">
                                <h5>SOU Zone (Southampton)</h5>
                                <div class="zone-toggle">
                                    <input type="checkbox" 
                                           id="sou-enabled" 
                                           class="zone-checkbox"
                                           ${this.data.cargo.sou?.enabled ? 'checked' : ''}>
                                    <label for="sou-enabled">Enable Zone</label>
                                </div>
                            </div>
                            
                            <div class="zone-content ${this.data.cargo.sou?.enabled ? '' : 'disabled'}">
                                <div class="row">
                                    <div class="col-4">
                                        <div class="form-group">
                                            <label class="form-label" for="sou-cars">Cars</label>
                                            <input type="number" 
                                                   id="sou-cars" 
                                                   class="form-control vehicle-count" 
                                                   min="0" 
                                                   value="${this.data.cargo.sou?.cars || 0}">
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="form-group">
                                            <label class="form-label" for="sou-trucks">Trucks</label>
                                            <input type="number" 
                                                   id="sou-trucks" 
                                                   class="form-control vehicle-count" 
                                                   min="0" 
                                                   value="${this.data.cargo.sou?.trucks || 0}">
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="form-group">
                                            <label class="form-label" for="sou-special">Special Vehicles</label>
                                            <input type="number" 
                                                   id="sou-special" 
                                                   class="form-control vehicle-count" 
                                                   min="0" 
                                                   value="${this.data.cargo.sou?.special || 0}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="cargo-notes">Cargo Notes</label>
                        <textarea id="cargo-notes" 
                                  class="form-control" 
                                  rows="3" 
                                  placeholder="Special cargo handling instructions">${this.data.cargo.notes || ''}</textarea>
                    </div>
                </div>
            </div>
        `;
    }

    renderTeamAssignmentStep() {
        return `
            <div class="wizard-step" data-step="3">
                <div class="step-header">
                    <h3>Team Assignments</h3>
                    <p>Assign operations leads and stevedores</p>
                </div>
                
                <div class="step-form">
                    <div class="team-section">
                        <h4>Operations Leadership</h4>
                        
                        <div class="row">
                            <div class="col-6">
                                <div class="form-group">
                                    <label class="form-label" for="auto-ops-lead">Auto Operations Lead *</label>
                                    <select id="auto-ops-lead" class="form-control" required>
                                        <option value="">Select auto ops lead</option>
                                        ${this.renderUserOptions('auto_ops', this.data.team.autoOpsLead)}
                                    </select>
                                    <div class="field-error" id="auto-ops-lead-error"></div>
                                </div>
                            </div>
                            
                            <div class="col-6">
                                <div class="form-group">
                                    <label class="form-label" for="heavy-ops-lead">Heavy Operations Lead *</label>
                                    <select id="heavy-ops-lead" class="form-control" required>
                                        <option value="">Select heavy ops lead</option>
                                        ${this.renderUserOptions('heavy_ops', this.data.team.heavyOpsLead)}
                                    </select>
                                    <div class="field-error" id="heavy-ops-lead-error"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="team-section">
                        <h4>Stevedore Teams</h4>
                        
                        <div class="stevedore-assignment">
                            <div class="zone-teams">
                                ${this.renderZoneTeamAssignment('BRV', 'brv')}
                                ${this.renderZoneTeamAssignment('ZEE', 'zee')}
                                ${this.renderZoneTeamAssignment('SOU', 'sou')}
                            </div>
                        </div>
                    </div>
                    
                    <div class="team-section">
                        <h4>Additional Resources</h4>
                        
                        <div class="row">
                            <div class="col-6">
                                <div class="form-group">
                                    <label class="form-label" for="crane-operators">Crane Operators Required</label>
                                    <input type="number" 
                                           id="crane-operators" 
                                           class="form-control" 
                                           min="0" 
                                           max="10"
                                           value="${this.data.team.craneOperators || 0}">
                                </div>
                            </div>
                            
                            <div class="col-6">
                                <div class="form-group">
                                    <label class="form-label" for="forklift-operators">Forklift Operators Required</label>
                                    <input type="number" 
                                           id="forklift-operators" 
                                           class="form-control" 
                                           min="0" 
                                           max="20"
                                           value="${this.data.team.forkliftOperators || 0}">
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="team-notes">Team Notes</label>
                            <textarea id="team-notes" 
                                      class="form-control" 
                                      rows="3" 
                                      placeholder="Special team requirements or notes">${this.data.team.notes || ''}</textarea>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderZoneTeamAssignment(zoneName, zoneKey) {
        const zoneData = this.data.cargo[zoneKey];
        if (!zoneData || !zoneData.enabled) {
            return '';
        }

        return `
            <div class="zone-team-card">
                <div class="zone-team-header">
                    <h5>${zoneName} Zone Team</h5>
                    <div class="zone-workload">
                        ${this.getZoneVehicleCount(zoneKey)} vehicles
                    </div>
                </div>
                
                <div class="team-assignment-grid">
                    <div class="form-group">
                        <label class="form-label" for="${zoneKey}-stevedores">Stevedores Required</label>
                        <input type="number" 
                               id="${zoneKey}-stevedores" 
                               class="form-control" 
                               min="1" 
                               max="50"
                               value="${this.data.team[zoneKey + 'Stevedores'] || this.calculateRequiredStevedores(zoneKey)}"
                               data-zone="${zoneKey}">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="${zoneKey}-supervisor">Team Supervisor</label>
                        <select id="${zoneKey}-supervisor" class="form-control">
                            <option value="">Select supervisor</option>
                            ${this.renderUserOptions('supervisor', this.data.team[zoneKey + 'Supervisor'])}
                        </select>
                    </div>
                </div>
            </div>
        `;
    }

    renderReviewStep() {
        return `
            <div class="wizard-step" data-step="4">
                <div class="step-header">
                    <h3>Review & Confirmation</h3>
                    <p>Review all information before submitting the vessel operation</p>
                </div>
                
                <div class="step-form">
                    <div class="review-sections">
                        ${this.renderVesselReview()}
                        ${this.renderCargoReview()}
                        ${this.renderTeamReview()}
                    </div>
                    
                    <div class="confirmation-section">
                        <div class="form-check">
                            <input type="checkbox" 
                                   id="confirm-accuracy" 
                                   class="form-check-input" 
                                   ${this.data.review.confirmed ? 'checked' : ''}>
                            <label class="form-check-label" for="confirm-accuracy">
                                I confirm that all information is accurate and complete
                            </label>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="final-notes">Final Notes (Optional)</label>
                            <textarea id="final-notes" 
                                      class="form-control" 
                                      rows="3" 
                                      placeholder="Any final notes or special instructions">${this.data.review.finalNotes || ''}</textarea>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderVesselReview() {
        return `
            <div class="review-section">
                <h4>Vessel Information</h4>
                <div class="review-grid">
                    <div class="review-item">
                        <span class="review-label">Vessel Name:</span>
                        <span class="review-value">${this.data.vessel.name || 'Not specified'}</span>
                    </div>
                    <div class="review-item">
                        <span class="review-label">Vessel Type:</span>
                        <span class="review-value">${this.data.vessel.type || 'Not specified'}</span>
                    </div>
                    <div class="review-item">
                        <span class="review-label">Shipping Line:</span>
                        <span class="review-value">${this.data.vessel.shippingLine || 'Not specified'}</span>
                    </div>
                    <div class="review-item">
                        <span class="review-label">Berth Assignment:</span>
                        <span class="review-value">${this.data.vessel.berth || 'Not specified'}</span>
                    </div>
                    <div class="review-item">
                        <span class="review-label">Expected Arrival:</span>
                        <span class="review-value">${this.formatDateTime(this.data.vessel.arrivalDate) || 'Not specified'}</span>
                    </div>
                    <div class="review-item">
                        <span class="review-label">Expected Departure:</span>
                        <span class="review-value">${this.formatDateTime(this.data.vessel.departureDate) || 'Not specified'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderCargoReview() {
        const activeZones = ['brv', 'zee', 'sou'].filter(zone => this.data.cargo[zone]?.enabled);
        
        return `
            <div class="review-section">
                <h4>Cargo Configuration</h4>
                <div class="cargo-summary-review">
                    <div class="summary-stat">
                        <span class="stat-number">${this.getTotalVehicles()}</span>
                        <span class="stat-label">Total Vehicles</span>
                    </div>
                    <div class="summary-stat">
                        <span class="stat-number">${activeZones.length}</span>
                        <span class="stat-label">Active Zones</span>
                    </div>
                </div>
                
                ${activeZones.map(zone => this.renderZoneCargoReview(zone)).join('')}
            </div>
        `;
    }

    renderZoneCargoReview(zone) {
        const zoneData = this.data.cargo[zone];
        const zoneName = zone.toUpperCase();
        
        return `
            <div class="zone-review">
                <h5>${zoneName} Zone</h5>
                <div class="zone-stats">
                    <span class="zone-stat">Cars: ${zoneData.cars || 0}</span>
                    <span class="zone-stat">Trucks: ${zoneData.trucks || 0}</span>
                    <span class="zone-stat">Special: ${zoneData.special || 0}</span>
                    <span class="zone-total">Total: ${(zoneData.cars || 0) + (zoneData.trucks || 0) + (zoneData.special || 0)}</span>
                </div>
            </div>
        `;
    }

    renderTeamReview() {
        return `
            <div class="review-section">
                <h4>Team Assignments</h4>
                <div class="team-review-grid">
                    <div class="team-leader-review">
                        <h5>Leadership</h5>
                        <div class="review-item">
                            <span class="review-label">Auto Ops Lead:</span>
                            <span class="review-value">${this.getUserName(this.data.team.autoOpsLead) || 'Not assigned'}</span>
                        </div>
                        <div class="review-item">
                            <span class="review-label">Heavy Ops Lead:</span>
                            <span class="review-value">${this.getUserName(this.data.team.heavyOpsLead) || 'Not assigned'}</span>
                        </div>
                    </div>
                    
                    <div class="team-resources-review">
                        <h5>Resources</h5>
                        <div class="review-item">
                            <span class="review-label">Crane Operators:</span>
                            <span class="review-value">${this.data.team.craneOperators || 0}</span>
                        </div>
                        <div class="review-item">
                            <span class="review-label">Forklift Operators:</span>
                            <span class="review-value">${this.data.team.forkliftOperators || 0}</span>
                        </div>
                        <div class="review-item">
                            <span class="review-label">Total Stevedores:</span>
                            <span class="review-value">${this.getTotalStevedores()}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderNavigation() {
        return `
            <div class="wizard-navigation">
                <button type="button" 
                        class="btn btn-outline" 
                        id="prev-btn" 
                        ${this.currentStep === 1 ? 'disabled' : ''}>
                    ← Previous
                </button>
                
                <div class="nav-spacer"></div>
                
                ${this.currentStep < this.totalSteps ? `
                    <button type="button" 
                            class="btn btn-primary" 
                            id="next-btn">
                        Next →
                    </button>
                ` : `
                    <button type="button" 
                            class="btn btn-success" 
                            id="submit-btn"
                            ${!this.data.review?.confirmed ? 'disabled' : ''}>
                        ${this.isSubmitting ? '<span class="spinner"></span> Submitting...' : 'Submit Operation'}
                    </button>
                `}
            </div>
        `;
    }

    renderAutoSaveStatus() {
        return `
            <div class="auto-save-status">
                <span class="save-indicator" id="save-indicator">
                    ${this.options.autoSave ? '💾 Auto-save enabled' : ''}
                </span>
                <span class="last-saved" id="last-saved"></span>
            </div>
        `;
    }

    // Helper methods for rendering
    renderUserOptions(role, selectedValue) {
        // Use cached team data if available, otherwise fall back to mock data
        if (this.teamData) {
            const users = this.teamData[role + '_leads'] || this.teamData.supervisors || [];
            return users.map(user => `
                <option value="${user.id}" ${user.id == selectedValue ? 'selected' : ''}>
                    ${user.name}
                </option>
            `).join('');
        }

        // Fallback mock data
        const mockUsers = [
            { id: 1, name: 'John Smith', role: 'auto_ops' },
            { id: 2, name: 'Sarah Johnson', role: 'heavy_ops' },
            { id: 3, name: 'Mike Wilson', role: 'supervisor' },
            { id: 4, name: 'Lisa Chen', role: 'auto_ops' },
            { id: 5, name: 'David Brown', role: 'heavy_ops' }
        ];

        return mockUsers
            .filter(user => user.role === role || role === 'supervisor')
            .map(user => `
                <option value="${user.id}" ${user.id == selectedValue ? 'selected' : ''}>
                    ${user.name}
                </option>
            `).join('');
    }

    getUserName(userId) {
        const mockUsers = {
            1: 'John Smith',
            2: 'Sarah Johnson', 
            3: 'Mike Wilson',
            4: 'Lisa Chen',
            5: 'David Brown'
        };
        return mockUsers[userId] || '';
    }

    getTotalVehicles() {
        let total = 0;
        ['brv', 'zee', 'sou'].forEach(zone => {
            if (this.data.cargo[zone]?.enabled) {
                total += (this.data.cargo[zone].cars || 0) + 
                        (this.data.cargo[zone].trucks || 0) + 
                        (this.data.cargo[zone].special || 0);
            }
        });
        return total;
    }

    getActiveZones() {
        return ['brv', 'zee', 'sou'].filter(zone => this.data.cargo[zone]?.enabled).length;
    }

    getZoneVehicleCount(zone) {
        const zoneData = this.data.cargo[zone];
        if (!zoneData || !zoneData.enabled) return 0;
        return (zoneData.cars || 0) + (zoneData.trucks || 0) + (zoneData.special || 0);
    }

    calculateRequiredStevedores(zone) {
        const vehicleCount = this.getZoneVehicleCount(zone);
        return Math.max(1, Math.ceil(vehicleCount / 20)); // 1 stevedore per 20 vehicles, minimum 1
    }

    getTotalStevedores() {
        let total = 0;
        ['brv', 'zee', 'sou'].forEach(zone => {
            if (this.data.cargo[zone]?.enabled) {
                total += parseInt(this.data.team[zone + 'Stevedores'] || 0);
            }
        });
        return total;
    }

    formatDateTime(dateTimeString) {
        if (!dateTimeString) return '';
        const date = new Date(dateTimeString);
        return date.toLocaleString();
    }

    // Event listeners and interactions will be continued in the next part...
    setupEventListeners() {
        // Navigation events
        this.container.addEventListener('click', (e) => {
            if (e.target.id === 'next-btn') {
                this.nextStep();
            } else if (e.target.id === 'prev-btn') {
                this.previousStep();
            } else if (e.target.id === 'submit-btn') {
                this.submitOperation();
            }
        });

        // Form input events
        this.container.addEventListener('input', (e) => {
            this.handleInputChange(e);
        });

        this.container.addEventListener('change', (e) => {
            this.handleInputChange(e);
        });

        // Zone toggle events
        this.container.addEventListener('change', (e) => {
            if (e.target.classList.contains('zone-checkbox')) {
                this.handleZoneToggle(e);
            }
        });

        // Vehicle count change events
        this.container.addEventListener('input', (e) => {
            if (e.target.classList.contains('vehicle-count')) {
                this.updateCargoSummary();
                this.updateStevedoreRequirements();
            }
        });
    }

    handleInputChange(e) {
        const { id, value, type, checked } = e.target;
        
        // Update data based on current step
        switch (this.currentStep) {
            case 1:
                this.updateVesselData(id, value);
                break;
            case 2:
                this.updateCargoData(id, value, type, checked);
                break;
            case 3:
                this.updateTeamData(id, value);
                break;
            case 4:
                this.updateReviewData(id, value, type, checked);
                break;
        }

        // Clear validation errors
        this.clearFieldError(id);
        
        // Trigger auto-save
        this.scheduleAutoSave();
    }

    updateVesselData(fieldId, value) {
        const fieldMap = {
            'vessel-name': 'name',
            'vessel-type': 'type', 
            'shipping-line': 'shippingLine',
            'berth-assignment': 'berth',
            'arrival-date': 'arrivalDate',
            'departure-date': 'departureDate',
            'vessel-notes': 'notes'
        };
        
        const field = fieldMap[fieldId];
        if (field) {
            this.data.vessel[field] = value;
        }
    }

    updateCargoData(fieldId, value, type, checked) {
        if (fieldId === 'cargo-notes') {
            this.data.cargo.notes = value;
            return;
        }

        // Handle zone toggles
        if (fieldId.endsWith('-enabled')) {
            const zone = fieldId.replace('-enabled', '');
            if (!this.data.cargo[zone]) {
                this.data.cargo[zone] = {};
            }
            this.data.cargo[zone].enabled = checked;
            return;
        }

        // Handle vehicle counts
        const match = fieldId.match(/^(brv|zee|sou)-(cars|trucks|special)$/);
        if (match) {
            const [, zone, vehicleType] = match;
            if (!this.data.cargo[zone]) {
                this.data.cargo[zone] = {};
            }
            this.data.cargo[zone][vehicleType] = parseInt(value) || 0;
        }
    }

    updateTeamData(fieldId, value) {
        const fieldMap = {
            'auto-ops-lead': 'autoOpsLead',
            'heavy-ops-lead': 'heavyOpsLead',
            'crane-operators': 'craneOperators',
            'forklift-operators': 'forkliftOperators',
            'team-notes': 'notes'
        };
        
        const field = fieldMap[fieldId];
        if (field) {
            this.data.team[field] = field.includes('operators') ? parseInt(value) || 0 : value;
            return;
        }

        // Handle zone-specific stevedore counts
        const stevedoreMatch = fieldId.match(/^(brv|zee|sou)-stevedores$/);
        if (stevedoreMatch) {
            const zone = stevedoreMatch[1];
            this.data.team[zone + 'Stevedores'] = parseInt(value) || 0;
            return;
        }

        // Handle zone supervisors
        const supervisorMatch = fieldId.match(/^(brv|zee|sou)-supervisor$/);
        if (supervisorMatch) {
            const zone = supervisorMatch[1];
            this.data.team[zone + 'Supervisor'] = value;
        }
    }

    updateReviewData(fieldId, value, type, checked) {
        if (fieldId === 'confirm-accuracy') {
            this.data.review.confirmed = checked;
            // Enable/disable submit button
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.disabled = !checked;
            }
        } else if (fieldId === 'final-notes') {
            this.data.review.finalNotes = value;
        }
    }

    handleZoneToggle(e) {
        const zoneId = e.target.id.replace('-enabled', '');
        const zoneContent = e.target.closest('.zone-section').querySelector('.zone-content');
        
        if (e.target.checked) {
            zoneContent.classList.remove('disabled');
        } else {
            zoneContent.classList.add('disabled');
            // Clear zone data when disabled
            if (this.data.cargo[zoneId]) {
                this.data.cargo[zoneId] = { enabled: false };
            }
        }
        
        this.updateCargoSummary();
        this.scheduleAutoSave();
    }

    updateCargoSummary() {
        const totalVehiclesEl = document.getElementById('total-vehicles');
        const activeZonesEl = document.getElementById('active-zones');
        
        if (totalVehiclesEl) {
            totalVehiclesEl.textContent = this.getTotalVehicles();
        }
        if (activeZonesEl) {
            activeZonesEl.textContent = this.getActiveZones();
        }
    }

    updateStevedoreRequirements() {
        ['brv', 'zee', 'sou'].forEach(zone => {
            const stevedoreInput = document.getElementById(`${zone}-stevedores`);
            if (stevedoreInput && this.data.cargo[zone]?.enabled) {
                const currentValue = parseInt(stevedoreInput.value) || 0;
                const recommended = this.calculateRequiredStevedores(zone);
                
                // Only update if field is empty or has default value
                if (currentValue === 0) {
                    stevedoreInput.value = recommended;
                    this.data.team[zone + 'Stevedores'] = recommended;
                }
            }
        });
    }

    // Navigation methods
    async nextStep() {
        if (await this.validateCurrentStep()) {
            this.currentStep++;
            this.render();
            this.scrollToTop();
        }
    }

    previousStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.render();
            this.scrollToTop();
        }
    }

    scrollToTop() {
        this.container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Validation methods
    async validateCurrentStep() {
        this.clearAllErrors();
        
        switch (this.currentStep) {
            case 1:
                return this.validateVesselInformation();
            case 2:
                return this.validateCargoConfiguration();
            case 3:
                return this.validateTeamAssignment();
            case 4:
                return this.validateReview();
            default:
                return true;
        }
    }

    validateVesselInformation() {
        let isValid = true;
        
        const requiredFields = {
            'vessel-name': 'Vessel name is required',
            'vessel-type': 'Vessel type is required', 
            'shipping-line': 'Shipping line is required',
            'berth-assignment': 'Berth assignment is required'
        };
        
        Object.entries(requiredFields).forEach(([fieldId, message]) => {
            const field = document.getElementById(fieldId);
            if (!field || !field.value.trim()) {
                this.showFieldError(fieldId, message);
                isValid = false;
            }
        });
        
        return isValid;
    }

    validateCargoConfiguration() {
        const activeZones = ['brv', 'zee', 'sou'].filter(zone => this.data.cargo[zone]?.enabled);
        
        if (activeZones.length === 0) {
            this.showError('At least one zone must be enabled with cargo');
            return false;
        }
        
        // Check if enabled zones have at least some cargo
        for (const zone of activeZones) {
            const zoneData = this.data.cargo[zone];
            const totalVehicles = (zoneData.cars || 0) + (zoneData.trucks || 0) + (zoneData.special || 0);
            if (totalVehicles === 0) {
                this.showError(`${zone.toUpperCase()} zone is enabled but has no vehicles assigned`);
                return false;
            }
        }
        
        return true;
    }

    validateTeamAssignment() {
        let isValid = true;
        
        // Check required leadership assignments
        if (!this.data.team.autoOpsLead) {
            this.showFieldError('auto-ops-lead', 'Auto Operations Lead is required');
            isValid = false;
        }
        
        if (!this.data.team.heavyOpsLead) {
            this.showFieldError('heavy-ops-lead', 'Heavy Operations Lead is required');
            isValid = false;
        }
        
        // Check stevedore assignments for enabled zones
        ['brv', 'zee', 'sou'].forEach(zone => {
            if (this.data.cargo[zone]?.enabled) {
                const stevedoreCount = this.data.team[zone + 'Stevedores'] || 0;
                if (stevedoreCount < 1) {
                    this.showError(`${zone.toUpperCase()} zone requires at least 1 stevedore`);
                    isValid = false;
                }
            }
        });
        
        return isValid;
    }

    validateReview() {
        if (!this.data.review.confirmed) {
            this.showError('Please confirm that all information is accurate');
            return false;
        }
        return true;
    }

    showFieldError(fieldId, message) {
        const errorElement = document.getElementById(fieldId + '-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
        
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.add('error');
        }
    }

    clearFieldError(fieldId) {
        const errorElement = document.getElementById(fieldId + '-error');
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.style.display = 'none';
        }
        
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.remove('error');
        }
    }

    clearAllErrors() {
        const errorElements = this.container.querySelectorAll('.field-error');
        errorElements.forEach(el => {
            el.textContent = '';
            el.style.display = 'none';
        });
        
        const errorFields = this.container.querySelectorAll('.error');
        errorFields.forEach(field => field.classList.remove('error'));
    }

    showError(message) {
        if (window.fleetApp) {
            window.fleetApp.showError(message);
        } else {
            alert(message);
        }
    }

    showSuccess(message) {
        if (window.fleetApp) {
            window.fleetApp.showNotification(message, 'success');
        } else {
            alert(message);
        }
    }

    // Auto-save functionality
    startAutoSave() {
        if (this.options.autoSave) {
            this.scheduleAutoSave();
        }
    }

    scheduleAutoSave() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        this.autoSaveTimer = setTimeout(() => {
            this.performAutoSave();
        }, this.options.autoSaveInterval);
    }

    async performAutoSave() {
        try {
            if (this.offlineDB) {
                await this.offlineDB.saveWizardData('vessel-operations', this.data);
                this.updateSaveStatus('Auto-saved');
            }
        } catch (error) {
            console.error('Auto-save failed:', error);
            this.updateSaveStatus('Save failed');
        }
    }

    updateSaveStatus(message) {
        const lastSavedEl = document.getElementById('last-saved');
        if (lastSavedEl) {
            lastSavedEl.textContent = `${message} at ${new Date().toLocaleTimeString()}`;
        }
    }

    async loadSavedData() {
        try {
            if (this.offlineDB) {
                const savedData = await this.offlineDB.getWizardData('vessel-operations');
                if (savedData) {
                    this.data = { ...this.data, ...savedData };
                    this.updateSaveStatus('Data loaded');
                }
            }
        } catch (error) {
            console.error('Failed to load saved data:', error);
        }
    }

    // Submission
    async submitOperation() {
        if (this.isSubmitting) return;
        
        this.isSubmitting = true;
        
        try {
            const operationData = this.prepareSubmissionData();
            
            if (window.fleetApp?.isOnline) {
                await this.submitToServer(operationData);
            } else {
                await this.saveForOfflineSubmission(operationData);
            }
            
            this.showSuccess('Vessel operation submitted successfully');
            this.clearSavedData();
            
            // Redirect or reset wizard
            this.resetWizard();
            
        } catch (error) {
            console.error('Submission failed:', error);
            this.showError('Failed to submit operation');
        } finally {
            this.isSubmitting = false;
            this.render(); // Re-render to update button state
        }
    }

    prepareSubmissionData() {
        return {
            timestamp: new Date().toISOString(),
            vessel: this.data.vessel,
            cargo: this.data.cargo,
            team: this.data.team,
            review: this.data.review,
            metadata: {
                submittedBy: window.currentUser?.id,
                clientVersion: '1.0.0',
                deviceInfo: navigator.userAgent
            }
        };
    }

    async submitToServer(data) {
        const response = await fetch('/api/maritime/ship-operations/wizard/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    }

    async saveForOfflineSubmission(data) {
        if (this.offlineDB) {
            await this.offlineDB.saveOfflineSubmission('vessel-operations', data);
        }
    }

    resetWizard() {
        this.currentStep = 1;
        this.data = {
            vessel: {},
            cargo: {},
            team: {},
            review: {}
        };
        this.render();
    }

    async clearSavedData() {
        if (this.offlineDB) {
            await this.offlineDB.clearWizardData('vessel-operations');
        }
    }
}

// Export for global access
window.VesselOperationsWizard = VesselOperationsWizard;