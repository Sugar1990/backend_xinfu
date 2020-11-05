# -*- coding: UTF-8 -*-
from flask import jsonify, request
import datetime
import json
from sqlalchemy import and_

from . import api_catalog as blue_print
from .get_leader_ids import get_leader_ids
from ..models import Catalog, Document, Customer, Permission, DocMarkComment
from .. import db
from .utils import success_res, fail_res
from ..conf import TAG_TABS
from .document import delete_doc_in_pg_es, modify_doc_es_doc_type, move_source_docs_to_target_catalog
import uuid


@blue_print.route('/insert_catalog', methods=['POST'])
def insert_catalog():
    try:
        name = request.json.get("name", "")
        customer_uuid = request.json.get("customer_uuid", "")
        catalog_pid = request.json.get("catalog_pid", "")

        catalog = Catalog.query.filter_by(name=name, create_by_uuid=customer_uuid, parent_uuid=catalog_pid).first()

        if catalog:
            res = fail_res(msg="目录已存在")
        else:
            sort = Catalog.query.filter_by(parent_uuid="").order_by(Catalog.sort.desc()).first()
            if sort:
                sort = sort + 1
            else:
                sort = 0
            catalog = Catalog(uuid=uuid.uuid1(), name=name, create_by_uuid=customer_uuid, parent_uuid=catalog_pid,
                              create_time=datetime.datetime.now(), sort=sort)
            db.session.add(catalog)
            db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg=str(e))

    return jsonify(res)


@blue_print.route('/del_catalog', methods=['POST'])
def del_catalog():
    try:
        catalog_uuid = request.json.get("catalog_uuid", "")
        customer_uuid = request.json.get("customer_uuid", "")

        flag, msg = judge_del_catalog_permission(customer_uuid, catalog_uuid)
        print(flag, msg)

        if flag:
            catalog_res = Catalog.query.filter_by(uuid=catalog_uuid).first()
            del_catalog_recursive(catalog_uuid)

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
def judge_del_catalog_permission(customer_uuid, catalog_uuid):
    try:
        catalog_res = Catalog.query.filter_by(uuid=catalog_uuid).first()
        customer = Customer.query.filter_by(uuid=customer_uuid).first()

        catalog = Catalog.query.filter_by(create_by_uuid=customer_uuid).all()
        document = Document.query.filter_by(catalog_uuid=catalog_uuid).all()

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
            if i.parent_uuid not in catalog_dictory.keys():
                catalog_dictory[i.parent_uuid] = [{i.uuid: i.name}]
            else:
                catalog_dictory[i.parent_uuid].append({i.uuid: i.name})

        # 递归检测下级目录有没有删除权限
        def get_subdir(uuid, data_dic):
            if not uuid:
                return ""
            if uuid not in data_dic:
                document = Document.query.filter_by(catalog_uuid=uuid).all()
                for i in document:
                    if i.get_power() > customer.get_power():
                        return 0
                return 1
            for dic in data_dic[id]:
                for key, value in dic.items():
                    document = Document.query.filter_by(catalog_uuid=key).all()
                    for i in document:
                        if i.get_power() > customer.get_power():
                            temp = get_subdir(False, data_dic)
                            return temp
                    temp = get_subdir(key, data_dic)
            return temp

        res = get_subdir(catalog_res.uuid, catalog_dictory)

        if res == 0:
            return False, "没有删除权限"

        # 递归检测下级目录有没有已标文档
        def get_descendants_docs(catalog_uuid):
            if not catalog_uuid:
                return False
            else:
                docs = Document.query.filter_by(catalog_uuid=catalog_uuid).all()
                for i in docs:
                    if i.status > 1:
                        return False

                catalog_children = Catalog.query.filter_by(parent_uuid=catalog_uuid).all()
                for catalog_child in catalog_children:
                    if not get_descendants_docs(catalog_child.uuid):
                        return False

                return True

        res = get_descendants_docs(catalog_res.uuid)
        if not res:
            return False, "目录下存在已标文档，不能删除"
        else:
            return True, ""
    except Exception as e:
        print(str(e))


# 彻底删除目录下子目录和所有文件
def del_catalog_recursive(catalog_uuid):
    try:
        docs = Document.query.filter_by(catalog_uuid=catalog_uuid).all()
        del_doc_ids = [i.uuid for i in docs]
        delete_doc_in_pg_es(del_doc_ids)

        catalog = Catalog.query.filter_by(uuid=catalog_uuid).first()
        db.session.delete(catalog)
        db.session.commit()

        catalog_children = Catalog.query.filter_by(parent_uuid=catalog_uuid).all()
        for catalog_child in catalog_children:
            del_catalog_recursive(catalog_child.uuid)
    except Exception as e:
        print(str(e))
        pass


