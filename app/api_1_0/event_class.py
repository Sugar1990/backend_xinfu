# -*- coding: UTF-8 -*-

from flask import jsonify, request
from . import api_event_class as blue_print
from ..models import EventClass
from ..models import EventCategory
from .. import db
from .utils import success_res, fail_res


@blue_print.route('/get_event_classes', methods=['GET'])
def get_event_classes():
    try:
        event_class = EventClass.query.filter_by(valid=1).all()
        if not event_class:
            res = []
        else:
            res = [{
                "id": i.id,
                "name": i.name
            } for i in event_class]

    except Exception:
        res = []

    return jsonify(res)


@blue_print.route('/get_one_event_class', methods=['GET'])
def get_one_event_class():
    event_id = request.args.get('id', 0)
    event_class = EventClass.query.filter_by(id=event_id, valid=1).first()
    if not event_class:
        res = []
    else:
        res = {
            "id": event_class.id,
            "name": event_class.name
        }
    return jsonify(res)


@blue_print.route('/add_event_class', methods=['POST'])
def add_event_class():
    try:
        name = request.json.get('name')
        event_class = EventClass.query.filter_by(name=name, valid=1).first()
        if event_class:
            res = fail_res(msg="事件类别已存在!")
        else:
            eventClass = EventClass(name=name, valid=1)
            db.session.add(eventClass)
            db.session.commit()
            res = success_res()
    except:
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_event_class', methods=['PUT'])
def modify_event_class():
    try:
        event_id = request.json.get('id')
        name = request.json.get('name')
        event_class = EventClass.query.filter_by(id=event_id, valid=1).first()

        if not event_class:
            res = fail_res(msg="事件类别id不存在!")
        else:
            event_class.name = name
            event_class.valid = 1
            db.session.commit()
            res = success_res()

    except RuntimeError:
        db.session.rollback()
        res = fail_res(msg="修改失败！")

    return jsonify(res)


@blue_print.route('/delete_event_class', methods=['POST'])
def delete_event_class():
    try:
        event_id = request.json.get("id", 0)
        event_class = EventClass.query.filter_by(id=event_id, valid=1).first()
        if event_class:
            event_category = EventCategory.query.filter_by(event_class_id=event_class.id, ).first()
            if event_category:
                res = fail_res(msg="该类型下有事件类型，不能删除！")
                return jsonify(res)
            event_class.valid = 0
            db.session.commit()
        res = success_res()
    except:
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


@blue_print.route('/delete_event_class_by_ids', methods=['POST'])
def delete_event_class_by_ids():
    try:
        event_ids = request.json.get("ids", [])
        for event_id in event_ids:
            event_class = EventClass.query.filter_by(id=event_id, valid=1).first()
            if event_class:
                event_category = EventCategory.query.filter_by(event_class_id=event_class.id).first()
                if event_category:
                    res = fail_res(msg="某些类型下有事件类型，不能全部删除！")
                    return jsonify(res)
                event_class.valid = 0
                db.session.commit()
        res = success_res()
    except:
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


@blue_print.route('/get_event_class_paginate', methods=['GET'])
def get_event_class_paginate():
    # 重要参数:(当前页和每页条目数)
    search = request.args.get("search", "")
    current_page = request.args.get('cur_page', 1, type=int)
    page_size = request.args.get('page_size', 15, type=int)
    # 注意下面的order_by:(目前可以只实现以id排序查看，后续可能实现多种排序方式)
    pagination = EventClass.query.filter(EventClass.name.like('%' + search + '%'), EventClass.valid == 1).order_by(
        EventClass.id.desc()).paginate(current_page, page_size, False)

    data = []
    for item in pagination.items:
        data.append({
            ## 对应models.py中的字段
            "id": item.id,
            "name": item.name
        })
    data = {
        "total_count": pagination.total,  # 总条目数
        "page_count": pagination.pages,  # 总页数
        "data": data,  # 当前页数据
        "cur_page": pagination.page  # 当前页标记
    }
    return jsonify(data)
