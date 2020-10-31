# -*- coding: UTF-8 -*-
import datetime
import time

from flask import jsonify, request
from sqlalchemy import or_, and_
from sqlalchemy.dialects.postgresql import Any

from . import api_doc_mark_event as blue_print
from ..models import DocMarkEvent, DocMarkTimeTag, DocMarkEntity, DocMarkPlace, Entity, EventCategory
from .. import db
from .utils import success_res, fail_res
from .document import get_event_list_from_docs
from ..conf import ES_SERVER_IP, ES_SERVER_PORT

# doc_mark_event表中删除了parent_name字段，保留了parent_id字段

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
                "create_time": doc_mark_event.create_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_event.create_time else None,
                "update_by": doc_mark_event.update_by,
                "update_time": doc_mark_event.update_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_event.update_time else None,
                "add_time": doc_mark_event.add_time.strftime("%Y-%m-%d %H:%M:%S") if doc_mark_event.add_time else None
            })
        else:
            res = fail_res(msg="事件数据不存在")

    except Exception as e:
        print(str(e))
        res = fail_res({
            "id": -1,
            "event_id": "",
            "event_desc": "",
            "event_subject": [],
            "event_predicate": "",
            "event_object": [],
            "event_time": [],
            "event_address": [],
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
            "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
            "update_by": i.update_by,
            "update_time": i.update_time.strftime("%Y-%m-%d %H:%M:%S") if i.update_time else None,
            "add_time": i.add_time.strftime("%Y-%m-%d %H:%M:%S") if i.add_time else None
        } for i in doc_mark_event_list])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


# add
@blue_print.route('/add_doc_mark_event', methods=['POST'])
def add_doc_mark_event():
    try:
        event_id = request.json.get("event_id", "")
        event_desc = request.json.get("event_desc", "")
        event_subject = request.json.get("event_subject", [])
        event_predicate = request.json.get("event_predicate", "")
        event_object = request.json.get("event_object", [])
        event_time = request.json.get("event_time", [])
        event_address = request.json.get("event_address", [])
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
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        add_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        if not (isinstance(doc_id, int) and isinstance(customer_id, int) and isinstance(parent_id, int)
                and isinstance(event_class_id, int) and isinstance(event_type_id, int) and isinstance(create_by, int)
                and isinstance(update_by, int)):
            res = fail_res(msg="参数 \"doc_id\"、 \"customer_id\"、 \"parent_id\"、\"event_class_id\"、"
                               "\"event_type_id\"、\"create_by\"、\"update_by\"应是整数类型")
        elif not (isinstance(event_subject, list) and isinstance(event_object, list) and isinstance(event_time, list)
                  and isinstance(event_address, list)):
            res = fail_res(msg="参数event_subject、event_object、event_time和event_address应为list类型")
        else:
            if event_time and event_address:
                doc_mark_event = DocMarkEvent(event_id=event_id, event_desc=event_desc, event_subject=event_subject,
                                              event_predicate=event_predicate, event_object=event_object,
                                              event_time=event_time,
                                              event_address=event_address, event_why=event_why,
                                              event_result=event_result,
                                              event_conduct=event_conduct, event_talk=event_talk, event_how=event_how,
                                              doc_id=doc_id,
                                              customer_id=customer_id, parent_id=parent_id, title=title,
                                              event_class_id=event_class_id,
                                              event_type_id=event_type_id, create_by=create_by, create_time=create_time,
                                              update_by=update_by, update_time=update_time, add_time=add_time,
                                              valid=1)
                db.session.add(doc_mark_event)
                db.session.commit()
                res = success_res(data={"id": doc_mark_event.id})
            else:
                res = fail_res(msg="事件时间和地点不能为空")

    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)


# modify
@blue_print.route('/modify_doc_mark_event', methods=['PUT'])
def modify_doc_mark_event():
    try:
        id = request.json.get("id", 0)
        event_id = request.json.get("event_id", "")
        event_desc = request.json.get("event_desc", "")
        event_subject = request.json.get("event_subject", [])
        event_predicate = request.json.get("event_predicate", "")
        event_object = request.json.get("event_object", [])
        event_time = request.json.get("event_time", [])
        event_address = request.json.get("event_address", [])
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

        if not (isinstance(id, int) and isinstance(doc_id, int) and isinstance(customer_id, int) and isinstance(
                parent_id, int)
                and isinstance(event_class_id, int) and isinstance(event_type_id, int) and isinstance(create_by, int)
                and isinstance(update_by, int)):
            res = fail_res(msg="参数 \"id\"、\"doc_id\"、\"customer_id\"、\"parent_id\"、\"event_class_id\"、"
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

    except Exception as e:
        print(str(e))
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

    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)


