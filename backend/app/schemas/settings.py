from pydantic import BaseModel


class DemoSettingsUpdate(BaseModel):
    generate_demo_events: bool | None = None


class NotificationPrefs(BaseModel):
    email_alerts: bool = True
    push_alerts: bool = False


class SettingsOut(BaseModel):
    notification_prefs: NotificationPrefs
    demo_mode_hint: str = "Use Events → Generate synthetic data for demos."
