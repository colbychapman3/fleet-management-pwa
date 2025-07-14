from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models.maritime.maritime_operation import MaritimeOperation
from models.maritime.wizard_step import WizardStep
from models.models.vessel import Vessel

maritime_bp = Blueprint('maritime', __name__, template_folder='templates')

@maritime_bp.route('/ship_operations/new/step1', methods=['GET', 'POST'])
def new_ship_operation_step1():
    if request.method == 'POST':
        # Create a new maritime operation
        vessel_id = request.form.get('vessel_id')
        operation_type = request.form.get('operation_type')

        new_operation = MaritimeOperation(vessel_id=vessel_id, operation_type=operation_type)
        db.session.add(new_operation)
        db.session.commit()

        # Create the first step of the wizard
        new_step = WizardStep(operation_id=new_operation.id, step_name='Step 1: Operation Details', is_completed=True)
        db.session.add(new_step)
        db.session.commit()

        return redirect(url_for('maritime.new_ship_operation_step2', operation_id=new_operation.id))

    vessels = Vessel.query.all()
    return render_template('maritime/new_ship_operation_step1.html', vessels=vessels)

@maritime_bp.route('/ship_operations/new/step2/<int:operation_id>', methods=['GET', 'POST'])
def new_ship_operation_step2(operation_id):
    operation = MaritimeOperation.query.get_or_404(operation_id)

    if request.method == 'POST':
        # Create the second step
        new_step = WizardStep(operation_id=operation.id, step_name='Step 2: Cargo Information', is_completed=True)
        db.session.add(new_step)
        db.session.commit()
        return redirect(url_for('maritime.new_ship_operation_step3', operation_id=operation.id))

    return render_template('maritime/new_ship_operation_step2.html', operation=operation)

@maritime_bp.route('/ship_operations/new/step3/<int:operation_id>', methods=['GET', 'POST'])
def new_ship_operation_step3(operation_id):
    operation = MaritimeOperation.query.get_or_404(operation_id)

    if request.method == 'POST':
        # Create the third step
        new_step = WizardStep(operation_id=operation.id, step_name='Step 3: Stowage Plan', is_completed=True)
        db.session.add(new_step)
        db.session.commit()
        return redirect(url_for('maritime.new_ship_operation_step4', operation_id=operation.id))

    return render_template('maritime/new_ship_operation_step3.html', operation=operation)

@maritime_bp.route('/ship_operations/new/step4/<int:operation_id>', methods=['GET', 'POST'])
def new_ship_operation_step4(operation_id):
    operation = MaritimeOperation.query.get_or_404(operation_id)

    if request.method == 'POST':
        # Create the fourth step
        new_step = WizardStep(operation_id=operation.id, step_name='Step 4: Confirmation', is_completed=True)
        db.session.add(new_step)

        # Mark the operation as in_progress
        operation.status = 'in_progress'
        db.session.commit()

        flash('New ship operation created successfully!', 'success')
        return redirect(url_for('dashboard.manager'))

    return render_template('maritime/new_ship_operation_step4.html', operation=operation)
