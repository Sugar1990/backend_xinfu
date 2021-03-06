# -*- coding: UTF-8 -*-

from flask import jsonify, request
from . import api_event_class as blue_print
from ..models import EventClass
from ..models import EventCategory
from .. import db
from .utils import success_res, fail_res
import uuid

@blue_print.route('/get_event_classes', methods=['GET'])
def get_event_classes():
    try:
        event_class = EventClass.query.filter_by(valid=1).all()
        if not event_class:
            res = []
        else:
            res = [{
                "uuid": i.uuid,
                "name": i.name
            } for i in event_class]
    except Exception as e:
        print(str(e))
        res = []

    return jsonify(res)


@blue_print.route('/get_one_event_class', methods=['GET'])
def get_one_event_class():
    try:
        event_uuid = request.args.get('uuid', '')
        event_class = EventClass.query.filter_by(uuid=event_uuid, valid=1).first()
        res = {
            "uuid": event_class.uuid,
            "name": event_class.name
        }
    except Exception as e:
        print(str(e))
        res = {
            "uuid": "-1",
            "name": ""
        }
    return jsonify(res)


@blue_print.route('/add_event_class', methods=['POST'])
def add_event_class():
    try:
        name = request.json.get('name')
        source = request.json.get('source', '')
        event_class = EventClass.query.filter_by(name=name, valid=1).first()
        if event_class:
            res = fail_res(msg="事件类别已存在!")
        else:
            eventClass = EventClass(uuid=uuid.uuid1(), name=name, valid=1, _source=source)
            db.session.add(eventClass)
            db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_event_class', methods=['PUT'])
def modify_event_class():
    try:
        event_uuid = request.json.get('uuid')
        name = request.json.get('name')
        event_class = EventClass.query.filter_by(uuid=event_uuid, valid=1).first()
        if event_class:
            event_class1 = EventClass.query.filter_by(name=name, valid=1).first()
            if event_class1:
                res = fail_res(msg="相同事件类别已存在")
            else:
                if name:
                    event_class.name = name
                db.session.commit()
                res = success_res()
        else:
            res = fail_res(msg="事件类别uuid不存在!")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="修改失败！")
    return jsonify(res)


@blue_print.route('/delete_event_class', methods=['POST'])
def delete_event_class():
    try:
        event_uuid = request.json.get("uuid", '')
        event_class = EventClass.query.filter_by(uuid=event_uuid, valid=1).first()
        if event_class:
            event_category = EventCategory.query.filter_by(event_class_uuid=event_class.uuid, valid=1).first()
            if event_category:
                res = fail_res(msg="该类型下有事件类型，不能删除！")
            else:
                event_class.valid = 0
                res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


@blue_print.route('/delete_event_class_by_ids', methods=['POST'])
def delete_event_class_by_ids():
    try:
        event_uuids = request.json.get("uuids", [])
        res_flag = True
        for event_uuid in event_uuids:
            event_class = EventClass.query.filter_by(uuid=event_uuid, valid=1).first()
            if event_class:
                event_category = EventCategory.query.filter_by(event_class_uuid=event_class.uuid, valid=1).first()
                if event_category:
                    flag = False
                    res_flag = res_flag & flag
                else:
                    event_class.valid = 0
                    flag = True
                    res_flag = res_flag & flag
        if res_flag:
            res = success_res()
        else:
            res = fail_res(msg="部分数据无法删除")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


@blue_print.route('/get_event_class_paginate', methods=['GET'])
def get_event_class_paginate():
    try:
        # 重要参数:(当前页和每页条目数)
        search = request.args.get("search", "")
        current_page = request.args.get('cur_page', 1, type=int)
        page_size = request.args.get('page_size', 15, type=int)
        # 注意下面的order_by:(目前可以只实现以id排序查看，后续可能实现多种排序方式)
        pagination = EventClass.query.filter(EventClass.name.like('%' + search + '%'), EventClass.valid == 1).paginate(
            current_page, page_size, False)

        data = []
        for item in pagination.items:
            data.append({
                ## 对应models.py中的字段
                "uuid": item.uuid,
                "name": item.name
            })
        data = {
            "total_count": pagination.total,  # 总条目数
            "page_count": pagination.pages,  # 总页数
            "data": data,  # 当前页数据
            "cur_page": pagination.page  # 当前页标记
        }

    except Exception as e:
        print(str(e))
        data = {
            "total_count": 0,
            "page_count": 0,
            "data": [],
            "cur_page": 0
        }
    return jsonify(data)
