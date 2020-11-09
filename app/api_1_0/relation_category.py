# -*- coding: UTF-8 -*-
import json
import uuid

from flask import jsonify, request
from . import api_relation_category as blue_print
from ..models import RelationCategory, EntityCategory
from .. import db
from .utils import success_res, fail_res
from sqlalchemy import and_


# insert
@blue_print.route('/add_relation_category', methods=['POST'])
def add_relation_category():
    source_entity_category_ids = request.json.get('source_entity_category_uuids', [])
    target_entity_category_ids = request.json.get('target_entity_category_uuids', [])
    name = request.json.get('name', '')
    try:

        entity_category_id_list = []
        entity_category = EntityCategory.query.filter_by(valid=1).all()
        for item in entity_category:
            entity_category_id_list.append(str(item.uuid))
        entity_category_id_list_set = set(entity_category_id_list)

        input_source_ids_set = set(source_entity_category_ids)
        input_target_ids_set = set(target_entity_category_ids)

        if input_source_ids_set.issubset(entity_category_id_list_set) and input_target_ids_set.issubset(
                entity_category_id_list_set):
            # <editor-fold desc="judging if same relation_category exits">
            if name:
                relation_same = RelationCategory.query.filter_by(relation_name=name, valid=1).all()
                if relation_same:
                    for item in relation_same:
                        source_ids_db = set(item.source_entity_category_uuids)
                        target_ids_db = set(item.target_entity_category_uuids)

                        # 已存在--输入数据与库里已有数据相等或是库里数据的子集
                        if input_source_ids_set.issubset(
                                source_ids_db) and input_target_ids_set.issubset(target_ids_db):
                            res = fail_res(msg="已存在相同关联记录")
                            return jsonify(res)

                        # update--源ids相等 and 目标ids不相等  update目标ids  取并集
                        elif (input_source_ids_set == source_ids_db) and input_target_ids_set != target_ids_db:
                            target_ids_result = list(input_target_ids_set.union(target_ids_db))
                            item.target_entity_category_uuids = target_ids_result
                            res = success_res(data={"uuid": item.uuid})
                            break

                        # update--目标ids相等 and 源ids不相等  update源ids  取并集
                        elif (input_source_ids_set != source_ids_db) and input_target_ids_set == target_ids_db:
                            source_ids_result = list(input_source_ids_set.union(source_ids_db))
                            item.source_entity_category_uuids = source_ids_result
                            res = success_res(data={"uuid": item.uuid})
                            break

                        # update--库里已有数据是输入数据的子集
                        elif source_ids_db.issubset(
                                input_source_ids_set) and target_ids_db.issubset(input_target_ids_set):
                            item.source_entity_category_uuids = source_entity_category_ids
                            item.target_entity_category_uuids = target_entity_category_ids
                            res = success_res(data={"uuid": item.uuid})
                            break

                        # insert--
                        else:
                            rc = RelationCategory(uuid=uuid.uuid1(), source_entity_category_uuids=source_entity_category_ids,
                                                  target_entity_category_uuids=target_entity_category_ids,
                                                  relation_name=name,
                                                  valid=1)
                            db.session.add(rc)
                            db.session.commit()
                            res = success_res(data={"uuid": rc.uuid})
                            break
                else:
                    rc = RelationCategory(uuid=uuid.uuid1(), source_entity_category_uuids=source_entity_category_ids,
                                          target_entity_category_uuids=target_entity_category_ids, relation_name=name,
                                          valid=1)
                    db.session.add(rc)
                    db.session.commit()
                    res = success_res(data={"uuid": rc.uuid})

            else:
                res = fail_res(msg="关联名称不得为空")
            # </editor-fold>
        else:
            res = fail_res(msg="实体类型不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# delete
@blue_print.route('/delete_relation_category', methods=['POST'])
def delete_relation_category():
    try:
        uuid = request.json.get("uuid", "")

        relation_category = RelationCategory.query.filter_by(uuid=uuid, valid=1).first()
        if not relation_category:
            res = fail_res(msg="关系记录不存在")
            return res
        else:
            relation_category.valid = 0
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# 批量删除
@blue_print.route('/delete_relation_category_by_ids', methods=['POST'])
def delete_relation_category_by_ids():
    try:
        uuids = request.json.get("uuids", [])
        relation_category = db.session.query(RelationCategory).filter(RelationCategory.uuid.in_(uuids),
                                                                      RelationCategory.valid == 1).all()
        if relation_category:
            for rc in relation_category:
                rc.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="关系记录不存在")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# modify
