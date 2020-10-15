# -*- coding: UTF-8 -*-
import time

from flask import jsonify, request
from sqlalchemy import or_, and_

from . import api_doc_mark_event as blue_print
from ..models import DocMarkEvent
from .. import db
from .utils import success_res, fail_res

#doc_mark_event表中删除了parent_name字段，保留了parent_id字段

# 按id查询
@blue_print.route('/get_doc_mark_event_by_id', methods=['GET'])
def get_doc_mark_event_by_id():
    try:
        id = request.args.get("id", 0, type=int)
        doc_mark_event = DocMarkEvent.query.filter_by(id=id, valid=1).first()
        if doc_mark_event:
            res = success_res({
                "id": doc_mark_event.id,
                "event_id": doc_mark_event.event_id,
                "event_desc": doc_mark_event.event_desc,
                "event_subject": doc_mark_event.event_subject,
                "event_predicate": doc_mark_event.event_predicate,
                "event_object": doc_mark_event.event_object,
                "event_time": doc_mark_event.event_time,
                "event_address": doc_mark_event.event_address,
                "event_why": doc_mark_event.event_why,
                "event_result": doc_mark_event.event_result,
                "event_conduct": doc_mark_event.event_conduct,
                "event_talk": doc_mark_event.event_talk,
                "event_how": doc_mark_event.event_how,
                "doc_id": doc_mark_event.doc_id,
                "customer_id": doc_mark_event.customer_id,
                "parent_id": doc_mark_event.parent_id,
                "title": doc_mark_event.title,
                "event_class_id": doc_mark_event.event_class_id,
                "event_type_id": doc_mark_event.event_type_id,
                "create_by": doc_mark_event.create_by,
                "create_time": doc_mark_event.create_time.strftime("%Y--%m--%d %H:%M:%S") if doc_mark_event.create_time else None,
                "update_by": doc_mark_event.update_by,
                "update_time": doc_mark_event.update_time.strftime("%Y--%m--%d %H:%M:%S") if doc_mark_event.update_time else None,
                "add_time": doc_mark_event.add_time.strftime("%Y--%m--%d %H:%M:%S") if doc_mark_event.add_time else None
            })
        else:
            res = fail_res(msg="事件数据不存在")

    except:
        res = fail_res({
            "id": -1,
            "event_id": "",
            "event_desc": "",
            "event_subject": "",
            "event_predicate": "",
            "event_object": "",
            "event_time": "",
            "event_address": "",
            "event_why": "",
            "event_result": "",
            "event_conduct": "",
            "event_talk": "",
            "event_how": "",
            "doc_id": -1,
            "customer_id": -1,
            "parent_id": -1,
            "title": "",
            "event_class_id": -1,
            "event_type_id": -1,
            "create_by": -1,
            "create_time": None,
            "update_by": -1,
            "update_time": None,
            "add_time": None
        })

    return jsonify(res)


# 按doc_id查询
@blue_print.route('/get_doc_mark_event_by_doc_id', methods=['GET'])
def get_doc_mark_event_by_doc_id():
    try:
        doc_id = request.args.get("doc_id", 0, type=int)
        doc_mark_event_list = DocMarkEvent.query.filter_by(doc_id=doc_id, valid=1).all()
        if doc_mark_event_list:
            res = success_res(data=[{
                "id": i.id,
                "event_id": i.event_id,
                "event_desc": i.event_desc,
                "event_subject": i.event_subject,
                "event_predicate": i.event_predicate,
                "event_object": i.event_object,
                "event_time": i.event_time,
                "event_address": i.event_address,
                "event_why": i.event_why,
                "event_result": i.event_result,
                "event_conduct": i.event_conduct,
                "event_talk": i.event_talk,
                "event_how": i.event_how,
                "doc_id": i.doc_id,
                "customer_id": i.customer_id,
                "parent_id": i.parent_id,
                "title": i.title,
                "event_class_id": i.event_class_id,
                "event_type_id": i.event_type_id,
                "create_by": i.create_by,
                "create_time": i.create_time.strftime("%Y--%m--%d %H:%M:%S") if i.create_time else None,
                "update_by": i.update_by,
                "update_time": i.update_time.strftime("%Y--%m--%d %H:%M:%S") if i.update_time else None,
                "add_time": i.add_time.strftime("%Y--%m--%d %H:%M:%S") if i.add_time else None
            } for i in doc_mark_event_list])
        else:
            res = fail_res(msg="事件数据不存在")

    except:
        res = fail_res(data=[])

    return jsonify(res)


