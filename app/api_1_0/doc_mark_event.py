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

        place_insert_ids = []
        object_insert_ids = []
        subject_insert_ids = []
        time_tag_insert_ids = []

        if not (isinstance(doc_id, int) and isinstance(customer_id, int) and isinstance(parent_id, int)
                and isinstance(event_class_id, int) and isinstance(event_type_id, int) and isinstance(create_by, int)
                and isinstance(update_by, int)):
            res = fail_res(msg="参数 \"doc_id\"、 \"customer_id\"、 \"parent_id\"、\"event_class_id\"、"
                               "\"event_type_id\"、\"create_by\"、\"update_by\"应是整数类型")
        elif not (isinstance(event_subject, list) and isinstance(event_object, list) and isinstance(event_time, list)
                  and isinstance(event_address, list)):
            res = fail_res(msg="参数event_subject、event_object、event_time和event_address应为list类型")
        else:
            if event_address:
                place_ids = DocMarkPlace.query.with_entities(DocMarkPlace.place_id).filter(
                    DocMarkPlace.id.in_(event_address)).all()
                if place_ids:
                    place_ids = [i[0] for i in place_ids]
                    places = Entity.query.filter(Entity.id.in_(place_ids), Entity.valid == 1).all()
                    if places:
                        for place in places:
                            doc_mark_place = DocMarkPlace.query.filter_by(place_id=place.id, valid=1).first()
                            if doc_mark_place:
                                place_insert_ids.append(doc_mark_place.id)
                        objects, subjects = [], []
                        if event_object or event_subject:
                            # object_id_list = event_object
                            # if event_subject:
                            #     object_id_list.extend(event_subject)
                            object_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_id).filter(
                                DocMarkEntity.id.in_(event_object)).all()
                            subject_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_id).filter(
                                DocMarkEntity.id.in_(event_subject)).all()
                            if object_ids or subject_ids:
                                object_ids = [i[0] for i in object_ids]
                                subject_ids = [i[0] for i in subject_ids]
                                objects = Entity.query.filter(Entity.id.in_(object_ids), Entity.valid == 1).all()
                                subjects = Entity.query.filter(Entity.id.in_(subject_ids), Entity.valid == 1).all()
                                if objects or subjects:
                                    for object in objects:
                                        doc_mark_entity = DocMarkEntity.query.filter_by(entity_id=object.id, doc_id= doc_id,
                                                                                        valid=1).first()
                                        if doc_mark_entity:
                                            object_insert_ids.append(doc_mark_entity.id)
                                    for subject in subjects:
                                        doc_mark_entity = DocMarkEntity.query.filter_by(entity_id=subject.id, doc_id= doc_id,
                                                                                        valid=1).first()
                                        if doc_mark_entity:
                                            subject_insert_ids.append(doc_mark_entity.id)
                                    if event_time:
                                        times = DocMarkTimeTag.query.filter(DocMarkTimeTag.id.in_(event_time)).all()
                                        if times:
                                            for time_tag in times:
                                                time_tag_insert_ids.append(time_tag.id)
                                            doc_mark_event = DocMarkEvent(event_id=event_id, event_desc=event_desc,
                                                                          event_subject=subject_insert_ids,
                                                                          event_predicate=event_predicate,
                                                                          event_object=object_insert_ids,
                                                                          event_time=time_tag_insert_ids,
                                                                          event_address=place_insert_ids,
                                                                          event_why=event_why,
                                                                          event_result=event_result,
                                                                          event_conduct=event_conduct,
                                                                          event_talk=event_talk, event_how=event_how,
                                                                          doc_id=doc_id,
                                                                          customer_id=customer_id, parent_id=parent_id,
                                                                          title=title,
                                                                          event_class_id=event_class_id,
                                                                          event_type_id=event_type_id,
                                                                          create_by=create_by, create_time=create_time,
                                                                          update_by=update_by, update_time=update_time,
                                                                          add_time=add_time,
                                                                          valid=1)
                                            db.session.add(doc_mark_event)
                                            db.session.commit()
                                            res = success_res(data={"id": doc_mark_event.id})
                                        else:
                                            res = fail_res(msg="doc_mark_time_tag中部分不含有该时间，事件插入失败！")
                                    else:
                                        res = fail_res(msg="事件时间不能为空,事件插入失败！")
                                else:
                                    res = fail_res(msg="实体库中不含有该实体,事件插入失败！")
                            else:
                                res = fail_res(msg="doc_mark_entity中不存在该实体,事件插入失败！")
                        else:
                            res = fail_res(msg="主语和宾语不能同时为空,事件插入失败！")
                    else:
                        res = fail_res(msg="地名库中不含有该地点,事件插入失败！")
                else:
                    res = fail_res(msg="doc_mark_place中不存在该地点,事件插入失败！")
            else:
                res = fail_res(msg="事件地点不能为空,事件插入失败！")

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
                    time_range_time_tags = DocMarkTimeTag.query.filter_by(time_type=2, valid=1).all()
                    # 取出与该时间段有交集的事件
                    for time_range_time_tag in time_range_time_tags:
                        if not (end_time < time_range_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S') or
                                start_time > time_range_time_tag.format_date_end.strftime('%Y-%m-%d %H:%M:%S')):
                            time_tag_ids.append(str(time_range_time_tag.uuid))
                    # 取出时间点在该时间段内的事件
                    date_time_tags = DocMarkTimeTag.query.filter_by(time_type=1, valid=1).all()
                    for date_time_tag in date_time_tags:
                        if start_time < date_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S') < end_time:
                            time_tag_ids.append(str(date_time_tag.uuid))
                print(time_tag_ids)

        places = request.json.get('places', {})
        doc_mark_place_ids = []
        if places.get("place_type", False):
            place_type = places.get("place_type", "")
            place_value = places.get("value", None)
            if place_type == "place":
                place = place_value
                entity = Entity.query.filter_by(name=place, category_uuid="87d323a1-b233-4a82-9883-981da29d7b13", valid=1).first()
                if entity:
                    doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=entity.uuid, valid=1).all() # multi
                    doc_mark_place_ids = [str(i.uuid) for i in doc_mark_places]

            elif place_type == "degrees":
                degrees = place_value
                if degrees.get("lon", None) and degrees.get("lat", None):
                    lon = degrees["lon"]
                    lat = degrees["lat"]
                    if lon.get("degrees",0) and lon.get("direction", 0) and lon.get("distance", 0) and lat.get("degrees",0) and lat.get("direction", 0) and lat.get("distance", 0):
                        lon = dfm_convert(lon.get("degrees"), lon.get("direction"), lon.get("distance", 0))
                        lat = dfm_convert(lat.get("degrees"), lat.get("direction"), lat.get("distance", 0))
                        entity = Entity.query.filter_by(longitude=lon, latitude=lat, category_uuid="87d323a1-b233-4a82-9883-981da29d7b13", valid=1).first()

                        if entity:
                            doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=entity.uuid, valid=1).all()
                            doc_mark_place_ids = [str(i.uuid) for i in doc_mark_places]

            elif place_type == 'location':
                location = place_value
                if location.get("lon", None) and location.get("lat", None):
                    lon = location["lon"]
                    lat = location["lat"]
                    entity = Entity.query.filter_by(longitude=lon, latitude=lat, category_uuid="87d323a1-b233-4a82-9883-981da29d7b13", valid=1).first()
                    if entity:
                        doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=entity.uuid, valid=1).all()
                        doc_mark_place_ids = [str(i.uuid) for i in doc_mark_places]

        object = request.json.get("object", {})
        doc_mark_entity_ids = []
        if object.get("category_uuid", "") and object.get("entity", ""):
            category_uuid = object["category_uuid"]
            entity = object["entity"]
            entity_db = Entity.query.filter_by(category_uuid=category_uuid, name=entity, valid=1).first()
            if entity_db:
                doc_mark_entities = DocMarkEntity.query.filter_by(entity_uuid=entity_db.uuid, valid=1).all()
                doc_mark_entity_ids = [str(i.uuid) for i in doc_mark_entities]
                print(doc_mark_entity_ids)

        event = request.json.get("event", {})
        title = request.json.get("title", "")

        conditions = [DocMarkEvent.valid == 1]
        condition_time = []
        condition_place = []
        condition_object = []
        if time_tag_ids:
            for time_tag_id in time_tag_ids:
                condition_time.append(DocMarkEvent.event_time_uuid.op('@>')([time_tag_id]))
            condition_time = tuple(condition_time)

        if doc_mark_place_ids:
            for doc_mark_place_id in doc_mark_place_ids:
                condition_place.append(DocMarkEvent.event_address_uuid.op('@>')([doc_mark_place_id]))
            condition_place = tuple(condition_place)

        if doc_mark_entity_ids:
            for doc_mark_entity_id in doc_mark_entity_ids:
                condition_object.append(or_(DocMarkEvent.event_subject_uuid.op('@>')([doc_mark_entity_id]), DocMarkEvent.event_object_uuid.op('@>')([doc_mark_entity_id])))
            condition_object = tuple(condition_object)

        if event.get("event_class", ""):
            conditions.append(DocMarkEvent.event_class_uuid == event.get("event_class"))
        if event.get("event_type", ""):
            conditions.append(DocMarkEvent.event_type_uuid == event.get("event_type"))
        if title:
            conditions.append(DocMarkEvent.title.contains(title))
        conditions = tuple(conditions)
        doc_mark_events = DocMarkEvent.query.filter(and_(*conditions), or_(*condition_time), or_(*condition_place),
                                                    or_(*condition_object)).order_by(
            DocMarkEvent.create_time.desc()).all()
        event_list = []
        event_dict = {}
        for doc_mark_event in doc_mark_events:
            event_id = doc_mark_event.uuid
            datetime = []
            doc_mark_time_tag = DocMarkTimeTag.query.filter(DocMarkTimeTag.uuid.in_(doc_mark_event.event_time_uuid),
                                                            DocMarkTimeTag.time_type.in_([1, 2]),
                                                            DocMarkTimeTag.valid == 1).first()
            if doc_mark_time_tag:
                if doc_mark_time_tag.time_type == 1:
                    datetime.append(doc_mark_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S'))
                if doc_mark_time_tag.time_type == 2:
                    datetime.append(doc_mark_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S'))
                    datetime.append(doc_mark_time_tag.format_date_end.strftime('%Y-%m-%d %H:%M:%S'))

            place = []
            for doc_mark_place_id in doc_mark_event.event_address_uuid:
                temp = {}
                doc_mark_place = DocMarkPlace.query.filter_by(uuid=doc_mark_place_id, valid=1).first()
                if doc_mark_place:
                    temp["word"] = doc_mark_place.word
                    temp["place_id"] = doc_mark_place.place_uuid
                    entity = Entity.query.filter_by(uuid=doc_mark_place.place_uuid, valid=1).first()
                    if entity:
                        temp["place_lon"] = entity.longitude
                        temp["place_lat"] = entity.latitude
                        place.append(temp)

            title = doc_mark_event.title
            subject_object = doc_mark_event.event_subject_uuid
            if doc_mark_event.event_object_uuid:
                subject_object.extend(doc_mark_event.event_object_uuid)
            object = []
            if subject_object:
                for entity_uuid in subject_object:
                    doc_mark_entity = DocMarkEntity.query.filter_by(uuid=entity_uuid, valid=1).first()
                    if doc_mark_entity:
                        object.append(doc_mark_entity.word)

            timeline_key = ",".join([str(i) for i in sorted(object)])
            event = {
                "event_id": event_id,
                "datetime": datetime,
                "place": place,
                "title": title,
                "object": object
            }

            if event_dict.get(timeline_key, []):
                event_dict[timeline_key].append(event)
            else:
                event_dict[timeline_key] = [event]

        event_list = [sorted(i, key=lambda x: x.get('datetime', '')) for i in event_dict.values()]
        res = success_res(data=event_list)

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


def dfm_convert(du, fen, miao):
    out_location = int(du) + int(fen) / 60 + int(miao) / 3600
    return float(format(out_location, ".4f"))


@blue_print.route('/get_during_time_event', methods=['POST'])
# @swag_from(get_doc_events_dict)
def get_during_time_event():
    try:
        start_date = request.json.get('start_date', '1900-01-01')
        end_date = request.json.get('end_date', '9999-01-01')
        doc_mark_time_tags = DocMarkTimeTag.query.filter(
            and_(DocMarkTimeTag.valid == 1, DocMarkTimeTag.time_type.in_(['1', '2']))).all()
        doc_mark_time_tag_ids = []

        for doc_mark_time_tag in doc_mark_time_tags:
            if doc_mark_time_tag.time_type == 1 and doc_mark_time_tag.format_date.strftime(
                    '%Y-%m-%d %H:%M:%S') >= start_date:
                doc_mark_time_tag_ids.append(doc_mark_time_tag.id)

            elif doc_mark_time_tag.time_type == 2 and not (
                    end_date < doc_mark_time_tag.format_date.strftime(
                '%Y-%m-%d %H:%M:%S') or start_date > doc_mark_time_tag.format_date_end.strftime('%Y-%m-%d %H:%M:%S')):
                doc_mark_time_tag_ids.append(doc_mark_time_tag.id)
            else:
                pass
        doc_mark_time_tag_ids_set = set(doc_mark_time_tag_ids)
        doc_mark_events = DocMarkEvent.query.filter(DocMarkEvent.valid == 1).all()
        event_list = []
        # event_dict = {}
        for doc_mark_event in doc_mark_events:
            if set(doc_mark_event.event_time) & doc_mark_time_tag_ids_set:
                time_id = list(set(doc_mark_event.event_time) & doc_mark_time_tag_ids_set)[0]
                datetime = [DocMarkTimeTag.query.filter_by(id=time_id, valid=1).first().format_date]
                try:
                    datetime.append(DocMarkTimeTag.query.filter_by(id=time_id, valid=1).first().format_date_end)
                except:
                    pass
                event_id = doc_mark_event.id
                place = []
                for item in doc_mark_event.event_address:
                    temp = {}
                    doc_mark_place = DocMarkPlace.query.filter_by(id=item, valid=1).first()
                    if doc_mark_place:
                        temp["word"] = doc_mark_place.word if doc_mark_place else None
                        temp["place_id"] = doc_mark_place.place_id
                        entity = Entity.query.filter_by(id=doc_mark_place.place_id, valid=1).first()
                        temp["place_lon"] = entity.longitude
                        temp["place_lat"] = entity.latitude
                        place.append(temp)
                title = doc_mark_event.title
                subject_object = doc_mark_event.event_subject
                if doc_mark_event.event_object:
                    subject_object.extend(doc_mark_event.event_object)
                object = []
                for item in subject_object:
                    doc_mark_entity = DocMarkEntity.query.filter_by(id=item, valid=1).first()
                    if doc_mark_entity:
                        object.append(doc_mark_entity.word)
                # timeline_key = ",".join([str(i) for i in sorted(object)])
                event = {
                    "event_id": event_id,
                    "datetime": datetime,
                    "place": place,
                    "title": title,
                    "object": object
                }
                event_list.append(event)

                # if event_dict.get(timeline_key, []):
                #     event_dict[timeline_key].append(event)
                # else:
                #     event_dict[timeline_key] = [event]
                event_list = sorted(event_list, key=lambda x: x.get('datetime', '')[0])

        res = event_list
    except Exception as e:
        print(str(e))
        res =[]
    return jsonify(res)


@blue_print.route('/get_during_time_event_by_entities', methods=['POST'])
# @swag_from(get_doc_events_dict)
def get_during_time_event_by_entities():
    try:
        start_date = request.json.get('start_date', '1900-01-01')
        end_date = request.json.get('end_date', '9999-01-01')
        doc_mark_time_tags = DocMarkTimeTag.query.filter(
            and_(DocMarkTimeTag.valid == 1, DocMarkTimeTag.time_type.in_(['1', '2']))).all()
        doc_mark_time_tag_ids = []

        for doc_mark_time_tag in doc_mark_time_tags:
            if doc_mark_time_tag.time_type == 1 and doc_mark_time_tag.format_date.strftime(
                    '%Y-%m-%d %H:%M:%S') >= start_date:
                doc_mark_time_tag_ids.append(doc_mark_time_tag.id)

            elif doc_mark_time_tag.time_type == 2 and not (
                    end_date < doc_mark_time_tag.format_date.strftime(
                '%Y-%m-%d %H:%M:%S') or start_date > doc_mark_time_tag.format_date_end.strftime('%Y-%m-%d %H:%M:%S')):
                doc_mark_time_tag_ids.append(doc_mark_time_tag.id)
            else:
                pass
        doc_mark_time_tag_ids_set = set(doc_mark_time_tag_ids)
        doc_mark_events = DocMarkEvent.query.filter(DocMarkEvent.valid == 1).all()
        event_dict = {}
        for doc_mark_event in doc_mark_events:
            if set(doc_mark_event.event_time) & doc_mark_time_tag_ids_set:
                time_id = list(set(doc_mark_event.event_time) & doc_mark_time_tag_ids_set)[0]
                datetime = [DocMarkTimeTag.query.filter_by(id=time_id, valid=1).first().format_date]
                try:
                    datetime.append(DocMarkTimeTag.query.filter_by(id=time_id, valid=1).first().format_date_end)
                except:
                    pass
                event_id = doc_mark_event.id
                place = []
                for item in doc_mark_event.event_address:
                    temp = {}
                    doc_mark_place = DocMarkPlace.query.filter_by(id=item, valid=1).first()
                    if doc_mark_place:
                        temp["word"] = doc_mark_place.word if doc_mark_place else None
                        temp["place_id"] = doc_mark_place.place_id
                        entity = Entity.query.filter_by(id=doc_mark_place.place_id, valid=1).first()
                        temp["place_lon"] = entity.longitude
                        temp["place_lat"] = entity.latitude
                        place.append(temp)
                title = doc_mark_event.title
                subject_object = doc_mark_event.event_subject
                if doc_mark_event.event_object:
                    subject_object.extend(doc_mark_event.event_object)
                object = []
                for item in subject_object:
                    doc_mark_entity = DocMarkEntity.query.filter_by(id=item, valid=1).first()
                    if doc_mark_entity:
                        object.append(doc_mark_entity.word)

                timeline_key = ",".join([str(i) for i in sorted(object)])
                event = {
                    "event_id": event_id,
                    "datetime": datetime,
                    "place": place,
                    "title": title,
                    "object": object
                }

                if event_dict.get(timeline_key, []):
                    event_dict[timeline_key].append(event)
                else:
                    event_dict[timeline_key] = [event]

        event_list = [sorted(i, key=lambda x: x.get('datetime', '')[0]) for i in event_dict.values()]
        res = event_list
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


# pg数据同步
@blue_print.route('/transform_jsonb_data', methods=['POST'])
def transform_jsonb_data():
    try:
        doc_mark_events = DocMarkEvent.query.filter_by(valid=1).all()
        for doc_mark_event in doc_mark_events:
            event_subject = doc_mark_event.event_subject
            if isinstance(event_subject, list):
                event_subject_list = []
                for id in event_subject:
                    if DocMarkEntity.query.filter_by(id=id, valid=1).first():
                        event_subject_list.append(str(DocMarkEntity.query.filter_by(id=id, valid=1).first().uuid))
                    print(event_subject_list)
                if event_subject_list:
                    doc_mark_event.event_subject_uuid = event_subject_list


            event_object = doc_mark_event.event_object
            if isinstance(event_object, list):
                event_object_list = []
                for id in event_object:
                    if DocMarkEntity.query.filter_by(id=id, valid=1).first():
                        event_object_list.append(str(DocMarkEntity.query.filter_by(id=id, valid=1).first().uuid))
                if event_object_list:
                    doc_mark_event.event_object_uuid = event_object_list

            event_address = doc_mark_event.event_address
            event_address_list = []
            if isinstance(event_address, list):
                for id in event_address:
                    if DocMarkEntity.query.filter_by(id=id, valid=1).first():
                        event_address_list.append(str(DocMarkEntity.query.filter_by(id=id, valid=1).first().uuid))
                if event_address_list:
                    doc_mark_event.event_address_uuid = event_address_list

            event_time = doc_mark_event.event_time
            event_time_list = []
            if isinstance(event_time, list):
                for id in event_time:
                    if DocMarkTimeTag.query.filter_by(id=id, valid=1).first():
                        event_time_list.append(str(DocMarkTimeTag.query.filter_by(id=id, valid=1).first().uuid))
                if event_time_list:
                    doc_mark_event.event_time_uuid = event_time_list

        res = success_res()
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


