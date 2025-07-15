from app import db

class WizardStep(db.Model):
    __tablename__ = 'wizard_steps'

    id = db.Column(db.Integer, primary_key=True)
    operation_id = db.Column(db.Integer, db.ForeignKey('maritime_operations.id'), nullable=False)
    step_name = db.Column(db.String(100), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<WizardStep {self.step_name}>'
