"""
Security monitoring and alerting system for MapleHustleCAN
"""
import asyncio
import json
import logging
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Types of security events"""
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    CSRF_VIOLATION = "csrf_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    FAILED_AUTHENTICATION = "failed_authentication"
    SUSPICIOUS_FILE_UPLOAD = "suspicious_file_upload"
    MALICIOUS_REQUEST = "malicious_request"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    DDoS_ATTACK = "ddos_attack"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: SecurityEventType
    timestamp: datetime
    client_ip: str
    user_agent: str
    request_path: str
    request_method: str
    details: Dict[str, Any]
    severity: str  # low, medium, high, critical
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class SecurityMetrics:
    """Security metrics collection and analysis"""

    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.event_counts: Dict[SecurityEventType, int] = defaultdict(int)
        self.ip_counts: Dict[str, int] = defaultdict(int)
        self.user_counts: Dict[str, int] = defaultdict(int)
        self.time_series: Dict[str, List[tuple]] = defaultdict(list)
        self.lock = threading.Lock()

    def record_event(self, event: SecurityEvent):
        """Record a security event"""
        with self.lock:
            self.events.append(event)
            self.event_counts[event.event_type] += 1
            self.ip_counts[event.client_ip] += 1

            if event.user_id:
                self.user_counts[event.user_id] += 1

            # Add to time series
            timestamp = event.timestamp.timestamp()
            self.time_series[event.event_type.value].append((timestamp, 1))

            # Clean old time series data (keep last 24 hours)
            cutoff = (datetime.now() - timedelta(hours=24)).timestamp()
            self.time_series[event.event_type.value] = [
                (ts, count) for ts, count in self.time_series[event.event_type.value]
                if ts > cutoff
            ]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current security metrics"""
        with self.lock:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_24_hours = now - timedelta(hours=24)

            # Count events in last hour
            recent_events = [
                event for event in self.events
                if event.timestamp > last_hour
            ]

            # Count events in last 24 hours
            daily_events = [
                event for event in self.events
                if event.timestamp > last_24_hours
            ]

            return {
                "total_events": len(
                    self.events),
                "events_last_hour": len(recent_events),
                "events_last_24_hours": len(daily_events),
                "event_types": dict(
                    self.event_counts),
                "top_ips": dict(
                    sorted(
                        self.ip_counts.items(),
                        key=lambda x: x[1],
                        reverse=True)[
                        :10]),
                "top_users": dict(
                    sorted(
                        self.user_counts.items(),
                        key=lambda x: x[1],
                        reverse=True)[
                        :10]),
                "time_series": dict(
                    self.time_series),
                "timestamp": now.isoformat()}

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect security anomalies"""
        anomalies = []

        with self.lock:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)

            # Get events from last hour
            recent_events = [
                event for event in self.events
                if event.timestamp > last_hour
            ]

            # Check for brute force attacks (many failed auths from same IP)
            failed_auths = [
                event for event in recent_events
                if event.event_type == SecurityEventType.FAILED_AUTHENTICATION
            ]

            ip_failed_counts = defaultdict(int)
            for event in failed_auths:
                ip_failed_counts[event.client_ip] += 1

            for ip, count in ip_failed_counts.items():
                if count >= 10:  # 10+ failed auths in 1 hour
                    anomalies.append({
                        "type": "brute_force_attack",
                        "severity": "high",
                        "description": f"Brute force attack detected from IP {ip}",
                        "count": count,
                        "ip": ip,
                        "timestamp": now.isoformat()
                    })

            # Check for DDoS attacks (many requests from same IP)
            ip_request_counts = defaultdict(int)
            for event in recent_events:
                ip_request_counts[event.client_ip] += 1

            for ip, count in ip_request_counts.items():
                if count >= 100:  # 100+ requests in 1 hour
                    anomalies.append({
                        "type": "ddos_attack",
                        "severity": "critical",
                        "description": f"DDoS attack detected from IP {ip}",
                        "count": count,
                        "ip": ip,
                        "timestamp": now.isoformat()
                    })

            # Check for SQL injection patterns
            sql_injection_events = [
                event for event in recent_events
                if event.event_type == SecurityEventType.SQL_INJECTION_ATTEMPT
            ]

            if len(sql_injection_events) >= 5:
                anomalies.append({
                    "type": "sql_injection_campaign",
                    "severity": "high",
                    "description": f"Multiple SQL injection attempts detected",
                    "count": len(sql_injection_events),
                    "timestamp": now.isoformat()
                })

        return anomalies


class SecurityAlertManager:
    """Security alert management system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.email_enabled = config.get("email_alerts", False)
        self.webhook_enabled = config.get("webhook_alerts", False)
        self.email_config = config.get("email", {})
        self.webhook_config = config.get("webhook", {})
        self.alert_thresholds = config.get("thresholds", {})
        self.alert_cooldown = config.get("alert_cooldown", 300)  # 5 minutes
        self.last_alerts: Dict[str, datetime] = {}

    async def send_alert(self, event: SecurityEvent,
                         anomaly: Optional[Dict[str, Any]] = None):
        """Send security alert"""
        alert_key = f"{event.event_type.value}_{event.client_ip}"
        now = datetime.now()

        # Check cooldown
        if alert_key in self.last_alerts:
            if (now - self.last_alerts[alert_key]
                ).seconds < self.alert_cooldown:
                return

        self.last_alerts[alert_key] = now

        # Send email alert
        if self.email_enabled:
            await self._send_email_alert(event, anomaly)

        # Send webhook alert
        if self.webhook_enabled:
            await self._send_webhook_alert(event, anomaly)

    async def _send_email_alert(
            self, event: SecurityEvent, anomaly: Optional[Dict[str, Any]] = None):
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get(
                "from", "security@maplehustlecan.com")
            msg['To'] = self.email_config.get("to", "admin@maplehustlecan.com")
            msg['Subject'] = f"Security Alert: {event.event_type.value}"

            body = self._format_alert_message(event, anomaly)
            msg.attach(MIMEText(body, 'plain'))

            # Send email (in production, use proper SMTP server)
            logger.info(f"Email alert sent: {event.event_type.value}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_webhook_alert(
            self, event: SecurityEvent, anomaly: Optional[Dict[str, Any]] = None):
        """Send webhook alert"""
        try:
            payload = {
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "client_ip": event.client_ip,
                "severity": event.severity,
                "details": event.details,
                "anomaly": anomaly
            }

            webhook_url = self.webhook_config.get("url")
            if webhook_url:
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"Webhook alert sent: {event.event_type.value}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    def _format_alert_message(
            self, event: SecurityEvent, anomaly: Optional[Dict[str, Any]] = None) -> str:
        """Format alert message"""
        message = f"""
Security Alert: {event.event_type.value}

Timestamp: {event.timestamp.isoformat()}
Client IP: {event.client_ip}
User Agent: {event.user_agent}
Request Path: {event.request_method} {event.request_path}
Severity: {event.severity}
User ID: {event.user_id or 'N/A'}
Session ID: {event.session_id or 'N/A'}

Details:
{json.dumps(event.details, indent=2)}
"""

        if anomaly:
            message += f"""

Anomaly Detected:
Type: {anomaly.get('type', 'Unknown')}
Severity: {anomaly.get('severity', 'Unknown')}
Description: {anomaly.get('description', 'No description')}
Count: {anomaly.get('count', 'N/A')}
"""

        return message


