import os
import re
from datetime import datetime

# Emoji stripper for console output
_EMOJI_PATTERN = re.compile(
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

# Priority map for ntfy.sh
_NTFY_PRIORITY = {
    'critical_alert': 'urgent',
    'safety_alert':   'high',
    'outdated_doc_alert': 'default',
    'tacit_alert':    'low',
}

# Emoji map for ntfy tags
_NTFY_TAGS = {
    'critical_alert':    'rotating_light,skull',
    'safety_alert':      'warning,construction_worker',
    'outdated_doc_alert':'page_facing_up,arrows_counterclockwise',
    'tacit_alert':       'brain,memo',
}


class PushEngine:
    """
    Proactive alert engine that pushes critical safety and maintenance notifications
    to field engineers via ntfy.sh (real mobile push) with console fallback.

    Set NTFY_TOPIC in your .env to a unique topic string (e.g. 'teevrgati-bpcl-demo').
    Install the ntfy app on your phone and subscribe to that topic for live demo alerts.
    """

    def __init__(self):
        self.dispatched_alerts = []
        self.ntfy_topic = os.getenv('NTFY_TOPIC', '')
        self.ntfy_server = os.getenv('NTFY_SERVER', 'https://ntfy.sh')

    def push_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        recipient: str = "Shift Supervisor"
    ) -> dict:
        """
        Dispatch an alert. Sends to ntfy.sh if NTFY_TOPIC is configured,
        always logs to console.
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert = {
            'timestamp': ts,
            'type':      alert_type,
            'title':     title,
            'message':   message,
            'recipient': recipient,
            'status':    'dispatched',
            'channel':   'console'
        }
        self.dispatched_alerts.append(alert)

        clean_title   = _EMOJI_PATTERN.sub("", title).strip()
        clean_message = _EMOJI_PATTERN.sub("", message).strip()

        # ── Real mobile push via ntfy.sh ──────────────────────────────────────
        if self.ntfy_topic:
            try:
                import urllib.request
                url = f"{self.ntfy_server}/{self.ntfy_topic}"
                body = f"[{recipient}] {clean_message}".encode("utf-8")
                headers = {
                    "Title":    clean_title,
                    "Priority": _NTFY_PRIORITY.get(alert_type, 'default'),
                    "Tags":     _NTFY_TAGS.get(alert_type, 'bell'),
                    "Content-Type": "text/plain; charset=utf-8"
                }
                req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        alert['channel'] = 'ntfy'
                        print(f"📲 [NTFY PUSH → {self.ntfy_topic}] {clean_title}: {clean_message}")
                    else:
                        print(f"⚠️  ntfy returned HTTP {resp.status} — falling back to console")
            except Exception as e:
                print(f"⚠️  ntfy push failed ({e}) — console only")

        # ── Console log (always) ─────────────────────────────────────────────
        print(f"📤 [ALERT → {recipient}] [{clean_title}] {clean_message}")
        return alert

    def push_shift_briefing(self, asset_id: str, open_near_misses: int, unresolved_rfis: int, pending_wo: int) -> dict:
        """
        Proactive shift-changeover briefing — pushed without being asked.
        This is the 'push, don't wait' differentiator from the plan.
        """
        msg = (
            f"Shift Briefing — {asset_id}: "
            f"{open_near_misses} open near-misses | "
            f"{unresolved_rfis} unresolved RFIs | "
            f"{pending_wo} pending work orders. "
            f"Review before equipment handover."
        )
        return self.push_alert(
            alert_type='safety_alert',
            title=f"🌅 Shift Briefing — {asset_id}",
            message=msg,
            recipient="Incoming Shift Supervisor"
        )

    def get_all_alerts(self) -> list:
        return self.dispatched_alerts
