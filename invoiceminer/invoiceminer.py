# -*- encoding: utf-8 -*-
import hashlib
import time

from pdfminer.converter import TextConverter
from pdfminer.layout import LTContainer, LTChar, LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

import config


class InvoiceType:
    # value-added tax: 增值税
    VAT = 1
    # sales tax: 营业税
    ST = 2

class InvoiceConverter(TextConverter):
    char_tuple_list = []
    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTContainer):
                for child in item:
                    render(child)
            elif isinstance(item, LTChar):
                c = item.get_text().strip()
                if c:
                    self.char_tuple_list.append((c, item.x0, item.y0, item.x1, item.y1, item.height))

        render(ltpage)

        return

# 实体类: 发票
class Invoice(object):
    def __init__(self):
        self.id = None
        self.type = None
        self.code = ''
        self.number = ''
        self.create_date = ''
        self.machine_code = ''
        self.check_code = ''
        self.buyer_name = ''
        self.buyer_taxpayer_id = ''
        self.buyer_address = ''
        self.buyer_phone = ''
        self.buyer_bank_name = ''
        self.buyer_bank_account = ''
        self.net_amount = ''
        self.tax_amount = ''
        self.total_amount = ''
        self.seller_name = ''
        self.seller_taxpayer_id = ''
        self.seller_address = ''
        self.seller_phone = ''
        self.seller_bank_name = ''
        self.seller_bank_account = ''
        self.hash = ''
        self.create_time = ''
        self.remark = ''

    def __repr__(self):
        return (
            '{'
            '"type":"' + str(self.type) + '"'
            ',"code":"' + str(self.code) + '"'
            ',"number":"' + str(self.number) + '"'
            ',"machine_code":"' + str(self.machine_code) + '"'
            ',"check_code":"' + str(self.check_code) + '"'
            ',"buyer_name":"' + str(self.buyer_name) + '"'
            ',"buyer_address":"' + str(self.buyer_address) + '"'
            ',"buyer_phone":"' + str(self.buyer_phone) + '"'
            ',"create_date":"' + str(self.create_date) + '"'
            ',"net_amount":"' + str(self.net_amount) + '"'
            ',"tax_amount":"' + str(self.tax_amount) + '"'
            ',"total_amount":"' + str(self.total_amount) + '"'
            ',"seller_name":"' + str(self.seller_name) + '"'
            ',"seller_taxpayer_id":"' + str(self.seller_taxpayer_id) + '"'
            ',"hash":"' + str(self.hash) + '"'
            ',"create_time":"' + str(self.create_time) + '"'
            '}'
        )

# 是否是英文字母
def is_alpha(char):
    try:
        return char.encode('ascii').isalpha()
    except:
        return False

# 获取指定文件的 SHA1 摘要
def sha1hex(file_name):
    sha1 = hashlib.sha1()
    with open(file_name, 'rb') as file:
        while True:
            data = file.read(10 * 1024)
            if not data:
                break
            else:
                sha1.update(data)
    digest = sha1.hexdigest()
    return digest

def mine(pdf_file_name):
    laparams = LAParams()
    resource_manager = PDFResourceManager()
    device = InvoiceConverter(resource_manager, None, laparams=laparams)

    pf = open(pdf_file_name, 'rb')
    interpreter = PDFPageInterpreter(resource_manager, device)
    interpreter.process_page(PDFPage.get_pages(pf).next())
    pf.close()
    device.close()

    char_tuple_list = device.char_tuple_list
    # avg_y0(char_tuple_list)

    row_str_list = line_list(char_tuple_list)

    return row_str_list

# 挖掘并解析
def mine_and_parse(pdf_name):
    row_list = mine(pdf_name)
    if not row_list:
        return None

    if config.config['debug']:
        for row in row_list:
            print(row)

    invoice = parse(row_list)
    if invoice:
        invoice.hash = sha1hex(pdf_name)
        cur = time.time()
        time_array = time.localtime(cur)
        invoice.create_time = time.strftime('%Y-%m-%d %H:%M:%S', time_array)

    return invoice

# 根据字符高度对 y0 进行修正
def avg_y0(char_tuple_list):
    height_sum = 2
    for char_tuple in char_tuple_list:
        height_sum += char_tuple[5]

    height_avg = height_sum / len(char_tuple_list)

    for i in range(len(char_tuple_list)):
        char_tuple = char_tuple_list[i]
        y0 = char_tuple[2]
        height = char_tuple[5]
        y0_new = y0 + (height_avg - height)

        char_tuple_list[i] = (char_tuple[0], char_tuple[1], y0_new, char_tuple[3], char_tuple[4], char_tuple[5])

