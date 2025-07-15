from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models.maritime.maritime_operation import MaritimeOperation
from models.maritime.wizard_step import WizardStep
from models.models.vessel import Vessel
from models.forms.maritime_forms import (
    MaritimeOperationStep1Form, MaritimeOperationStep2Form, 
    MaritimeOperationStep3Form, MaritimeOperationStep4Form,
    MaritimeOperationEditForm
)
from datetime import datetime

maritime_bp = Blueprint('maritime', __name__, template_folder='templates')

@maritime_bp.route('/ship_operations')
@login_required
def list_operations():
    """List all maritime operations"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Filter by status if provided
    status_filter = request.args.get('status')
    search_query = request.args.get('search', '')
    
    query = MaritimeOperation.query
    
    if status_filter:
        query = query.filter(MaritimeOperation.status == status_filter)
    
    if search_query:
        query = query.join(Vessel).filter(
            db.or_(
                MaritimeOperation.operation_type.contains(search_query),
                MaritimeOperation.cargo_type.contains(search_query),
                Vessel.name.contains(search_query)
            )
        )
    
    operations = query.order_by(MaritimeOperation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('maritime/operations_list.html', 
                         operations=operations, 
                         status_filter=status_filter,
                         search_query=search_query)

@maritime_bp.route('/ship_operations/<int:operation_id>')
@login_required
def view_operation(operation_id):
    """View details of a specific maritime operation"""
    operation = MaritimeOperation.query.get_or_404(operation_id)
    return render_template('maritime/operation_detail.html', operation=operation)

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
            return redirect(url_for('maritime.view_operation', operation_id=operation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating operation: {str(e)}', 'error')
    
    return render_template('maritime/edit_operation.html', form=form, operation=operation)

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

@maritime_bp.route('/ship_operations/new/step1', methods=['GET', 'POST'])
@login_required
def new_ship_operation_step1():
    """Step 1: Operation Details"""
    form = MaritimeOperationStep1Form()
    
    # Populate vessel choices
    form.vessel_id.choices = [(v.id, v.name) for v in Vessel.query.all()]
    
    if form.validate_on_submit():
        try:
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
    
    return render_template('maritime/new_ship_operation_step1.html', form=form)

@maritime_bp.route('/ship_operations/new/step2/<int:operation_id>', methods=['GET', 'POST'])
@login_required
def new_ship_operation_step2(operation_id):
    """Step 2: Cargo Information"""
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
    operation = MaritimeOperation.query.get_or_404(operation_id)
    form = MaritimeOperationStep4Form()
    
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
            
            flash('New ship operation created successfully!', 'success')
            return redirect(url_for('maritime.view_operation', operation_id=operation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error completing operation: {str(e)}', 'error')
    
    return render_template('maritime/new_ship_operation_step4.html', form=form, operation=operation)

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
