# AI Implementation Prompt: Automated Alerting System

**Feature ID**: 2.6 from ROADMAP.md
**Priority**: MEDIUM
**Effort**: 3-4 weeks
**Type**: Infrastructure

## Objective

Implement automated monitoring and alerting system that proactively notifies federation operators about compliance regressions, new non-compliant entities, threshold violations, and positive milestones via email, Slack, webhooks, or RSS feeds.

## Objective

Build a proactive alerting system that monitors eduGAIN metadata quality over time and sends notifications when issues are detected, enabling rapid response to compliance problems and celebrating quality improvements.

## Context

**Current State**:
- Tool must be run manually to detect issues
- No proactive monitoring or alerts
- Federation operators discover problems weeks/months after they occur
- No notification system for new non-compliant entities
- Can't track regression alerts automatically

**Current Workflow** (Manual, Reactive):
```
1. Federation operator manually runs tool (weekly/monthly)
2. Reviews output, compares to previous runs mentally
3. May or may not notice regressions
4. No alerts for new problematic entities
5. Issues discovered too late to act quickly
```

**Improved Workflow** (Automated, Proactive):
```
1. Cron job runs tool daily (scheduled)
2. Alert system compares to historical baseline
3. Detects: regressions, new issues, thresholds exceeded
4. Sends notifications immediately (email/Slack/webhook)
5. Federation operator receives actionable alert:
   "⚠️ Privacy coverage dropped 5.2% (85% → 79.8%)
    - 8 entities lost privacy statements
    - Federation XYZ needs attention"
6. Operator investigates and remediates quickly
```

**Problem**:
- **Reactive instead of proactive**: Issues discovered too late
- **Manual monitoring burden**: Time-consuming to check regularly
- **Missed regressions**: Small drops go unnoticed
- **Slow response**: Days/weeks to detect and fix issues
- **No positive feedback**: Improvements go unnoticed/uncelebrated

## Requirements

### Core Functionality

1. **Alert Trigger Types**:

   **Regression Alerts**:
   - Federation compliance drops > N% in specified window (e.g., 5% in 7 days)
   - Previously compliant entity becomes non-compliant
   - Previously accessible privacy URL now returns 404/error
   - Security contact removed from entity

   **New Entity Alerts**:
   - New SP added without privacy statement
   - New entity added without security contact
   - New SIRTFI entity without proper contacts/compliance

   **Threshold Alerts**:
   - Federation drops below specified compliance threshold (e.g., < 80%)
   - Privacy URL validation success rate < N%
   - Bot protection blocking > N% of validation attempts

   **Positive Alerts** (optional, for morale):
   - Federation reaches new compliance milestone (80%, 90%, 95%)
   - Entity fixes long-standing issue
   - Federation improves by > N% in time window

2. **Alert Configuration**:
   YAML-based configuration file for alert rules:

   ```yaml
   # alerts.yaml
   alerts:
     - name: "Federation Regression Alert"
       trigger: "federation_compliance_drops"
       metric: "privacy_coverage"
       threshold: 5.0  # percentage points
       window: 7d      # compare to 7 days ago
       severity: high
       delivery: [email, slack]

     - name: "New Non-Compliant SP"
       trigger: "new_entity_missing_privacy"
       entity_type: SP
       severity: medium
       delivery: [webhook]

     - name: "Low Compliance Threshold"
       trigger: "federation_below_threshold"
       metric: "privacy_coverage"
       threshold: 80.0  # absolute percentage
       severity: critical
       delivery: [email, slack]

     - name: "Compliance Milestone"
       trigger: "federation_milestone"
       metric: "privacy_coverage"
       milestones: [80, 90, 95]
       severity: info
       delivery: [slack]
       positive: true  # Optional positive alert

   delivery:
     email:
       smtp_server: "smtp.example.org"
       smtp_port: 587
       smtp_user: "alerts@example.org"
       smtp_password: "${SMTP_PASSWORD}"  # Environment variable
       from_address: "edugain-alerts@example.org"
       to_addresses: ["operator@federation.org"]

     slack:
       webhook_url: "${SLACK_WEBHOOK_URL}"
       channel: "#edugain-alerts"

     webhook:
       url: "https://example.org/api/alerts"
       method: POST
       headers:
         Authorization: "Bearer ${API_TOKEN}"
   ```