# 按行计算字符串列表
def line_list(char_tuple_list):
    row_group = {}
    for tp in char_tuple_list:
        key = str(tp[2])
        if row_group.get(key) == None:
            row_group[key] = []

        row_group[key].append(tp)
    #print("修正前的行数: " + str(len(row_group)))

    y0_list = []
    for key in row_group:
        y0_list.append(float(key))
    y0_list.sort(reverse = True)

    delta = 3
    y0_group_list = None
    for y0 in y0_list:
        if y0_group_list == None:
            y0_group_list = []
            y0_group_list.append([])

        if len(y0_group_list[len(y0_group_list) - 1]) == 0:
            y0_group_list[len(y0_group_list) - 1].append(y0)
            continue

        # 0
        # len(y0_group_list[len(y0_group_list) - 1]) - 1
        last_index = len(y0_group_list[len(y0_group_list) - 1]) - 1
        if y0 >= y0_group_list[len(y0_group_list) - 1][last_index] - delta:
            y0_group_list[len(y0_group_list) - 1].append(y0)
        else:
            y0_group_list.append([])
            y0_group_list[len(y0_group_list) - 1].append(y0)

    '''
    print("票面信息行数: " + str(len(y0_group_list)))
    for y0_group in y0_group_list:
        print(y0_group)
    '''

    row_list = []
    for y0_group in y0_group_list:
        row = []
        for y0 in y0_group:
            row += row_group[str(y0)]
        row_list.append(row)

    # print('票面信息行数2: ' + str(len(row_list)))

    row_str_list = []
    for row in row_list:
        x0_list = []
        for row_char_tuple in row:
            x0_list.append(row_char_tuple[1])
        x0_list.sort()

        row_str = ''
        for x0 in x0_list:
            for row_char_tuple in row:
                if row_char_tuple[1] == x0:
                    row_str += row_char_tuple[0]
                    break

        row_str_list.append(row_str)

    return row_str_list

# 由发票 PDF 的字符内容解析出发票对象
def parse(line_list):
    inv = Invoice()
    type = get_invoice_type(line_list)
    inv.type = type

    inv.code = get_code(line_list)
    inv.number = get_number(line_list)

    if type == InvoiceType.VAT:
        inv.buyer_name = get_buyer_name(line_list)
    elif type == InvoiceType.ST:
        inv.buyer_name = get_buyer_name_st(line_list)

    buyer_addr_phone = get_buyer_address_phone2(line_list)
    inv.buyer_address = buyer_addr_phone[0]
    inv.buyer_phone = buyer_addr_phone[1]

    if type == InvoiceType.VAT:
        inv.create_date = get_create_date(line_list)
    elif type == InvoiceType.ST:
        inv.create_date = get_create_date_st(line_list)

    inv.machine_code = get_machine_code(line_list)
    inv.check_code = get_check_code(line_list)

    if type == InvoiceType.VAT:
        inv.net_amount = get_net_amount(line_list)

    if type == InvoiceType.VAT:
        inv.tax_amount = get_tax_amount2(line_list)

    if type == InvoiceType.VAT:
        inv.total_amount = get_total_amount2(line_list)
    elif type == InvoiceType.ST:
        inv.total_amount = get_total_amount_st(line_list)

    if type == InvoiceType.VAT:
        inv.seller_name = get_seller_name(line_list)
    elif type == InvoiceType.ST:
        inv.seller_name = get_seller_name_st(line_list)

    if type == InvoiceType.VAT:
        inv.seller_taxpayer_id = get_seller_taxpayer_id(line_list)
    elif type == InvoiceType.ST:
        inv.seller_taxpayer_id = get_seller_taxpayer_id_st(line_list)

    return inv

# 判断发票类型，增值税票和普通发票
def get_invoice_type(row_list):
    if not row_list:
        return None

    type_key = u'增值税'
    type = InvoiceType.ST
    stop = len(row_list) / 2
    for i in range(stop):
        if row_list[i].find(type_key) != -1:
            type = InvoiceType.VAT
            break

    return type

