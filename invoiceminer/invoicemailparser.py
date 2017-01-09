# -*- coding: utf-8 -*-
import json
from collections import OrderedDict
from datetime import datetime
from email.header import decode_header
from email.parser import Parser

# 邮件
class InvoiceMail:
    def __init__(self):
        self.id = None
        self.mailfrom = None
        self.mailto = None
        self.subject = None
        self.messageid = None
        self.senttime = None
        self.textcontent = None
        self.htmlcontent = None
        self.createtime = None
        self.description = None
        self.attachments = None

    def tojson(self):
        ordereddict = OrderedDict([
            ('id', self.id),
            ('mailFrom', self.mailfrom),
            ('mailTo', self.mailto),
            ('subject', self.subject),
            ('textContent', self.textcontent),
            ('htmlContent', self.htmlcontent)
        ])

        if self.createtime:
            ordereddict['createTime'] = self.createtime.strftime('%Y-%m-%d %H:%M:%S')

        ordereddict['description'] = self.description

        if self.attachments:
            attach_list = []
            for attach in self.attachments:
                aod = OrderedDict([
                    ('id', attach.id),
                    ('name', attach.name),
                    ('containerPath', attach.containerpath),
                    ('path', attach.path)
                ])

                if attach.createtime:
                    aod['createTime'] = attach.createtime.strftime('%Y-%m-%d %H:%M:%S')

                aod['description'] = attach.description

                attach_list.append(aod)

            ordereddict['attachments'] = attach_list

        return json.dumps(ordereddict, ensure_ascii=False, indent=2)

# 附件
class InvoiceMailAttachment:
    def __init__(self):
        self.id = None
        self.name = None
        self.path = None
        self.containerpath = None
        self.createtime = None
        self.description = None
        self.content = None
        self.invoicemail = None

def parse(mfile):
    fp = open(mfile, 'rb')
    parser = Parser()
    message = parser.parse(fp)
    fp.close()

    invoicemail = InvoiceMail()
    invoicemail.createtime = datetime.now()
    fill_headers(message, invoicemail)

    fill_content(message, invoicemail)

    return invoicemail

# 填充邮件头
def fill_headers(message, invoicemail):
    hfrom = message.get('From')
    if hfrom:
        invoicemail.mailfrom = get_from(hfrom)

    hto = message.get('To')
    if hto:
        invoicemail.mailto = get_to(hto)

    hsubject = message.get('Subject')
    if hsubject:
        invoicemail.subject = get_subject(hsubject)

    hmessageid = message.get('Message-ID')
    if hmessageid:
        invoicemail.messageid = get_messageid(hmessageid)

    hdate = message.get('Date')
    if hdate:
        invoicemail.senttime = get_senttime(hdate)

# 获取发件人
def get_from(mailfrom):
    decoded = decode_header(mailfrom)
    faddr = None
    for item in decoded:
        if not item[1]:
            faddr = item[0]
            break

    if faddr and len(faddr) > 2:
        start = 0
        end = len(faddr)
        index = faddr.find('<')
        if index != -1:
            start = index + 1
        index = faddr.find('>')
        if index != -1:
            end = index
        return faddr[start:end]

# 获取收件人
def get_to(mailto):
    decoded = decode_header(mailto)
    faddr = None
    for item in decoded:
        if not item[1]:
            faddr = item[0]
            break

    if faddr and len(faddr) > 2:
        start = 0
        end = len(faddr)
        index = faddr.find('<')
        if index != -1:
            start = index + 1
        index = faddr.find('>')
        if index != -1:
            end = index
        return faddr[start:end]

# 获取主题
def get_subject(subject):
    decoded = decode_header(subject)

    if decoded and decoded[0]:
        return decoded[0][0]

# 获取 Message-ID
def get_messageid(hmessageid):
    decoded = decode_header(hmessageid)

    if decoded and decoded[0]:
        msgid = decoded[0][0]
        start = 0
        end = len(msgid)
        if msgid[0] == '<':
            start = 1
        if msgid[len(msgid) - 1] == '>':
            end = len(msgid) - 1

        return msgid[start:end]

def get_senttime(hdate):
    return hdate

def fill_content(message, invoicemail):
    contenttype = message.get_content_type();
    if not message.is_multipart():
        invoicemail.textcontent = message.get_payload(decode = True)
        return
    elif contenttype == 'multipart/alternative':
        for part in message.get_payload():
            contenttype = part.get_content_type()
            if contenttype == 'text/plain':
                invoicemail.textcontent = part.get_payload(decode = True)
            elif contenttype == 'text/html':
                invoicemail.htmlcontent = part.get_payload(decode = True)

        return

    if contenttype != 'multipart/mixed':
        return

    for part in message.get_payload():
        contenttype = part.get_content_type()
        if contenttype.startswith('text/'):
            invoicemail.textcontent = part.get_payload(decode=True)
        elif contenttype == 'multipart/alternative':
            for item in part.get_payload():
                contenttype = item.get_content_type()
                if contenttype == 'text/plain':
                    invoicemail.textcontent = item.get_payload(decode = True)
                elif contenttype == 'text/html':
                    invoicemail.htmlcontent = item.get_payload(decode = True)
        else:
            encoded_filename = part.get_filename()
            decoded = decode_header(encoded_filename)
            if not decoded or not decoded[0] or not decoded[0][0]:
                continue

            filename = decoded[0][0]
            if not filename:
                continue

            filecontent = part.get_payload(decode=True)
            attachment = InvoiceMailAttachment()
            attachment.createtime = datetime.now()
            attachment.invoicemail = invoicemail
            attachment.name = filename
            attachment.content = filecontent
            if not invoicemail.attachments:
                invoicemail.attachments = []
            invoicemail.attachments.append(attachment)
