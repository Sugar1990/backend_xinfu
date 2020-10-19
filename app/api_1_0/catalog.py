# -*- coding: UTF-8 -*-
from flask import jsonify, request
import datetime
import json
from sqlalchemy import and_

from . import api_catalog as blue_print
from ..models import Catalog, Document, Customer, Permission
from .. import db
from .utils import success_res, fail_res
from ..conf import TAG_TABS
from .document import delete_doc_in_pg_es, modify_doc_es_doc_type


@blue_print.route('/insert_catalog', methods=['POST'])
def insert_catalog():
    try:
        name = request.json.get("name", "")
        customer_id = request.json.get("customer_id", 0)
        catalog_pid = request.json.get("catalog_pid", 0)

        catalog = Catalog.query.filter_by(name=name, create_by=customer_id, parent_id=catalog_pid).first()

        if catalog:
            res = fail_res(msg="目录已存在")
        else:
            catalog = Catalog(name=name, create_by=customer_id, parent_id=catalog_pid
                              , create_time=datetime.datetime.now())
            db.session.add(catalog)
            db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/del_catalog', methods=['POST'])
def del_catalog():
    try:
        catalog_id = request.json.get("catalog_id", 0)
        customer_id = request.json.get("customer_id", 0)

        flag, msg = judge_del_catalog_permission(customer_id, catalog_id)
        print(flag, msg)

        if flag:
            catalog_res = Catalog.query.filter_by(id=catalog_id).first()
            del_catalog_recursive(catalog_id)

            db.session.delete(catalog_res)
            db.session.commit()
            res = success_res()
        else:
            res = fail_res(msg=msg)
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# 判断用户是否有删除权限
def judge_del_catalog_permission(customer_id, catalog_id):
    try:
        catalog_res = Catalog.query.filter_by(id=catalog_id).first()
        customer = Customer.query.filter_by(id=customer_id).first()

        catalog = Catalog.query.filter_by(create_by=customer_id).all()
        document = Document.query.filter_by(catalog_id=catalog_id).all()

        if not customer:
            return False, "当前无效用户，没有删除权限"

        # 测试第一级目录下面有没有删除权限
        for i in document:
            if i.get_power() > customer.get_power():
                return False, "没有删除权限"
        if not catalog_res:
            return False, "没有该目录"

        catalog_dictory = {}
        # 构建目录字典
        for i in catalog:
            if i.parent_id not in catalog_dictory.keys():
                catalog_dictory[i.parent_id] = [{i.id: i.name}]
            else:
                catalog_dictory[i.parent_id].append({i.id: i.name})

        # 递归检测下级目录有没有删除权限
        def get_subdir(id, data_dic):
            if not id:
                return 0
            if id not in data_dic:
                document = Document.query.filter_by(catalog_id=id).all()
                for i in document:
                    if i.get_power() > customer.get_power():
                        return 0
                return 1
            for dic in data_dic[id]:
                for key, value in dic.items():
                    document = Document.query.filter_by(catalog_id=key).all()
                    for i in document:
                        if i.get_power() > customer.get_power():
                            temp = get_subdir(False, data_dic)
                            return temp
                    temp = get_subdir(key, data_dic)
            return temp

        res = get_subdir(catalog_res.id, catalog_dictory)

        if res == 0:
            return False, "没有删除权限"

        # 递归检测下级目录有没有已标文档
        def get_descendants_docs(catalog_id):
            if not catalog_id:
                return False
            else:
                docs = Document.query.filter_by(catalog_id=catalog_id).all()
                for i in docs:
                    if i.status > 1:
                        return False

                catalog_children = Catalog.query.filter_by(parent_id=catalog_id).all()
                for catalog_child in catalog_children:
                    if not get_descendants_docs(catalog_child.id):
                        return False

                return True

        res = get_descendants_docs(catalog_res.id)
        if not res:
            return False, "目录下存在已标文档，不能删除"
        else:
            return True, ""
    except Exception as e:
        print(str(e))


# 彻底删除目录下子目录和所有文件
def del_catalog_recursive(catalog_id):
    try:
        docs = Document.query.filter_by(catalog_id=catalog_id).all()
        del_doc_ids = [i.id for i in docs]
        delete_doc_in_pg_es(del_doc_ids)

        catalog = Catalog.query.filter_by(id=catalog_id).first()
        db.session.delete(catalog)
        db.session.commit()

        catalog_children = Catalog.query.filter_by(parent_id=catalog_id).all()
        for catalog_child in catalog_children:
            del_catalog_recursive(catalog_child.id)
    except Exception as e:
        print(str(e))
        pass


