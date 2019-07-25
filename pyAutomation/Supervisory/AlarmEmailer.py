from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.Supervisory.AlarmNotifier import AlarmNotifier
from email.mime.text import MIMEText
import threading
import smtplib
import logging

class AlarmEmailer(AlarmNotifier):

    parameters = {
      'mailhost': 'localhost',
      'mailport': '587',
      'local_hostname': 'automation',
      'mail_sender': 'alarm_notifier',
      'mail_receivers': 'alarm_reciever@email.com'
    }

    def __init__(self, name: str, logger: str) -> None:
        self.logger = logging.getLogger(logger)
        self.name = name
        self.mailhost = ""
        self.mailport = ""
        self.local_hostname = ""
        self.mail_sender = ""
        self.mail_receivers = ""

    def notify(self, alarm: Alarm, verb: str) -> None:
        message = MIMEText(
            "Alarm: {} {} \n"
            "Consequences: {} \n"
            "More info: {}".format(
                alarm.description,
                verb,
                alarm.consequences,
                alarm.more_info))

        message['Subject'] = alarm.description + " alarm"
        message['From'] = self.mail_sender
        message['To'] = self.mail_receivers

        # sending e-mail is slow. Do it in another thread.
        t = threading.Thread(
          target=self.send_email,
          args=(
            message,
            self.mailhost,
            self.mailport,
            self.local_hostname,
            self.logger,))
        t.start()

    @staticmethod
    def send_email(message, mailhost, mailport, local_hostname, logger) -> None:
        try:
            smtp_obj = smtplib.SMTP(
              mailhost,
              mailport,
              local_hostname)
            smtp_obj.sendmail(message['From'], message['To'], str(message))
            smtp_obj.quit()
            logger.info("Successfully sent email")
        except smtplib.SMTPException:
            logger.error(traceback.format_exc())
            logger.error("Error: unable to send email: " + str(message))