3. **Delivery Methods**:

   **Email**:
   - Plain text or HTML format
   - Subject line with severity and alert name
   - Body with detailed alert information
   - Links to entities or CSV exports

   **Slack**:
   - Rich message with Markdown formatting
   - Color-coded by severity (red=critical, yellow=warning, green=info)
   - Action buttons (view details, export CSV)
   - Inline charts/sparklines if possible

   **Generic Webhook**:
   - JSON payload with alert details
   - Configurable HTTP method (POST/PUT)
   - Custom headers (for authentication)
   - Integration with ticketing systems (Jira, ServiceNow, etc.)

   **RSS Feed** (optional):
   - Generate RSS feed of recent alerts
   - Useful for aggregators or dashboards
   - Stored in `alerts.xml`

4. **Alert History & Deduplication**:
   - Store alerts in `history.db` to prevent duplicates
   - Don't re-send same alert within N hours (configurable cooldown)
   - Track: alert_id, timestamp, alert_type, details, delivered_to
   - Query history: `edugain-alert --history` shows recent alerts

5. **Rate Limiting**:
   - Maximum N alerts per day (prevent alert fatigue)
   - Batch similar alerts (e.g., "5 entities lost privacy statements")
   - Digest mode: Daily/weekly summary instead of individual alerts

6. **CLI Commands**:
   ```bash
   # Run alerting system with config
   edugain-alert --config alerts.yaml

   # Dry-run mode (show what would be alerted, don't send)
   edugain-alert --config alerts.yaml --dry-run

   # Show alert history
   edugain-alert --history --last 7d

   # Test delivery methods
   edugain-alert --test-email
   edugain-alert --test-slack
   edugain-alert --test-webhook

   # Scheduled execution (via cron)
   0 9 * * * /usr/local/bin/edugain-alert --config /etc/edugain/alerts.yaml
   ```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/alerting/engine.py`** (NEW):
   - Alert evaluation engine
   - Trigger detection logic
   - Alert history management

2. **`src/edugain_analysis/alerting/config.py`** (NEW):
   - YAML configuration parsing
   - Alert rule validation
   - Delivery configuration

3. **`src/edugain_analysis/alerting/delivery.py`** (NEW):
   - Email delivery (SMTP)
   - Slack webhook delivery
   - Generic webhook delivery
   - RSS feed generation

4. **`src/edugain_analysis/cli/alert.py`** (NEW):
   - CLI entry point for alerting
   - Dry-run mode
   - History display
   - Test delivery methods

5. **Database Schema** (extend `history.db`):
   ```sql
   CREATE TABLE alerts (
       alert_id TEXT PRIMARY KEY,
       timestamp INTEGER NOT NULL,
       alert_type TEXT NOT NULL,
       severity TEXT NOT NULL,
       details TEXT NOT NULL,  -- JSON
       delivered_to TEXT,      -- Comma-separated delivery methods
       silenced_until INTEGER  -- Cooldown timestamp
   );

   CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);
   CREATE INDEX idx_alerts_type ON alerts(alert_type);
   ```

**Dependencies**:
- `pyyaml` for YAML configuration parsing
- `requests` for webhook delivery (already used)
- `smtplib` (standard library) for email
- Historical Snapshot Storage (Feature 1.4) for baseline comparison

**Edge Cases**:
- No historical data: Skip regression alerts, only check thresholds
- Alert delivery failure: Log error, don't crash, retry later
- Missing environment variables: Fail with clear error message
- Invalid YAML config: Validate and report errors clearly
- Circular alert loops: Prevent alerts about alerting system itself

## Acceptance Criteria

### Functional Requirements
- [ ] Alert configuration loaded from YAML file
- [ ] All trigger types implemented (regression, new entity, threshold, milestone)
- [ ] Email delivery works (plain text and HTML)
- [ ] Slack webhook delivery works
- [ ] Generic webhook delivery works
- [ ] Alert history stored in database
- [ ] Deduplication prevents duplicate alerts (cooldown period)
- [ ] Rate limiting prevents alert fatigue
- [ ] `--dry-run` mode shows what would be alerted
- [ ] `--history` displays recent alerts
- [ ] Test delivery methods work (`--test-email`, etc.)

### Quality Requirements
- [ ] Alerts are accurate (no false positives)
- [ ] Alert cooldown works correctly
- [ ] Email formatting is professional and readable
- [ ] Slack messages use rich formatting
- [ ] Configuration validation catches errors early
- [ ] Delivery failures are logged but don't crash system
- [ ] Performance overhead < 10% (alerting is not critical path)

### Testing Requirements
- [ ] Test each alert trigger type
- [ ] Test email delivery (mock SMTP server)
- [ ] Test Slack delivery (mock webhook)
- [ ] Test webhook delivery
- [ ] Test alert deduplication logic
- [ ] Test rate limiting
- [ ] Test configuration validation
- [ ] Integration test with real historical data

## Testing Strategy

**Unit Tests**:
```python
def test_detect_regression_alert():
    """Test regression detection."""
    current_stats = {"privacy_coverage": 75.0}
    baseline_stats = {"privacy_coverage": 82.0}

    alerts = detect_alerts(current_stats, baseline_stats, rules={
        "threshold": 5.0,  # 5 percentage points
        "trigger": "federation_compliance_drops"
    })

    assert len(alerts) == 1
    assert alerts[0]["type"] == "federation_compliance_drops"
    assert alerts[0]["severity"] == "high"

