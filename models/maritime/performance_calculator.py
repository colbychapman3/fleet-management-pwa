"""
Team Performance Calculator for Maritime Stevedoring Operations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from statistics import mean, median

class TeamPerformanceCalculator:
    """
    Comprehensive team performance calculator for stevedoring operations
    """
    
    # Performance benchmarks and targets
    PERFORMANCE_BENCHMARKS = {
        'efficiency': {
            'excellent': 95.0,
            'good': 85.0,
            'average': 75.0,
            'poor': 65.0
        },
        'throughput': {
            'excellent': 200.0,  # MT/hour
            'good': 150.0,
            'average': 100.0,
            'poor': 75.0
        },
        'safety': {
            'excellent': 0.0,    # Incidents per 100 operations
            'good': 0.5,
            'average': 1.0,
            'poor': 2.0
        },
        'completion_rate': {
            'excellent': 98.0,   # Percentage
            'good': 92.0,
            'average': 85.0,
            'poor': 75.0
        }
    }
    
    @staticmethod
    def calculate_team_efficiency(cargo_processed: float, hours_worked: float, 
                                 target_throughput: float = 150.0) -> float:
        """
        Calculate team efficiency based on cargo processed vs target throughput
        
        Args:
            cargo_processed: Metric tons of cargo processed
            hours_worked: Hours worked by the team
            target_throughput: Target throughput in MT/hour
            
        Returns:
            Efficiency rating as percentage (0-100)
        """
        if hours_worked <= 0:
            return 0.0
        
        actual_throughput = cargo_processed / hours_worked
        efficiency = (actual_throughput / target_throughput) * 100
        
        # Cap efficiency at 100% for standard calculation
        return min(efficiency, 100.0)
    
    @staticmethod
    def calculate_cargo_throughput(cargo_processed: float, hours_worked: float) -> float:
        """
        Calculate cargo throughput in MT/hour
        
        Args:
            cargo_processed: Metric tons of cargo processed
            hours_worked: Hours worked by the team
            
        Returns:
            Throughput in MT/hour
        """
        if hours_worked <= 0:
            return 0.0
        
        return cargo_processed / hours_worked
    
    @staticmethod
    def calculate_safety_incident_rate(safety_incidents: int, operations_count: int) -> float:
        """
        Calculate safety incident rate per 100 operations
        
        Args:
            safety_incidents: Number of safety incidents
            operations_count: Number of operations
            
        Returns:
            Safety incident rate per 100 operations
        """
        if operations_count <= 0:
            return 0.0
        
        return (safety_incidents / operations_count) * 100
    
    @staticmethod
    def calculate_operation_completion_rate(completed_operations: int, total_operations: int) -> float:
        """
        Calculate operation completion rate
        
        Args:
            completed_operations: Number of completed operations
            total_operations: Total number of operations
            
        Returns:
            Completion rate as percentage
        """
        if total_operations <= 0:
            return 0.0
        
        return (completed_operations / total_operations) * 100
    
    @staticmethod
    def calculate_workload_distribution(team_performances: Dict[str, Dict]) -> Dict[str, float]:
        """
        Calculate workload distribution across teams
        
        Args:
            team_performances: Dictionary of team performance data
            
        Returns:
            Dictionary with team workload percentages
        """
        total_cargo = sum(
            team_data.get('cargo_processed', 0.0) 
            for team_data in team_performances.values()
        )
        
        if total_cargo <= 0:
            return {team_id: 0.0 for team_id in team_performances.keys()}
        
        workload_distribution = {}
        for team_id, team_data in team_performances.items():
            team_cargo = team_data.get('cargo_processed', 0.0)
            workload_distribution[team_id] = (team_cargo / total_cargo) * 100
        
        return workload_distribution
    
    @staticmethod
    def calculate_team_performance_trend(historical_data: List[Dict], 
                                       days_back: int = 30) -> Dict[str, float]:
        """
        Calculate team performance trend over time
        
        Args:
            historical_data: List of historical performance data
            days_back: Number of days to look back
            
        Returns:
            Dictionary with trend indicators
        """
        if not historical_data:
            return {'trend': 0.0, 'direction': 'stable'}
        
        # Filter data by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        recent_data = [
            data for data in historical_data 
            if datetime.fromisoformat(data.get('timestamp', '')) >= cutoff_date
        ]
        
        if len(recent_data) < 2:
            return {'trend': 0.0, 'direction': 'stable'}
        
        # Calculate trend in efficiency
        efficiencies = [data.get('efficiency', 0.0) for data in recent_data]
        first_half = efficiencies[:len(efficiencies)//2]
        second_half = efficiencies[len(efficiencies)//2:]
        
        first_avg = mean(first_half) if first_half else 0.0
        second_avg = mean(second_half) if second_half else 0.0
        
        if first_avg > 0:
            trend = ((second_avg - first_avg) / first_avg) * 100
        else:
            trend = 0.0
        
        # Determine direction
        if trend > 5:
            direction = 'improving'
        elif trend < -5:
            direction = 'declining'
        else:
            direction = 'stable'
        
        return {'trend': trend, 'direction': direction}
    
    @staticmethod
    def get_performance_rating(metric_value: float, metric_type: str) -> str:
        """
        Get performance rating based on metric value and type
        
        Args:
            metric_value: Value of the metric
            metric_type: Type of metric (efficiency, throughput, safety, completion_rate)
            
        Returns:
            Performance rating string
        """
        if metric_type not in TeamPerformanceCalculator.PERFORMANCE_BENCHMARKS:
            return 'unknown'
        
        benchmarks = TeamPerformanceCalculator.PERFORMANCE_BENCHMARKS[metric_type]
        
        # For safety metrics, lower is better
        if metric_type == 'safety':
            if metric_value <= benchmarks['excellent']:
                return 'excellent'
            elif metric_value <= benchmarks['good']:
                return 'good'
            elif metric_value <= benchmarks['average']:
                return 'average'
            else:
                return 'poor'
        else:
            # For other metrics, higher is better
            if metric_value >= benchmarks['excellent']:
                return 'excellent'
            elif metric_value >= benchmarks['good']:
                return 'good'
            elif metric_value >= benchmarks['average']:
                return 'average'
            else:
                return 'poor'
    
    @staticmethod
    def calculate_team_score(efficiency: float, throughput: float, 
                           safety_rate: float, completion_rate: float) -> float:
        """
        Calculate overall team performance score
        
        Args:
            efficiency: Team efficiency percentage
            throughput: Team throughput in MT/hour
            safety_rate: Safety incident rate
            completion_rate: Operation completion rate
            
        Returns:
            Overall performance score (0-100)
        """
        # Normalize throughput to 0-100 scale
        throughput_normalized = min((throughput / 200) * 100, 100)
        
        # Safety score (invert since lower is better)
        safety_score = max(0, 100 - (safety_rate * 20))
        
        # Weighted average of all metrics
        weights = {
            'efficiency': 0.35,
            'throughput': 0.25,
            'safety': 0.25,
            'completion': 0.15
        }
        
        total_score = (
            efficiency * weights['efficiency'] +
            throughput_normalized * weights['throughput'] +
            safety_score * weights['safety'] +
            completion_rate * weights['completion']
        )
        
        return round(total_score, 2)
    
    @staticmethod
    def identify_performance_bottlenecks(team_performances: Dict[str, Dict]) -> List[Dict]:
        """
        Identify performance bottlenecks and improvement opportunities
        
        Args:
            team_performances: Dictionary of team performance data
            
        Returns:
            List of bottleneck findings
        """
        bottlenecks = []
        
        for team_id, performance in team_performances.items():
            efficiency = performance.get('efficiency', 0.0)
            throughput = performance.get('throughput_rate', 0.0)
            safety_rate = performance.get('safety_incident_rate', 0.0)
            completion_rate = performance.get('completion_rate', 0.0)
            
            # Check for low efficiency
            if efficiency < 70:
                bottlenecks.append({
                    'team_id': team_id,
                    'type': 'efficiency',
                    'severity': 'high' if efficiency < 60 else 'medium',
                    'current_value': efficiency,
                    'target_value': 85.0,
                    'recommendation': 'Review team processes and provide efficiency training'
                })
            
            # Check for low throughput
            if throughput < 100:
                bottlenecks.append({
                    'team_id': team_id,
                    'type': 'throughput',
                    'severity': 'high' if throughput < 75 else 'medium',
                    'current_value': throughput,
                    'target_value': 150.0,
                    'recommendation': 'Analyze cargo handling processes and equipment utilization'
                })
            
            # Check for high safety incidents
            if safety_rate > 1.0:
                bottlenecks.append({
                    'team_id': team_id,
                    'type': 'safety',
                    'severity': 'high' if safety_rate > 2.0 else 'medium',
                    'current_value': safety_rate,
                    'target_value': 0.5,
                    'recommendation': 'Implement additional safety training and procedures'
                })
            
            # Check for low completion rate
            if completion_rate < 85:
                bottlenecks.append({
                    'team_id': team_id,
                    'type': 'completion',
                    'severity': 'high' if completion_rate < 75 else 'medium',
                    'current_value': completion_rate,
                    'target_value': 92.0,
                    'recommendation': 'Review task assignment and resource allocation'
                })
        
        return bottlenecks
    
    @staticmethod
    def calculate_team_utilization(team_performances: Dict[str, Dict], 
                                 total_available_hours: float) -> Dict[str, float]:
        """
        Calculate team utilization rates
        
        Args:
            team_performances: Dictionary of team performance data
            total_available_hours: Total available working hours
            
        Returns:
            Dictionary with team utilization percentages
        """
        utilization = {}
        
        for team_id, performance in team_performances.items():
            hours_worked = performance.get('hours_worked', 0.0)
            if total_available_hours > 0:
                utilization[team_id] = (hours_worked / total_available_hours) * 100
            else:
                utilization[team_id] = 0.0
        
        return utilization
    
    @staticmethod
    def generate_performance_insights(team_performances: Dict[str, Dict], 
                                    historical_data: Optional[List[Dict]] = None) -> Dict:
        """
        Generate comprehensive performance insights
        
        Args:
            team_performances: Current team performance data
            historical_data: Historical performance data for trends
            
        Returns:
            Dictionary with performance insights
        """
        insights = {
            'summary': {},
            'top_performers': [],
            'improvement_needed': [],
            'bottlenecks': [],
            'recommendations': []
        }
        
        # Calculate summary metrics
        if team_performances:
            efficiencies = [p.get('efficiency', 0.0) for p in team_performances.values()]
            throughputs = [p.get('throughput_rate', 0.0) for p in team_performances.values()]
            safety_rates = [p.get('safety_incident_rate', 0.0) for p in team_performances.values()]
            
            insights['summary'] = {
                'average_efficiency': mean(efficiencies) if efficiencies else 0.0,
                'median_efficiency': median(efficiencies) if efficiencies else 0.0,
                'average_throughput': mean(throughputs) if throughputs else 0.0,
                'average_safety_rate': mean(safety_rates) if safety_rates else 0.0,
                'total_teams': len(team_performances)
            }
        
        # Identify top performers and teams needing improvement
        for team_id, performance in team_performances.items():
            efficiency = performance.get('efficiency', 0.0)
            throughput = performance.get('throughput_rate', 0.0)
            safety_rate = performance.get('safety_incident_rate', 0.0)
            
            team_score = TeamPerformanceCalculator.calculate_team_score(
                efficiency, throughput, safety_rate, 
                performance.get('completion_rate', 0.0)
            )
            
            team_info = {
                'team_id': team_id,
                'team_name': performance.get('team_name', f'Team {team_id}'),
                'score': team_score,
                'efficiency': efficiency,
                'throughput': throughput,
                'safety_rate': safety_rate
            }
            
            if team_score >= 85:
                insights['top_performers'].append(team_info)
            elif team_score < 70:
                insights['improvement_needed'].append(team_info)
        
        # Sort by score
        insights['top_performers'].sort(key=lambda x: x['score'], reverse=True)
        insights['improvement_needed'].sort(key=lambda x: x['score'])
        
        # Identify bottlenecks
        insights['bottlenecks'] = TeamPerformanceCalculator.identify_performance_bottlenecks(
            team_performances
        )
        
        # Generate recommendations
        insights['recommendations'] = TeamPerformanceCalculator._generate_recommendations(
            team_performances, insights['bottlenecks']
        )
        
        return insights
    
    @staticmethod
    def _generate_recommendations(team_performances: Dict[str, Dict], 
                                bottlenecks: List[Dict]) -> List[str]:
        """
        Generate performance improvement recommendations
        
        Args:
            team_performances: Team performance data
            bottlenecks: Identified bottlenecks
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for efficiency issues
        low_efficiency_teams = [
            team_id for team_id, perf in team_performances.items()
            if perf.get('efficiency', 0.0) < 75
        ]
        
        if low_efficiency_teams:
            recommendations.append(
                f"Provide efficiency training for {len(low_efficiency_teams)} teams "
                f"with below-average performance"
            )
        
        # Check for throughput issues
        low_throughput_teams = [
            team_id for team_id, perf in team_performances.items()
            if perf.get('throughput_rate', 0.0) < 100
        ]
        
        if low_throughput_teams:
            recommendations.append(
                f"Review cargo handling processes for {len(low_throughput_teams)} teams "
                f"with low throughput rates"
            )
        
        # Check for safety issues
        high_safety_teams = [
            team_id for team_id, perf in team_performances.items()
            if perf.get('safety_incident_rate', 0.0) > 1.0
        ]
        
        if high_safety_teams:
            recommendations.append(
                f"Implement additional safety measures for {len(high_safety_teams)} teams "
                f"with elevated incident rates"
            )
        
        # Check for workload balance
        workload_distribution = TeamPerformanceCalculator.calculate_workload_distribution(
            team_performances
        )
        
        workload_values = list(workload_distribution.values())
        if workload_values:
            max_workload = max(workload_values)
            min_workload = min(workload_values)
            
            if max_workload - min_workload > 30:  # 30% difference
                recommendations.append(
                    "Consider redistributing workload to balance team utilization"
                )
        
        return recommendations