from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models.maritime.maritime_operation import MaritimeOperation
from models.maritime.wizard_step import WizardStep
from models.maritime.validation import MaritimeValidator
from models.models.vessel import Vessel
from models.forms.maritime_forms import (
    MaritimeOperationStep1Form, MaritimeOperationStep2Form,
    MaritimeOperationStep3Form, MaritimeOperationStep4Form,
    MaritimeOperationEditForm, MaritimeOperationWizardForm,
    MaritimeOperationAPIForm
)
import json
from datetime import datetime

maritime_bp = Blueprint('maritime', __name__, template_folder='templates')

# Enhanced single-page wizard route
@maritime_bp.route('/ship_operations/new', methods=['GET', 'POST'])
@login_required
def new_ship_operation_wizard():
    """Enhanced single-page maritime operation wizard with form validation"""
    form = MaritimeOperationWizardForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Create new maritime operation from form data
            operation = MaritimeOperation()
            
            # Populate operation with form data
            _populate_operation_from_form(operation, form)
            operation.status = 'pending'
            
            db.session.add(operation)
            db.session.commit()
            
            flash('Maritime operation created successfully!', 'success')
            return redirect(url_for('maritime.ship_operation_details', operation_id=operation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating operation: {str(e)}', 'error')
    
    vessels = Vessel.query.all()
    return render_template('maritime/ship_operation_wizard.html', form=form, vessels=vessels)

# List operations (from Manus' version)
@maritime_bp.route('/ship_operations')
@login_required
def list_operations():
    """List all maritime operations with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Filter by status if provided
    status_filter = request.args.get('status')
    search_query = request.args.get('search', '')
    
    query = MaritimeOperation.query
    
    if status_filter:
        query = query.filter(MaritimeOperation.status == status_filter)
    
    if search_query:
        query = query.filter(
            db.or_(
                MaritimeOperation.vessel_name.contains(search_query),
                MaritimeOperation.operation_type.contains(search_query),
                MaritimeOperation.shipping_line.contains(search_query),
                MaritimeOperation.port.contains(search_query)
            )
        )
    
    operations = query.order_by(MaritimeOperation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('maritime/operations_list.html', 
                         operations=operations, 
                         status_filter=status_filter,
                         search_query=search_query)

# Edit operation (from Manus' version with enhancements)
@maritime_bp.route('/ship_operations/<int:operation_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_operation(operation_id):
    """Edit an existing maritime operation"""
    operation = MaritimeOperation.query.get_or_404(operation_id)
    form = MaritimeOperationEditForm(obj=operation)
    
    # Populate vessel choices
    form.vessel_id.choices = [(v.id, v.name) for v in Vessel.query.all()]
    
    if form.validate_on_submit():
        try:
            # Update operation with form data
            form.populate_obj(operation)
            operation.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Maritime operation updated successfully!', 'success')
            return redirect(url_for('maritime.ship_operation_details', operation_id=operation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating operation: {str(e)}', 'error')
    
    return render_template('maritime/edit_operation.html', form=form, operation=operation)

# Delete operation (from Manus' version)
@maritime_bp.route('/ship_operations/<int:operation_id>/delete', methods=['POST'])
@login_required
def delete_operation(operation_id):
    """Delete a maritime operation"""
    operation = MaritimeOperation.query.get_or_404(operation_id)
    
    try:
        # Delete associated wizard steps first
        WizardStep.query.filter_by(operation_id=operation_id).delete()
        
        # Delete the operation
        db.session.delete(operation)
        db.session.commit()
        
        flash('Maritime operation deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting operation: {str(e)}', 'error')
    
    return redirect(url_for('maritime.list_operations'))

# API endpoints for wizard functionality (enhanced with form validation)
@maritime_bp.route('/api/wizard/save', methods=['POST'])
@login_required
def wizard_save():
    """Auto-save wizard progress with form validation"""
    try:
        data = request.get_json()
        
        # Validate required fields for save
        if not data or 'operation_id' not in data:
            return jsonify({'error': 'Operation ID required'}), 400
        
        operation_id = data['operation_id']
        
        # Create new operation if needed
        if operation_id == 'new':
            operation = MaritimeOperation()
            db.session.add(operation)
            db.session.flush()  # Get ID without committing
            operation_id = operation.id
        else:
            operation = MaritimeOperation.query.get(operation_id)
            if not operation:
                return jsonify({'error': 'Operation not found'}), 404
        
        # Use form validation for API data
        form = MaritimeOperationAPIForm(data=data)
        
        if form.validate():
            # Update operation with validated form data
            _populate_operation_from_form(operation, form)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'operation_id': operation.id,
                'message': 'Progress saved'
            })
        else:
            # Return validation errors
            return jsonify({
                'success': False,
                'errors': form.errors,
                'message': 'Validation failed'
            }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@maritime_bp.route('/api/wizard/validate', methods=['POST'])
@login_required
def wizard_validate():
    """Real-time validation for wizard fields using form validation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Use form validation for real-time validation
        form = MaritimeOperationAPIForm(data=data)
        
        # Also use Phase 1 validation system as fallback
        is_valid_phase1, phase1_errors = MaritimeValidator.validate_maritime_operation(data)
        
        # Combine form and phase1 validation
        form_valid = form.validate()
        combined_valid = form_valid and is_valid_phase1
        
        # Combine errors
        combined_errors = list(phase1_errors) if phase1_errors else []
        if form.errors:
            for field, errors in form.errors.items():
                combined_errors.extend([f"{field}: {error}" for error in errors])
        
        return jsonify({
            'valid': combined_valid,
            'errors': combined_errors,
            'field_errors': _get_field_errors(combined_errors),
            'form_errors': form.errors if form.errors else {}
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@maritime_bp.route('/api/wizard/submit', methods=['POST'])
@login_required
def wizard_submit():
    """Final wizard submission with comprehensive form validation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Use form validation for submission
        form = MaritimeOperationWizardForm(data=data)
        
        # Also use Phase 1 validation system
        is_valid_phase1, phase1_errors = MaritimeValidator.validate_maritime_operation(data)
        
        # Check both validations
        form_valid = form.validate()
        
        if not form_valid or not is_valid_phase1:
            combined_errors = list(phase1_errors) if phase1_errors else []
            if form.errors:
                for field, errors in form.errors.items():
                    combined_errors.extend([f"{field}: {error}" for error in errors])
            
            return jsonify({
                'success': False,
                'errors': combined_errors,
                'field_errors': _get_field_errors(combined_errors),
                'form_errors': form.errors if form.errors else {}
            }), 400
        
        # Create or update operation
        operation_id = data.get('operation_id')
        
        if operation_id and operation_id != 'new':
            operation = MaritimeOperation.query.get(operation_id)
            if not operation:
                return jsonify({'error': 'Operation not found'}), 404
        else:
            operation = MaritimeOperation()
            db.session.add(operation)
        
        # Update operation with validated form data
        _populate_operation_from_form(operation, form)
        operation.status = 'completed'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'operation_id': operation.id,
            'message': 'Maritime operation created successfully',
            'redirect_url': url_for('maritime.ship_operation_details', operation_id=operation.id)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@maritime_bp.route('/api/wizard/load/<int:operation_id>', methods=['GET'])
@login_required
def wizard_load(operation_id):
    """Load existing operation for editing"""
    try:
        operation = MaritimeOperation.query.get_or_404(operation_id)
        
        return jsonify({
            'success': True,
            'data': operation.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@maritime_bp.route('/api/vessels/search', methods=['GET'])
@login_required
def vessel_search():
    """Search vessels for wizard autocomplete"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        
        if query:
            vessels = Vessel.search_vessels(query)[:limit]
        else:
            vessels = Vessel.get_active_vessels()[:limit]
        
        return jsonify({
            'vessels': [vessel.to_dict() for vessel in vessels]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@maritime_bp.route('/ship_operations/<int:operation_id>')
@login_required
def ship_operation_details(operation_id):
    """View completed operation details"""
    operation = MaritimeOperation.query.get_or_404(operation_id)
    return render_template('maritime/ship_operation_details.html', operation=operation)

# Helper functions
def _update_operation_from_data(operation, data):
    """Update MaritimeOperation model from form data (legacy method)"""
    # Direct field mappings
    field_mappings = {
        'vessel_name': 'vessel_name',
        'vessel_type': 'vessel_type',
        'shipping_line': 'shipping_line',
        'port': 'port',
        'operation_type': 'operation_type',
        'berth': 'berth',
        'operation_manager': 'operation_manager',
        'auto_ops_lead': 'auto_ops_lead',
        'auto_ops_assistant': 'auto_ops_assistant',
        'heavy_ops_lead': 'heavy_ops_lead',
        'heavy_ops_assistant': 'heavy_ops_assistant',
        'total_vehicles': 'total_vehicles',
        'total_automobiles_discharge': 'total_automobiles_discharge',
        'heavy_equipment_discharge': 'heavy_equipment_discharge',
        'total_electric_vehicles': 'total_electric_vehicles',
        'total_static_cargo': 'total_static_cargo',
        'brv_target': 'brv_target',
        'zee_target': 'zee_target',
        'sou_target': 'sou_target',
        'expected_rate': 'expected_rate',
        'total_drivers': 'total_drivers',
        'shift_start': 'shift_start',
        'shift_end': 'shift_end',
        'break_duration': 'break_duration',
        'target_completion': 'target_completion',
        'start_time': 'start_time',
        'estimated_completion': 'estimated_completion',
        'tico_vans': 'tico_vans',
        'tico_station_wagons': 'tico_station_wagons',
        'progress': 'progress',
        'imo_number': 'imo_number',
        'mmsi': 'mmsi',
        'call_sign': 'call_sign',
        'flag_state': 'flag_state'
    }
    
    # Update fields
    for form_field, model_field in field_mappings.items():
        if form_field in data and data[form_field] is not None:
            setattr(operation, model_field, data[form_field])
    
    # Handle date fields
    if 'operation_date' in data and data['operation_date']:
        try:
            operation.operation_date = datetime.strptime(data['operation_date'], '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Handle ETA datetime
    if 'eta' in data and data['eta']:
        try:
            operation.eta = datetime.fromisoformat(data['eta'].replace('Z', '+00:00'))
        except ValueError:
            pass
    
    # Handle JSON fields
    json_fields = ['deck_data', 'turnaround_data', 'inventory_data', 'hourly_quantity_data']
    for field in json_fields:
        if field in data and data[field] is not None:
            setattr(operation, field, json.dumps(data[field]) if isinstance(data[field], (dict, list)) else data[field])

def _populate_operation_from_form(operation, form):
    """Populate MaritimeOperation model from WTForm object"""
    # List of fields to copy from form to operation
    form_fields = [
        'vessel_name', 'vessel_type', 'shipping_line', 'port', 'berth',
        'operation_type', 'operation_date', 'company', 'operation_manager',
        'auto_ops_lead', 'auto_ops_assistant', 'heavy_ops_lead', 'heavy_ops_assistant',
        'total_vehicles', 'total_automobiles_discharge', 'heavy_equipment_discharge',
        'total_electric_vehicles', 'total_static_cargo', 'brv_target', 'zee_target',
        'sou_target', 'expected_rate', 'total_drivers', 'shift_start', 'shift_end',
        'break_duration', 'target_completion', 'start_time', 'estimated_completion',
        'tico_vans', 'tico_station_wagons', 'progress', 'imo_number', 'mmsi',
        'call_sign', 'flag_state', 'eta'
    ]
    
    for field in form_fields:
        if hasattr(form, field) and hasattr(operation, field):
            field_data = getattr(form, field).data
            if field_data is not None:
                setattr(operation, field, field_data)
    
    # Set updated timestamp
    operation.updated_at = datetime.utcnow()

def _get_field_errors(errors):
    """Convert validation errors to field-specific errors"""
    field_errors = {}
    
    for error in errors:
        # Extract field name from error message
        if 'vessel_name' in error.lower():
            field_errors['vessel_name'] = error
        elif 'vessel_type' in error.lower():
            field_errors['vessel_type'] = error
        elif 'shipping_line' in error.lower():
            field_errors['shipping_line'] = error
        elif 'operation_type' in error.lower():
            field_errors['operation_type'] = error
        elif 'imo_number' in error.lower() or 'imo' in error.lower():
            field_errors['imo_number'] = error
        elif 'mmsi' in error.lower():
            field_errors['mmsi'] = error
        elif 'progress' in error.lower():
            field_errors['progress'] = error
        elif 'port' in error.lower():
            field_errors['port'] = error
        elif 'berth' in error.lower():
            field_errors['berth'] = error
        elif 'eta' in error.lower():
            field_errors['eta'] = error
        elif 'call_sign' in error.lower():
            field_errors['call_sign'] = error
        elif 'flag_state' in error.lower():
            field_errors['flag_state'] = error
        else:
            # Generic error
            field_errors['general'] = field_errors.get('general', [])
            if isinstance(field_errors['general'], list):
                field_errors['general'].append(error)
            else:
                field_errors['general'] = [field_errors['general'], error]
    
    return field_errors

# Enhanced multi-step wizard routes
@maritime_bp.route('/ship_operations/new/step1', methods=['GET', 'POST'])
@login_required
def new_ship_operation_step1():
    """Step 1: Operation Details"""
    from models.forms.maritime_forms import MaritimeOperationStep1Form
    from flask import session
    
    form = MaritimeOperationStep1Form()
    
    # Populate vessel choices
    vessels = Vessel.query.all()
    form.vessel_id.choices = [(v.id, v.name) for v in vessels]
    
    if form.validate_on_submit():
        try:
            # Get vessel name for session
            vessel = Vessel.query.get(form.vessel_id.data)
            
            # Store data in session for multi-step wizard
            session['wizard_data'] = {
                'vessel_id': form.vessel_id.data,
                'vessel_name': vessel.name if vessel else 'Unknown',
                'operation_type': form.operation_type.data
            }
            
            # Create a new maritime operation
            new_operation = MaritimeOperation(
                vessel_id=form.vessel_id.data,
                operation_type=form.operation_type.data
            )
            db.session.add(new_operation)
            db.session.flush()  # Get the ID without committing
            
            # Create the first step of the wizard
            new_step = WizardStep(
                operation_id=new_operation.id, 
                step_name='Step 1: Operation Details', 
                is_completed=True
            )
            db.session.add(new_step)
            db.session.commit()
            
            flash('Operation details saved. Please continue with cargo information.', 'info')
            return redirect(url_for('maritime.new_ship_operation_step2', operation_id=new_operation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating operation: {str(e)}', 'error')
    
    return render_template('maritime/new_ship_operation_step1.html', form=form, vessels=vessels)

@maritime_bp.route('/ship_operations/new/step2/<int:operation_id>', methods=['GET', 'POST'])
@login_required
def new_ship_operation_step2(operation_id):
    """Step 2: Cargo Information"""
    from models.forms.maritime_forms import MaritimeOperationStep2Form
    from flask import session
    
    operation = MaritimeOperation.query.get_or_404(operation_id)
    form = MaritimeOperationStep2Form()
    
    if form.validate_on_submit():
        try:
            # Update operation with cargo information
            operation.cargo_type = form.cargo_type.data
            operation.cargo_weight = form.cargo_weight.data
            operation.cargo_description = form.cargo_description.data
            operation.cargo_origin = form.cargo_origin.data
            operation.cargo_destination = form.cargo_destination.data
            operation.updated_at = datetime.utcnow()
            
            # Update session data
            wizard_data = session.get('wizard_data', {})
            wizard_data.update({
                'cargo_type': form.cargo_type.data,
                'cargo_weight': form.cargo_weight.data,
                'cargo_description': form.cargo_description.data,
                'cargo_origin': form.cargo_origin.data,
                'cargo_destination': form.cargo_destination.data
            })
            session['wizard_data'] = wizard_data
            
            # Create the second step
            new_step = WizardStep(
                operation_id=operation.id, 
                step_name='Step 2: Cargo Information', 
                is_completed=True
            )
            db.session.add(new_step)
            db.session.commit()
            
            flash('Cargo information saved. Please continue with stowage plan.', 'info')
            return redirect(url_for('maritime.new_ship_operation_step3', operation_id=operation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving cargo information: {str(e)}', 'error')
    
    return render_template('maritime/new_ship_operation_step2.html', form=form, operation=operation)

@maritime_bp.route('/ship_operations/new/step3/<int:operation_id>', methods=['GET', 'POST'])
@login_required
def new_ship_operation_step3(operation_id):
    """Step 3: Stowage Plan"""
    from models.forms.maritime_forms import MaritimeOperationStep3Form
    from flask import session
    
    operation = MaritimeOperation.query.get_or_404(operation_id)
    form = MaritimeOperationStep3Form()
    
    if form.validate_on_submit():
        try:
            # Update operation with stowage plan
            operation.stowage_location = form.stowage_location.data
            operation.stowage_notes = form.stowage_notes.data
            operation.safety_requirements = form.safety_requirements.data
            operation.loading_sequence = form.loading_sequence.data
            operation.updated_at = datetime.utcnow()
            
            # Update session data
            wizard_data = session.get('wizard_data', {})
            wizard_data.update({
                'stowage_location': form.stowage_location.data,
                'stowage_notes': form.stowage_notes.data,
                'safety_requirements': form.safety_requirements.data,
                'loading_sequence': form.loading_sequence.data
            })
            session['wizard_data'] = wizard_data
            
            # Create the third step
            new_step = WizardStep(
                operation_id=operation.id, 
                step_name='Step 3: Stowage Plan', 
                is_completed=True
            )
            db.session.add(new_step)
            db.session.commit()
            
            flash('Stowage plan saved. Please continue with confirmation details.', 'info')
            return redirect(url_for('maritime.new_ship_operation_step4', operation_id=operation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving stowage plan: {str(e)}', 'error')
    
    return render_template('maritime/new_ship_operation_step3.html', form=form, operation=operation)

@maritime_bp.route('/ship_operations/new/step4/<int:operation_id>', methods=['GET', 'POST'])
@login_required
def new_ship_operation_step4(operation_id):
    """Step 4: Confirmation Details"""
    from models.forms.maritime_forms import MaritimeOperationStep4Form
    from flask import session
    
    operation = MaritimeOperation.query.get_or_404(operation_id)
    form = MaritimeOperationStep4Form()
    
    # Get session data for display
    session_data = session.get('wizard_data', {})
    
    if form.validate_on_submit():
        try:
            # Update operation with confirmation details
            operation.estimated_completion = form.estimated_completion.data
            operation.special_instructions = form.special_instructions.data
            operation.priority_level = form.priority_level.data
            operation.assigned_crew = form.assigned_crew.data
            operation.status = 'in_progress'
            operation.updated_at = datetime.utcnow()
            
            # Create the fourth step
            new_step = WizardStep(
                operation_id=operation.id, 
                step_name='Step 4: Confirmation', 
                is_completed=True
            )
            db.session.add(new_step)
            db.session.commit()
            
            # Clear session data
            session.pop('wizard_data', None)
            
            flash('New ship operation created successfully!', 'success')
            return redirect(url_for('maritime.ship_operation_details', operation_id=operation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error completing operation: {str(e)}', 'error')
    
    return render_template('maritime/new_ship_operation_step4.html', form=form, operation=operation, session_data=session_data)

# API endpoints (from Manus' version)
@maritime_bp.route('/api/operations')
@login_required
def api_operations():
    """API endpoint for maritime operations"""
    operations = MaritimeOperation.query.all()
    return jsonify([op.to_dict() for op in operations])

@maritime_bp.route('/api/operations/<int:operation_id>')
@login_required
def api_operation_detail(operation_id):
    """API endpoint for single maritime operation"""
    operation = MaritimeOperation.query.get_or_404(operation_id)
    return jsonify(operation.to_dict())

# Fix routing conflict by removing the redundant route
# The single-page wizard is already handled by new_ship_operation_wizard above
=======
"""
Maritime Ship Operations API - 4-step wizard implementation
Handles vessel arrival, cargo manifest, team assignment, and berth allocation
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import uuid
import structlog
import json

# Access app components via current_app or direct import
def get_app_db():
    import app
    return app.db

def get_cache_functions():
    import app
    return app.cache_get, app.cache_set, app.cache_delete, app.get_cache_key

from models.models.user import User
from models.models.vessel import Vessel
from models.models.maritime_models import (
    CargoOperation, StevedoreTeam, TicoVehicle, MaritimeDocument, 
    DischargeProgress, MaritimeOperationsHelper
)
from models.models.sync_log import SyncLog

logger = structlog.get_logger()

ship_operations_bp = Blueprint('ship_operations', __name__)

# Maritime role validation decorator
def maritime_access_required(required_roles=None):
    """Decorator to check maritime-specific role permissions"""
    if required_roles is None:
        required_roles = ['manager', 'maritime_supervisor', 'stevedore_lead']
    
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Allow managers full access
            if current_user.is_manager():
                return f(*args, **kwargs)
            
            # Check specific maritime roles
            user_role = getattr(current_user, 'maritime_role', current_user.role)
            if user_role not in required_roles:
                return jsonify({'error': 'Insufficient maritime permissions'}), 403
            
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# Ship Operations Wizard API

@ship_operations_bp.route('/', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def create_ship_operation():
    """
    Step 1: Create new ship operation (vessel arrival)
    POST /api/maritime/ship-operations/
    """
    try:
        data = request.get_json()
        
        # Validate required fields for step 1
        required_fields = ['vessel_name', 'arrival_date', 'expected_duration']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if vessel already exists or create new one
        vessel = Vessel.query.filter_by(name=data['vessel_name']).first()
        if not vessel:
            vessel = Vessel(
                name=data['vessel_name'],
                vessel_type=data.get('vessel_type', 'cargo'),
                status='arriving',
                imo_number=data.get('imo_number'),
                call_sign=data.get('call_sign'),
                flag_state=data.get('flag_state'),
                gross_tonnage=data.get('gross_tonnage'),
                created_at=datetime.utcnow()
            )
        else:
            # Update existing vessel status
            vessel.status = 'arriving'
            vessel.updated_at = datetime.utcnow()
        
        # Parse arrival date
        try:
            arrival_date = datetime.fromisoformat(data['arrival_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid arrival_date format. Use ISO format.'}), 400
        
        # Update vessel with operation details
        vessel.arrival_date = arrival_date
        vessel.expected_duration = data.get('expected_duration')
        vessel.total_vehicles = data.get('total_vehicles', 0)
        vessel.expected_rate = data.get('expected_rate', 150)  # vehicles per hour
        vessel.port_of_origin = data.get('port_of_origin')
        vessel.next_port = data.get('next_port')
        vessel.agent_company = data.get('agent_company')
        vessel.operation_notes = data.get('operation_notes', '')
        
        # Set operation metadata
        operation_metadata = {
            'wizard_step': 1,
            'created_by': current_user.id,
            'operation_id': str(uuid.uuid4()),
            'step_1_completed': True,
            'step_2_completed': False,
            'step_3_completed': False,
            'step_4_completed': False
        }
        vessel.operation_metadata = json.dumps(operation_metadata)
        
        db = get_app_db()
        db.session.add(vessel)
        db.session.commit()
        
        # Log operation creation
        SyncLog.log_action(
            user_id=current_user.id,
            action='create',
            table_name='ship_operations',
            record_id=vessel.id,
            data_after=vessel.to_dict()
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('vessels', '*'))
        cache_delete(get_cache_key('ship_operations', '*'))
        
        logger.info(f"Ship operation created: {vessel.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'Ship operation created successfully',
            'operation': {
                'vessel_id': vessel.id,
                'operation_id': operation_metadata['operation_id'],
                'wizard_step': 1,
                'next_step': 2,
                'vessel': vessel.to_dict()
            }
        }), 201
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Create ship operation error: {e}")
        return jsonify({'error': 'Failed to create ship operation'}), 500

@ship_operations_bp.route('/<int:vessel_id>', methods=['GET'])
@login_required
@maritime_access_required()
def get_ship_operation(vessel_id):
    """
    Get ship operation details with wizard progress
    GET /api/maritime/ship-operations/{id}
    """
    try:
        vessel = Vessel.query.get_or_404(vessel_id)
        
        # Get operation metadata
        operation_metadata = {}
        if vessel.operation_metadata:
            try:
                operation_metadata = json.loads(vessel.operation_metadata)
            except (json.JSONDecodeError, TypeError):
                operation_metadata = {}
        
        # Build comprehensive operation data
        operation_data = {
            'vessel': vessel.to_dict(),
            'wizard_progress': {
                'current_step': operation_metadata.get('wizard_step', 1),
                'step_1_completed': operation_metadata.get('step_1_completed', False),
                'step_2_completed': operation_metadata.get('step_2_completed', False),
                'step_3_completed': operation_metadata.get('step_3_completed', False),
                'step_4_completed': operation_metadata.get('step_4_completed', False),
                'operation_id': operation_metadata.get('operation_id'),
                'created_by': operation_metadata.get('created_by')
            },
            'cargo_operations': [co.to_dict() for co in vessel.cargo_operations] if hasattr(vessel, 'cargo_operations') else [],
            'stevedore_teams': [st.to_dict() for st in vessel.stevedore_teams] if hasattr(vessel, 'stevedore_teams') else [],
            'tico_vehicles': [tv.to_dict() for tv in vessel.tico_vehicles] if hasattr(vessel, 'tico_vehicles') else [],
            'discharge_progress': [dp.to_dict() for dp in vessel.discharge_progress] if hasattr(vessel, 'discharge_progress') else [],
            'maritime_documents': [md.to_dict() for md in vessel.maritime_documents] if hasattr(vessel, 'maritime_documents') else []
        }
        
        # Add zone summary
        operation_data['zone_summary'] = MaritimeOperationsHelper.get_zone_summary(vessel_id)
        
        # Add estimated completion
        estimated_completion = MaritimeOperationsHelper.calculate_estimated_completion(vessel_id)
        operation_data['estimated_completion'] = estimated_completion.isoformat() if estimated_completion else None
        
        return jsonify(operation_data)
        
    except Exception as e:
        logger.error(f"Get ship operation error: {e}")
        return jsonify({'error': 'Failed to retrieve ship operation'}), 500

@ship_operations_bp.route('/<int:vessel_id>/step/<int:step>', methods=['PUT'])
@login_required
@maritime_access_required()
def update_wizard_step(vessel_id, step):
    """
    Update specific wizard step
    PUT /api/maritime/ship-operations/{id}/step/{step}
    """
    try:
        vessel = Vessel.query.get_or_404(vessel_id)
        data = request.get_json()
        
        # Get current operation metadata
        operation_metadata = {}
        if vessel.operation_metadata:
            try:
                operation_metadata = json.loads(vessel.operation_metadata)
            except (json.JSONDecodeError, TypeError):
                operation_metadata = {}
        
        db = get_app_db()
        
        if step == 2:
            # Step 2: Cargo Manifest Processing
            return process_step_2_cargo_manifest(vessel, data, operation_metadata, db)
        elif step == 3:
            # Step 3: Team Assignment
            return process_step_3_team_assignment(vessel, data, operation_metadata, db)
        elif step == 4:
            # Step 4: Berth Allocation
            return process_step_4_berth_allocation(vessel, data, operation_metadata, db)
        else:
            return jsonify({'error': f'Invalid step: {step}'}), 400
            
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Update wizard step error: {e}")
        return jsonify({'error': f'Failed to update step {step}'}), 500

def process_step_2_cargo_manifest(vessel, data, operation_metadata, db):
    """Process Step 2: Cargo Manifest and Vehicle Data"""
    required_fields = ['cargo_manifest']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required for step 2'}), 400
    
    cargo_manifest = data['cargo_manifest']
    
    # Clear existing cargo operations for this vessel
    CargoOperation.query.filter_by(vessel_id=vessel.id).delete()
    
    # Process cargo manifest data
    for cargo_item in cargo_manifest:
        cargo_op = CargoOperation(
            vessel_id=vessel.id,
            zone=cargo_item.get('zone', 'General'),
            vehicle_type=cargo_item.get('vehicle_type'),
            quantity=cargo_item.get('quantity', 0),
            discharged=cargo_item.get('discharged', 0),
            location=cargo_item.get('location', '')
        )
        db.session.add(cargo_op)
    
    # Update vessel totals
    vessel.total_vehicles = sum(item.get('quantity', 0) for item in cargo_manifest)
    
    # Update operation metadata
    operation_metadata.update({
        'wizard_step': 2,
        'step_2_completed': True,
        'step_2_data': {
            'manifest_processed': True,
            'total_cargo_items': len(cargo_manifest),
            'processed_at': datetime.utcnow().isoformat()
        }
    })
    vessel.operation_metadata = json.dumps(operation_metadata)
    
    db.session.commit()
    
    logger.info(f"Step 2 completed for vessel {vessel.id}: cargo manifest processed")
    
    return jsonify({
        'message': 'Cargo manifest processed successfully',
        'step': 2,
        'next_step': 3,
        'cargo_operations': [co.to_dict() for co in vessel.cargo_operations]
    })

def process_step_3_team_assignment(vessel, data, operation_metadata, db):
    """Process Step 3: Stevedore Team Assignment"""
    required_fields = ['teams']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required for step 3'}), 400
    
    teams_data = data['teams']
    
    # Clear existing team assignments for this vessel
    StevedoreTeam.query.filter_by(vessel_id=vessel.id).delete()
    
    # Process team assignments
    teams_created = []
    for team_data in teams_data:
        team = StevedoreTeam(
            vessel_id=vessel.id,
            team_type=team_data.get('team_type', 'General'),
            lead_id=team_data.get('lead_id'),
            assistant_id=team_data.get('assistant_id'),
            shift_start=datetime.strptime(team_data['shift_start'], '%H:%M').time() if team_data.get('shift_start') else None,
            shift_end=datetime.strptime(team_data['shift_end'], '%H:%M').time() if team_data.get('shift_end') else None
        )
        
        # Set team members
        if team_data.get('members'):
            team.set_members(team_data['members'])
        
        db.session.add(team)
        teams_created.append(team)
    
    # Process TICO vehicle assignments if provided
    if data.get('tico_vehicles'):
        TicoVehicle.query.filter_by(vessel_id=vessel.id).delete()
        
        for tico_data in data['tico_vehicles']:
            tico_vehicle = TicoVehicle(
                vessel_id=vessel.id,
                vehicle_type=tico_data.get('vehicle_type', 'Van'),
                vehicle_id=tico_data.get('vehicle_id'),
                capacity=tico_data.get('capacity', 7),
                driver_id=tico_data.get('driver_id'),
                status=tico_data.get('status', 'available')
            )
            db.session.add(tico_vehicle)
    
    # Update operation metadata
    operation_metadata.update({
        'wizard_step': 3,
        'step_3_completed': True,
        'step_3_data': {
            'teams_assigned': len(teams_data),
            'tico_vehicles_assigned': len(data.get('tico_vehicles', [])),
            'processed_at': datetime.utcnow().isoformat()
        }
    })
    vessel.operation_metadata = json.dumps(operation_metadata)
    
    db.session.commit()
    
    logger.info(f"Step 3 completed for vessel {vessel.id}: teams assigned")
    
    return jsonify({
        'message': 'Team assignments completed successfully',
        'step': 3,
        'next_step': 4,
        'teams': [team.to_dict() for team in teams_created],
        'tico_vehicles': [tv.to_dict() for tv in vessel.tico_vehicles] if hasattr(vessel, 'tico_vehicles') else []
    })

def process_step_4_berth_allocation(vessel, data, operation_metadata, db):
    """Process Step 4: Berth Allocation and Final Setup"""
    required_fields = ['berth_assignment']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required for step 4'}), 400
    
    berth_data = data['berth_assignment']
    
    # Update vessel with berth information
    vessel.berth_number = berth_data.get('berth_number')
    vessel.berth_location = berth_data.get('berth_location')
    vessel.berth_side = berth_data.get('berth_side', 'port')
    vessel.status = 'berthed'
    
    # Set operation start time
    if berth_data.get('operation_start_time'):
        try:
            vessel.operation_start = datetime.fromisoformat(berth_data['operation_start_time'].replace('Z', '+00:00'))
        except ValueError:
            vessel.operation_start = datetime.utcnow()
    else:
        vessel.operation_start = datetime.utcnow()
    
    # Update operation metadata
    operation_metadata.update({
        'wizard_step': 4,
        'step_4_completed': True,
        'operation_complete': True,
        'step_4_data': {
            'berth_allocated': True,
            'berth_number': vessel.berth_number,
            'operation_start': vessel.operation_start.isoformat(),
            'processed_at': datetime.utcnow().isoformat()
        }
    })
    vessel.operation_metadata = json.dumps(operation_metadata)
    
    # Create initial discharge progress entry
    initial_progress = DischargeProgress(
        vessel_id=vessel.id,
        zone='All',
        timestamp=datetime.utcnow(),
        vehicles_discharged=0,
        hourly_rate=0.0,
        total_progress=0.0,
        created_by=current_user.id
    )
    db.session.add(initial_progress)
    
    db.session.commit()
    
    # Clear relevant caches
    cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
    cache_delete(get_cache_key('vessels', '*'))
    cache_delete(get_cache_key('ship_operations', '*'))
    
    logger.info(f"Step 4 completed for vessel {vessel.id}: operation fully configured")
    
    return jsonify({
        'message': 'Ship operation setup completed successfully',
        'step': 4,
        'operation_complete': True,
        'vessel': vessel.to_dict(),
        'next_actions': [
            'Begin cargo discharge tracking',
            'Monitor team performance',
            'Update discharge progress regularly'
        ]
    })

@ship_operations_bp.route('/', methods=['GET'])
@login_required
@maritime_access_required()
def list_ship_operations():
    """
    Get list of all ship operations with filtering
    GET /api/maritime/ship-operations/?status=active&page=1&per_page=20
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')  # active, completed, all
        vessel_name = request.args.get('vessel_name')
        
        # Build query
        query = Vessel.query
        
        # Apply status filter
        if status == 'active':
            query = query.filter(Vessel.status.in_(['arriving', 'berthed', 'discharging']))
        elif status == 'completed':
            query = query.filter(Vessel.status.in_(['departed', 'completed']))
        
        # Apply vessel name filter
        if vessel_name:
            query = query.filter(Vessel.name.ilike(f'%{vessel_name}%'))
        
        # Only show vessels with operation metadata (ship operations)
        query = query.filter(Vessel.operation_metadata.isnot(None))
        
        # Order by arrival date (most recent first)
        query = query.order_by(Vessel.arrival_date.desc())
        
        # Paginate
        vessels_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Build response with operation summaries
        operations = []
        for vessel in vessels_paginated.items:
            operation_metadata = {}
            if vessel.operation_metadata:
                try:
                    operation_metadata = json.loads(vessel.operation_metadata)
                except (json.JSONDecodeError, TypeError):
                    operation_metadata = {}
            
            operation_summary = {
                'vessel': vessel.to_dict(),
                'wizard_progress': {
                    'current_step': operation_metadata.get('wizard_step', 1),
                    'operation_complete': operation_metadata.get('operation_complete', False),
                    'operation_id': operation_metadata.get('operation_id')
                },
                'summary_stats': {
                    'total_vehicles': vessel.total_vehicles or 0,
                    'estimated_completion': MaritimeOperationsHelper.calculate_estimated_completion(vessel.id).isoformat() if MaritimeOperationsHelper.calculate_estimated_completion(vessel.id) else None
                }
            }
            
            # Add latest progress if available
            latest_progress = DischargeProgress.get_latest_progress_by_vessel(vessel.id)
            if latest_progress:
                operation_summary['latest_progress'] = latest_progress.to_dict()
            
            operations.append(operation_summary)
        
        return jsonify({
            'operations': operations,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': vessels_paginated.total,
                'pages': vessels_paginated.pages,
                'has_next': vessels_paginated.has_next,
                'has_prev': vessels_paginated.has_prev
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"List ship operations error: {e}")
        return jsonify({'error': 'Failed to retrieve ship operations'}), 500

@ship_operations_bp.route('/<int:vessel_id>', methods=['DELETE'])
@login_required
@maritime_access_required(['manager'])
def delete_ship_operation(vessel_id):
    """
    Delete ship operation (managers only)
    DELETE /api/maritime/ship-operations/{id}
    """
    try:
        vessel = Vessel.query.get_or_404(vessel_id)
        
        # Store data for logging
        vessel_data = vessel.to_dict()
        
        # Delete related maritime data
        CargoOperation.query.filter_by(vessel_id=vessel_id).delete()
        StevedoreTeam.query.filter_by(vessel_id=vessel_id).delete()
        TicoVehicle.query.filter_by(vessel_id=vessel_id).delete()
        DischargeProgress.query.filter_by(vessel_id=vessel_id).delete()
        MaritimeDocument.query.filter_by(vessel_id=vessel_id).delete()
        
        # Log deletion before removing vessel
        SyncLog.log_action(
            user_id=current_user.id,
            action='delete',
            table_name='ship_operations',
            record_id=vessel_id,
            data_before=vessel_data
        )
        
        db = get_app_db()
        db.session.delete(vessel)
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('vessels', '*'))
        cache_delete(get_cache_key('ship_operations', '*'))
        
        logger.info(f"Ship operation deleted: {vessel_id} by user {current_user.id}")
        
        return jsonify({'message': 'Ship operation deleted successfully'})
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Delete ship operation error: {e}")
        return jsonify({'error': 'Failed to delete ship operation'}), 500
>>>>>>> maritime-integration