@blue_print.route('/get_all', methods=['GET'])
def get_all():
    try:
        catalog = Catalog.query.order_by(Catalog.id.asc()).all()

        catalog_dictory = {}
        # 构建目录字典
        for i in catalog:
            if i.parent_id not in catalog_dictory.keys():
                catalog_dictory[i.parent_id] = [{i.id: i.name}]
            else:
                catalog_dictory[i.parent_id].append({i.id: i.name})

        # 递归获取所有的目录
        def get_subdir(id, data_dic):
            if id not in data_dic:
                return []
            result = []
            for dic in data_dic[id]:
                sub_result = {}
                for key, value in dic.items():
                    sub_result = {'id': key, 'name': value, 'children': []}
                    temp = get_subdir(key, data_dic)
                    if temp:
                        sub_result['children'].extend(temp)
                result.append(sub_result)
            return result

        res = get_subdir(0, catalog_dictory)
    except Exception as e:
        print(str(e))
        res = []

    return jsonify(res)


@blue_print.route('/get_favorite_files', methods=['GET'])
def get_favorite_files():
    customer_id = request.args.get("customer_id", 0, type=int)

    try:
        docs = Document.query.all()
        customer = Customer.query.filter_by(id=customer_id).first()

        if not customer:
            res = fail_res(msg="无效用户")
        else:
            if customer:
                res = {
                    "files": [{
                        "id": d.id,
                        "name": d.name,
                        "create_time": d.create_time,
                        "create_username": Customer.get_username_by_id(d.create_by),
                        "extension": d.category.replace('\n\"', ""),
                        'tag_flag': 1 if d.status == 1 else 0,
                        "status": d.get_status_name(),
                        "permission": 1 if Permission.judge_power(customer_id, d.id) else 0
                    } for d in docs if d.is_favorite == 1],
                    # } for i in docs if i.get_power() <= customer.get_power()],
                    "catalogs": []
                }
            else:
                res = {"files": [], "catalogs": []}
    except Exception as e:
        print(str(e))
        res = {"files": [], "catalogs": []}
    return jsonify(res)


@blue_print.route('/get_catalog_files', methods=['GET'])
def get_catalog_files():
    catalog_id = request.args.get("catalog_id", 0, type=int)
    customer_id = request.args.get("customer_id", 0, type=int)

    try:
        docs = Document.query.filter_by(catalog_id=catalog_id).all()
        customer = Customer.query.filter_by(id=customer_id).first()
        catalogs = Catalog.query.filter_by(parent_id=catalog_id).all()

        if not customer:
            res = fail_res(msg="无效用户")
        else:
            if customer:
                res = {
                    "files": [{
                        "id": d.id,
                        "name": d.name,
                        "create_time": d.create_time,
                        "create_username": Customer.get_username_by_id(d.create_by),
                        "extension": d.category.replace('\n\"', ""),
                        'tag_flag': 1 if d.status == 1 else 0,
                        "status": d.get_status_name(),
                        "permission": 1 if Permission.judge_power(customer_id, d.id) else 0
                    } for d in docs],
                    # } for i in docs if i.get_power() <= customer.get_power()],
                    "catalogs": [{
                        'id': i.id,
                        'name': i.name
                    } for i in catalogs]
                }
            else:
                res = {"files": [], "catalogs": []}
    except Exception as e:
        print(str(e))
        res = {"files": [], "catalogs": []}
    return jsonify(res)


@blue_print.route('/batch_del_catalog', methods=['POST'])
def batch_del_catalog():
    del_catalog_list = request.json.get('ids', [])
    customer_id = request.json.get('customer_id', 0)

    try:
        msg = ""
        for catalog_id in del_catalog_list:

            flag, msg = judge_del_catalog_permission(customer_id, catalog_id)
            if not flag:
                msg = msg

            if flag:
                catalog_res = Catalog.query.filter_by(id=catalog_id).first()
                del_catalog_recursive(catalog_id)

                db.session.delete(catalog_res)
                db.session.commit()

        res = success_res(msg=msg)
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/insert_1stfloor_catalog', methods=['POST'])
def insert_1stfloor_catalog():
    try:
        name = request.json.get("name", "")
        customer_id = request.json.get("customer_id", 0)
        tabs = request.json.get("tabs", [])
        catalog = Catalog.query.filter_by(name=name, create_by=customer_id, parent_id=0, tagging_tabs=tabs).first()

        if catalog:
            res = fail_res(msg="相同根目录已存在")
        else:
            catalog = Catalog(name=name, create_by=customer_id, parent_id=0
                              , create_time=datetime.datetime.now(), tagging_tabs=tabs)
            db.session.add(catalog)
            db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="创建根目录失败")

    return jsonify(res)