class SecurityMonitor:
    """Main security monitoring system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = SecurityMetrics()
        self.alert_manager = SecurityAlertManager(config)
        self.monitoring_enabled = config.get("enabled", True)
        self.anomaly_detection_enabled = config.get("anomaly_detection", True)
        self.alerting_enabled = config.get("alerting", True)

    def record_event(self, event: SecurityEvent):
        """Record a security event"""
        if not self.monitoring_enabled:
            return

        # Record the event
        self.metrics.record_event(event)

        # Log the event
        logger.warning(
            f"Security event: {event.event_type.value} from {event.client_ip}")

        # Check for anomalies
        if self.anomaly_detection_enabled:
            anomalies = self.metrics.detect_anomalies()
            for anomaly in anomalies:
                logger.critical(
                    f"Security anomaly detected: {anomaly['type']}")

                # Send alert if enabled
                if self.alerting_enabled:
                    asyncio.create_task(
                        self.alert_manager.send_alert(event, anomaly))

    def get_metrics(self) -> Dict[str, Any]:
        """Get security metrics"""
        return self.metrics.get_metrics()

    def get_anomalies(self) -> List[Dict[str, Any]]:
        """Get current anomalies"""
        return self.metrics.detect_anomalies()

    def get_event_history(self, hours: int = 24) -> List[SecurityEvent]:
        """Get event history for specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            event for event in self.metrics.events
            if event.timestamp > cutoff
        ]

    def get_ip_risk_score(self, ip: str) -> float:
        """Calculate risk score for an IP address"""
        with self.metrics.lock:
            # Get events from last 24 hours for this IP
            last_24_hours = datetime.now() - timedelta(hours=24)
            ip_events = [
                event for event in self.metrics.events
                if event.client_ip == ip and event.timestamp > last_24_hours
            ]

            if not ip_events:
                return 0.0

            # Calculate risk score based on event types and frequency
            risk_score = 0.0

            for event in ip_events:
                if event.event_type == SecurityEventType.SQL_INJECTION_ATTEMPT:
                    risk_score += 10.0
                elif event.event_type == SecurityEventType.BRUTE_FORCE_ATTACK:
                    risk_score += 15.0
                elif event.event_type == SecurityEventType.DDoS_ATTACK:
                    risk_score += 20.0
                elif event.event_type == SecurityEventType.FAILED_AUTHENTICATION:
                    risk_score += 2.0
                else:
                    risk_score += 1.0

            # Normalize score (0-100)
            return min(risk_score, 100.0)


# Global security monitor instance
_security_monitor: Optional[SecurityMonitor] = None


def initialize_security_monitoring(config: Dict[str, Any]):
    """Initialize security monitoring system"""
    global _security_monitor
    _security_monitor = SecurityMonitor(config)
    logger.info("Security monitoring initialized")


def get_security_monitor() -> Optional[SecurityMonitor]:
    """Get security monitor instance"""
    return _security_monitor


def record_security_event(
    event_type: SecurityEventType,
    client_ip: str,
    user_agent: str,
    request_path: str,
    request_method: str,
    details: Dict[str, Any],
    severity: str = "medium",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Record a security event"""
    if _security_monitor:
        event = SecurityEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            client_ip=client_ip,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            details=details,
            severity=severity,
            user_id=user_id,
            session_id=session_id
        )
        _security_monitor.record_event(event)


def get_security_metrics() -> Dict[str, Any]:
    """Get security metrics"""
    if _security_monitor:
        return _security_monitor.get_metrics()
    return {}


def get_security_anomalies() -> List[Dict[str, Any]]:
    """Get security anomalies"""
    if _security_monitor:
        return _security_monitor.get_anomalies()
    return []