def test_alert_deduplication():
    """Test that duplicate alerts are not sent."""
    alert = {
        "alert_id": "test_alert_123",
        "type": "privacy_regression",
        "details": "Privacy dropped 5%"
    }

    # First alert should be sent
    assert should_send_alert(alert, cooldown_hours=24) is True

    # Record alert
    record_alert(alert)

    # Second alert within cooldown should not be sent
    assert should_send_alert(alert, cooldown_hours=24) is False

def test_alert_config_validation():
    """Test YAML configuration validation."""
    invalid_config = """
    alerts:
      - name: "Test Alert"
        trigger: "invalid_trigger_type"  # Invalid
        threshold: "not_a_number"        # Invalid
    """

    with pytest.raises(ConfigValidationError) as exc_info:
        parse_alert_config(invalid_config)

    assert "invalid_trigger_type" in str(exc_info.value)

def test_email_delivery(mock_smtp):
    """Test email alert delivery."""
    alert = {
        "name": "Test Alert",
        "severity": "high",
        "details": "Privacy coverage dropped 5%"
    }

    config = {
        "smtp_server": "smtp.test.org",
        "smtp_port": 587,
        "from_address": "test@example.org",
        "to_addresses": ["operator@test.org"]
    }

    deliver_email_alert(alert, config)

    # Verify mock SMTP was called
    assert mock_smtp.sendmail.called
```

## Implementation Guidance

### Step 1: Create Alert Engine

```python
# src/edugain_analysis/alerting/engine.py

from typing import Dict, List
import sqlite3
from datetime import datetime, timedelta
import hashlib

def detect_alerts(
    current_stats: Dict,
    baseline_stats: Dict,
    alert_rules: List[Dict],
    entities_current: List[Dict],
    entities_baseline: List[Dict]
) -> List[Dict]:
    """
    Detect alerts based on current vs. baseline comparison.

    Args:
        current_stats: Current statistics
        baseline_stats: Baseline statistics (from history)
        alert_rules: List of alert rule configurations
        entities_current: Current entity list
        entities_baseline: Baseline entity list

    Returns:
        List of alerts to be sent
    """
    alerts = []

    for rule in alert_rules:
        trigger_type = rule.get("trigger")

        if trigger_type == "federation_compliance_drops":
            alert = check_compliance_regression(
                current_stats,
                baseline_stats,
                rule
            )
            if alert:
                alerts.append(alert)

        elif trigger_type == "new_entity_missing_privacy":
            alert = check_new_non_compliant_entities(
                entities_current,
                entities_baseline,
                rule
            )
            if alert:
                alerts.append(alert)

        elif trigger_type == "federation_below_threshold":
            alert = check_threshold_violation(
                current_stats,
                rule
            )
            if alert:
                alerts.append(alert)

        elif trigger_type == "federation_milestone":
            alert = check_milestone_reached(
                current_stats,
                baseline_stats,
                rule
            )
            if alert:
                alerts.append(alert)

    return alerts

