# -*- coding: UTF-8 -*-
from flask import jsonify, request
from . import api_event_category as blue_print
from ..models import EventClass
from ..models import EventCategory
from .. import db
from .utils import success_res, fail_res
import uuid

@blue_print.route('/add_event_category', methods=['POST'])
def add_event_category():
    try:
        name = request.json.get('name')
        event_class_uuid = request.json.get("event_class_uuid", '')
        event_class_id_find = EventClass.query.filter_by(uuid=event_class_uuid, valid=1).first()
        if event_class_id_find:
            event_category = EventCategory.query.filter_by(name=name, event_class_uuid=event_class_uuid, valid=1).first()
            if event_category:
                res = fail_res(msg="事件类型已存在!")
            else:
                eventCategory = EventCategory(uuid=uuid.uuid1(), name=name, event_class_uuid=event_class_uuid, valid=1)
                db.session.add(eventCategory)
                db.session.commit()
                res = success_res()
        else:
            res = fail_res(msg="event_class_uuid找不到，无法插入")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/delete_event_category', methods=['POST'])
def delete_event_category():
    try:
        event_category_uuid = request.json.get("uuid", '')

        if not event_category_uuid:
            res = fail_res(msg='event_category_uuid为空')
        else:
            catalog_id_frist = EventCategory.query.filter_by(uuid=event_category_uuid, valid=1).first()

            if catalog_id_frist and catalog_id_frist.valid:
                try:
                    catalog_id_frist.valid = 0
                    db.session.commit()
                    res = success_res()
                except Exception as e:
                    print(str(e))
                    db.session.rollback()
                    res = fail_res()
            else:
                res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/delete_event_category_by_ids', methods=['POST'])
def delete_event_category_by_ids():
    try:
        event_category_uuids = request.json.get("uuids", [])

        if not event_category_uuids:
            res = fail_res(msg='event_category_uuids为空')
        else:
            for event_category_uuid in event_category_uuids:
                catalog_id_frist = EventCategory.query.filter_by(uuid=event_category_uuid, valid=1).first()

                if catalog_id_frist and catalog_id_frist.valid:
                    try:
                        catalog_id_frist.valid = 0
                        db.session.commit()
                        res = success_res()
                    except Exception as e:
                        print(str(e))
                        db.session.rollback()
                        res = fail_res()
                else:
                    res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_event_category', methods=['PUT'])
def modify_event_category():
    try:
        event_category_uuid = request.json.get('uuid', '')
        event_category_name = request.json.get('name', '')
        event_class_uuid = request.json.get('event_class_uuid', '')

        event_category_find = EventCategory.query.filter_by(uuid=event_category_uuid, valid=1).first()
        if event_category_find:
            event_category_find1 = EventCategory.query.filter_by(name=event_category_name,
                                                                 event_class_uuid=event_class_uuid, valid=1).first()
            if event_category_find1:
                res = fail_res(msg="同名实体类型已存在")
            else:
                event_category_find.name = event_category_name
                event_category_find.event_class_uuid = event_class_uuid
                db.session.commit()
                res = success_res()
        else:
            res = fail_res(msg="找不到修改对象")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="修改失败！")

    return jsonify(res)


@blue_print.route('/get_one_event_category', methods=['GET'])
def get_one_event_category():
    try:
        event_category_uuid = request.args.get('uuid', '')

        eventCategory_find = EventCategory.query.filter_by(uuid=event_category_uuid, valid=1).first()
        res = {
            "uuid": eventCategory_find.uuid,
            "name": eventCategory_find.name,
            "event_class_uuid": eventCategory_find.event_class_uuid
        }
    except Exception as e:
        print(str(e))
        res = {
            "uuid": "-1",
            "name": "",
            "event_class_uuid": "-1"
        }

    return jsonify(res)


@blue_print.route('/get_event_categories', methods=['GET'])
def get_event_categories():
    try:
        eventCategory_find = EventCategory.query.filter_by(valid=1).all()

        res = [{
            "uuid": i.uuid,
            "name": i.name,
            "event_class_uuid": i.event_class_uuid,
        } for i in eventCategory_find]
    except Exception as e:
        print(str(e))
        res = []

    return jsonify(res)


@blue_print.route('/get_event_category_paginate', methods=['GET'])
def get_event_category_paginate():
    try:
        search = request.args.get("search", "")
        current_page = request.args.get('cur_page', 1, type=int)
        page_size = request.args.get('page_size', 15, type=int)
        pagination = EventCategory.query.filter(EventCategory.name.like('%' + search + '%'),
                                                EventCategory.valid == 1).paginate(current_page, page_size, False)

        data = []
        for item in pagination.items:
            data.append({
                "uuid": item.uuid,
                "name": item.name,
                "event_class_uuid": item.event_class_uuid,
                "event_class_name": EventClass.get_classname(item.event_class_uuid)
            })
        data = {
            "total_count": pagination.total,
            "page_count": pagination.pages,
            "data": data,
            "cur_page": pagination.page
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


@blue_print.route('/get_event_categories_by_classid', methods=['GET'])
def get_event_categories_by_classid():
    try:
        class_uuid = request.args.get('class_uuid', '')

        categories = EventCategory.query.filter_by(event_class_uuid=class_uuid, valid=1).all()
        res = [{
            "uuid": i.uuid,
            "name": i.name,
        } for i in categories]
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)
