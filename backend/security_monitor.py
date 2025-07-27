#!/usr/bin/env python3
"""
BOQMate Security Monitor
Monitors security events and provides alerts
"""

import os
import time
import json
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityMonitor:
    def __init__(self):
        self.db_path = "boqmate.db"
        self.alert_threshold = int(os.getenv("ALERT_THRESHOLD", "10"))
        self.monitoring_interval = int(os.getenv("MONITORING_INTERVAL", "300"))  # 5 minutes
        
        # Email configuration
        self.smtp_server = os.getenv("SMTP_SERVER", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.alert_email = os.getenv("ALERT_EMAIL", "")
        
        # Security event counters
        self.event_counters = {
            "failed_auth": 0,
            "rate_limit_violations": 0,
            "malicious_input": 0,
            "file_upload_violations": 0,
            "ip_blocking": 0,
            "sql_injection": 0,
            "xss_attempts": 0
        }
        
        # Alert history
        self.alert_history = []
    
    def get_security_events(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get security events from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT * FROM security_logs 
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(hours)
            
            cursor = conn.execute(query)
            events = []
            for row in cursor.fetchall():
                events.append(dict(row))
            
            conn.close()
            return events
        except Exception as e:
            logger.error(f"Error getting security events: {e}")
            return []
    
    def analyze_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security events for patterns"""
        analysis = {
            "total_events": len(events),
            "event_types": {},
            "suspicious_ips": {},
            "high_severity_events": [],
            "rate_limit_violations": 0,
            "failed_auth_attempts": 0,
            "malicious_inputs": 0
        }
        
        for event in events:
            event_type = event.get("event_type", "unknown")
            ip_address = event.get("ip_address", "unknown")
            severity = event.get("severity", "INFO")
            
            # Count event types
            analysis["event_types"][event_type] = analysis["event_types"].get(event_type, 0) + 1
            
            # Count suspicious IPs
            if ip_address != "unknown":
                analysis["suspicious_ips"][ip_address] = analysis["suspicious_ips"].get(ip_address, 0) + 1
            
            # Track high severity events
            if severity in ["WARNING", "ERROR"]:
                analysis["high_severity_events"].append(event)
            
            # Count specific event types
            if "RATE_LIMIT" in event_type:
                analysis["rate_limit_violations"] += 1
            elif "FAILED_AUTH" in event_type or "INVALID_TOKEN" in event_type:
                analysis["failed_auth_attempts"] += 1
            elif "MALICIOUS" in event_type:
                analysis["malicious_inputs"] += 1
        
        return analysis
    
    def check_alert_conditions(self, analysis: Dict[str, Any]) -> List[str]:
        """Check if alert conditions are met"""
        alerts = []
        
        # Check for high event volume
        if analysis["total_events"] > self.alert_threshold:
            alerts.append(f"High security event volume: {analysis['total_events']} events")
        
        # Check for rate limit violations
        if analysis["rate_limit_violations"] > 5:
            alerts.append(f"Multiple rate limit violations: {analysis['rate_limit_violations']}")
        
        # Check for failed authentication attempts
        if analysis["failed_auth_attempts"] > 10:
            alerts.append(f"Multiple failed authentication attempts: {analysis['failed_auth_attempts']}")
        
        # Check for malicious inputs
        if analysis["malicious_inputs"] > 3:
            alerts.append(f"Multiple malicious input attempts: {analysis['malicious_inputs']}")
        
        # Check for suspicious IPs
        for ip, count in analysis["suspicious_ips"].items():
            if count > 5:
                alerts.append(f"Suspicious IP activity: {ip} with {count} events")
        
        # Check for high severity events
        if len(analysis["high_severity_events"]) > 3:
            alerts.append(f"Multiple high severity events: {len(analysis['high_severity_events'])}")
        
        return alerts
    
    def send_alert_email(self, alerts: List[str], analysis: Dict[str, Any]):
        """Send alert email"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.alert_email]):
            logger.warning("Email configuration incomplete, skipping email alert")
            return
        
        try:
            subject = f"BOQMate Security Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            body = f"""
BOQMate Security Alert

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ALERTS:
{chr(10).join(f"- {alert}" for alert in alerts)}

ANALYSIS:
- Total Events: {analysis['total_events']}
- Rate Limit Violations: {analysis['rate_limit_violations']}
- Failed Auth Attempts: {analysis['failed_auth_attempts']}
- Malicious Inputs: {analysis['malicious_inputs']}
- High Severity Events: {len(analysis['high_severity_events'])}

Suspicious IPs:
{chr(10).join(f"- {ip}: {count} events" for ip, count in analysis['suspicious_ips'].items() if count > 2)}

Event Types:
{chr(10).join(f"- {event_type}: {count}" for event_type, count in analysis['event_types'].items())}

Please review the security logs and take appropriate action.
            """
            
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Security alert email sent to {self.alert_email}")
            
        except Exception as e:
            logger.error(f"Error sending alert email: {e}")
    
    def log_alert(self, alerts: List[str], analysis: Dict[str, Any]):
        """Log alert to file"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "analysis": analysis
        }
        
        # Save to alert log file
        alert_log_path = Path("security_alerts.log")
        with open(alert_log_path, "a") as f:
            f.write(json.dumps(alert_data) + "\n")
        
        # Add to alert history
        self.alert_history.append(alert_data)
        
        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        events = self.get_security_events(24)  # Last 24 hours
        analysis = self.analyze_events(events)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "period": "24 hours",
            "summary": {
                "total_events": analysis["total_events"],
                "high_severity_events": len(analysis["high_severity_events"]),
                "unique_ips": len(analysis["suspicious_ips"]),
                "event_types": len(analysis["event_types"])
            },
            "analysis": analysis,
            "recommendations": []
        }
        
        # Generate recommendations
        if analysis["rate_limit_violations"] > 10:
            report["recommendations"].append("Consider reducing rate limits or implementing additional IP blocking")
        
        if analysis["failed_auth_attempts"] > 20:
            report["recommendations"].append("Review authentication logs and consider implementing account lockout")
        
        if analysis["malicious_inputs"] > 5:
            report["recommendations"].append("Review input validation and consider additional sanitization")
        
        if len(analysis["suspicious_ips"]) > 5:
            report["recommendations"].append("Consider implementing IP whitelisting or additional monitoring")
        
        return report
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            logger.info("Starting security monitoring cycle")
            
            # Get recent security events
            events = self.get_security_events(1)  # Last hour
            analysis = self.analyze_events(events)
            
            # Check for alerts
            alerts = self.check_alert_conditions(analysis)
            
            if alerts:
                logger.warning(f"Security alerts detected: {alerts}")
                self.log_alert(alerts, analysis)
                self.send_alert_email(alerts, analysis)
            else:
                logger.info("No security alerts detected")
            
            # Log summary
            logger.info(f"Monitoring cycle completed: {analysis['total_events']} events analyzed")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        logger.info("Starting BOQMate Security Monitor")
        logger.info(f"Monitoring interval: {self.monitoring_interval} seconds")
        logger.info(f"Alert threshold: {self.alert_threshold} events")
        
        while True:
            try:
                self.run_monitoring_cycle()
                time.sleep(self.monitoring_interval)
            except KeyboardInterrupt:
                logger.info("Security monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring: {e}")
                time.sleep(60)  # Wait before retrying

def main():
    """Main function"""
    monitor = SecurityMonitor()
    
    # Check if running as daemon or single cycle
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--report":
        # Generate and print security report
        report = monitor.generate_security_report()
        print(json.dumps(report, indent=2))
    else:
        # Start continuous monitoring
        monitor.start_monitoring()

if __name__ == "__main__":
    main()