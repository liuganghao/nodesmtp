#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time

from invoiceminer import mine_and_parse


def usage():
    print('usage: python pdf2json.py path_to_invoice_pdf_file')

def main():
    if len(sys.argv) != 2:
        usage()
        exit(1)

    pdf_name = os.path.abspath(sys.argv[1])
    if not os.path.exists(pdf_name):
        print('not exists: %s' % (pdf_name))
        exit(1)

    if not os.path.isfile(pdf_name):
        print('not file: %s' % (pdf_name))
        exit(1)

    try:
        invoice = mine_and_parse(pdf_name)
        invoice.create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print(invoice)
    except Exception as e:
        ename = '%s.%s' % (e.__module__, e.__class__.__name__)
        print('error %s %s %s' % (pdf_name, ename, str(e)))

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    main()