@blue_print.route('/modify_relation_category', methods=['PUT'])
def modify_relation_category():
    try:
        uuid = request.json.get('uuid', "")
        source_entity_category_uuids = request.json.get('source_entity_category_uuids', [])
        target_entity_category_uuids = request.json.get('target_entity_category_uuids', [])
        name = request.json.get('name')

        relation_category = RelationCategory.query.filter_by(uuid=uuid, valid=1).first()
        if not relation_category:
            res = fail_res(msg="关系记录不存在!")
        else:
            relation_category_same = RelationCategory.query.filter(RelationCategory.relation_name==name,
                                                                   RelationCategory.valid==1,
                                                                   RelationCategory.uuid!=uuid).all()

            if relation_category_same:
                flag = True
                res_flag = True
                for rc in relation_category_same:
                    source_uuid = rc.source_entity_category_uuids
                    target_uuid = rc.target_entity_category_uuids
                    source_entity_category_ids_set = set(source_uuid)
                    target_entity_category_ids_set = set(target_uuid)

                    if (set(source_entity_category_uuids).issubset(source_entity_category_ids_set)) and (
                    set(target_entity_category_uuids).issubset(target_entity_category_ids_set)):
                        res_flag = False
                    if not res_flag:
                        break

                if not flag & res_flag:
                    res = fail_res(msg="已存在相同关系记录!")
                else:
                    entity_category_id_list = []
                    entity_category = EntityCategory.query.filter_by(valid=1).all()
                    for item in entity_category:
                        entity_category_id_list.append(str(item.uuid))

                    source_entity_category_ids_set = set(source_entity_category_uuids)
                    target_entity_category_ids_set = set(target_entity_category_uuids)
                    entity_category_id_list_set = set(entity_category_id_list)

                    if source_entity_category_ids_set.issubset(entity_category_id_list_set) \
                            and target_entity_category_ids_set.issubset(entity_category_id_list_set):

                        if not name:
                            res = fail_res(msg="关联名称不能为空!")
                        else:
                            relation_category.relation_name = name
                            relation_category.source_entity_category_uuids = source_entity_category_uuids
                            relation_category.target_entity_category_uuids = target_entity_category_uuids
                            db.session.commit()
                            res = success_res()
                    else:
                        res = fail_res(msg="实体类型不存在!")
            else:
                relation_category.relation_name = name
                relation_category.source_entity_category_uuids = source_entity_category_uuids
                relation_category.target_entity_category_uuids = target_entity_category_uuids
                db.session.commit()
                res = success_res()

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="修改失败!")

    return jsonify(res)


# 全集遍历查询
@blue_print.route('/get_relation_categories', methods=['GET'])
def get_relation_categories():
    try:
        relation_category = RelationCategory.query.filter_by(valid=1).all()
        data = [{
            "uuid": rc.uuid,
            "source_entity_category_uuids": rc.source_entity_category_uuids,
            "target_entity_category_uuids": rc.target_entity_category_uuids,
            "name": rc.relation_name
        } for rc in relation_category]
        res = success_res(data=data)
    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


