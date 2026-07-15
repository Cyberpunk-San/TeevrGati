from datetime import datetime

class PushEngine:
    """
    Simulated proactive alert engine responsible for pushing critical, 
    safety, and tacit knowledge updates to field engineers and safety coordinators.
    """
    
    def __init__(self):
        self.dispatched_alerts = []
        
    def push_alert(self, alert_type: str, title: str, message: str, recipient: str = "Shift Supervisor") -> dict:
        """
        Simulate alert dispatch. In a live system, this sends a mobile push, 
        SMS, Slack hook, or email notification.
        """
        alert = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': alert_type,
            'title': title,
            'message': message,
            'recipient': recipient,
            'status': 'dispatched'
        }
        self.dispatched_alerts.append(alert)
        
        # Strip emoji indicators if printing to standard console to prevent encoding issues on Windows
        import re
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f1e0-\U0001f1ff"
            "\u2700-\u27bf"
            "\u2600-\u26ff"
            "\ufe0f"
            "\u200d"
            "\U0001f000-\U0001ffff"
            "]+", flags=re.UNICODE
        )
        clean_title = emoji_pattern.sub("", title).strip()
        clean_message = emoji_pattern.sub("", message).strip()
        print(f"📤 [ALERT PUSHED] Recipient: {recipient} | [{clean_title}] {clean_message}")
        
        return alert
        
    def get_all_alerts(self) -> list:
        return self.dispatched_alerts
