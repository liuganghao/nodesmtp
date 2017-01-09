#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime
from math import ceil
from random import SystemRandom

from invoicedao import save_invoice
from invoicemailparser import parse
from invoiceminer import mine_and_parse

config = {
    'debug': False,
    'dir.attachment': '/data/invoiceminer'
}

def usage():
    print('python emlintomysql.py /path/to/emlfile')

def main():
    if not sys.argv or len(sys.argv) < 2:
        usage()
        exit(1)

    emlname = os.path.abspath(sys.argv[1])
    if not os.path.exists(emlname):
        usage()
        exit(1)
    if not os.path.isfile(emlname):
        usage()
        exit(1)

    invoicemail = parse(emlname)
    if not invoicemail:
        return

    if invoicemail.attachments:
        save_attachments(invoicemail.attachments)

    save_to_mysql(invoicemail)

    if config['debug']:
        print(invoicemail.tojson())

def save_to_mysql(invoicemail):
    try:
        for attach in invoicemail.attachments:
            pdf_name = os.path.join(attach.containerpath, attach.path[1:])
            invoice = mine_and_parse(pdf_name)
            invoice.create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_invoice(invoice, filepath = pdf_name)
    except Exception as e:
        ename = '%s.%s' % (e.__module__, e.__class__.__name__)
        print('error %s %s %s' % (pdf_name, ename, str(e)))

def save_attachments(attachments):
    for attachment in attachments:
        attachment.containerpath = config['dir.attachment']

        now = datetime.now()
        wom = week_of_month(now)
        dirpath = '%s%s' % (now.strftime('%Y%m'), str(wom).zfill(2))

        name, extension = os.path.splitext(attachment.name)
        if not extension:
            extension = ''
        filename = '%s%s%s' % (now.strftime('%Y%m%d%H%M%S%f')[:-3], random_digit_string(4), extension)
        attachment.path = ''.join(['/', dirpath, '/', filename])

        absdirpath = os.path.join(config['dir.attachment'], dirpath)
        if not os.path.exists(absdirpath):
            os.makedirs(absdirpath)

        absfilepath = os.path.join(config['dir.attachment'], dirpath, filename)
        with open(absfilepath, 'wb') as file:
            file.write(attachment.content)


def random_digit_string(length):
    cryptorandom = SystemRandom()
    randomlist = cryptorandom.sample(range(0, 9), length)

    return ''.join(str(x) for x in randomlist)

def week_of_month(dt):
    first_day = dt.replace(day=1)

    dom = dt.day
    adjusted_dom = dom + first_day.weekday()

    return int(ceil(adjusted_dom / 7.0))

def get_file_name():
    now = datetime.now()


if __name__ == '__main__':
    main()
