# -*- coding: UTF-8 -*-
from flask import jsonify, request
import datetime
from . import api_catalog as blue_print
from ..models import Catalog, Document, Customer
from .. import db
from .utils import success_res, fail_res


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

        catalog_res = Catalog.query.filter_by(id=catalog_id).first()
        customer = Customer.query.filter_by(id=customer_id).first()

        catalog = Catalog.query.filter_by(create_by=customer_id).all()
        document = Document.query.filter_by(catalog_id=catalog_id).all()

        if not customer:
            res = fail_res(msg="当前无效用户，没有删除权限")
            return res

        # 测试第一级目录下面有没有删除权限
        for i in document:
            if i.get_power() > customer.get_power():
                res = fail_res(msg="没有删除权限")
                return res
        if not catalog_res:
            res = fail_res(msg="没有该目录")
            return res

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
            res = fail_res(msg="没有删除权限")
            return res
        db.session.delete(catalog_res)
        db.session.commit()
        res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/get_all', methods=['GET'])
def get_all():
    try:
        # customer_id = request.args.get("customer_id", 0, type=int)

        catalog = Catalog.query.all()

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
    except:
        res = []

    return jsonify(res)


@blue_print.route('/get_catalog_files', methods=['GET'])
def get_catalog_files():
    catalog_id = request.args.get("catalog_id", 0, type=int)
    customer_id = request.args.get("customer_id", 0, type=int)

    try:
        docs = Document.query.filter_by(catalog_id=catalog_id).all()
        customer = Customer.query.filter_by(id=customer_id).first()
        catalogs = Catalog.query.filter_by(parent_id=catalog_id).all()

        doc_status = lambda x: "上传处理中" if x == 0 else "未标注" if x == 1 else "已标注" if x == 2 else ""
        if customer:
            res = {
                "files": [{
                    "id": i.id,
                    "name": i.name,
                    "createtime": i.create_time,
                    "create_username": Customer.get_username_by_id(i.create_by),
                    "extension": i.category.replace('\n\"', ""),
                    "status": doc_status(i.status)
                } for i in docs if i.get_power() <= customer.get_power()],
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

    try:
        for catalog_id in del_catalog_list:
            catalog = Catalog.query.filter_by(id=catalog_id).first()
            if catalog:
                db.session.delete(catalog)
                db.session.commit()
        res = success_res()
    except:
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
            if not catalog.tagging_tabs:  # 不是根目录   ??修改的必须是根目录吗
                res = fail_res(msg="非文档类型目录")
            else:
                catalog1 = Catalog.query.filter_by(name=name, parent_id=parent_id, tagging_tabs=tabs).first()
                if catalog1:
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
    except:
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/get_tagging_tabs', methods=['GET'])
def get_tagging_tabs():
    try:
        cataloges = Catalog.query.all()
        if not cataloges:
            res = []
        else:
            res = []
            for catalog in cataloges:
                if catalog.tagging_tabs:
                    res.append(catalog.tagging_tabs)
    except Exception:
        res = []

    return jsonify(res)


@blue_print.route('/get_1stfloor_catalog', methods=['GET'])
def get_1stfloor_catalog():
    try:
        cataloges = Catalog.query.all()
        if not cataloges:
            res = []
        else:
            res = []
            for catalog in cataloges:
                if catalog.tagging_tabs:
                    res.append(
                        {
                            "catalog_id": catalog.id,
                            "name": catalog.name,
                            "parent_id": catalog.parent_id,
                            "create_by": catalog.create_by,
                            "create_time": catalog.create_time,
                            "tagging_tabs": catalog.tagging_tabs
                        }
                    )
    except Exception:
        res = []

    return jsonify(res)
