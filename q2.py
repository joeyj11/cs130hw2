import time
import random
from datetime import datetime, timedelta

# how often to check metrics
CHECK_INTERVAL_MINUTES = 5

# thresholds
THRESHOLDS = {
    'P0': {'latency': 2000, 'failure_rate': 0.10},
    'P1': {'latency': 1000, 'failure_rate': 0.05},
    'P2': {'latency': 500,  'failure_rate': 0.02},
}

# how often to repeat notifs
REPEAT_HOURS = {
    'P0': 2,
    'P1': 12,
    'P2': 48,
}

class Alert:
    def __init__(self, severity):
        self.severity = severity
        self.start_time = datetime.now()
        self.last_notified = self.start_time
        self.skip_level_boss_deadline = self.start_time + timedelta(
            hours=REPEAT_HOURS[severity] * 5
        )
    
    def __str__(self):
        return f"<Alert severity={self.severity}, since={self.start_time}>"

# global state

active_alert = None
logs = []            # Store all log messages
LOG_RETENTION_DAYS = 90

# logging logic

def log(message):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{now_str}] {message}"
    logs.append((datetime.now(), entry))
    print(entry)

def cleanup_logs():
    cutoff = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    remaining = [(t, msg) for (t, msg) in logs if t >= cutoff]
    logs.clear()
    logs.extend(remaining)

# alerting logic

def get_alert_severity(latency, failure_rate):
    # check severity
    if latency > THRESHOLDS['P0']['latency'] or failure_rate > THRESHOLDS['P0']['failure_rate']:
        return 'P0'
    elif latency > THRESHOLDS['P1']['latency'] or failure_rate > THRESHOLDS['P1']['failure_rate']:
        return 'P1'
    elif latency > THRESHOLDS['P2']['latency'] or failure_rate > THRESHOLDS['P2']['failure_rate']:
        return 'P2'
    else:
        return None

def check_and_update_alert(latency, failure_rate):
    global active_alert
    current_severity = get_alert_severity(latency, failure_rate)
    
    if active_alert is None:
        if current_severity is not None:
            # start alert
            active_alert = Alert(current_severity)
            log(f"{current_severity} Alert Triggered! (Latency={latency}ms, FailRate={failure_rate*100:.2f}%)")
    else:
        existing_sev = active_alert.severity
        
        # no severity = resolve
        if current_severity is None:
            log(f"Latency/Failure Rate Normalized. Resolving {existing_sev} alert.")
            active_alert = None
        else:
            # might escalate
            severity_order = ['P2', 'P1', 'P0']
            if severity_order.index(current_severity) < severity_order.index(existing_sev):
                log(f"Alert Escalated from {existing_sev} to {current_severity}!")
                active_alert = Alert(current_severity)

def handle_alert_notifications():
    global active_alert
    if active_alert is None:
        return
    
    severity = active_alert.severity
    now = datetime.now()
    # check if we need to resend notification
    hours_since_last_notify = (now - active_alert.last_notified).total_seconds() / 3600.0
    
    if hours_since_last_notify >= REPEAT_HOURS[severity]:
        log(f"ALERT: Resending {severity} alert")
        active_alert.last_notified = now
    
    # see if we need to escalate
    if now >= active_alert.skip_level_boss_deadline:
        log(f"ALERT: Sending escalation to skip-level boss for {severity} alert")
        active_alert.skip_level_boss_deadline = now + timedelta(
            hours=REPEAT_HOURS[severity] * 5
        )


# simulating the error metrics
def generate_metrics():
    # poisson distribution
    latency_base = int(random.gammavariate(700, 1))
    if random.random() < 0.5:
        latency_base += random.randint(1000, 3000)
    
    fail_base = int(random.gammavariate(2, 1))
    
    latency = latency_base
    failure_rate = fail_base / 100.0
    return latency, failure_rate

# main test

def main():
    log("Starting Alert Monitoring System...")
    try:
        while True:
            latency, failure_rate = generate_metrics()
            
            log(f"INFO: Current metrics => Latency={latency}ms, Failure Rate={failure_rate*100:.2f}%")
            check_and_update_alert(latency, failure_rate)
            handle_alert_notifications()
            cleanup_logs()
            
            time.sleep(CHECK_INTERVAL_MINUTES)  
    except KeyboardInterrupt:
        log("Shutting down system...")

if __name__ == "__main__":
    main()
