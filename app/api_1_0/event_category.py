# -*- coding: UTF-8 -*-
from flask import jsonify, request
from . import api_event_category as blue_print
from ..models import EventClass
from ..models import EventCategory
from .. import db
from .utils import success_res, fail_res

@blue_print.route('/add_event_category', methods=['POST'])
def add_event_category():
    name = request.json.get("name", "")
    event_class_id = request.json.get("event_class_id", 0)

    if not name:
        res = fail_res(msg="category_name为空")
    elif not event_class_id:
        res = fail_res(msg="event_class_id为空")
    else:

        event_class_id_find = EventClass.query.filter_by(valid=1).all()
        event_class_list = []
        for i in event_class_id_find:
            event_class_list.append(i.id)

        if event_class_id not in event_class_list:
            res = fail_res(msg="event_class_id找不到，无法插入")
        else:
            try:
                eventCategory = EventCategory(name=name, event_class_id=event_class_id, valid=1)
                db.session.add(eventCategory)
                db.session.commit()
                res = success_res()
            except:
                db.session.rollback()
                res = fail_res()

    return jsonify(res)




@blue_print.route('/delete_event_category', methods=['POST'])
def delete_event_category():
    event_category_id = request.json.get("id", 0)

    if not event_category_id:
        res = fail_res(msg='event_category_id为空')
    else:
        catalog_id_frist = EventCategory.query.filter_by(id=event_category_id).first()

        if catalog_id_frist and catalog_id_frist.valid:
            try:
                catalog_id_frist.valid = 0
                db.session.commit()
                res = success_res()
            except:
                db.session.rollback()
                res = fail_res()
        else:
            res = success_res()

    return jsonify(res)


@blue_print.route('/delete_event_category_by_ids', methods=['POST'])
def delete_event_category_by_ids():
    event_category_ids = request.json.get("ids", [])

    if not event_category_ids:
        res = fail_res(msg='event_category_ids为空')
    else:
        for event_category_id in event_category_ids:
            catalog_id_frist = EventCategory.query.filter_by(id=event_category_id).first()

            if catalog_id_frist and catalog_id_frist.valid:
                try:
                    catalog_id_frist.valid = 0
                    db.session.commit()
                    res = success_res()
                except:
                    db.session.rollback()
                    res = fail_res()
            else:
                res = success_res()

    return jsonify(res)


@blue_print.route('/modify_event_category', methods=['PUT'])
def modify_event_category():
    try:
        event_category_id = request.json.get('id', 0)
        event_category_name = request.json.get('name', '')
        event_class_id = request.json.get('event_class_id', 0)

        event_category_find = EventCategory.query.filter_by(id=event_category_id, valid=1).first()
        if event_category_find:
            event_category_find_same_name = EventCategory.query.filter_by(name=event_category_name, event_class_id=event_class_id, valid=1).first()
            if event_category_find_same_name:
                res = fail_res("同名实体类型已存在")
            else:
                if not eventCategory_find:
                    res = fail_res(msg="找不到修改对象")
                else:
                    event_category_find.name = event_category_name
                    event_category_find.event_class_id = event_class_id
                    db.session.commit()
                    res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="修改失败！")

    return jsonify(res)


@blue_print.route('/get_one_event_category', methods=['GET'])
def get_one_event_category():
    try:
        event_category_id = request.args.get('id', 0)

        eventCategory_find = EventCategory.query.filter_by(id=event_category_id, valid=1).first()
        res = {
            "id": eventCategory_find.id,
            "name": eventCategory_find.name,
            "event_class_id": eventCategory_find.event_class_id
        }
    except:
        res = []

    return jsonify(res)


@blue_print.route('/get_event_categories', methods=['GET'])
def get_event_categories():
    try:
        eventCategory_find = EventCategory.query.filter_by(valid=1).all()

        res = [{
            "id": i.id,
            "name": i.name,
            "event_class_id": i.event_class_id,
        } for i in eventCategory_find]
    except:
        res = []

    return jsonify(res)


@blue_print.route('/get_event_category_paginate', methods=['GET'])
def get_event_category_paginate():
    search = request.args.get("search", "")
    current_page = request.args.get('cur_page', 1, type=int)
    page_size = request.args.get('page_size', 15, type=int)
    pagination = EventCategory.query.filter(EventCategory.name.like('%' + search + '%'),
                                            EventCategory.valid == 1).order_by(
        EventCategory.id.desc()).paginate(current_page, page_size, False)

    data = []
    for item in pagination.items:
        data.append({
            "id": item.id,
            "name": item.name,
            "event_class_id": item.event_class_id,
            "event_class_name": EventClass.get_classname(item.event_class_id)
        })
    data = {
        "total_count": pagination.total,
        "page_count": pagination.pages,
        "data": data,
        "cur_page": pagination.page
    }
    return jsonify(data)


@blue_print.route('/get_event_categories_by_classid', methods=['GET'])
def get_event_categories_by_classid():
    try:
        class_id = request.args.get('class_id', 0, type=int)

        categories = EventCategory.query.filter_by(event_class_id=class_id, valid=1).all()
        res = [{
            "id": i.id,
            "name": i.name,
        } for i in categories]
    except:
        res = []
    return jsonify(res)
