# -*- coding: UTF-8 -*-
from flask import jsonify, request
from . import api_relation_category as blue_print
from ..models import RelationCategory, EntityCategory
from .. import db
from .utils import success_res, fail_res
from sqlalchemy import and_


# insert
@blue_print.route('/add_ relation_category', methods=['POST'])
def add_relation_category():
    source_entity_category_id = request.json.get('source_entity_category_id', 0)
    target_entity_category_id = request.json.get('target_entity_category_id', 0)
    name = request.json.get('name', '')
    try:
        entity_category_id_list = []
        entity_category = EntityCategory.query.all()
        for item in entity_category:
            entity_category_id_list.append(item.id)
        if source_entity_category_id in entity_category_id_list and target_entity_category_id in entity_category_id_list:
            if name:
                relation = RelationCategory.query.filter_by(source_entity_category_id=source_entity_category_id,
                                                            target_entity_category_id=target_entity_category_id,
                                                            relation_name=name).first()
                if relation:
                    res = fail_res(msg="关联信息已存在")
                else:
                    rc = RelationCategory(source_entity_category_id=source_entity_category_id,
                                          target_entity_category_id=target_entity_category_id, relation_name=name,
                                          valid=1)
                    db.session.add(rc)
                    db.session.commit()

                    res = success_res()
            else:
                res = fail_res(msg="关联名称不得为空")
        else:
            res = fail_res(msg="实体类型不存在")
    except:
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# delete
@blue_print.route('/delete_relation_category', methods=['POST'])
def delete_relation_category():
    try:
        id = request.json.get("id", 0)

        relation_category = RelationCategory.query.filter_by(id=id, valid=1).first()
        if not relation_category:
            res = fail_res(msg="关系记录不存在")
            return res
        else:
            relation_category.valid = 0
            res = success_res()
    except:
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# 批量删除
@blue_print.route('/delete_relation_category_by_ids', methods=['POST'])
def delete_relation_category_by_ids():
    try:
        ids = request.json.get("ids", [])
        relation_category = db.session.query(RelationCategory).filter(RelationCategory.id.in_(ids),
                                                                      RelationCategory.valid == 1).all()
        if relation_category:
            for rc in relation_category:
                rc.valid = 0
            res = success_res()
        else:
            res = False, "关系记录不存在"

    except:
        db.session.rollback()
        res = fail_res(msg="关系记录不存在")

    return jsonify(res)


# modify
@blue_print.route('/modify_relation_category', methods=['PUT'])
def modify_relation_category():
    try:
        id = request.json.get('id', 0)
        source_entity_category_id = request.json.get('source_entity_category_id', 0)
        target_entity_category_id = request.json.get('target_entity_category_id', 0)
        name = request.json.get('name')

        relation_category = RelationCategory.query.filter_by(id=id, valid=1).first()
        if not relation_category:
            res = fail_res(msg="关系记录不存在")
            return res
        else:
            entity_category_id_list = []
            entity_category = EntityCategory.query.all()
            for item in entity_category:
                entity_category_id_list.append(item.id)
            if source_entity_category_id in entity_category_id_list and target_entity_category_id in entity_category_id_list:
                relation_category.source_entity_category_id = source_entity_category_id
                relation_category.target_entity_category_id = target_entity_category_id
                if not name:
                    name = None
                relation_category.relation_name = name
                db.session.commit()
                res = success_res()
            else:
                res = fail_res(msg="实体类型不存在")

    except:
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# 全集遍历查询
@blue_print.route('/get_relation_categories', methods=['GET'])
def get_relation_categories():
    try:
        relation_category = RelationCategory.query.filter_by(valid=1).all()
        res = [{
            "id": rc.id,
            "source_entity_category_id": rc.source_entity_category_id,
            "target_entity_category_id": rc.target_entity_category_id,
            "name": rc.relation_name
        } for rc in relation_category]
    except:
        res = []

    return jsonify(res)


# search by id
@blue_print.route('/get_one_relation_category', methods=['GET'])
def get_one_relation_category():
    try:
        id = request.args.get('id', 0, type=int)
        relation_category = RelationCategory.query.filter_by(id=id, valid=1).first()
        if relation_category:
            res = [{
                "id": relation_category.id,
                "source_entity_category_id": relation_category.source_entity_category_id,
                "target_entity_category_id": relation_category.target_entity_category_id,
                "name": relation_category.relation_name
            }]
        else:
            res = []
    except:
        res = []

    return jsonify(res)


# 分页查询
@blue_print.route('/get_relation_category_paginate', methods=['GET'])
def get_relation_category_paginate():
    try:
        current_page = request.args.get('cur_page', 1, type=int)
        page_size = request.args.get('page_size', 15, type=int)
        search = request.args.get("search", "")
        pagination = RelationCategory.query.filter(RelationCategory.relation_name.like('%' + search + '%'),
                                                   RelationCategory.valid == 1).order_by(
            RelationCategory.id.desc()).paginate(current_page, page_size, False)

        print(len(pagination.items), flush=True)
        data = []
        for item in pagination.items:
            data.append({
                "id": item.id,
                "source_entity_category_id": item.source_entity_category_id,
                "source_entity_category": item.source_entity_category(),
                "target_entity_category_id": item.target_entity_category_id,
                "target_entity_category": item.target_entity_category(),
                "name": item.relation_name
            })
            res = {
                "total_count": pagination.total,
                "page_count": pagination.pages,
                "data": data,
                "cur_page": pagination.page
            }
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


# 关联查询
@blue_print.route('/get_source_entity_category', methods=['GET'])
def get_source_entity_category():
    try:
        source_entity_category_id = request.args.get("source_entity_category_id", 0, type=int)
        relation_category = RelationCategory.query.filter_by(
            source_entity_category_id=source_entity_category_id, valid=1).first()
        source_entity_category = relation_category.source_entity_category()
        res = [{
            "source_entity_category": source_entity_category
        }]
    except:
        res = []
    return jsonify(res)


@blue_print.route('/get_target_entity_category', methods=['GET'])
def get_target_entity_category():
    try:
        target_entity_category_id = request.args.get("target_entity_category_id", 0, type=int)
        relation_category = RelationCategory.query.filter_by(
            target_entity_category_id=target_entity_category_id, valid=1).first()
        target_entity_category = relation_category.target_entity_category()
        res = [{
            "target_entity_category": target_entity_category
        }]
    except:
        res = []
    return jsonify(res)


@blue_print.route('/get_entity_category_tuple', methods=['GET'])
def get_entity_category_tuple():
    try:
        source_entity_category_id = request.args.get("source_entity_category_id", 0, type=int)
        target_entity_category_id = request.args.get("target_entity_category_id", 0, type=int)
        relation_category = RelationCategory.query.filter_by(source_entity_category_id=source_entity_category_id,
                                                             target_entity_category_id=target_entity_category_id,
                                                             valid=1).first()
        source_entity_category = relation_category.source_entity_category()
        target_entity_category = relation_category.target_entity_category()
        res = [{
            "source_entity_category": source_entity_category,
            "target_entity_category": target_entity_category
        }]
    except:
        res = []
    return jsonify(res)
