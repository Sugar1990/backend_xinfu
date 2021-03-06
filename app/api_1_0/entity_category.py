# -*- coding: UTF-8 -*-
from flask import jsonify, request
from sqlalchemy import or_, and_

from . import api_entity_category as blue_print
from ..models import EntityCategory, RelationCategory, Entity
from .. import db
from .utils import success_res, fail_res
from ..conf import PLACE_BASE_NAME
import uuid

# <editor-fold desc="实体类型，type=1：国家、地名、机构……">
# 返回地名uuid
@blue_print.route('/get_uuid_of_place_base_name', methods=['GET'])
def get_uuid_of_place_base_name():
    try:
        category = EntityCategory.query.filter(EntityCategory.name == PLACE_BASE_NAME, EntityCategory.valid==1).first()
        if category:
            res = {
                "uuid": category.uuid
            }
        else:
            res = fail_res(msg="未找到地名uuid")
    except Exception as e:
        print(str(e))
        res = {
            "uuid": "-1"
        }

    return jsonify(res)


# 查全集实体类型
@blue_print.route('/get_entity_categories', methods=['GET'])
def get_entity_categories():
    try:
        categories = EntityCategory.query.filter_by(type=1, valid=1).all()
        res = [{
            "uuid": i.uuid,
            "name": i.name
        } for i in categories]
    except Exception as e:

        print(str(e))
        res = []

    return jsonify(res)


# 查全集实体类型（不含地名）
@blue_print.route('/get_entity_categories_without_place', methods=['GET'])
def get_entity_categories_without_place():
    try:
        categories = EntityCategory.query.filter(EntityCategory.type == 1, EntityCategory.valid == 1,
                                                 EntityCategory.name != PLACE_BASE_NAME).all()
        res = [{
            "uuid": i.uuid,
            "name": i.name
        } for i in categories]
    except Exception as e:

        print(str(e))
        res = []

    return jsonify(res)


# 查单条数据
@blue_print.route('/get_one_entity_category', methods=['GET'])
def get_one_entity_category():
    try:
        uuid = request.args.get('uuid', '')
        category = EntityCategory.query.filter_by(uuid=uuid, type=1, valid=1).first()
        if category:
            res = {
                "uuid": category.uuid,
                "name": category.name
            }
        else:
            res = fail_res(msg="实体类型不存在")
    except Exception as e:
        print(str(e))
        res = {
            "uuid": "-1",
            "name": ""
        }

    return jsonify(res)


# insert
@blue_print.route('/add_entity_category', methods=['POST'])
def add_entity_category():
    try:
        name = request.json.get('name', '')
        source = request.json.get('source', '')
        # if name == PLACE_BASE_NAME:
        #     res = fail_res(msg="地名库由专业团队维护，不能添加！")
        # else:
        entity_category = EntityCategory.query.filter_by(name=name, type=1, valid=1).all()
        if entity_category:
            res = fail_res(msg="同名实体类型已存在")
        else:
            entity = EntityCategory(uuid=uuid.uuid1(), name=name, type=1, valid=1, _source=source)
            db.session.add(entity)
            db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# modify
@blue_print.route('/modify_entity_category', methods=['PUT'])
def modify_entity_category():
    try:
        uuid = request.json.get('uuid', '')
        name = request.json.get('name', '')
        if name:
            entity_category_same = EntityCategory.query.filter_by(name=name, type=1, valid=1).first()
            if entity_category_same:
                res = fail_res(msg="同名实体类型已存在")
            else:
                entity_category = EntityCategory.query.filter_by(uuid=uuid, type=1, valid=1).first()
                if entity_category:
                    # if entity_category.name != PLACE_BASE_NAME:
                    entity_category.name = name
                    db.session.commit()
                    res = success_res()
                    # else:
                    #     res = fail_res(msg="地名库由专业团队维护，不能修改")
                else:
                    res = fail_res(msg="实体类型不存在")
        else:
            res = fail_res(msg="修改名称不能为空")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# delete
@blue_print.route('/delete_entity_category', methods=['POST'])
def delete_entity_category():
    try:
        uuid = request.json.get("uuid", '')
        flag, msg = del_entity_category(uuid)
        if flag:
            res = success_res()
        else:
            res = fail_res(msg=msg)
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


def del_entity_category(uuid):
    try:
        entity_category = EntityCategory.query.filter_by(uuid=uuid, type=1, valid=1).first()
        relation_category = RelationCategory.query.filter(RelationCategory.valid == 1,
                                                          or_(RelationCategory.source_entity_category_uuids.op('@>')([uuid]),
                                                              RelationCategory.target_entity_category_uuids.op('@>')([uuid]))).all()
        entity = Entity.query.filter_by(category_uuid=uuid, valid=1).first()

        if not entity_category:
            res = False, "实体类型不存在"
        # elif entity_category.name == PLACE_BASE_NAME:
        #     res = False, "地名库由专业团队维护，不能修改"
        elif entity:
            res = False, "该类型存在实体，不能删除"
        elif relation_category:
            res = False, "该类型存在关联关系，不能删除"
        else:
            entity_category.valid = 0
            res = True, ""
    except Exception as e:
        print(str(e))
        res = False, ""
    return res