# 获取发票代码
def get_code(line_list):
    key = u'发票代码'

    index = 0
    value = ''
    for line in line_list:
        index = line.find(key)
        if index != -1:
            value = line
            break

    if not value:
        return ''

    # 发票代码为 12 位数字
    length = 12
    if len(value) - index < length:
        return ''

    code = ''
    for i in range(index + len(key), len(value)):
        if len(code) == length:
            break

        if value[i].isdigit():
            code += value[i]

    return code

# 获取发票号码
def get_number(line_list):
    key = u'发票号码'

    index = 0
    value = ''
    for line in line_list:
        index = line.find(key)
        if index != -1:
            value = line
            break

    if not value:
        return ''

    # 发票号码为 8 位数字
    length = 8
    if len(value) - index < length:
        return ''

    number = ''
    for i in range(index + len(key), len(value)):
        if len(number) == length:
            break

        if value[i].isdigit():
            number += value[i]

    return number

# 获取购买方名称
def get_buyer_name(line_list):
    key = u'名称'

    # 第一次匹配为购买方名称
    index = 0
    value = ''
    for line in line_list:
        index = line.find(key)
        if index != -1:
            value = line
            break

    if not value:
        return ''

    # 到 '密' 字 或 行尾停止, 因购买方名称与密码区在同一行
    if len(value) <= len(key):
        return ''

    sw = u'密'
    bname = ''
    for i in range(index + len(key), len(value)):
        if value[i] == u'：' or value[i] == ':':
            continue
        if value[i] == sw and bname:
            break

        bname += value[i]

    return bname

# 获取普通发票购买方名称
def get_buyer_name_st(row_list):
    key = u'付款单位'
    key2 = u'付款方名称'

    value = ''
    for row in row_list:
        if row.find(key) != -1 or row.find(key2) != -1:
            value = row
            break
    if not value:
        return ''

    # ':' 或 '：' 后的所有
    sep = ':'
    sep2 = u'：'
    bname = ''
    for i in range(len(value)):
        if value[i] == sep or value[i] == sep2:
            if i < len(value) - 1:
                bname = value[i + 1:]
            break

    return bname

# 获取购买方地址
def get_buyer_address(line_list):
    # 第一次匹配为购买方的
    key = u'地址、电话'

    index = 0
    value = ''
    for line in line_list:
        index = line.find(key)
        if index != -1:
            value = line
            break

    if not value or len(value) == len(key):
        return ''

    # 跳过: ':' 或 '：'
    sv = value[len(key) + 1:]
    # 非汉字开头
    if not (sv[0] >= u'\u4e00' and sv[0] <= u'\u9fa5'):
        return ''

    # 汉字开头且汉字结尾为
    addr = ''
    for i in range(len(key), len(value), 1):
        if i == len(key):
            if value[i] == ':' or value[i] == '：':
                continue

        if not addr and (value[i].isdigit() or value[i] == '-' or value[i] == '+' or value[i] == '*' or value[i] == '/' or value[i] == '>' or value[i] == '<'):
            break

# 获取购买方地址、电话(手机号)
def get_buyer_address_phone2(line_list):
    # 第一次匹配为购买方的
    key = u'地址、电话'

    index = 0
    value = ''
    for line in line_list:
        index = line.find(key)
        if index != -1:
            value = line
            break

    if not value:
        return ('', '')

    # 跳过 ':' 或 '：'
    ap = value[index + len(key) + 1:]
    if not ap:
        return ('', '')

    # 电话号码模式: 手机号 11 位, 座机 11 或 12 位, 12 位的座机号带'-'
    address = ''
    phone = ''
    addr_phone = ''
    found = True
    for i in range(len(ap)):
        addr_phone += ap[i]

        if len(addr_phone) < 11:
            continue

        ph = addr_phone[len(addr_phone) - 11 : ]
        for char in ph:
            if not char.isdigit():
                found = False
                break

        if found:
            address = addr_phone[0 : len(addr_phone) - 11]
            phone = ph
            break
        else:
            found = True
            continue

        ph = addr_phone[len(addr_phone) - 12:]
        for char in ph:
            if not (char.isdigit() or char == '-'):
                found = False

        if found:
            address = addr_phone[0 : len(addr_phone) - 12]
            phone = ph
            break

    return (address, phone)

