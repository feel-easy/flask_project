from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from info import constants

import smtplib


class SendEmail(object):

    def __init__(self,to_addr, num):
        self.to_addr = to_addr
        self.num = num

    @staticmethod
    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))


    def send(self):
        msg = MIMEText('网页的验证码 %s 请在10分钟内有效！！！' % self.num , 'plain', 'utf-8')
        msg['From'] = self._format_addr('网页 <%s>' % constants.from_addr)
        msg['To'] = self._format_addr('管理员<%s>' % self.to_addr)
        msg['Subject'] = Header('消息验证码', 'utf-8').encode()

        server = smtplib.SMTP(constants.smtp_server, 25)
        # server.set_debuglevel(1)
        server.login(constants.from_addr, constants.password)
        server.sendmail(constants.from_addr, self.to_addr, msg.as_string())
        server.quit()
        return 1

if __name__ == '__main__':
    em = SendEmail([constants.to_addr],'66666')
    em.send()