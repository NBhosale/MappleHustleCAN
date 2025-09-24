"""
Security dashboard and monitoring endpoints
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security_monitoring import (
    SecurityEventType,
    get_security_anomalies,
    get_security_metrics,
    get_security_monitor,
)
from app.db import SessionLocal
from app.utils.deps import require_admin

router = APIRouter(prefix="/security", tags=["Security"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/metrics")
def get_security_metrics_endpoint(
    current_user=Depends(require_admin),
):
    """
    Get security metrics (admin only)
    """
    try:
        metrics = get_security_metrics()
        return {
            "status": "success",
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get security metrics: {
                str(e)}")


@router.get("/anomalies")
def get_security_anomalies_endpoint(
    current_user=Depends(require_admin),
):
    """
    Get current security anomalies (admin only)
    """
    try:
        anomalies = get_security_anomalies()
        return {
            "status": "success",
            "data": anomalies,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get security anomalies: {
                str(e)}")


@router.get("/events")
def get_security_events(
    hours: int = Query(
        24, ge=1, le=168, description="Hours of history to retrieve"),
    event_type: Optional[str] = Query(
        None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    current_user=Depends(require_admin),
):
    """
    Get security events history (admin only)
    """
    try:
        monitor = get_security_monitor()
        if not monitor:
            raise HTTPException(
                status_code=503, detail="Security monitoring not available")

        events = monitor.get_event_history(hours)

        # Filter by event type if specified
        if event_type:
            try:
                event_type_enum = SecurityEventType(event_type)
                events = [
                    event for event in events if event.event_type == event_type_enum]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {event_type}")

        # Filter by severity if specified
        if severity:
            events = [event for event in events if event.severity == severity]

        # Convert events to dict format
        events_data = []
        for event in events:
            events_data.append({
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "client_ip": event.client_ip,
                "user_agent": event.user_agent,
                "request_path": event.request_path,
                "request_method": event.request_method,
                "severity": event.severity,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "details": event.details
            })

        return {
            "status": "success",
            "data": events_data,
            "count": len(events_data),
            "filters": {
                "hours": hours,
                "event_type": event_type,
                "severity": severity
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get security events: {str(e)}")


@router.get("/ip-risk/{ip_address}")
def get_ip_risk_score(
    ip_address: str,
    current_user=Depends(require_admin),
):
    """
    Get risk score for a specific IP address (admin only)
    """
    try:
        monitor = get_security_monitor()
        if not monitor:
            raise HTTPException(
                status_code=503, detail="Security monitoring not available")

        risk_score = monitor.get_ip_risk_score(ip_address)

        return {
            "status": "success",
            "data": {
                "ip_address": ip_address,
                "risk_score": risk_score,
                "risk_level": get_risk_level(risk_score),
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get IP risk score: {str(e)}")


@router.get("/dashboard")
def get_security_dashboard(
    current_user=Depends(require_admin),
):
    """
    Get comprehensive security dashboard data (admin only)
    """
    try:
        monitor = get_security_monitor()
        if not monitor:
            raise HTTPException(
                status_code=503, detail="Security monitoring not available")

        # Get all metrics
        metrics = get_security_metrics()
        anomalies = get_security_anomalies()

        # Get recent events (last 24 hours)
        recent_events = monitor.get_event_history(24)

        # Calculate additional statistics
        total_events = len(recent_events)
        critical_events = len(
            [e for e in recent_events if e.severity == "critical"])
        high_events = len([e for e in recent_events if e.severity == "high"])
        medium_events = len(
            [e for e in recent_events if e.severity == "medium"])
        low_events = len([e for e in recent_events if e.severity == "low"])

        # Get top threat IPs
        ip_counts = {}
        for event in recent_events:
            ip_counts[event.client_ip] = ip_counts.get(event.client_ip, 0) + 1

        top_threat_ips = sorted(
            ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Get event type distribution
        event_type_counts = {}
        for event in recent_events:
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(
                event_type, 0) + 1

        dashboard_data = {
            "overview": {
                "total_events_24h": total_events,
                "critical_events": critical_events,
                "high_events": high_events,
                "medium_events": medium_events,
                "low_events": low_events,
                "active_anomalies": len(anomalies),
                "timestamp": datetime.now().isoformat()
            },
            "metrics": metrics,
            "anomalies": anomalies,
            "top_threat_ips": [
                {"ip": ip, "count": count,
                    "risk_score": monitor.get_ip_risk_score(ip)}
                for ip, count in top_threat_ips
            ],
            "event_type_distribution": event_type_counts,
            "recent_events_summary": {
                "last_hour": len([e for e in recent_events if e.timestamp > datetime.now() - timedelta(hours=1)]),
                "last_6_hours": len([e for e in recent_events if e.timestamp > datetime.now() - timedelta(hours=6)]),
                "last_12_hours": len([e for e in recent_events if e.timestamp > datetime.now() - timedelta(hours=12)]),
                "last_24_hours": total_events
            }
        }

        return {
            "status": "success",
            "data": dashboard_data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get security dashboard: {
                str(e)}")


@router.get("/health")
def get_security_health(
    current_user=Depends(require_admin),
):
    """
    Get security system health status (admin only)
    """
    try:
        monitor = get_security_monitor()
        if not monitor:
            return {
                "status": "error",
                "message": "Security monitoring not available",
                "timestamp": datetime.now().isoformat()
            }

        # Check if monitoring is working
        metrics = get_security_metrics()
        anomalies = get_security_anomalies()

        health_status = "healthy"
        issues = []

        # Check for critical anomalies
        critical_anomalies = [
            a for a in anomalies if a.get("severity") == "critical"]
        if critical_anomalies:
            health_status = "critical"
            issues.append(
                f"{len(critical_anomalies)} critical anomalies detected")

        # Check for high severity anomalies
        high_anomalies = [a for a in anomalies if a.get("severity") == "high"]
        if high_anomalies:
            if health_status == "healthy":
                health_status = "warning"
            issues.append(
                f"{len(high_anomalies)} high severity anomalies detected")

        # Check event volume
        events_last_hour = metrics.get("events_last_hour", 0)
        if events_last_hour > 1000:  # High volume threshold
            if health_status == "healthy":
                health_status = "warning"
            issues.append(
                f"High event volume: {events_last_hour} events in last hour")

        return {
            "status": "success",
            "data": {
                "health_status": health_status,
                "issues": issues,
                "monitoring_enabled": monitor.monitoring_enabled,
                "anomaly_detection_enabled": monitor.anomaly_detection_enabled,
                "alerting_enabled": monitor.alerting_enabled,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get security health: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


def get_risk_level(risk_score: float) -> str:
    """
    Convert risk score to risk level
    """
    if risk_score >= 80:
        return "critical"
    elif risk_score >= 60:
        return "high"
    elif risk_score >= 40:
        return "medium"
    elif risk_score >= 20:
        return "low"
    else:
        return "minimal"