# 获取购买方地址、电话(手机号)
def get_buyer_address_phone(line_list):
    # 第一次匹配为购买方的
    key = u'地址、电话'

    index = 0
    value = ''
    for line in line_list:
        index = line.find(key)
        if index != -1:
            value = line
            break

    if not value:
        return ('', '')

    # 跳过 ':' 或 '：'
    ap = value[index + len(key) + 1:]
    if not ap:
        return ('', '')

    address = ''
    phone = ''
    is_phone = True
    for i in range(len(ap) - 1, -1, -1):
        if ap[i] == ' ':
            is_phone = False

        if is_phone:
            phone = ap[i] + phone
        else:
            address = ap[i] + address

    return (address, phone)

# 获取开票日期
def get_create_date(line_list):
    key = u'开票日期'

    index = 0
    value = ''
    for line in line_list:
        index = line.find(key)
        if index != -1:
            value = line
            break

    if not value:
        return ''

    cd = value[index + len(key):]
    if not cd:
        return ''

    y = ''
    m = ''
    d = ''
    iy = True
    im = False
    id = False
    for i in range(0, len(cd)):
        if cd[i] == u'日':
            break
        elif cd[i] == u'年':
            iy = False
            im = True
            continue
        elif cd[i] == u'月':
            im = False
            id = True
            continue
        elif not cd[i].isdigit():
            continue

        if iy:
            y += cd[i]
            continue
        if im:
            m += cd[i]
            continue
        if id:
            d += cd[i]

    return y + '-' + m + '-' + d

# 获取普通发票开票日期
def get_create_date_st(row_list):
    key = u'开票日期'

    value = ''
    for row in row_list:
        if row.find(key) != -1:
            value = row
            break
    if not value:
        return ''

    # 忽略 ':' 或 '：'
    net_value = value[len(key) + 1:]
    if not net_value:
        return ''
    if not net_value[0].isdigit():
        return ''

    sep = '-'
    sepy = u'年'
    sepm = u'月'
    cdate = ''
    for char in net_value:
        if char.isdigit() or char == sep:
            cdate += char
        elif char == sepy or char == sepm:
            cdate += '-'
        else:
            break

    return cdate

# 获取机器编号
def get_machine_code(line_list):
    key = u'机器编号'

    index = 0
    value = ''
    for line in line_list:
        index = line.find(key)
        if index != -1:
            value = line
            break

    if not value:
        return ''

    # key 后的连续数字为机器编号
    if len(value) <= len(key):
        return ''

    mcode = ''
    for i in range(index + len(key), len(value)):
        if value[i].isdigit():
            mcode += value[i]
        else:
            if not mcode:
                continue
            else:
                break

    return mcode

# 获取校验码
def get_check_code(line_list):
    key = u'校验码'

    index = 0
    value = ''
    for line in line_list:
        index = line.find(key)
        if index != -1:
            value = line
            break

    if not value:
        return ''

    # key 后的连续数字为机器编号
    if len(value) <= len(key):
        return ''

    ccode = ''
    for i in range(index + len(key), len(value)):
        if value[i].isdigit():
            ccode += value[i]
        else:
            if not ccode:
                continue
            else:
                break

    return ccode

# 获取金额
def get_net_amount(line_list):
    # 首次匹配, 本行及下一行
    key = u'合计'

    rmb = u'¥'
    rmb2 = u'￥'
    value = ''
    found = False
    for i in range(len(line_list)):
        if line_list[i].find(key) != -1:
            value = line_list[i]
            for c in value:
                if c == rmb or c == rmb2 or c.isdigit():
                    found = True
                    break

            if found:
                break
            else:
                value = ''

            value = line_list[i - 1]
            if value[0] == rmb or value[0] == rmb2 or value[0].isdigit():
                break
            else:
                value = ''

            if i < len(line_list) - 1:
                value = line_list[i + 1]
                if value[0] == rmb or value[0] == rmb2 or value[0].isdigit:
                    break
                else:
                    value = ''

    if not value:
        return ''

    dot = '.'
    net_amount = ''
    for i in range(len(value)):
        # 到 .00 停止
        if len(net_amount) > 3 and net_amount[len(net_amount) - 3] == dot:
            break

        if value[i].isdigit():
            net_amount += value[i]
        elif value[i] == dot:
            if net_amount.find(dot) != -1:
                break
            else:
                net_amount += value[i]
        else:
            if net_amount:
                break

    return net_amount

