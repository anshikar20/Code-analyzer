from fastapi import APIRouter
from ..services.history_service import history_service
from collections import defaultdict
from datetime import datetime

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("")
async def get_analytics():
    """Get aggregated scan history for the Analytics dashboard."""
    history = history_service.get_history()
    
    if not history:
        # Return default shape if no data yet
        return {
            "trendData": [],
            "categoryData": [
                {"name": "Security", "value": 0},
                {"name": "Quality", "value": 0},
                {"name": "Performance", "value": 0},
                {"name": "Style", "value": 0},
            ]
        }

    # Process trend data (aggregate by hour or just keep sequential scans)
    trend_data = []
    # To keep it simple, we'll return the last 10 scans as "time" points for the chart
    for i, scan in enumerate(history[-10:]):
        # Format time nicely, e.g. "HH:MM:SS"
        try:
            from datetime import timezone
            dt = datetime.fromisoformat(scan["timestamp"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone()
            time_str = dt.strftime("%I:%M:%S %p")
        except:
            time_str = f"Scan {i+1}"
            
        trend_data.append({
            "time": time_str,
            "issues": scan["total_issues"],
            "security": scan["security"],
            "quality": scan["quality"]
        })

    # Category data is an aggregate of all issues across the stored history
    total_sec = sum(s["security"] for s in history)
    total_qual = sum(s["quality"] for s in history)
    total_perf = sum(s["performance"] for s in history)
    total_style = sum(s["style"] for s in history)

    category_data = [
        {"name": "Security", "value": total_sec},
        {"name": "Quality", "value": total_qual},
        {"name": "Performance", "value": total_perf},
        {"name": "Style", "value": total_style},
    ]

    return {
        "trendData": trend_data,
        "categoryData": category_data
    }