# 模糊搜索-pg
@blue_print.route('/search_doc_mark_event_by_sources', methods=['POST'])
def search_doc_mark_event_by_sources():
    try:
        start_time = request.json.get("start_time", "1900-01-01")
        end_time = request.json.get("end_time", "9999-12-31")
        search = request.json.get("search", "")
        current_page = request.json.get("current_page", 1)
        page_size = request.json.get("page_size", 10)

        if isinstance(current_page, str) and current_page.isdigit():
            current_page = int(current_page)
        if isinstance(page_size, str) and page_size.isdigit():
            page_size = int(page_size)

        # 时间条件
        conditions = [DocMarkTimeTag.valid == 1,
                      DocMarkTimeTag.format_date.between(start_time, end_time),
                      DocMarkTimeTag.time_type == 1]
        conditions = tuple(conditions)
        event_time_tag_ids = DocMarkTimeTag.query.with_entities(DocMarkTimeTag.id).filter(and_(*conditions)).all()
        event_time_tag_ids = [i[0] for i in event_time_tag_ids]

        # 标记主宾语条件
        conditions = [DocMarkEntity.word.like("%{}%".format(search)),
                      DocMarkEntity.valid == 1]
        conditions = tuple(conditions)
        event_entity_ids = DocMarkEntity.query.with_entities(DocMarkEntity.id).filter(and_(*conditions)).all()
        event_entity_ids = [i[0] for i in event_entity_ids]

        # 标记地点条件
        conditions = [DocMarkPlace.word.like("%{}%".format(search)),
                      DocMarkPlace.valid == 1]
        conditions = tuple(conditions)
        event_place_ids = DocMarkPlace.query.with_entities(DocMarkPlace.id).filter(and_(*conditions)).all()
        event_place_ids = [i[0] for i in event_place_ids]

        # 综合搜索
        conditions = [
            DocMarkEvent.valid == 1,
        ]

        if event_entity_ids:
            DocMarkEvent.event_subject.contains(event_entity_ids)
            DocMarkEvent.event_object.contains(event_entity_ids)
        if event_time_tag_ids:
            DocMarkEvent.event_time.contains(event_time_tag_ids)
        if event_place_ids:
            DocMarkEvent.event_address.contains(event_place_ids)

        or_conditions = [
            DocMarkEvent.title.like("%{}%".format(search)),
            DocMarkEvent.event_why.like("%{}%".format(search)),
            DocMarkEvent.event_result.like("%{}%".format(search)),
            DocMarkEvent.event_conduct.like("%{}%".format(search)),
            DocMarkEvent.event_talk.like("%{}%".format(search)),
            DocMarkEvent.event_how.like("%{}%".format(search))
        ]

        pagination = DocMarkEvent.query.filter(and_(*conditions, or_(*or_conditions))).paginate(current_page, page_size,
                                                                                                False)

        data = [{
            "title": i.title,
            "event_subject": i.event_subject,
            "event_object": i.event_object,
            "event_time": i.event_time,
            "event_address": i.event_address,
            "event_why": i.event_why,
            "event_result": i.event_result,
            "event_conduct": i.event_conduct,
            "event_talk": i.event_talk,
            "event_how": i.event_how,
        } for i in pagination.items]

        res = success_res(data={
            "total_count": pagination.total,
            "data": data,
            "cur_page": pagination.page
        })

    except Exception as e:
        print(str(e))
        res = fail_res(data={
            "total_count": 0,
            "data": [],
            "cur_page": 1})

    return jsonify(res)


# 高级搜索结果doc_ids和时间 筛选事件
@blue_print.route('/get_events_by_doc_ids_and_time_range', methods=['POST'])
def get_events_by_doc_ids_and_time_range():
    try:
        doc_ids = request.json.get('doc_ids', [])
        start_date = request.json.get('start_date', '1900-01-01')
        end_date = request.json.get('end_date', '9999-12-31')
        res = get_event_list_from_docs(doc_ids, start_date, end_date)
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


@blue_print.route('/get_doc_events_to_earth', methods=['GET'])
# @swag_from(get_doc_events_dict)
def get_doc_events_to_earth():
    try:
        doc_id = request.args.get("doc_id", 0, type=int)
        doc_mark_event_list = DocMarkEvent.query.filter_by(doc_id=doc_id, valid=1).all()

        result = []
        for doc_mark_event in doc_mark_event_list:
            places = doc_mark_event.get_places()
            place_list = [{
                "word": i.word,
                "place_id": i.place_id,
                "place_lon": i.place_lon,
                "place_lat": i.place_lat
            } for i in places if i.place_lon and i.place_lat]
            if place_list:
                datetime = ""
                if doc_mark_event.event_time:
                    time_tag = DocMarkTimeTag.query.filter(DocMarkTimeTag.id.in_(doc_mark_event.event_time),
                                                           DocMarkTimeTag.time_type.in_(['1', '2'])).first()
                    if time_tag:
                        datetime = time_tag.format_date.strftime("%Y-%m-%d %H:%M:%S")
                if datetime:
                    object_list = doc_mark_event.get_object_entity_names()
                    object_list.extend(doc_mark_event.get_subject_entity_names())
                    if object_list:
                        result.append({
                            "title": doc_mark_event.title,
                            "object": object_list,
                            "datetime": datetime,
                            "place": place_list})
        res = success_res(data=result)

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