# 获取税额
def get_tax_amount2(line_list):
    # 首次匹配, 本行及下一行
    key = u'合计'

    rmb = u'¥'
    rmb2 = u'￥'
    value = ''
    found = False
    for i in range(len(line_list)):
        if line_list[i].find(key) != -1:
            value = line_list[i]
            for c in value:
                if c == rmb or c == rmb2 or c.isdigit():
                    found = True
                    break

            if found:
                break
            else:
                value = ''

            value = line_list[i - 1]
            if value[0] == rmb or value[0] == rmb2 or value[0].isdigit():
                break
            else:
                value = ''

            if i < len(line_list) - 1:
                value = line_list[i + 1]
                if value[0] == rmb or value[0] == rmb2 or value[0].isdigit:
                    break
                else:
                    value = ''

    if not value:
        return ''

    dot = '.'
    net_amount = ''
    index_net = 0
    for i in range(len(value)):
        index_net = i
        # 到 .00 停止
        if len(net_amount) > 3 and net_amount[len(net_amount) - 3] == dot:
            break

        if value[i].isdigit():
            net_amount += value[i]
        elif value[i] == dot:
            if net_amount.find(dot) != -1:
                break
            else:
                net_amount += value[i]
        else:
            if net_amount:
                break

    tax_amount = ''
    for i in range(index_net, len(value), 1):
        # 到 .00 停止
        if len(tax_amount) > 3 and tax_amount[len(tax_amount) - 3] == dot:
            break

        if value[i].isdigit():
            tax_amount += value[i]
        elif value[i] == dot:
            if tax_amount.find(dot) != -1:
                break
            else:
                tax_amount += value[i]
        else:
            if tax_amount:
                break

    return tax_amount

# 获取税额. 废弃
def get_tax_amount(line_list):
    # 首次匹配, 本行及下一行
    key = u'合计'

    line1 = ''
    line2 = ''
    for i in range(len(line_list)):
        if line_list[i].find(key) != -1:
            line1 = line_list[i]
            if i < len(line_list) - 1:
                line2 = line_list[i+1]
            break

    value = line1 + line2
    if not value:
        return ''

    rmb = '¥'
    index = value.rfind(rmb)
    if index == -1:
        rmb = '￥'
        index = value.rfind(rmb)
        if index == -1 or index == len(value) - 1:
            return ''

    dot = '.'
    tax_amount = ''
    for i in range(index + 1, len(value), 1):
        if value[i].isdigit():
            tax_amount += value[i]
        elif value[i] == dot:
            if tax_amount.find(dot) != -1:
                break
            else:
                tax_amount += value[i]
        else:
            break

    return tax_amount

# 获取价税合计金额
def get_total_amount2(line_list):
    # 首次匹配, 本行及下一行
    key = u'价税合计'

    rmb = u'¥'
    rmb2 = u'￥'
    value = ''
    found = False
    for i in range(len(line_list)):
        if line_list[i].find(key) != -1:
            value = line_list[i]
            for c in value:
                if c == rmb or c == rmb2 or c.isdigit():
                    found = True
                    break

            if found:
                break
            else:
                value = ''

            # 上一行
            value = line_list[i - 1]
            dot_count = 0
            dot = '.'
            for char in value:
                if char == dot:
                    dot_count += 1
            if dot_count == 1:
                break
            else:
                value = ''
                dot_count = 0

            # 下一行
            if i < len(line_list) - 1:
                value = line_list[i + 1]
                for char in value:
                    if char == dot:
                        dot_count += 1
                if dot_count == 1:
                    break
                else:
                    value = ''

            break

    if not value:
        return ''

    dot = '.'
    total_amount = ''
    for i in range(len(value)):
        # 到 .00 停止
        if len(total_amount) > 3 and total_amount[len(total_amount) - 3] == dot:
            break

        if value[i].isdigit():
            total_amount += value[i]
        elif value[i] == dot:
            if total_amount.find(dot) != -1:
                break
            else:
                total_amount += value[i]
        else:
            if total_amount:
                break

    return total_amount

# 获取价税合计金额. 废弃
def get_total_amount(line_list):
    # 首次匹配, 本行及下一行
    key = u'价税合计'

    line1 = ''
    line2 = ''
    for i in range(len(line_list)):
        if line_list[i].find(key) != -1:
            line1 = line_list[i]
            if i < len(line_list) - 1:
                line2 = line_list[i+1]
            break

    value = line1 + line2
    if not value:
        return ''

    rmb = '¥'
    index = value.rfind(rmb)
    if index == -1:
        rmb = u'￥'
        index = value.rfind(rmb)
        if index == -1 or index == len(value):
            return ''

    dot = '.'
    total_amount = ''
    for i in range(index + 1, len(value), 1):
        if value[i].isdigit():
            total_amount += value[i]
        elif value[i] == dot:
            if total_amount.find(dot) != -1:
                break
            else:
                total_amount += value[i]
        else:
            break

    return total_amount

