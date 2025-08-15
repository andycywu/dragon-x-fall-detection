from typing import Dict, List
import time
from dataclasses import dataclass

@dataclass
class AlertEvent:
    """Represents an alert event with timestamp and details."""
    timestamp: float
    fall_detected: bool
    help_detected: bool
    confidence: float
    message: str

class FusionTrigger:
    def __init__(self, cooldown_seconds: float = 5.0):
        """
        Initialize fusion trigger with cooldown period.
        Args:
            cooldown_seconds: Minimum time between alerts to prevent spam
        """
        self.cooldown_seconds = cooldown_seconds
        self.last_alert_time = 0
        self.alert_history: List[AlertEvent] = []
        
    def should_trigger_alert(self, fall_detected: bool, help_detected: bool) -> bool:
        """
        Determine if an alert should be triggered based on detection results.
        Args:
            fall_detected: Whether a fall was detected
            help_detected: Whether help keyword was detected
        Returns:
            bool: True if alert should be triggered
        """
        current_time = time.time()
        
        # Check if either detection method triggered
        should_alert = fall_detected or help_detected
        
        # Apply cooldown to prevent spam alerts
        if should_alert and (current_time - self.last_alert_time) >= self.cooldown_seconds:
            self.last_alert_time = current_time
            
            # Create alert event
            confidence = self._calculate_confidence(fall_detected, help_detected)
            message = self._generate_alert_message(fall_detected, help_detected)
            
            alert_event = AlertEvent(
                timestamp=current_time,
                fall_detected=fall_detected,
                help_detected=help_detected,
                confidence=confidence,
                message=message
            )
            
            self.alert_history.append(alert_event)
            
            # Keep only last 100 alerts
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]
                
            return True
            
        return False
    
    def _calculate_confidence(self, fall_detected: bool, help_detected: bool) -> float:
        """Calculate confidence score for the alert."""
        if fall_detected and help_detected:
            return 0.95  # Very high confidence when both detected
        elif fall_detected or help_detected:
            return 0.75  # Medium-high confidence for single detection
        else:
            return 0.0
    
    def _generate_alert_message(self, fall_detected: bool, help_detected: bool) -> str:
        """Generate appropriate alert message."""
        if fall_detected and help_detected:
            return "EMERGENCY: Fall detected and help requested!"
        elif fall_detected:
            return "ALERT: Potential fall detected!"
        elif help_detected:
            return "ALERT: Help request detected!"
        else:
            return "No alert"
    
    def get_recent_alerts(self, last_n: int = 10) -> List[AlertEvent]:
        """Get the most recent alerts."""
        return self.alert_history[-last_n:] if self.alert_history else []
    
    def clear_history(self):
        """Clear alert history."""
        self.alert_history.clear()

# Global fusion trigger instance
_fusion_trigger = None

def should_trigger_alert(fall_detected: bool, help_detected: bool) -> bool:
    """
    Legacy function for backward compatibility.
    Determine if alert should be triggered using global fusion trigger.
    """
    global _fusion_trigger
    if _fusion_trigger is None:
        _fusion_trigger = FusionTrigger()
    return _fusion_trigger.should_trigger_alert(fall_detected, help_detected)
