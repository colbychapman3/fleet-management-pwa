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