'''
获取普通发票合计金额
'''
def get_total_amount_st(row_list):
    key1 = u'合计人民币'
    key2 = u'合计金额'
    key3 = u'金额(大写)'

    row = ''
    for i in range(len(row_list) - 1, -1, -1):
        if row_list[i].find(key1) != -1 or row_list[i].find(key2) != -1 or row_list[i].find(key3) != -1:
            row = row_list[i]
            break
    if not row:
        return ''

    dot = '.'
    ret = ''
    for char in row:
        if len(ret) > 3 and ret[len(ret) - 3] == dot:
            break

        if char.isdigit() or char == dot:
            ret += char

    return ret

'''
获取销售方名称
从尾至头, '名称' 开始, '公司' 结束
'''
def get_seller_name(line_list):
    key = u'名称'
    value = ''
    for i in range(len(line_list) - 1, -1, -1):
        value = line_list[i]
        if value.startswith(key):
            break

    if not value or len(value) <= len(key):
        return ''

    # 忽略 ':' 或 '：'
    valuesuf = value[len(key) + 1:]

    seller_name = ''
    sw = u'公司'
    for i in range(len(valuesuf) - 1, -1, -1):
        if valuesuf[i - 1 : i + 1] == sw:
            seller_name = valuesuf[:i + 1]
            break

    # 至行尾
    if not seller_name:
        seller_name = valuesuf

    return seller_name

'''
获取普通发票的销售方名称
模式: 从尾至头, 包含'收款方'或'收款单位'且包含'名称'的行
'''
def get_seller_name_st(row_list):
    key1 = u'收款方'
    key2 = u'收款单位'
    key3 = u'开票单位'
    key4 = u'名称'

    row = ''
    for i in range(len(row_list) - 1, -1, -1):
        row = row_list[i]
        if (row.find(key1) != -1 or row.find(key2) != -1 or row.find(key3) != -1) and row.find(key4) != -1:
            break

    if not row:
        return ''

    sname = ''
    colon1 = u':'
    colon2 = u'：'
    # ':' 或 '：' 至行尾
    index = -1
    for i in range(len(row)):
        if row[i] == colon1 or row[i] == colon2:
            index = i
            break
    if index != -1 and index < len(row) - 1:
        sname = row[index + 1:]

    return sname

'''
获取销售方纳税人识别号
上中下三行, 连续数字字母组合, 最长者胜出
'''
def get_seller_taxpayer_id(line_list):
    key = u'纳税人识别号'

    line0 = ''
    line = ''
    line1 = ''
    for i in range(len(line_list) - 1, -1, -1):
        if line_list[i].find(key) != -1:
            line1 = line_list[i + 1]
            line = line_list[i]
            if i >= 0:
                line0 = line_list[i - 1]
            break

    def get_tpid(line):
        tpid = ''
        for char in line:
            if (char >= u'\u0030' and char <= u'\u0039') \
                    or (char >= u'\u0041' and char <= u'\u0051') \
                    or (char >= u'\u0061' and char <= u'\u007a'):
                tpid += char
            else:
                if not tpid:
                    continue
                else:
                    break

        return tpid

    tpid0 = get_tpid(line0)
    tpid = get_tpid(line)
    tpid1 = get_tpid(line1)

    taxpayer_id = ''
    if len(tpid0) > len(tpid):
        if len(tpid0) > len(tpid1):
            taxpayer_id = tpid0
        else:
            taxpayer_id = tpid1
    else:
        if len(tpid) > len(tpid1):
            taxpayer_id = tpid
        else:
            taxpayer_id = tpid1

    return taxpayer_id

'''
获取普通发票的销售方纳税人识别号
'''
def get_seller_taxpayer_id_st(row_list):
    key = u'收款方识别号'

    row = ''
    for i in range(len(row_list) - 1, -1, -1):
        if row_list[i].find(key) != -1:
            row = row_list[i]
            break
    if not row:
        return ''

    ret = ''
    for char in row:
        if char.isdigit() or is_alpha(char):
            ret += char
        else:
            if ret:
                break

    return ret
