#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

def usage():
    print('usage: python pdfcount.py root_dir')

def main():
    if len(sys.argv) != 2:
        usage()
        exit(1)

    abspath = os.path.abspath(sys.argv[1])
    if not os.path.exists(abspath):
        print('not exists: %s' % (abspath))
        exit(1)
    if not os.path.isdir(abspath):
        print('not directory: %s' % (abspath))
        exit(1)

    suffix = '.pdf'
    count = 0
    for dirpath, dirnames, filenames in os.walk(abspath):
        for filename in filenames:
            if filename.endswith(suffix):
                count += 1

    print('pdf file count: %s' % (count))

if __name__ == '__main__':
    main()