@blue_print.route('/modify_catalog', methods=['PUT'])
def modify_catalog():
    catalog_id = request.json.get('catalog_id', 0)
    parent_id = request.json.get('parent_id', 0)
    name = request.json.get('name', '')
    tabs = request.json.get('tabs', [])
    try:
        catalog = Catalog.query.filter_by(id=catalog_id).first()
        if catalog:
            catalog_same = Catalog.query.filter(
                and_(Catalog.name == name, Catalog.parent_id == parent_id, Catalog.id != catalog_id)).first()
            if catalog_same:
                res = fail_res(msg="相同目录已存在")
            else:
                if name:
                    catalog.name = name
                if parent_id:
                    catalog.parent_id = parent_id
                if tabs:
                    catalog.tagging_tabs = tabs
                db.session.commit()
                res = success_res()
        else:
            res = fail_res(msg="操作对象不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/move_catalog', methods=['PUT'])
def move_catalog():
    catalog_id = request.json.get('catalog_id', 0)
    parent_id = request.json.get('parent_id', 0)

    try:
        if not parent_id:
            res = fail_res(msg="请移动到已知目录类型下")
        else:
            catalog = Catalog.query.filter_by(id=catalog_id).first()
            if catalog:
                catalog_same = Catalog.query.filter_by(name=catalog.name, parent_id=parent_id).first()
                if catalog_same:
                    move_catalog_same_recursive(catalog_id, catalog_same.id)
                else:
                    catalog.parent_id = parent_id
                    db.session.commit()
                    move_catalog_recursive(catalog.id)
                res = success_res()
            else:
                res = fail_res(msg="操作对象不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 移动目录-处理文件和子目录
def move_catalog_recursive(source_catalog_id):
    # 处理文件
    source_docs = Document.query.filter_by(catalog_id=source_catalog_id).all()
    doc_ids = [i.id for i in source_docs]
    modify_doc_es_doc_type(doc_ids)

    # 处理目录
    source_catalog_children = Catalog.query.filter_by(parent_id=source_catalog_id).all()
    for source_catalog_child in source_catalog_children:
        move_catalog_recursive(source_catalog_child.id)


# 移动目录-处理重名目录下文件和子目录
def move_catalog_same_recursive(source_catalog_id, target_catalog_id):
    source_docs = Document.query.filter_by(catalog_id=source_catalog_id).all()
    target_docs = Document.query.filter_by(catalog_id=target_catalog_id).all()

    # 处理重名文件
    del_doc_id = []
    save_target_docs_dict = {i.md5: i for i in target_docs if i.md5 and i.id}
    for source_doc_item in source_docs:
        if source_doc_item.md5 in save_target_docs_dict:
            target_doc_item = save_target_docs_dict[source_doc_item.md5]
            if target_doc_item.status < 2 and source_doc_item.status > 1:
                # 目标文件未标注，移动文件已标注，删除目标文件
                del_doc_id.append(target_doc_item.id)
                source_doc_item.catalog_id = target_catalog_id
                modify_doc_es_doc_type([source_doc_item.id])
                db.session.commit()
            else:
                # 目标文件已标注，删除移动文件
                del_doc_id.append(source_doc_item.id)
        else:
            source_doc_item.catalog_id = target_catalog_id
            modify_doc_es_doc_type([source_doc_item.id])
            db.session.commit()
    delete_doc_in_pg_es(del_doc_id)

    # 处理重名目录
    source_catalog_children = Catalog.query.filter_by(parent_id=source_catalog_id).all()
    target_catalog_children = Catalog.query.filter_by(parent_id=target_catalog_id).all()

    target_catalog_children_name_dict = {i.name: i for i in target_catalog_children}

    for source_catalog_child in source_catalog_children:
        if source_catalog_child.name in target_catalog_children_name_dict:
            target_catalog_child = target_catalog_children_name_dict[source_catalog_child.name]
            move_catalog_same_recursive(source_catalog_child.id, target_catalog_child.id)

    source_catalog = Catalog.query.filter_by(id=source_catalog_id).first()
    db.session.delete(source_catalog)
    db.session.commit()


@blue_print.route('/get_tagging_tabs', methods=['GET'])
def get_tagging_tabs():
    try:
        res = json.loads(TAG_TABS)
    except Exception as e:
        print(str(e))
        res = {}

    return jsonify(res)


@blue_print.route('/get_1stfloor_catalog', methods=['GET'])
def get_1stfloor_catalog():
    try:
        cataloges = Catalog.query.filter_by(parent_id=0).order_by(Catalog.id.asc()).all()
        if not cataloges:
            res = []
        else:
            res = [{"catalog_id": catalog.id,
                    "name": catalog.name,
                    "parent_id": catalog.parent_id,
                    "create_by": catalog.create_by,
                    "create_time": catalog.create_time,
                    "tagging_tabs": catalog.tagging_tabs if catalog.tagging_tabs else []
                    } for catalog in cataloges]
    except Exception as e:
        print(str(e))
        res = []

    return jsonify(res)