def check_compliance_regression(
    current_stats: Dict,
    baseline_stats: Dict,
    rule: Dict
) -> Dict | None:
    """
    Check if compliance has regressed beyond threshold.

    Args:
        current_stats: Current statistics
        baseline_stats: Baseline statistics
        rule: Alert rule configuration

    Returns:
        Alert dictionary if triggered, None otherwise
    """
    metric = rule.get("metric", "privacy_coverage")
    threshold = rule.get("threshold", 5.0)

    current_value = current_stats.get(metric, 0)
    baseline_value = baseline_stats.get(metric, 0)

    drop = baseline_value - current_value

    if drop >= threshold:
        return {
            "alert_id": generate_alert_id(rule["name"], current_value),
            "name": rule["name"],
            "type": rule["trigger"],
            "severity": rule.get("severity", "medium"),
            "metric": metric,
            "current_value": current_value,
            "baseline_value": baseline_value,
            "drop": drop,
            "details": f"{metric} dropped {drop:.1f}% ({baseline_value:.1f}% → {current_value:.1f}%)",
            "timestamp": datetime.now().isoformat(),
        }

    return None

def check_new_non_compliant_entities(
    entities_current: List[Dict],
    entities_baseline: List[Dict],
    rule: Dict
) -> Dict | None:
    """
    Check for new entities that are non-compliant.

    Args:
        entities_current: Current entity list
        entities_baseline: Baseline entity list
        rule: Alert rule configuration

    Returns:
        Alert dictionary if triggered, None otherwise
    """
    # Find entity IDs in current but not in baseline (new entities)
    baseline_ids = {e["entity_id"] for e in entities_baseline}
    new_entities = [
        e for e in entities_current
        if e["entity_id"] not in baseline_ids
    ]

    # Filter by entity type if specified
    entity_type = rule.get("entity_type")
    if entity_type:
        new_entities = [e for e in new_entities if e.get("entity_type") == entity_type]

    # Check compliance (e.g., missing privacy statement)
    non_compliant_new = [
        e for e in new_entities
        if not e.get("has_privacy", False)  # Missing privacy statement
    ]

    if non_compliant_new:
        return {
            "alert_id": generate_alert_id(rule["name"], len(non_compliant_new)),
            "name": rule["name"],
            "type": rule["trigger"],
            "severity": rule.get("severity", "medium"),
            "count": len(non_compliant_new),
            "entities": [e["entity_id"] for e in non_compliant_new[:10]],  # First 10
            "details": f"{len(non_compliant_new)} new non-compliant entities added",
            "timestamp": datetime.now().isoformat(),
        }

    return None

def check_threshold_violation(
    current_stats: Dict,
    rule: Dict
) -> Dict | None:
    """
    Check if metric is below absolute threshold.

    Args:
        current_stats: Current statistics
        rule: Alert rule configuration

    Returns:
        Alert dictionary if triggered, None otherwise
    """
    metric = rule.get("metric", "privacy_coverage")
    threshold = rule.get("threshold", 80.0)

    current_value = current_stats.get(metric, 0)

    if current_value < threshold:
        return {
            "alert_id": generate_alert_id(rule["name"], current_value),
            "name": rule["name"],
            "type": rule["trigger"],
            "severity": rule.get("severity", "high"),
            "metric": metric,
            "current_value": current_value,
            "threshold": threshold,
            "gap": threshold - current_value,
            "details": f"{metric} is {current_value:.1f}%, below threshold of {threshold:.1f}%",
            "timestamp": datetime.now().isoformat(),
        }

    return None

