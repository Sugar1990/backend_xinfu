# -*- coding: UTF-8 -*-
import datetime
import hashlib

from flask import jsonify, request
from sqlalchemy import not_, and_

from . import api_customer as blue_print
from .utils import success_res, fail_res
from .. import db
from ..conf import ADMIN_ROLE_POWER, ASSIS_ROLE_POWER, ADMIN_NAME, ASSIS_NAME, ADMIN_ROLE_NAME, ASSIS_ROLE_NAME,MIN_PRICISE_OF_PERMSSION
from ..models import Customer, Permission
import uuid


# 修改时，如果找不到是报错
@blue_print.route('/login', methods=['POST'])
def login():
    input_name = request.json.get('username', '')
    input_pwd = request.json.get('pwd', '')
    try:
        if not input_name or not input_pwd:
            res = fail_res(msg="用户或密码不得为空")
        else:
            customer = Customer.query.filter_by(username=input_name, valid=1).first()
            if customer:
                if input_pwd == customer.pwd:
                    md5_hash = hashlib.md5(
                        "{}{}{}".format(customer.uuid, datetime.datetime.now().timestamp(), customer.username).encode(
                            encoding="utf-8"))
                    token = md5_hash.hexdigest()
                    print(token)
                    customer.token = token
                    db.session.commit()
                    res = success_res(data={"token": token})
                else:
                    res = fail_res(msg="密码不正确")
            else:
                res = fail_res(msg="用户不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg='登录失败')
    return jsonify(res)


@blue_print.route('/verify_token', methods=['POST'])
def verify_token():
    token = request.json.get('token', '')
    try:
        if not token:
            res = fail_res(msg="无效空token")
        else:
            customer = Customer.query.filter_by(token=token, valid=1).first()
            if customer:
                role = 3
                if customer.get_power() == ADMIN_ROLE_POWER:
                    role = 1
                elif customer.get_power() == ASSIS_ROLE_POWER:
                    role = 2
                res = success_res(data={"uuid": customer.uuid, "uname": customer.username, "role": role,
                                        "power_score": customer.power_score})
            else:
                res = fail_res(msg="验证失败")
    except Exception as e:
        print(str(e))
        res = fail_res(msg='验证异常')
    return jsonify(res)


# 修改时，如果找不到是报错
@blue_print.route('/logout', methods=['POST'])
def logout():
    token = request.json.get('token', '')
    try:
        if not token:
            res = fail_res(msg="无效空token")
        else:
            customer = Customer.query.filter_by(token=token, valid=1).first()
            if customer:
                customer.token = ""
                db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg='退出异常')
    return jsonify(res)


@blue_print.route('/insert_customer', methods=['POST'])
def insert_customer():
    username = request.json.get('customer_username', '')
    pwd = request.json.get('customer_pwd', '')
    permission_id = request.json.get('customer_permission_id', 0)
    try:
        customer = db.session.query(Customer).filter(and_(Customer.username == username, Customer.valid == 1)).first()
        if customer:
            res = fail_res(msg="用户已存在")
        else:
            customer_name = Customer(username=username, pwd=pwd, permission_id=permission_id, valid=1, uuid=uuid.uuid1())
            db.session.add(customer_name)
            db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="插入失败")

    return jsonify(res)


@blue_print.route('/update_customer', methods=['PUT'])
def update_customer():
    uuid = request.json.get('customer_uuid', '')
    username = request.json.get('customer_username', '')
    pwd = request.json.get('customer_pwd', '')
    permission_id = request.json.get('customer_permission_uuid', 0)
    try:
        customer = db.session.query(Customer).filter(and_(Customer.uuid == uuid, Customer.valid == 1)).first()
        if customer:
            customer1 = db.session.query(Customer).filter(and_(Customer.username == username, Customer.pwd == pwd,
                                                               Customer.permission_id == permission_id,
                                                               Customer.valid == 1)).first()
            if customer1:
                res = fail_res(msg="相同用户已存在")
            else:
                if username:
                    customer.username = username
                if pwd:
                    customer.pwd = pwd
                if permission_id:
                    customer.permission_id = permission_id
                    if customer.power_score < Permission.get_power(permission_id):
                        customer.power_score = Permission.get_power(permission_id)
                    elif customer.power_score > Permission.get_power(permission_id):
                        customer.power_score = Permission.get_power(permission_id) - MIN_PRICISE_OF_PERMSSION
                db.session.commit()
                res = success_res()
        else:
            res = fail_res(msg="用户不存在")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/del_customer', methods=['POST'])
def del_customer():
    customer_uuid = request.json.get("customer_uuid", '')

    try:
        customer = db.session.query(Customer).filter(and_(Customer.uuid == customer_uuid, Customer.valid == 1)).first()
        customer.valid = 0
        res = success_res(msg="删除成功")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败")

    return jsonify(res)


@blue_print.route('/query_by_id', methods=['GET'])
def query_by_uuid():
    uuid = request.args.get('customer_uuid', '')
    try:
        customer = Customer.query.filter_by(uuid=uuid, valid=1).first()
        res = {
            "uuid": customer.uuid,
            "username": customer.username,
            "permission_id": customer.permission_id,
            "power_score": customer.power_score
            # "permission_power": Permission.get_power(customer.permission_id),
        }
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = {"uuid": '-1',
               "username": ""}
    return jsonify(res)


