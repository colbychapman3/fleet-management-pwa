"""
Forms module for the Fleet Management PWA
Contains WTForms classes for maritime operations and other forms
"""

from .maritime_forms import (
    MaritimeOperationStep1Form,
    MaritimeOperationStep2Form,
    MaritimeOperationStep3Form,
    MaritimeOperationStep4Form,
    MaritimeOperationEditForm
)

__all__ = [
    'MaritimeOperationStep1Form',
    'MaritimeOperationStep2Form',
    'MaritimeOperationStep3Form',
    'MaritimeOperationStep4Form',
    'MaritimeOperationEditForm'
]