# 批量删除
@blue_print.route('/delete_entity_category_by_ids', methods=['POST'])
def delete_entity_category_by_ids():
    try:
        uuids = request.json.get("uuids", [])
        res_flag = True
        for uuid in uuids:
            flag, msg = del_entity_category(uuid)
            res_flag = res_flag & flag
        if res_flag:
            res = success_res()
        else:
            res = fail_res(msg=msg)
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# get_entity_category_paginate
@blue_print.route('/get_entity_category_paginate', methods=['GET'])
def get_entity_category_paginate():
    ### 重要参数:(当前页和每页条目数)
    current_page = request.args.get('cur_page', 1, type=int)
    page_size = request.args.get('page_size', 15, type=int)
    search = request.args.get("search", "")
    try:
        pagination = EntityCategory.query.filter(EntityCategory.valid == 1, EntityCategory.type == 1,
                                                 EntityCategory.name.like('%' + search + '%')).paginate(current_page, page_size, False)
        data = []
        for item in pagination.items:
            data.append({
                "uuid": item.uuid,
                "name": item.name
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


# </editor-fold>

# <editor-fold desc="实体概念，type=2：条约公约、战略、战法……">
# 查全集实体类型
@blue_print.route('/get_entity_ideas', methods=['GET'])
def get_entity_ideas():
    try:
        categories = EntityCategory.query.filter_by(type=2, valid=1).all()
        res = success_res(data=[{
            "uuid": i.uuid,
            "name": i.name
        } for i in categories])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


# 查单条数据
@blue_print.route('/get_one_entity_idea', methods=['GET'])
def get_one_entity_idea():
    try:
        uuid = request.args.get('uuid', '')
        category = EntityCategory.query.filter_by(uuid=uuid, type=2, valid=1).first()
        if category:
            res = success_res({
                "uuid": category.uuid,
                "name": category.name
            })
        else:
            res = fail_res(msg="实体概念不存在")
    except Exception as e:
        print(str(e))
        res = fail_res({
            "uuid": "-1",
            "name": ""
        })

    return jsonify(res)


# insert
@blue_print.route('/add_entity_idea', methods=['POST'])
def add_entity_idea():
    try:
        name = request.json.get('name', '')
        # if name == PLACE_BASE_NAME:
        #     res = fail_res(msg="地名库由专业团队维护，不能添加！")
        # else:
        entity_category = EntityCategory.query.filter_by(name=name, type=2, valid=1).all()
        if entity_category:
            res = fail_res(msg="同名实体概念已存在")
        else:
            entity = EntityCategory(uuid=uuid.uuid1(), name=name, type=2, valid=1)
            db.session.add(entity)
            db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# modify
@blue_print.route('/modify_entity_idea', methods=['PUT'])
def modify_entity_idea():
    try:
        uuid = request.json.get('uuid', '')
        name = request.json.get('name', '')
        if name:
            entity_category_same = EntityCategory.query.filter_by(name=name, type=2, valid=1).first()
            if entity_category_same:
                res = fail_res(msg="同名实体概念已存在")
            else:
                entity_category = EntityCategory.query.filter_by(uuid=uuid, type=2, valid=1).first()
                if entity_category:
                    # if entity_category.name != PLACE_BASE_NAME:
                    entity_category.name = name
                    db.session.commit()
                    res = success_res()
                    # else:
                    #     res = fail_res(msg="地名库由专业团队维护，不能修改")
                else:
                    res = fail_res(msg="实体概念不存在")
        else:
            res = fail_res(msg="修改名称不能为空")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# delete
@blue_print.route('/delete_entity_idea', methods=['POST'])
def delete_entity_idea():
    try:
        uuid = request.json.get("uuid", "")
        flag, msg = del_entity_idea(uuid)
        if flag:
            res = success_res()
        else:
            res = fail_res(msg=msg)
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


def del_entity_idea(uuid):
    try:
        entity_category = EntityCategory.query.filter_by(uuid=uuid, type=2, valid=1).first()
        relation_category = RelationCategory.query.filter(RelationCategory.valid == 1,
                                                          or_(RelationCategory.source_entity_category_uuids.op('@>')([uuid]),
                                                              RelationCategory.target_entity_category_uuids.op('@>')([uuid]))).all()
        entity = Entity.query.filter_by(category_uuid=uuid, valid=1).first()

        if not entity_category:
            res = False, "实体概念不存在"
        # elif entity_category.name == PLACE_BASE_NAME:
        #     res = False, "地名库由专业团队维护，不能修改"
        elif entity:
            res = False, "该概念存在实体，不能删除"
        elif relation_category:
            res = False, "该概念存在关联关系，不能删除"
        else:
            entity_category.valid = 0
            res = True, ""
    except Exception as e:
        print(str(e))
        res = False, ""
    return res


# 批量删除
@blue_print.route('/delete_entity_idea_by_ids', methods=['POST'])
def delete_entity_idea_by_ids():
    try:
        uuids = request.json.get("uuids", [])
        res_flag = True
        for uuid in uuids:
            flag, msg = del_entity_idea(uuid)
            res_flag = res_flag & flag
        if res_flag:
            res = success_res()
        else:
            res = fail_res(msg=msg)
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# get_entity_category_paginate
@blue_print.route('/get_entity_idea_paginate', methods=['GET'])
def get_entity_idea_paginate():
    ### 重要参数:(当前页和每页条目数)
    current_page = request.args.get('cur_page', 1, type=int)
    page_size = request.args.get('page_size', 15, type=int)
    search = request.args.get("search", "")
    try:
        pagination = EntityCategory.query.filter(EntityCategory.valid == 1, EntityCategory.type == 2,
                                                 EntityCategory.name.like('%' + search + '%')).paginate(current_page, page_size, False)
        data = []
        for item in pagination.items:
            data.append({
                "uuid": item.uuid,
                "name": item.name
            })
        res = success_res(data={
            "total_count": pagination.total,
            "page_count": pagination.pages,
            "data": data,
            "cur_page": pagination.page
        })

    except Exception as e:
        print(str(e))
        res = fail_res({
            "total_count": 0,
            "page_count": 0,
            "data": [],
            "cur_page": 0
        })
    return jsonify(res)
# </editor-fold>