def check_milestone_reached(
    current_stats: Dict,
    baseline_stats: Dict,
    rule: Dict
) -> Dict | None:
    """
    Check if metric has crossed a milestone threshold.

    Args:
        current_stats: Current statistics
        baseline_stats: Baseline statistics
        rule: Alert rule configuration

    Returns:
        Alert dictionary if triggered, None otherwise
    """
    metric = rule.get("metric", "privacy_coverage")
    milestones = rule.get("milestones", [80, 90, 95])

    current_value = current_stats.get(metric, 0)
    baseline_value = baseline_stats.get(metric, 0)

    # Check if we crossed any milestone
    for milestone in milestones:
        if baseline_value < milestone <= current_value:
            return {
                "alert_id": generate_alert_id(rule["name"], milestone),
                "name": rule["name"],
                "type": rule["trigger"],
                "severity": "info",
                "positive": True,
                "metric": metric,
                "milestone": milestone,
                "current_value": current_value,
                "details": f"🎉 {metric} reached {milestone}% milestone (now {current_value:.1f}%)",
                "timestamp": datetime.now().isoformat(),
            }

    return None

def generate_alert_id(alert_name: str, value: any) -> str:
    """
    Generate unique alert ID for deduplication.

    Args:
        alert_name: Name of alert
        value: Value to include in ID (for uniqueness)

    Returns:
        Alert ID hash
    """
    content = f"{alert_name}:{value}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def should_send_alert(alert: Dict, cooldown_hours: int = 24) -> bool:
    """
    Check if alert should be sent (not in cooldown).

    Args:
        alert: Alert dictionary with alert_id
        cooldown_hours: Cooldown period in hours

    Returns:
        True if alert should be sent, False if in cooldown
    """
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    # Check if alert was sent recently
    cooldown_threshold = datetime.now() - timedelta(hours=cooldown_hours)
    cooldown_timestamp = int(cooldown_threshold.timestamp())

    cursor.execute("""
        SELECT timestamp FROM alerts
        WHERE alert_id = ? AND timestamp > ?
    """, (alert["alert_id"], cooldown_timestamp))

    result = cursor.fetchone()
    conn.close()

    return result is None  # Send if not found in recent history

def record_alert(alert: Dict, delivered_to: List[str]):
    """
    Record alert in history database.

    Args:
        alert: Alert dictionary
        delivered_to: List of delivery methods used
    """
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts (alert_id, timestamp, alert_type, severity, details, delivered_to)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        alert["alert_id"],
        int(datetime.now().timestamp()),
        alert["type"],
        alert.get("severity", "medium"),
        str(alert.get("details", "")),
        ",".join(delivered_to)
    ))

    conn.commit()
    conn.close()
```

### Step 2: Create Delivery Module

```python
# src/edugain_analysis/alerting/delivery.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json

def deliver_email_alert(alert: Dict, config: Dict):
    """
    Send alert via email.

    Args:
        alert: Alert dictionary
        config: Email configuration
    """
    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[{alert['severity'].upper()}] {alert['name']}"
    msg["From"] = config["from_address"]
    msg["To"] = ", ".join(config["to_addresses"])

    # Plain text version
    text_body = format_alert_text(alert)
    msg.attach(MIMEText(text_body, "plain"))

    # HTML version (optional)
    html_body = format_alert_html(alert)
    msg.attach(MIMEText(html_body, "html"))

    # Send via SMTP
    with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
        server.starttls()
        if config.get("smtp_user") and config.get("smtp_password"):
            server.login(config["smtp_user"], config["smtp_password"])
        server.send_message(msg)

