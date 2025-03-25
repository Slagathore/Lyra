import os
import json
import time
import logging
import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ScheduleLearner:
    """Learns and manages the user's daily schedule"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        else:
            self.data_dir = data_dir
            
        # Create the directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.schedule_file = os.path.join(self.data_dir, "user_schedule.json")
        
        # Schedule data
        self.weekly_schedule = {
            "Monday": {},
            "Tuesday": {},
            "Wednesday": {},
            "Thursday": {},
            "Friday": {},
            "Saturday": {},
            "Sunday": {}
        }
        
        # Event history to learn patterns
        self.event_history = []
        
        # Regular activities detected
        self.regular_activities = []
        
        # Last detected user state
        self.last_user_state = "unknown"
        self.last_state_time = time.time()
        
        # Load existing schedule if available
        self.load()
    
    def load(self) -> bool:
        """Load schedule data from disk"""
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "weekly_schedule" in data:
                    self.weekly_schedule = data["weekly_schedule"]
                    
                if "event_history" in data:
                    self.event_history = data["event_history"]
                    
                if "regular_activities" in data:
                    self.regular_activities = data["regular_activities"]
                    
                if "last_user_state" in data:
                    self.last_user_state = data["last_user_state"]
                    
                if "last_state_time" in data:
                    self.last_state_time = data["last_state_time"]
                
                logger.info("Loaded user schedule data")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading schedule data: {str(e)}")
            return False
    
    def save(self) -> bool:
        """Save schedule data to disk"""
        try:
            data = {
                "weekly_schedule": self.weekly_schedule,
                "event_history": self.event_history,
                "regular_activities": self.regular_activities,
                "last_user_state": self.last_user_state,
                "last_state_time": self.last_state_time,
                "timestamp": time.time()
            }
            
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Saved user schedule data")
            return True
        except Exception as e:
            logger.error(f"Error saving schedule data: {str(e)}")
            return False
    
    def record_event(self, activity: str, duration_minutes: int = 0, details: str = ""):
        """Record an activity event"""
        try:
            now = datetime.datetime.now()
            day_of_week = now.strftime("%A")
            hour = now.hour
            minute = now.minute
            
            time_str = f"{hour:02d}:{minute:02d}"
            
            # Create event record
            event = {
                "activity": activity,
                "day": day_of_week,
                "time": time_str,
                "timestamp": time.time(),
                "duration_minutes": duration_minutes,
                "details": details
            }
            
            # Add to event history
            self.event_history.append(event)
            
            # Trim event history if it gets too long
            if len(self.event_history) > 1000:
                self.event_history = self.event_history[-1000:]
                
            # Update weekly schedule
            hour_key = f"{hour:02d}"
            if hour_key not in self.weekly_schedule[day_of_week]:
                self.weekly_schedule[day_of_week][hour_key] = []
                
            # Add activity to this time slot
            activity_entry = {
                "activity": activity,
                "count": 1,
                "last_seen": time.time(),
                "details": details
            }
            
            # Check if this activity exists in this time slot
            existing = False
            for entry in self.weekly_schedule[day_of_week][hour_key]:
                if entry["activity"] == activity:
                    entry["count"] += 1
                    entry["last_seen"] = time.time()
                    if details:
                        entry["details"] = details
                    existing = True
                    break
                    
            if not existing:
                self.weekly_schedule[day_of_week][hour_key].append(activity_entry)
                
            # Sort activities by count (most common first)
            self.weekly_schedule[day_of_week][hour_key].sort(key=lambda x: x["count"], reverse=True)
            
            # Update regular activities
            self._update_regular_activities()
            
            # Save changes
            self.save()
            
            return True
        except Exception as e:
            logger.error(f"Error recording event: {str(e)}")
            return False
    
    def _update_regular_activities(self):
        """Update the list of regular activities based on patterns"""
        # This implementation looks for activities that occur frequently at the same time
        try:
            regular_activities = []
            
            # Minimum count to consider an activity regular
            min_count = 3
            
            # Check each day and time slot
            for day, hours in self.weekly_schedule.items():
                for hour, activities in hours.items():
                    for activity in activities:
                        if activity["count"] >= min_count:
                            regular_activities.append({
                                "day": day,
                                "hour": hour,
                                "activity": activity["activity"],
                                "count": activity["count"],
                                "confidence": min(100, activity["count"] * 10)  # Higher count = higher confidence
                            })
            
            # Sort by count
            regular_activities.sort(key=lambda x: x["count"], reverse=True)
            
            # Update regular activities
            self.regular_activities = regular_activities
            
        except Exception as e:
            logger.error(f"Error updating regular activities: {str(e)}")
    
    def get_current_probable_activity(self) -> Dict[str, Any]:
        """Get the most probable activity for the current time"""
        try:
            now = datetime.datetime.now()
            day_of_week = now.strftime("%A")
            hour = now.hour
            
            hour_key = f"{hour:02d}"
            
            # Check if we have activities for this time slot
            if hour_key in self.weekly_schedule[day_of_week] and self.weekly_schedule[day_of_week][hour_key]:
                # Return the most common activity for this time
                top_activity = self.weekly_schedule[day_of_week][hour_key][0]
                
                return {
                    "activity": top_activity["activity"],
                    "confidence": min(100, top_activity["count"] * 10),
                    "details": top_activity.get("details", "")
                }
            
            # If no data for this specific time, check for any activities on this day
            activities_today = []
            for hour_slot, activities in self.weekly_schedule[day_of_week].items():
                if activities:
                    activities_today.extend(activities)
            
            if activities_today:
                # Sort by count and return the most common activity for this day
                activities_today.sort(key=lambda x: x["count"], reverse=True)
                top_activity = activities_today[0]
                
                return {
                    "activity": top_activity["activity"],
                    "confidence": min(50, top_activity["count"] * 5),  # Lower confidence as it's just the day match
                    "details": top_activity.get("details", "")
                }
            
            # No data for today, return unknown
            return {
                "activity": "unknown",
                "confidence": 0,
                "details": ""
            }
            
        except Exception as e:
            logger.error(f"Error getting probable activity: {str(e)}")
            return {"activity": "unknown", "confidence": 0, "details": ""}
    
    def get_next_scheduled_activity(self) -> Dict[str, Any]:
        """Get the next scheduled activity based on learned patterns"""
        try:
            now = datetime.datetime.now()
            current_day = now.strftime("%A")
            current_hour = now.hour
            current_minute = now.minute
            
            # Build a list of all future activities for today
            future_activities = []
            
            # Check activities for today
            for hour_str, activities in self.weekly_schedule[current_day].items():
                hour = int(hour_str)
                
                # Only consider future hours for today
                if hour > current_hour and activities:
                    for activity in activities:
                        future_activities.append({
                            "day": current_day,
                            "hour": hour,
                            "minute": 0,  # We don't have minute-level precision
                            "activity": activity["activity"],
                            "confidence": min(100, activity["count"] * 10),
                            "details": activity.get("details", "")
                        })
            
            # If we have future activities today, return the earliest one
            if future_activities:
                future_activities.sort(key=lambda x: x["hour"])
                return future_activities[0]
            
            # No future activities today, check for tomorrow
            tomorrow = (now + datetime.timedelta(days=1)).strftime("%A")
            tomorrow_activities = []
            
            for hour_str, activities in self.weekly_schedule[tomorrow].items():
                hour = int(hour_str)
                
                if activities:
                    for activity in activities:
                        tomorrow_activities.append({
                            "day": tomorrow,
                            "hour": hour,
                            "minute": 0,
                            "activity": activity["activity"],
                            "confidence": min(80, activity["count"] * 8),  # Slightly less confidence for tomorrow
                            "details": activity.get("details", "")
                        })
            
            if tomorrow_activities:
                tomorrow_activities.sort(key=lambda x: x["hour"])
                return tomorrow_activities[0]
            
            # No scheduled activities found
            return {
                "activity": "unknown",
                "confidence": 0,
                "day": "unknown",
                "hour": 0,
                "minute": 0,
                "details": ""
            }
            
        except Exception as e:
            logger.error(f"Error getting next activity: {str(e)}")
            return {"activity": "unknown", "confidence": 0, "day": "unknown", "hour": 0, "minute": 0, "details": ""}
    
    def set_user_state(self, state: str):
        """Set the current user state"""
        try:
            self.last_user_state = state
            self.last_state_time = time.time()
            
            # Also record this as an event
            self.record_event(f"User state: {state}")
            
            return True
        except Exception as e:
            logger.error(f"Error setting user state: {str(e)}")
            return False
    
    def get_user_state(self) -> Dict[str, Any]:
        """Get the current user state"""
        return {
            "state": self.last_user_state,
            "last_update": self.last_state_time,
            "elapsed_seconds": time.time() - self.last_state_time
        }
    
    def check_sleep_patterns(self) -> Dict[str, Any]:
        """Analyze sleep patterns based on activity data"""
        try:
            # Look for activities or state changes that could indicate sleep
            sleep_indicators = ["sleeping", "inactive", "away", "User state: away", "User state: inactive"]
            
            sleep_events = []
            for event in self.event_history:
                if any(indicator in event["activity"].lower() for indicator in sleep_indicators):
                    sleep_events.append(event)
            
            # Get the most common sleep and wake times
            sleep_hours = {}
            wake_hours = {}
            
            for i in range(len(sleep_events) - 1):
                current = sleep_events[i]
                next_event = sleep_events[i + 1]
                
                # If we have two consecutive sleep events, one might indicate sleep time and the other wake time
                if current["timestamp"] < next_event["timestamp"]:
                    # Check if this could be a sleep event (typically evening)
                    current_hour = int(current["time"].split(":")[0])
                    if 18 <= current_hour <= 23 or 0 <= current_hour <= 3:
                        sleep_hour = current_hour
                        if sleep_hour not in sleep_hours:
                            sleep_hours[sleep_hour] = 0
                        sleep_hours[sleep_hour] += 1
                    
                    # Check if next could be a wake event (typically morning)
                    next_hour = int(next_event["time"].split(":")[0])
                    if 5 <= next_hour <= 12:
                        wake_hour = next_hour
                        if wake_hour not in wake_hours:
                            wake_hours[wake_hour] = 0
                        wake_hours[wake_hour] += 1
            
            # Find the most common sleep and wake times
            most_common_sleep = max(sleep_hours.items(), key=lambda x: x[1])[0] if sleep_hours else None
            most_common_wake = max(wake_hours.items(), key=lambda x: x[1])[0] if wake_hours else None
            
            return {
                "typical_sleep_hour": most_common_sleep,
                "typical_wake_hour": most_common_wake,
                "sleep_pattern_confidence": min(100, len(sleep_events) * 5),
                "has_enough_data": len(sleep_events) >= 3
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sleep patterns: {str(e)}")
            return {"typical_sleep_hour": None, "typical_wake_hour": None, "sleep_pattern_confidence": 0, "has_enough_data": False}
    
    def get_schedule_for_day(self, day: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get the schedule for a specific day, or today if not specified"""
        if day is None:
            day = datetime.datetime.now().strftime("%A")
            
        if day not in self.weekly_schedule:
            return {}
            
        # Format the schedule for this day into a more usable structure
        formatted_schedule = {}
        
        for hour_str, activities in self.weekly_schedule[day].items():
            if activities:
                hour = int(hour_str)
                formatted_schedule[hour] = []
                
                for activity in activities:
                    formatted_schedule[hour].append({
                        "activity": activity["activity"],
                        "confidence": min(100, activity["count"] * 10),
                        "details": activity.get("details", "")
                    })
        
        return formatted_schedule
    
    def get_regular_activities(self) -> List[Dict[str, Any]]:
        """Get the list of regular activities"""
        return self.regular_activities
    
    def get_suggestions_for_now(self) -> List[Dict[str, Any]]:
        """Get activity suggestions based on the current time"""
        now = datetime.datetime.now()
        day = now.strftime("%A")
        hour = now.hour
        hour_str = f"{hour:02d}"
        
        suggestions = []
        
        # Check this exact time slot first
        if hour_str in self.weekly_schedule[day]:
            for activity in self.weekly_schedule[day][hour_str]:
                suggestions.append({
                    "activity": activity["activity"],
                    "confidence": min(100, activity["count"] * 10),
                    "reason": f"You often do this at {hour:02d}:00 on {day}",
                    "details": activity.get("details", "")
                })
        
        # Add regular activities that occur on this day
        for regular in self.regular_activities:
            if regular["day"] == day and regular["activity"] not in [s["activity"] for s in suggestions]:
                suggestions.append({
                    "activity": regular["activity"],
                    "confidence": regular["confidence"],
                    "reason": f"Regular activity on {day}",
                    "details": ""
                })
        
        # Add some activities from similar times on other days
        for other_day, hours in self.weekly_schedule.items():
            if other_day != day and hour_str in hours:
                for activity in hours[hour_str]:
                    if activity["activity"] not in [s["activity"] for s in suggestions]:
                        suggestions.append({
                            "activity": activity["activity"],
                            "confidence": min(50, activity["count"] * 5),  # Lower confidence for other days
                            "reason": f"You sometimes do this at {hour:02d}:00 on {other_day}",
                            "details": activity.get("details", "")
                        })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Return top 5 suggestions
        return suggestions[:5]

# Global instance
_schedule_learner = None

def get_schedule_learner():
    """Get the global schedule learner instance"""
    global _schedule_learner
    if _schedule_learner is None:
        _schedule_learner = ScheduleLearner()
    return _schedule_learner
