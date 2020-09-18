# -*- coding: UTF-8 -*-
from flask import jsonify, request
from sqlalchemy import not_, and_, or_
from . import api_customer as blue_print
from ..models import Customer
from .. import db
from .utils import success_res, fail_res
from ..conf import ADMIN_ROLE_POWER, ASSIS_ROLE_POWER, ADMIN_NAME, ASSIS_NAME


# 修改时，如果找不到是报错
@blue_print.route('/login', methods=['POST'])
def login():
    input_name = request.json.get('username', '')
    input_pwd = request.json.get('pwd', '')
    try:
        if not input_name or not input_pwd:
            res = fail_res(msg="用户或密码设置为空")
        else:
            customer = db.session.query(Customer).filter(
                and_(Customer.username == input_name, Customer.valid == 1)).first()
            if customer:
                if input_pwd == customer.pwd:
                    role = 3
                    if customer.get_power() == ADMIN_ROLE_POWER:
                        role = 1
                    elif customer.get_power() == ASSIS_ROLE_POWER:
                        role = 2
                    res = success_res(data={"uid": customer.id, "role": role})
                else:
                    res = fail_res(msg="密码不正确")
            else:
                res = fail_res(msg="用户不存在")
    except:
        res = fail_res(msg='登录失败')
    return jsonify(res)


# 修改时，如果找不到是报错
@blue_print.route('/logout', methods=['POST'])
def logout():
    uid = request.json.get('uid', '')
    try:
        if not uid:
            customer = db.session.query(Customer).filter(
                and_(Customer.username == input_name, Customer.valid == 1)).first()
            if customer:
                if input_pwd == customer.pwd:
                    role = 3
                    if customer.get_power() == ADMIN_ROLE_POWER:
                        role = 1
                    elif customer.get_power() == ASSIS_ROLE_POWER:
                        role = 2
                    res = success_res(data={"uid": customer.id, "role": role})
                else:
                    res = fail_res(msg="密码不正确")
            else:
                res = fail_res(msg="用户不存在")
    except:
        res = fail_res(msg='登录失败')
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
            customer_name = Customer(username=username, pwd=pwd, permission_id=permission_id, valid=1)
            db.session.add(customer_name)
            db.session.commit()
            res = success_res()
    except:
        db.session.rollback()
        res = fail_res(msg="插入失败")

    return jsonify(res)


@blue_print.route('/update_customer', methods=['PUT'])
def update_customer():
    uid = request.json.get('customer_id', 0)
    username = request.json.get('customer_username', '')
    pwd = request.json.get('customer_pwd', '')
    permission_id = request.json.get('customer_permission_id', 0)
    try:
        customer = db.session.query(Customer).filter(and_(Customer.id == uid, Customer.valid == 1)).first()
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
                db.session.commit()
                res = success_res()
        else:
            res = fail_res(msg="用户不存在")

    except:
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/del_customer', methods=['POST'])
def del_customer():
    customer_id = request.json.get("customer_id", 0)

    try:
        customer = db.session.query(Customer).filter(and_(Customer.id == customer_id, Customer.valid == 1)).first()
        customer.valid = 0
        res = success_res(msg="删除成功")
    except:
        db.session.rollback()
        res = fail_res(msg="删除失败")

    return jsonify(res)


@blue_print.route('/query_by_id', methods=['GET'])
def query_by_id():
    uid = request.args.get('customer_id', 0, type=int)
    try:
        customer = Customer.query.filter_by(id=uid, valid=1).first()
        res = {
            "id": customer.id,
            "username": customer.username,
            "permission_id": customer.permission_id
        }
    except:
        db.session.rollback()
        res = {"id": -1,
               "username": ""}
    return jsonify(res)


@blue_print.route('/query_all', methods=['GET'])
def query_all():
    try:
        customer = Customer.query.filter_by(valid=1).all()
        res = []
        for i in customer:
            if i.valid:
                res.append({"id": i.id, "username": i.username, "permission_id": i.permission_id})
    except:
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
        pagination = Customer.query.filter(*cons).order_by(
            Customer.id.desc()).paginate(current_page, page_size, False)
        data = []
        for item in pagination.items:
            data.append({
                "id": item.id,
                "name": item.username,
                "permission_id": item.permission_id
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
    del_customer_list = request.json.get('ids', [])

    try:
        for customer_id in del_customer_list:
            customer = db.session.query(Customer).filter(and_(Customer.id == customer_id, Customer.valid == 1)).first()
            if customer:
                customer.valid = 0
        res = success_res(msg="批量删除成功")
    except:
        db.session.rollback()
        res = fail_res(msg="批量删除失败")

    return jsonify(res)