def deliver_slack_alert(alert: Dict, config: Dict):
    """
    Send alert via Slack webhook.

    Args:
        alert: Alert dictionary
        config: Slack configuration
    """
    # Color based on severity
    colors = {
        "critical": "#FF0000",
        "high": "#FF6600",
        "medium": "#FFCC00",
        "low": "#00FF00",
        "info": "#0099FF"
    }

    color = colors.get(alert.get("severity", "medium"), "#CCCCCC")

    # Build Slack message
    payload = {
        "channel": config.get("channel", "#alerts"),
        "attachments": [{
            "color": color,
            "title": alert["name"],
            "text": alert["details"],
            "fields": [
                {"title": "Severity", "value": alert.get("severity", "medium"), "short": True},
                {"title": "Time", "value": alert.get("timestamp", ""), "short": True},
            ],
            "footer": "eduGAIN Quality Monitor"
        }]
    }

    # Send webhook
    response = requests.post(config["webhook_url"], json=payload)
    response.raise_for_status()

def deliver_webhook_alert(alert: Dict, config: Dict):
    """
    Send alert via generic webhook.

    Args:
        alert: Alert dictionary
        config: Webhook configuration
    """
    # Build payload
    payload = {
        "alert": alert,
        "timestamp": alert.get("timestamp"),
        "source": "edugain-analysis"
    }

    # Send webhook
    headers = config.get("headers", {})
    method = config.get("method", "POST").upper()

    if method == "POST":
        response = requests.post(config["url"], json=payload, headers=headers)
    elif method == "PUT":
        response = requests.put(config["url"], json=payload, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    response.raise_for_status()

def format_alert_text(alert: Dict) -> str:
    """Format alert as plain text."""
    return f"""
eduGAIN Quality Alert

Alert: {alert['name']}
Severity: {alert.get('severity', 'medium').upper()}
Time: {alert.get('timestamp', '')}

{alert['details']}
"""

def format_alert_html(alert: Dict) -> str:
    """Format alert as HTML."""
    severity_colors = {
        "critical": "#FF0000",
        "high": "#FF6600",
        "medium": "#FFCC00",
        "low": "#00FF00",
        "info": "#0099FF"
    }

    color = severity_colors.get(alert.get("severity", "medium"), "#CCCCCC")

    return f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: {color};">eduGAIN Quality Alert</h2>
    <h3>{alert['name']}</h3>
    <p><strong>Severity:</strong> {alert.get('severity', 'medium').upper()}</p>
    <p><strong>Time:</strong> {alert.get('timestamp', '')}</p>
    <p>{alert['details']}</p>
</body>
</html>
"""
```

### Step 3: CLI Integration

```python
# src/edugain_analysis/cli/alert.py

import argparse
import yaml
from ..alerting.engine import detect_alerts, should_send_alert, record_alert
from ..alerting.delivery import deliver_email_alert, deliver_slack_alert, deliver_webhook_alert

def main():
    parser = argparse.ArgumentParser(description="eduGAIN Alerting System")
    parser.add_argument("--config", required=True, help="Alert configuration YAML file")
    parser.add_argument("--dry-run", action="store_true", help="Show alerts without sending")
    parser.add_argument("--history", action="store_true", help="Show alert history")
    parser.add_argument("--test-email", action="store_true", help="Test email delivery")
    parser.add_argument("--test-slack", action="store_true", help="Test Slack delivery")

    args = parser.parse_args()

    # Load configuration
    with open(args.config) as f:
        config = yaml.safe_load(f)

    # ... rest of implementation
```

## Success Metrics

- Regressions detected within 24 hours of occurrence
- Zero false positives (incorrect alerts)
- Alert delivery success rate > 99%
- Time-to-remediation reduced by 50% (thanks to early alerts)
- Federation operators report high alert value
- Alert fatigue avoided (rate limiting works)

## References

- Similar systems: AWS CloudWatch Alarms, Prometheus Alertmanager
- Slack Incoming Webhooks: https://api.slack.com/messaging/webhooks
- SMTP with Python: https://docs.python.org/3/library/smtplib.html

## Dependencies

**Required**:
- Historical Snapshot Storage (Feature 1.4) for baseline comparison
- `pyyaml` for configuration parsing

**Optional**:
- `rich` library for better CLI formatting of alert history