@blue_print.route('/query_all', methods=['GET'])
def query_all():
    try:
        permission_ids = Permission.query.with_entities(Permission.id).filter(not_(Permission.name.in_([ADMIN_ROLE_NAME, ASSIS_ROLE_NAME])),
                                             Permission.valid == 1).all()
        permission_ids = [i[0] for i in permission_ids]
        customer = Customer.query.filter(Customer.valid==1, Customer.permission_id.in_(permission_ids)).all()
        res = []
        for i in customer:
            if i.valid:
                res.append({"uuid": i.uuid, "username": i.username, "permission_id": i.permission_id, "power_score": i.power_score})
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = []
    return jsonify(res)


@blue_print.route('/query_customer_paginate', methods=['GET'])
def query_customer_paginate():
    try:
        current_page = request.args.get('cur_page', 1, type=int)
        page_size = request.args.get('page_size', 15, type=int)
        search = request.args.get("search", "")

        cons = [
            Customer.username.like('%' + search + '%'), Customer.valid == 1,
            not_(Customer.username.in_([ADMIN_NAME, ASSIS_NAME]))
        ]
        permission_ids = Permission.query.with_entities(Permission.id).filter(
            not_(Permission.name.in_([ADMIN_ROLE_NAME, ASSIS_ROLE_NAME])),
            Permission.valid == 1).all()
        permission_ids = [i[0] for i in permission_ids]

        pagination = Customer.query.filter(*cons, Customer.permission_id.in_(permission_ids)).paginate(current_page, page_size, False)
        data = []
        for item in pagination.items:
            data.append({
                "uuid": item.uuid,
                "name": item.username,
                "permission_id": item.permission_id,
                "power_score": item.power_score
            })
        data = {
            "totalCount": pagination.total,
            "totalPage": pagination.pages,
            "data": data,
            "currentPage": pagination.page
        }

    except Exception as e:
        print(str(e))
        data = {
            "totalCount": 0,
            "totalPage": 0,
            "data": [],
            "currentPage": 0
        }
    return jsonify(data)


@blue_print.route('/batch_del_customer', methods=['POST'])
def batch_del_customer():
    del_customer_list = request.json.get('uuids', [])

    try:
        for customer_uuid in del_customer_list:
            customer = db.session.query(Customer).filter(and_(Customer.uuid == customer_uuid, Customer.valid == 1)).first()
            if customer:
                customer.valid = 0
        res = success_res(msg="批量删除成功")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="批量删除失败")

    return jsonify(res)


@blue_print.route('/get_custom_info', methods=['POST'])
def query_by_uuids():
    uuid_list = request.json.get('uuids', [])
    try:
        data = []
        for uuid in uuid_list:
            customer = Customer.query.filter_by(uuid=uuid, valid=1).first()
            res = {
                "uuid": customer.uuid,
                "username": customer.username,
                "permission_id": customer.permission_id,
                "permission_power": Permission.get_power(customer.permission_id)
            }
            data.append(res)
    except:
        db.session.rollback()
        result = {"data": [],
                  "code": 0,
                  "msg": ""}
        return jsonify(result)
    result = {"data": data,
              "code": 0,
              "msg": ""}
    return jsonify(result)

@blue_print.route('/get_eidt_permission', methods=['POST'])
def query_by_uuid_doc_uuid():
    try:
        uuid = request.json.get('uuid', '')
        doc_uuid = request.json.get('doc_uuid', '')

        customer_uuid = Customer.query.filter_by(uuid=uuid, valid=1).first()
        customer_doc_uuid = Customer.query.filter_by(uuid=doc_uuid, valid=1).first()
        if Permission.get_power(customer_uuid.permission_id) - Permission.get_power(customer_doc_uuid .permission_id) >= 0:
            result = {"data": 1,
                      "code": 1,
                      "msg": ""}
        else:
            result = {"data": 0,
                      "code": 1,
                      "msg": ""}
    except:
        db.session.rollback()
        result = {"data": [],
                  "code": 0,
                  "msg": "N"}
        return jsonify(result)
    return jsonify(result)

@blue_print.route('/update_power_score', methods=['PUT'])
def update_power_score():
    uuid = request.json.get('customer_uuid', '')
    try:
        customer = db.session.query(Customer).filter(and_(Customer.uuid == uuid, Customer.valid == 1)).first()
        if customer:
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            cursor.callproc('get_customer_power',[uuid])
            customer.power_score = cursor.fetchall()[0][0]
            db.session.commit()
            res = success_res()
        else:
            res = fail_res(msg="用户不存在")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)

@blue_print.route('/update_all_power_score', methods=['PUT'])
def update_all_power_score():
    customer_uuids = Customer.query.with_entities(Customer.uuid).filter_by(valid=1).all()
    try:
        for uuid in customer_uuids:
            uuid = uuid[0]
            customer = db.session.query(Customer).filter(and_(Customer.uuid == str(uuid), Customer.valid == 1)).first()
            if customer:
                connection = db.engine.raw_connection()
                cursor = connection.cursor()
                cursor.callproc('get_customer_power',[str(uuid)])
                customer.power_score = cursor.fetchall()[0][0]
            else:
                pass
        db.session.commit()
        res = success_res()

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)