# add
@blue_print.route('/add_doc_mark_event', methods=['POST'])
def add_doc_mark_event():
    try:
        event_id = request.json.get("event_id", "")
        event_desc = request.json.get("event_desc", "")
        event_subject = request.json.get("event_subject", "")
        event_predicate = request.json.get("event_predicate", "")
        event_object = request.json.get("event_object", "")
        event_time = request.json.get("event_time", "")
        event_address = request.json.get("event_address", "")
        event_why = request.json.get("event_why", "")
        event_result = request.json.get("event_result", "")
        event_conduct = request.json.get("event_conduct", "")
        event_talk = request.json.get("event_talk", "")
        event_how = request.json.get("event_how", "")
        doc_id = request.json.get("doc_id", 0)
        customer_id = request.json.get("customer_id", 0)
        parent_id = request.json.get("parent_id", 0)
        title = request.json.get("title", "")
        event_class_id = request.json.get("event_class_id", 0)
        event_type_id = request.json.get("event_type_id", 0)
        create_by = request.json.get("create_by", 0)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_by = request.json.get("update_by", 0)
        update_time = request.json.get("update_time", None)
        add_time = request.json.get("add_time", None)

        if not (isinstance(doc_id, int) and isinstance(customer_id, int) and isinstance(parent_id, int)
                and isinstance(event_class_id, int) and isinstance(event_type_id, int) and isinstance(create_by, int)
                and isinstance(update_by, int)):
            res = fail_res(msg="参数 \"doc_id\"、 \"customer_id\"、 \"parent_id\"、\"event_class_id\"、"
                               "\"event_type_id\"、\"create_by\"、\"update_by\"应是整数类型")

        else:
            doc_mark_event = DocMarkEvent(event_id=event_id, event_desc=event_desc, event_subject=event_subject,
                                          event_predicate=event_predicate, event_object=event_object, event_time=event_time,
                                          event_address=event_address,event_why=event_why, event_result=event_result,
                                          event_conduct=event_conduct, event_talk=event_talk, event_how=event_how, doc_id=doc_id,
                                          customer_id=customer_id, parent_id=parent_id, title=title, event_class_id=event_class_id,
                                          event_type_id=event_type_id, create_by=create_by, create_time=create_time,
                                          update_by=update_by, update_time=update_time, add_time=add_time,
                                          valid=1)
            db.session.add(doc_mark_event)
            db.session.commit()
            res = success_res()

    except:
        res = fail_res()

    return jsonify(res)


# modify
@blue_print.route('/modify_doc_mark_event', methods=['PUT'])
def modify_doc_mark_event():
    try:
        id = request.json.get("id", 0)
        event_id = request.json.get("event_id", "")
        event_desc = request.json.get("event_desc", "")
        event_subject = request.json.get("event_subject", "")
        event_predicate = request.json.get("event_predicate", "")
        event_object = request.json.get("event_object", "")
        event_time = request.json.get("event_time", "")
        event_address = request.json.get("event_address", "")
        event_why = request.json.get("event_why", "")
        event_result = request.json.get("event_result", "")
        event_conduct = request.json.get("event_conduct", "")
        event_talk = request.json.get("event_talk", "")
        event_how = request.json.get("event_how", "")
        doc_id = request.json.get("doc_id", 0)
        customer_id = request.json.get("customer_id", 0)
        parent_id = request.json.get("parent_id", 0)
        title = request.json.get("title", "")
        event_class_id = request.json.get("event_class_id", 0)
        event_type_id = request.json.get("event_type_id", 0)
        create_by = request.json.get("create_by", 0)
        create_time = request.json.get("create_time", None)
        update_by = request.json.get("update_by", 0)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        add_time = request.json.get("add_time", None)

        if not (isinstance(id, int) and isinstance(doc_id, int) and isinstance(customer_id, int) and isinstance(parent_id, int)
                and isinstance(event_class_id, int) and isinstance(event_type_id, int) and isinstance(create_by, int)
                and isinstance(update_by, int)):
            res =fail_res(msg="参数 \"id\"、\"doc_id\"、\"customer_id\"、\"parent_id\"、\"event_class_id\"、"
                              "\"event_type_id\"、\"create_by\"、\"update_by\"应是整数类型")

        else:
            doc_mark_event = DocMarkEvent.query.filter_by(id=id, valid=1).first()
            if doc_mark_event:
                if event_id:
                    doc_mark_event.doc_id = event_id
                if event_desc:
                    doc_mark_event.event_desc = event_desc
                if event_subject:
                    doc_mark_event.event_subject = event_subject
                if event_predicate:
                    doc_mark_event.event_predicate = event_predicate
                if event_object:
                    doc_mark_event.event_object = event_object
                if event_time:
                    doc_mark_event.event_time = event_time
                if event_address:
                    doc_mark_event.event_address = event_address
                if event_why:
                    doc_mark_event.event_why = event_why
                if event_result:
                    doc_mark_event.event_result = event_result
                if event_conduct:
                    doc_mark_event.event_conduct = event_conduct
                if event_talk:
                    doc_mark_event.event_talk = event_talk
                if event_how:
                    doc_mark_event.event_how = event_how
                if doc_id:
                    doc_mark_event.doc_id = doc_id
                if customer_id:
                    doc_mark_event.customer_id = customer_id
                if parent_id:
                    doc_mark_event.parent_id = parent_id
                if title:
                    doc_mark_event.title = title
                if event_class_id:
                    doc_mark_event.event_class_id = event_class_id
                if event_type_id:
                    doc_mark_event.event_type_id = event_type_id
                if create_by:
                    doc_mark_event.create_by = create_by
                if create_time:
                    doc_mark_event.create_time = create_time
                if update_by:
                    doc_mark_event.update_by = update_by
                if update_time:
                    doc_mark_event.update_time = update_time
                if add_time:
                    doc_mark_event.add_time = add_time

                db.session.commit()
                res = success_res()
            else:
                res = fail_res(msg="事件数据不存在")

    except:
        res = fail_res()

    return jsonify(res)


# delete
@blue_print.route('/delete_doc_mark_event_by_id', methods=['POST'])
def delete_doc_mark_entity_by_id():
    try:
        id = request.json.get("id", 0)
        if isinstance(id, int):
            doc_mark_event = DocMarkEvent.query.filter_by(id=id, valid=1).first()
            if doc_mark_event:
                doc_mark_event.valid = 0
                res = success_res()
            else:
                res = fail_res(msg="事件数据不存在")
        else:
            res = fail_res(msg="参数 \"id\" 应是整数类型")

    except:
        res = fail_res()

    return jsonify(res)
