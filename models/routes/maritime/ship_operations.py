from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models.maritime.maritime_operation import MaritimeOperation
from models.maritime.wizard_step import WizardStep
from models.maritime.validation import MaritimeValidator
from models.models.vessel import Vessel
import json
from datetime import datetime

maritime_bp = Blueprint('maritime', __name__, template_folder='templates')

# Enhanced single-page wizard route
@maritime_bp.route('/ship_operations/new', methods=['GET'])
def new_ship_operation_wizard():
    """Enhanced single-page maritime operation wizard"""
    vessels = Vessel.query.all()
    return render_template('maritime/ship_operation_wizard.html', vessels=vessels)

# API endpoints for wizard functionality
@maritime_bp.route('/api/wizard/save', methods=['POST'])
def wizard_save():
    """Auto-save wizard progress"""
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
        
        # Update operation with form data
        _update_operation_from_data(operation, data)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'operation_id': operation.id,
            'message': 'Progress saved'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@maritime_bp.route('/api/wizard/validate', methods=['POST'])
def wizard_validate():
    """Real-time validation for wizard fields"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Use Phase 1 validation system
        is_valid, errors = MaritimeValidator.validate_maritime_operation(data)
        
        return jsonify({
            'valid': is_valid,
            'errors': errors,
            'field_errors': _get_field_errors(errors)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@maritime_bp.route('/api/wizard/submit', methods=['POST'])
def wizard_submit():
    """Final wizard submission"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Comprehensive validation
        is_valid, errors = MaritimeValidator.validate_maritime_operation(data)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'errors': errors,
                'field_errors': _get_field_errors(errors)
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
        
        # Update operation with validated data
        _update_operation_from_data(operation, data)
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

@maritime_bp.route('/ship_operations/<int:operation_id>', methods=['GET'])
def ship_operation_details(operation_id):
    """View completed operation details"""
    operation = MaritimeOperation.query.get_or_404(operation_id)
    return render_template('maritime/ship_operation_details.html', operation=operation)

# Helper functions
def _update_operation_from_data(operation, data):
    """Update MaritimeOperation model from form data"""
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
        else:
            # Generic error
            field_errors['general'] = field_errors.get('general', [])
            if isinstance(field_errors['general'], list):
                field_errors['general'].append(error)
            else:
                field_errors['general'] = [field_errors['general'], error]
    
    return field_errors

# Legacy route redirects for backward compatibility
@maritime_bp.route('/ship_operations/new/step1', methods=['GET'])
def legacy_step1():
    """Redirect legacy step1 to new wizard"""
    return redirect(url_for('maritime.new_ship_operation_wizard'))

@maritime_bp.route('/ship_operations/new/step2/<int:operation_id>', methods=['GET'])
def legacy_step2(operation_id):
    """Redirect legacy step2 to new wizard"""
    return redirect(url_for('maritime.new_ship_operation_wizard') + f'?operation_id={operation_id}')

@maritime_bp.route('/ship_operations/new/step3/<int:operation_id>', methods=['GET'])
def legacy_step3(operation_id):
    """Redirect legacy step3 to new wizard"""
    return redirect(url_for('maritime.new_ship_operation_wizard') + f'?operation_id={operation_id}')

@maritime_bp.route('/ship_operations/new/step4/<int:operation_id>', methods=['GET'])
def legacy_step4(operation_id):
    """Redirect legacy step4 to new wizard"""
    return redirect(url_for('maritime.new_ship_operation_wizard') + f'?operation_id={operation_id}')