# search by id
@blue_print.route('/get_one_relation_category', methods=['GET'])
def get_one_relation_category():
    try:
        id = request.args.get('uuid', "")
        relation_category = RelationCategory.query.filter_by(uuid=id, valid=1).first()
        if relation_category:
            data = {
                "uuid": relation_category.uuid,
                "source_entity_category_uuids": relation_category.source_entity_category_uuids,
                "target_entity_category_uuids": relation_category.target_entity_category_uuids,
                "name": relation_category.relation_name
            }
            res = success_res(data=data)
        else:
            res = fail_res(msg="关系记录不存在!")
    except Exception as e:
        print(str(e))
        res = fail_res(data={
            "uuid": -1,
            "source_entity_category_uuids": [],
            "target_entity_category_uuids": [],
            "name": ""
        })

    return jsonify(res)


# 分页查询
@blue_print.route('/get_relation_category_paginate', methods=['GET'])
def get_relation_category_paginate():
    try:
        current_page = request.args.get('cur_page', 1, type=int)
        page_size = request.args.get('page_size', 15, type=int)
        search = request.args.get("search", "")
        # pagination = RelationCategory.query.filter(RelationCategory.relation_name.like('%' + search + '%'),
        #                                            RelationCategory.valid == 1).order_by(
        #     RelationCategory.id.desc()).paginate(current_page, page_size, False)
        pagination = RelationCategory.query.filter(RelationCategory.relation_name.like('%' + search + '%'),
                                                   RelationCategory.valid == 1).paginate(current_page, page_size, False)

        data = [{
            "uuid": item.uuid,
            "source_entity_category_uuids": item.source_entity_category_uuids,
            "source_entity_category": item.source_entity_category(),
            "target_entity_category_uuids": item.target_entity_category_uuids,
            "target_entity_category": item.target_entity_category(),
            "name": item.relation_name
        } for item in pagination.items]
        res = success_res(data={
            "total_count": pagination.total,
            "page_count": pagination.pages,
            "data": data,
            "cur_page": pagination.page
        })
    except Exception as e:
        print(str(e))
        res = fail_res(data={
            "total_count": 0,
            "page_count": 0,
            "data": [],
            "cur_page": 0
        })
    return jsonify(res)


# 关联查询--待修改
'''
@blue_print.route('/get_source_entity_category', methods=['GET'])
def get_source_entity_category():
    try:
        source_entity_category_id = request.args.get("source_entity_category_id", 0, type=int)
        # relation_category = RelationCategory.query.filter(RelationCategory.source_entity_category_ids.contains(source_entity_category_id), RelationCategory.valid==1).first()
        # relation_category = RelationCategory.query.filter(
        #         #     RelationCategory.source_entity_category_ids.contains(source_entity_category_id),
        #         #     RelationCategory.valid == 1).first()
        #         # source_entity_category = relation_category.source_entity_category()
        # res = [{
        #     "source_entity_category": source_entity_category
        # }]
        entity_category = EntityCategory.query.filter_by(id=source_entity_category_id, valid=1).first()
        if entity_category:
            res = success_res(data=[{
                "source_entity_category": entity_category.name
            }])
        else:
            res=fail_res(msg="实体类型不存在")
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


@blue_print.route('/get_target_entity_category', methods=['GET'])
def get_target_entity_category():
    try:
        target_entity_category_ids = request.args.get("target_entity_category_ids", [])
        relation_category = RelationCategory.query.filter_by(
            target_entity_category_ids=target_entity_category_ids, valid=1).first()
        target_entity_category = relation_category.target_entity_category()
        res = [{
            "target_entity_category": target_entity_category
        }]
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


@blue_print.route('/get_entity_category_tuple', methods=['GET'])
def get_entity_category_tuple():
    try:
        source_entity_category_ids = request.args.get("source_entity_category_ids", [])
        target_entity_category_ids = request.args.get("target_entity_category_ids", [])
        relation_category = RelationCategory.query.filter_by(source_entity_category_ids=source_entity_category_ids,
                                                             target_entity_category_ids=target_entity_category_ids,
                                                             valid=1).first()
        source_entity_category = relation_category.source_entity_category()
        target_entity_category = relation_category.target_entity_category()
        res = [{
            "source_entity_category": source_entity_category,
            "target_entity_category": target_entity_category
        }]
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)
'''
