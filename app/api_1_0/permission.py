from flask import jsonify, request
from sqlalchemy import not_, and_, or_

from . import api_permission as blue_print
from ..models import Permission, Customer
from .. import db
from .utils import success_res, fail_res
from ..conf import ADMIN_ROLE_NAME, ASSIS_ROLE_NAME


# insert
@blue_print.route('/insert_permission', methods=['POST'])
def insert_permission():
    permission_name = request.json.get('permission_name', '')
    permission_power = request.json.get('permission_power', 0)
    try:
        permission = Permission.query.filter_by(name=permission_name, valid=1).first()
        if permission:
            res = fail_res(msg="权限已存在")
        else:
            permission_insert = Permission(name=permission_name, power=permission_power, valid=1)
            db.session.add(permission_insert)
            db.session.commit()
            res = success_res()

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# delete_by_id
@blue_print.route('/del_permission', methods=['POST'])
def del_permission():
    permission_id = request.json.get("permission_id", 0)

    try:
        permission = db.session.query(Permission).filter(not_(Permission.name.in_([ADMIN_ROLE_NAME, ASSIS_ROLE_NAME])),
                                                         Permission.id == permission_id, Permission.valid == 1).first()
        if permission:
            customers = Customer.query.filter_by(permission_id=permission_id, valid=1).all()
            if customers:
                res = fail_res(msg="该权限下存在用户，不能删除")
            else:
                permission.valid = 0
                res = success_res()
        else:
            res = fail_res(msg="权限不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# 批量删除
@blue_print.route('/batch_del_permission', methods=['POST'])
def batch_del_permission():
    ids = request.json.get('ids', [])
    res_flag = True
    try:
        permissions = db.session.query(Permission).filter(not_(Permission.name.in_([ADMIN_ROLE_NAME, ASSIS_ROLE_NAME])),
                                                         and_(Permission.id.in_(ids), Permission.valid == 1)).all()
        if permissions:
            for permission_item in permissions:
                customers = Customer.query.filter_by(permission_id=permission_item.id, valid=1).all()
                if not customers:
                    permission_item.valid = 0
                    flag = True
                    res_flag = res_flag & flag
                else:
                    flag = False
                    res_flag = res_flag & flag
            if res_flag:
                res = success_res()
            else:
                res = fail_res(msg="权限下存在用户，部分数据无法删除")
        else:
            res = fail_res(msg="权限不存在")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# update
@blue_print.route('/update_permission', methods=['PUT'])
def update_permission():
    try:
        id = request.json.get('permission_id', 0)
        name = request.json.get('permission_name', '')
        power = request.json.get('permission_power', '')
        if name in [ADMIN_ROLE_NAME, ASSIS_ROLE_NAME]:
            res = fail_res(msg="无权限更新")
        else:
            permission = Permission.query.filter_by(name=name, power=power, valid=1).first()
            if permission:
                res = fail_res(msg="相同权限用户已存在")
            else:
                permission = Permission.query.filter(not_(Permission.name.in_([ADMIN_ROLE_NAME, ASSIS_ROLE_NAME])),
                                                     Permission.id == id, Permission.valid == 1).first()
                if permission:
                    if name:
                        permission.name = name
                    if power:
                        permission.power = power
                    db.session.commit()
                    res = success_res()
                else:
                    res = fail_res(msg="权限不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 查询单条数据
@blue_print.route('/query_by_id', methods=['GET'])
def query_by_id():
    uid = request.args.get('permission_id', 0, type=int)
    try:
        permission = Permission.query.filter(not_(Permission.name.in_([ADMIN_ROLE_NAME, ASSIS_ROLE_NAME])),
                                             Permission.id == uid, Permission.valid == 1).first()
        if permission:
            res = {
                "id": permission.id,
                "name": permission.name,
                "power": permission.power
            }
        else:
            res = fail_res(msg="权限不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = []
    return jsonify(res)


# 查全集
@blue_print.route('/query_all', methods=['GET'])
def query_all():
    try:
        permission = Permission.query.filter(not_(Permission.name.in_([ADMIN_ROLE_NAME, ASSIS_ROLE_NAME])),
                                             Permission.valid == 1).all()
        res = [{"id": i.id, "name": i.name, "power": i.power} for i in permission]
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = []
    return jsonify(res)


# 分页查询
@blue_print.route('/query_permission_paginate', methods=['GET'])
def query_permission_paginate():
    current_page = request.args.get('cur_page', 0, type=int)
    page_size = request.args.get('page_size', 0, type=int)
    search = request.args.get("search", "")
    cons = [
        Permission.name.like('%' + search + '%'),
        not_(Permission.name.in_([ADMIN_ROLE_NAME, ASSIS_ROLE_NAME])),
        Permission.valid == 1
    ]
    try:
        pagination = Permission.query.filter(*cons).order_by(
            Permission.id.desc()).paginate(current_page, page_size, False)

        data = []
        for item in pagination.items:
            data.append({
                "id": item.id,
                "name": item.name,
                "power": item.power
            })
        res = {
            "total_count": pagination.total,
            "page_count": pagination.pages,
            "data": data,
            "cur_page": pagination.page
        }

    except Exception as e:
        print(str(e))
        res = {
            "total_count": 0,
            "page_count": 0,
            "data": [],
            "cur_page": 0
        }
    return jsonify(res)
