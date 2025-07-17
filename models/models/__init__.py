# Models package initialization

# Use enhanced models as primary
from .enhanced_user import User
from .enhanced_vessel import Vessel
from .enhanced_task import Task
from .sync_log import SyncLog
from .maritime_models import (
    CargoOperation, 
    MaritimeDocument, 
    DischargeProgress, 
    MaritimeOperationsHelper
)
from .tico_vehicle import (
    TicoVehicle,
    TicoVehicleAssignment,
    TicoVehicleLocation,
    TicoRouteOptimizer
)
from .alert import Alert, AlertGenerator

# Import StevedoreTeam from maritime directory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'maritime'))
from stevedore_team import StevedoreTeam

__all__ = [
    'User',
    'Vessel', 
    'Task',
    'StevedoreTeam',
    'SyncLog',
    'CargoOperation',
    'TicoVehicle',
    'TicoVehicleAssignment',
    'TicoVehicleLocation',
    'TicoRouteOptimizer',
    'MaritimeDocument',
    'DischargeProgress',
    'MaritimeOperationsHelper',
    'Alert',
    'AlertGenerator'
]