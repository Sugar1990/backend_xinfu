# -*- coding:utf-8 -*-
# @Author :MaYuhui
# work_location: Bei Jing
# @File : document_records.py 
# @Time : 2020/9/5 9:25

import datetime

from flask import jsonify, request
from . import api_document_records as blue_print
from ..models import DocumentRecords, Document, Customer
from .. import db
from .utils import success_res, fail_res


@blue_print.route('/insert_records', methods=['POST'])
def insert_records():
    try:
        doc_id = request.json.get('doc_id', 0)
        customer_id = request.json.get('customer_id', 0)
        operate_type = request.json.get('operate_type', 0)
        document = Document.query.filter_by(id=doc_id).first()
        customer = Customer.query.filter_by(id=customer_id).first()
        if not document:
            res = fail_res(msg="文档id不存在!")
        elif not customer:
            res = fail_res(msg="用户id不存在!")
        else:
            documentRecords = DocumentRecords(doc_id=doc_id,
                                              create_by=customer_id,
                                              create_time=datetime.datetime.now(),
                                              operate_type=operate_type)
            db.session.add(documentRecords)
            db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/get_doc_records', methods=['GET'])
def get_doc_records():
    try:
        doc_id = request.args.get('doc_id', 0)
        doc_records = DocumentRecords.query.filter(DocumentRecords.doc_id == doc_id).order_by(
            DocumentRecords.create_time.desc())
        res = []
        if doc_records:
            for doc_record in doc_records:
                customer = Customer.query.filter_by(id=doc_record.create_by).first()
                if customer:
                    res.append({
                        # 对应models.py中的字段
                        "username": customer.username,
                        "create_time": doc_record.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "operate": "标注" if doc_record.operate_type == 2 else "浏览" if doc_record.operate_type == 1 else ""
                    })
        else:
            res = []
    except Exception:
        res = []

    return jsonify(res)
