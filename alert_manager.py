import yagmail
import time

class AlertManager:
    def __init__(self, sender_email, app_password, cooldown=300):
        self.cooldown = cooldown
        self.last_alert = 0

        try:
            self.mail = yagmail.SMTP(sender_email, app_password)
            print("✅ Email service ready")
        except Exception as e:
            self.mail = None
            print(f"❌ Email init failed: {e}")

    def send_alert(self, to_email, subject, message, image=None):
        if not self.mail:
            return

        if time.time() - self.last_alert < self.cooldown:
            print("🕒 Cooldown active, alert skipped")
            return

        contents = [message]
        if image:
            contents.append(yagmail.inline(image))

        try:
            self.mail.send(to=to_email, subject=subject, contents=contents)
            self.last_alert = time.time()
            print("📧 Alert sent")
        except Exception as e:
            print(f"❌ Email send failed: {e}")
