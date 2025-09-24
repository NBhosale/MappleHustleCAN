"""
Security monitoring dashboard endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.db.session import get_db
from app.core.security_hardening import get_security_hardening
from app.core.security_monitoring import get_security_monitor, SecurityEventType

router = APIRouter(prefix="/security", tags=["Security Dashboard"])


@router.get("/dashboard")
async def get_security_dashboard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive security dashboard data
    """
    security = get_security_hardening()
    monitor = get_security_monitor()
    
    # Get security metrics
    metrics = monitor.get_security_metrics()
    
    # Get recent security events
    recent_events = monitor.get_recent_events(hours=24)
    
    # Get threat intelligence
    threat_intel = security.get_threat_intelligence()
    
    # Get security recommendations
    recommendations = security.get_security_recommendations()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "healthy" if metrics["threat_level"] == "low" else "warning",
        "metrics": metrics,
        "recent_events": recent_events,
        "threat_intelligence": threat_intel,
        "recommendations": recommendations,
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/events")
async def get_security_events(
    hours: int = 24,
    event_type: str = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get security events with filtering
    """
    monitor = get_security_monitor()
    
    events = monitor.get_recent_events(hours=hours)
    
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    
    return {
        "events": events,
        "total_count": len(events),
        "time_range_hours": hours,
        "event_type_filter": event_type
    }


@router.get("/threats")
async def get_threat_analysis(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current threat analysis
    """
    security = get_security_hardening()
    monitor = get_security_monitor()
    
    # Get threat intelligence
    threat_intel = security.get_threat_intelligence()
    
    # Get security metrics
    metrics = monitor.get_security_metrics()
    
    # Analyze threat patterns
    recent_events = monitor.get_recent_events(hours=1)
    threat_patterns = security.analyze_threat_patterns(recent_events)
    
    return {
        "threat_level": metrics["threat_level"],
        "threat_intelligence": threat_intel,
        "threat_patterns": threat_patterns,
        "active_threats": len([e for e in recent_events if e.get("severity") == "high"]),
        "last_analysis": datetime.utcnow().isoformat()
    }


@router.get("/recommendations")
async def get_security_recommendations(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get security recommendations
    """
    security = get_security_hardening()
    
    recommendations = security.get_security_recommendations()
    
    return {
        "recommendations": recommendations,
        "total_count": len(recommendations),
        "priority_high": len([r for r in recommendations if r.get("priority") == "high"]),
        "priority_medium": len([r for r in recommendations if r.get("priority") == "medium"]),
        "priority_low": len([r for r in recommendations if r.get("priority") == "low"])
    }


@router.get("/alerts")
async def get_security_alerts(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get active security alerts
    """
    monitor = get_security_monitor()
    
    alerts = monitor.get_active_alerts()
    
    return {
        "alerts": alerts,
        "total_count": len(alerts),
        "critical_count": len([a for a in alerts if a.get("severity") == "critical"]),
        "warning_count": len([a for a in alerts if a.get("severity") == "warning"]),
        "info_count": len([a for a in alerts if a.get("severity") == "info"])
    }


@router.get("/compliance")
async def get_compliance_status(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get security compliance status
    """
    security = get_security_hardening()
    
    compliance = security.get_compliance_status()
    
    return {
        "compliance": compliance,
        "overall_score": compliance.get("overall_score", 0),
        "status": "compliant" if compliance.get("overall_score", 0) >= 80 else "non_compliant",
        "last_assessment": datetime.utcnow().isoformat()
    }


@router.get("/incidents")
async def get_security_incidents(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get security incidents
    """
    monitor = get_security_monitor()
    
    incidents = monitor.get_security_incidents()
    
    return {
        "incidents": incidents,
        "total_count": len(incidents),
        "open_count": len([i for i in incidents if i.get("status") == "open"]),
        "resolved_count": len([i for i in incidents if i.get("status") == "resolved"]),
        "investigating_count": len([i for i in incidents if i.get("status") == "investigating"])
    }


@router.get("/vulnerabilities")
async def get_vulnerability_scan(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get vulnerability scan results
    """
    security = get_security_hardening()
    
    vulnerabilities = security.get_vulnerability_scan()
    
    return {
        "vulnerabilities": vulnerabilities,
        "total_count": len(vulnerabilities),
        "critical_count": len([v for v in vulnerabilities if v.get("severity") == "critical"]),
        "high_count": len([v for v in vulnerabilities if v.get("severity") == "high"]),
        "medium_count": len([v for v in vulnerabilities if v.get("severity") == "medium"]),
        "low_count": len([v for v in vulnerabilities if v.get("severity") == "low"]),
        "last_scan": datetime.utcnow().isoformat()
    }


@router.get("/audit-log")
async def get_audit_log(
    hours: int = 24,
    user_id: str = None,
    action: str = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get audit log entries
    """
    monitor = get_security_monitor()
    
    audit_entries = monitor.get_audit_log(hours=hours, user_id=user_id, action=action)
    
    return {
        "audit_entries": audit_entries,
        "total_count": len(audit_entries),
        "time_range_hours": hours,
        "filters": {
            "user_id": user_id,
            "action": action
        }
    }


@router.get("/security-score")
async def get_security_score(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get overall security score
    """
    security = get_security_hardening()
    
    score = security.calculate_security_score()
    
    return {
        "security_score": score,
        "grade": "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F",
        "status": "excellent" if score >= 90 else "good" if score >= 80 else "fair" if score >= 70 else "poor",
        "last_calculated": datetime.utcnow().isoformat()
    }


@router.get("/health")
async def get_security_health(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get security system health status
    """
    security = get_security_hardening()
    monitor = get_security_monitor()
    
    # Check security components
    components = {
        "authentication": security.check_authentication_health(),
        "authorization": security.check_authorization_health(),
        "encryption": security.check_encryption_health(),
        "monitoring": monitor.check_monitoring_health(),
        "logging": monitor.check_logging_health()
    }
    
    overall_health = all(comp["status"] == "healthy" for comp in components.values())
    
    return {
        "overall_status": "healthy" if overall_health else "unhealthy",
        "components": components,
        "last_checked": datetime.utcnow().isoformat()
    }
