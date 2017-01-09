#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mysql.connector

import config

dbconfig = {
    'host': '127.0.0.1',
    'port': 3306,
    'database': 'invoicerepo2',
    'user': 'invoicerepo',
    'password': 'invoicerepo',
    'charset': 'utf8',
    'use_unicode': True,
    'get_warnings': True
}

cnx = mysql.connector.connect(pool_name = 'mypool',
                              pool_size = config.config['mysql_pool_size'],
                              **dbconfig)
cur = cnx.cursor()

# 获取最大发票 ID
def get_max_id():
    stmt = 'select max(id) from in_invoice'
    cur.execute(stmt)

    maxid = 0
    for row in cur.fetchall():
        maxid = row[0]
        break

    if maxid == None:
        maxid = 0

    return maxid

# 保存发票
def save_invoice(invoice, filepath = None):
    if not invoice.hash:
        maxid = get_max_id()
        invoice.id = maxid + 1
        insert_invoice(invoice, filepath = filepath)
    else:
        id = get_id_by_hash(invoice.hash)
        if not id:
            maxid = get_max_id()
            invoice.id = maxid + 1
            insert_invoice(invoice, filepath=filepath)
        else:
            invoice.id = id
            update_invoice(invoice, filepath = filepath)

# 根据文件 hash 获取发票
def get_id_by_hash(hash):
    stmt = "select id from in_invoice where hash = '{0}' limit 0, 1".format(hash)
    cur.execute(stmt)

    id = None
    for row in cur.fetchall():
        id = row[0]
        break

    return id

# 插入发票
def insert_invoice(invoice, filepath = None):
    if not invoice:
        return

    stmt = '''
        insert into in_invoice(
        id, code, number, create_date, machine_code, check_code, buyer_name, buyer_taxpayer_id,
        buyer_address, buyer_phone, buyer_bank_name, buyer_bank_account, net_amount, tax_amount,
        total_amount, seller_name, seller_taxpayer_id, seller_address, seller_phone,
        seller_bank_name, seller_bank_account, hash, file_path, remark
        ) values(
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s
        )
    '''
    data = (invoice.id, invoice.code, invoice.number, invoice.create_date, invoice.machine_code,
            invoice.check_code, invoice.buyer_name, invoice.buyer_taxpayer_id, invoice.buyer_address,
            invoice.buyer_phone, invoice.buyer_bank_name, invoice.buyer_bank_account, invoice.net_amount,
            invoice.tax_amount, invoice.total_amount, invoice.seller_name, invoice.seller_taxpayer_id,
            invoice.seller_address, invoice.seller_phone, invoice.seller_bank_name,
            invoice.seller_bank_account, invoice.hash, filepath, invoice.remark)
    cur.execute(stmt, data)
    cnx.commit()

# 根据 ID 更新发票
def update_invoice(invoice, filepath = None):
    stmt = (
        'update in_invoice set code = %s, number = %s, create_date = %s, machine_code = %s, '
        'check_code = %s, buyer_name = %s, buyer_taxpayer_id = %s, buyer_address = %s, '
        'buyer_phone = %s, buyer_bank_name = %s, buyer_bank_account = %s, net_amount = %s, '
        'tax_amount = %s, total_amount = %s, seller_name = %s, seller_taxpayer_id = %s, '
        'seller_address = %s, seller_phone = %s, seller_bank_name = %s, seller_bank_account = %s, '
        'hash = %s, file_path = %s, remark = %s '
        'where id = %s'
    )

    cur.execute(stmt, (invoice.code, invoice.number, invoice.create_date, invoice.machine_code,
                       invoice.check_code, invoice.buyer_name, invoice.buyer_taxpayer_id,
                       invoice.buyer_address, invoice.buyer_phone, invoice.buyer_bank_name,
                       invoice.buyer_bank_account, invoice.net_amount, invoice.tax_amount,
                       invoice.total_amount, invoice.seller_name, invoice.seller_taxpayer_id,
                       invoice.seller_address, invoice.seller_phone, invoice.seller_bank_name,
                       invoice.seller_bank_account, invoice.hash, filepath, invoice.remark,
                       invoice.id))
    cnx.commit()