@blue_print.route('/get_advanced_search_of_events', methods=['POST'])
def get_advanced_search_of_events():
    try:
        dates = request.json.get('dates', {})
        time_tag_ids = []
        if dates.get("date_type", False):
            date_type = dates.get("date_type", "")
            date_value = dates.get("value", None)
            if date_type == "time_range":
                time_range = date_value
                start_time = time_range.get("start_time", None)
                end_time = time_range.get("end_time", None)

                if start_time and end_time:
                    doc_mark_time_tag = DocMarkTimeTag.query.filter_by(format_date=start_time, format_date_end=end_time,
                                                                       time_type=2, valid=1).first()
                    # doc_mark_time_tags = DocMarkTimeTag.query.filter_by(format_date=start_time, format_date_end=end_time,
                    #                                                    time_type=2, valid=1).all()
                    # time_tag_ids = [i.id for i in doc_mark_time_tags]
                    time_tag_ids.append(doc_mark_time_tag.id)
                    print(time_tag_ids)

        places = request.json.get('places', {})
        doc_mark_place_ids = []
        if places.get("place_type", False):
            place_type = places.get("place_type", "")
            place_value = places.get("value", None)
            if place_type == "place":
                place = place_value
                entity = Entity.query.filter_by(name=place, category_id=8, valid=1).first()
                # doc_mark_places = DocMarkPlace.query.filter_by(place_id=entity.id, valid=1).all()
                # doc_mark_place_ids = [i.id for i in doc_mark_places]
                doc_mark_places = DocMarkPlace.query.filter_by(place_id=entity.id, valid=1).first()
                if doc_mark_places:
                    doc_mark_place_ids.append(doc_mark_places.id)
                print(len(doc_mark_place_ids))
                print([i for i in doc_mark_place_ids])
            elif place_type == "degrees":
                degrees = place_value
                if degrees.get("lon", None) and degrees.get("lat", None):
                    lon = degrees["lon"]
                    lat = degrees["lat"]
                    if lon.get("degrees",0) and lon.get("direction", 0) and lon.get("distance", 0) and lat.get("degrees",0) and lat.get("direction", 0) and lat.get("distance", 0):
                        lon = dfm_convert(lon.get("degrees"), lon.get("direction"), lon.get("distance", 0))
                        lat = dfm_convert(lat.get("degrees"), lat.get("direction"), lat.get("distance", 0))
                        entity = Entity.query.filter_by(longitude=lon, latitude=lat, category_id=8, valid=1).first()
                        # doc_mark_places = DocMarkPlace.query.filter_by(place_id=entity.id, valid=1).all()
                        # doc_mark_place_ids = [i.id for i in doc_mark_places]
                        if entity:
                            doc_mark_places = DocMarkPlace.query.filter_by(place_id=entity.id, valid=1).first()
                            if doc_mark_places:
                                doc_mark_place_ids.append(doc_mark_places.id)

            elif place_type == 'location':
                location = place_value
                if location.get("lon", None) and location.get("lat", None):
                    lon = location["lon"]
                    lat = location["lat"]
                    entity = Entity.query.filter_by(longitude=lon, latitude=lat, category_id=8, valid=1).first()
                    # doc_mark_places = DocMarkPlace.query.filter_by(place_id=entity.id, valid=1).all()
                    # doc_mark_place_ids = [i.id for i in doc_mark_places]
                    if entity:
                        doc_mark_places = DocMarkPlace.query.filter_by(place_id=entity.id, valid=1).first()
                        if doc_mark_places:
                            doc_mark_place_ids.append(doc_mark_places.id)

        object = request.json.get("object", {})
        doc_mark_entity_ids = []
        if object.get("category_id", 0) and object.get("entity", ""):
            category_id = object["category_id"]
            entity = object["entity"]
            entity_db = Entity.query.filter_by(category_id=category_id, name=entity, valid=1).first()
            # doc_mark_entity = DocMarkEntity.query.filter_by(entity_id=entity_db.id, valid=1).all()
            # doc_mark_entity_ids = [i.id for i in doc_mark_entity]
            if entity_db:
                doc_mark_entity = DocMarkEntity.query.filter_by(entity_id=entity_db.id, valid=1).first()
                if doc_mark_entity:
                    doc_mark_entity_ids.append(doc_mark_entity.id)
                    print(doc_mark_entity_ids)

        event = request.json.get("event", {})
        # if event.get("event_class", 0):
        #     event_class = event["event_class"]
        # if event.get("event_type", 0):
        #     event_category = event["event_type"]


        # filter条件应是前后两个list求交集..，暂时限制time_tag_ids等只有一个元素
        conditions = [DocMarkEvent.valid == 1]
        if time_tag_ids:
            conditions.append(DocMarkEvent.event_time.op('@>')(time_tag_ids))
        if doc_mark_place_ids:
            conditions.append(DocMarkEvent.event_address.op('@>')(doc_mark_place_ids))
        if doc_mark_entity_ids:
            conditions.append(or_(DocMarkEvent.event_subject.op('@>')(doc_mark_entity_ids), DocMarkEvent.event_object.op('@>')(doc_mark_entity_ids)))
        if event.get("event_class", 0):
            conditions.append(DocMarkEvent.event_class_id == event.get("event_class"))
        if event.get("event_type", 0):
            conditions.append(DocMarkEvent.event_type_id == event.get("event_type"))

        conditions = tuple(conditions)
        doc_mark_events = DocMarkEvent.query.filter(and_(*conditions)).all()

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
            "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
            "update_by": i.update_by,
            "update_time": i.update_time.strftime("%Y-%m-%d %H:%M:%S") if i.update_time else None,
            "add_time": i.add_time.strftime("%Y-%m-%d %H:%M:%S") if i.add_time else None
        } for i in doc_mark_events])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