@blue_print.route('/get_all', methods=['GET'])
def get_all():
    try:
        # catalog = Catalog.query.order_by(Catalog.sort.asc()).all()
        catalog = Catalog.query.all()

        catalog_dictory = {}
        # 构建目录字典
        for i in catalog:
            if i.parent_uuid not in catalog_dictory.keys():
                catalog_dictory[i.parent_uuid] = [{i.uuid: i.name}]
            else:
                catalog_dictory[i.parent_uuid].append({i.uuid: i.name})

        # 递归获取所有的目录
        def get_subdir(id, data_dic):
            if id not in data_dic:
                return []
            result = []
            for dic in data_dic[id]:
                sub_result = {}
                for key, value in dic.items():
                    sub_result = {'uuid': key, 'name': value, 'children': []}
                    temp = get_subdir(key, data_dic)
                    if temp:
                        sub_result['children'].extend(temp)
                result.append(sub_result)
            return result

        res = get_subdir(None, catalog_dictory)
    except Exception as e:
        print(str(e))
        res = []

    return jsonify(res)


@blue_print.route('/get_favorite_files', methods=['GET'])
def get_favorite_files():
    customer_uuid = request.args.get("customer_uuid", "")

    try:
        docs = Document.query.all()
        customer = Customer.query.filter_by(uuid=customer_uuid).first()

        if not customer:
            res = fail_res(msg="无效用户")
        else:
            if customer:
                leader_ids = get_leader_ids()
                res = {
                    "files": [{
                        "uuid": d.uuid,
                        "name": d.name,
                        "create_time": d.create_time,
                        "create_username": Customer.get_username_by_id(d.create_by_uuid),
                        "extension": d.category.replace('\n\"', ""),
                        'tag_flag': 1 if d.status == 1 else 0,
                        "status": d.get_status_name(),
                        "permission": 1 if Permission.judge_power(customer_uuid, d.uuid) else 0,
                        "leader_operate":  1 if DocMarkComment.query.filter(DocMarkComment.doc_uuid == d.uuid,
                                                    DocMarkComment.create_by_uuid.in_(leader_ids),
                                                    DocMarkComment.valid == 1).all() else 0

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
    catalog_uuid = request.args.get("catalog_uuid", "")
    customer_uuid = request.args.get("customer_uuid", "")

    try:
        docs = Document.query.filter_by(catalog_uuid=catalog_uuid).all()
        customer = Customer.query.filter_by(uuid=customer_uuid).first()
        catalogs = Catalog.query.filter_by(parent_uuid=catalog_uuid).all()

        if not customer:
            res = fail_res(msg="无效用户")
        else:
            if customer:
                doc_list = []
                leader_ids = get_leader_ids()
                if leader_ids:
                    for d in docs:
                        doc_json = {}
                        doc_json["id"] = d.uuid
                        doc_json["name"] = d.name
                        doc_json["create_time"] = d.create_time
                        doc_json["create_username"] = Customer.get_username_by_id(d.create_by_uuid)
                        doc_json["extension"] = d.category.replace('\n\"', "")
                        doc_json["tag_flag"] = 1 if d.status == 1 else 0
                        doc_json["status"] = d.get_status_name()
                        doc_json["permission"] = 1 if Permission.judge_power(customer_uuid, d.uuid) else 0
                        doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_uuid == d.uuid,
                                                                        DocMarkComment.create_by_uuid.in_(leader_ids),
                                                                        DocMarkComment.valid==1).all()
                        doc_json["leader_operate"] = 1 if doc_mark_comments else 0

                        doc_list.append(doc_json)

                    res = {
                        "files": doc_list,
                        "catalogs": [{
                            'id': i.uuid,
                            'name': i.name
                        } for i in catalogs]
                    }
                else:
                    res = {"files": [], "catalogs": []}
                # res = {
                #     "files": [{
                #         "id": d.id,
                #         "name": d.name,
                #         "create_time": d.create_time,
                #         "create_username": Customer.get_username_by_id(d.create_by),
                #         "extension": d.category.replace('\n\"', ""),
                #         'tag_flag': 1 if d.status == 1 else 0,
                #         "status": d.get_status_name(),
                #         "permission": 1 if Permission.judge_power(customer_id, d.id) else 0
                #     } for d in docs],
                #     # } for i in docs if i.get_power() <= customer.get_power()],
                #     "catalogs": [{
                #         'id': i.id,
                #         'name': i.name
                #     } for i in catalogs]
                # }
            else:
                res = {"files": [], "catalogs": []}
    except Exception as e:
        print(str(e))
        res = {"files": [], "catalogs": []}
    return jsonify(res)


@blue_print.route('/batch_del_catalog', methods=['POST'])
def batch_del_catalog():
    del_catalog_list = request.json.get('uuids', [])
    customer_uuid = request.json.get('customer_uuid', 0)

    try:
        msg = ""
        for catalog_uuid in del_catalog_list:

            flag, msg = judge_del_catalog_permission(customer_uuid, catalog_uuid)
            if not flag:
                msg = msg

            if flag:
                catalog_res = Catalog.query.filter_by(uuid=catalog_uuid).first()
                del_catalog_recursive(catalog_uuid)

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
        customer_uuid = request.json.get("customer_uuid", "")
        tabs = request.json.get("tabs", [])
        catalog = Catalog.query.filter_by(name=name, create_by_uuid=customer_uuid, parent_uuid=None, tagging_tabs=tabs).first()

        if catalog:
            res = fail_res(msg="相同根目录已存在")
        else:
            sort = Catalog.query.filter_by(parent_uuid="").order_by(Catalog.sort.desc()).first()
            if sort:
                sort = sort + 1
            else:
                sort = 0
            catalog = Catalog(uuid=uuid.uuid1(), name=name, create_by_uuid=customer_uuid, parent_uuid=None,
                              create_time=datetime.datetime.now(), tagging_tabs=tabs, sort=sort)
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
    catalog_uuid = request.json.get('catalog_uuid', "")
    parent_uuid = request.json.get('parent_uuid', "")
    name = request.json.get('name', '')
    tabs = request.json.get('tabs', [])
    try:
        catalog = Catalog.query.filter_by(uuid=catalog_uuid).first()
        if catalog:
            catalog_same = Catalog.query.filter(
                and_(Catalog.name == name, Catalog.parent_uuid == parent_uuid, Catalog.uuid != catalog_uuid)).first()
            if catalog_same:
                res = fail_res(msg="相同目录已存在")
            else:
                if name:
                    catalog.name = name
                if parent_uuid:
                    catalog.parent_uuid = parent_uuid
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
    catalog_uuid = request.json.get('catalog_uuid', "")
    parent_uuid = request.json.get('parent_uuid', "")

    try:
        if not parent_uuid:
            res = fail_res(msg="请移动到已知目录类型下")
        else:
            catalog = Catalog.query.filter_by(uuid=catalog_uuid).first()
            if catalog:
                catalog_same = Catalog.query.filter_by(name=catalog.name, parent_uuid=parent_uuid).first()
                if catalog_same:
                    move_catalog_same_recursive(catalog_uuid, catalog_same.uuid)
                else:
                    catalog.parent_uuid = parent_uuid
                    db.session.commit()
                    move_catalog_recursive(catalog.uuid)
                res = success_res()
            else:
                res = fail_res(msg="操作对象不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 移动目录-处理文件和子目录
def move_catalog_recursive(source_catalog_uuid):
    # 处理文件
    source_docs = Document.query.filter_by(catalog_uuid=source_catalog_uuid).all()
    doc_ids = [str(i.uuid) for i in source_docs]
    modify_doc_es_doc_type(doc_ids)

    # 处理目录
    source_catalog_children = Catalog.query.filter_by(parent_uuid=source_catalog_uuid).all()
    for source_catalog_child in source_catalog_children:
        move_catalog_recursive(source_catalog_child.uuid)


# 移动目录-处理重名目录下文件和子目录
def move_catalog_same_recursive(source_catalog_id, target_catalog_id):
    source_docs = Document.query.filter_by(catalog_uuid=source_catalog_id).all()
    # 移动文件到指定目录
    move_source_docs_to_target_catalog(source_docs, target_catalog_id)

    # 处理重名目录
    source_catalog_children = Catalog.query.filter_by(parent_uuid=source_catalog_id).all()
    target_catalog_children = Catalog.query.filter_by(parent_uuid=target_catalog_id).all()

    target_catalog_children_name_dict = {i.name: i for i in target_catalog_children}

    for source_catalog_child in source_catalog_children:
        if source_catalog_child.name in target_catalog_children_name_dict:
            target_catalog_child = target_catalog_children_name_dict[source_catalog_child.name]
            move_catalog_same_recursive(source_catalog_child.uuid, target_catalog_child.uuid)

    source_catalog = Catalog.query.filter_by(uuid=source_catalog_id).first()
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
        cataloges = Catalog.query.filter_by(parent_uuid=None).order_by(Catalog.sort.asc()).all()
        if not cataloges:
            res = []
        else:
            res = [{"catalog_id": catalog.uuid,
                    "name": catalog.name,
                    "parent_id": catalog.parent_uuid,
                    "create_by": catalog.create_by_uuid,
                    "create_time": catalog.create_time,
                    "tagging_tabs": catalog.tagging_tabs if catalog.tagging_tabs else []
                    } for catalog in cataloges]
    except Exception as e:
        print(str(e))
        res = []

    return jsonify(res)