def dfm_convert(du, fen, miao):
    out_location = int(du) + int(fen) / 60 + int(miao) / 3600
    return float(format(out_location, ".5f"))



@blue_print.route('/get_during_time_event', methods=['POST'])
def get_during_time_event():
    try:
        start_date = request.values.get('start_date', '1900-01-01')
        end_date = request.values.get('end_date', '9999-01-01')
        event_list = []
        events = DocMarkEvent.query.all()
        for i in events:
            if i.event_address and isinstance(i.event_address, list):
                place_ids = DocMarkPlace.query.with_entities(DocMarkPlace.place_id).filter(
                    DocMarkPlace.id.in_(i.event_address)).all()
                if place_ids:
                    place_ids = [i[0] for i in place_ids]
                    places = Entity.query.filter(Entity.id.in_(place_ids), Entity.valid == 1).all()
                    if places:
                        objects, subjects, form_time = [], [], ""
                        if i.event_object and isinstance(i.event_object, list):
                            object_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_id).filter(
                                DocMarkEntity.id.in_(i.event_object)).all()
                            if object_ids:
                                object_ids = [i[0] for i in object_ids]
                                objects = Entity.query.filter(Entity.id.in_(object_ids), Entity.valid == 1).all()
                        if i.event_subject and isinstance(i.event_subject, list):
                            subject_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_id).filter(
                                DocMarkEntity.id.in_(i.event_subject)).all()
                            if subject_ids:
                                subject_ids = [i[0] for i in subject_ids]
                                subjects = Entity.query.filter(Entity.id.in_(subject_ids), Entity.valid == 1).all()

                        # subject和object结合，返回给前端
                        objects.extend(subjects)
                        if objects:
                            if i.event_time and isinstance(i.event_time, list):
                                mark_time_ids = i.event_time
                                times = DocMarkTimeTag.query.with_entities(DocMarkTimeTag.format_date).filter(
                                    DocMarkTimeTag.id.in_(mark_time_ids),
                                    or_(and_(DocMarkTimeTag.format_date.between(start_date, end_date),
                                             DocMarkTimeTag.time_type == 1),
                                        and_(DocMarkTimeTag.format_date > start_date,
                                             DocMarkTimeTag.format_date_end < end_date,
                                             DocMarkTimeTag.time_type == 2))
                                ).all()
                                for time_tag in times:
                                    item = {
                                        "datetime": time_tag.format_date,
                                        "place": [{
                                            "place_lat": place.latitude,
                                            "place_lon": place.longitude,
                                            "place_id": place.id,
                                            # "type": 1,
                                            "word": place.name,
                                        } for place in places],
                                        "title": i.title,
                                        "object": [i.name for i in objects],
                                        "event_id": i.id}
                                    event_list.append(item) # </editor-fold>
        event_list = sorted(event_list, key=lambda x: x.get('datetime', ''))
    except Exception as e:
        print(str(e))
        event_list = fail_res(data={})
    return jsonify(event_list)