# -*- coding: UTF-8 -*-
import datetime
import time

from flask import jsonify, request
from sqlalchemy import or_, and_
from sqlalchemy.dialects.postgresql import Any
import uuid
from . import api_doc_mark_event as blue_print
from ..models import DocMarkEvent, DocMarkTimeTag, DocMarkEntity, DocMarkPlace, Entity, EventCategory
from .. import db
from .utils import success_res, fail_res
from .document import get_event_list_from_docs
from ..conf import ES_SERVER_IP, ES_SERVER_PORT, PLACE_BASE_NAME


# doc_mark_event表中删除了parent_name字段，保留了parent_id字段

# 按id查询
@blue_print.route('/get_doc_mark_event_by_id', methods=['GET'])
def get_doc_mark_event_by_id():
    try:
        uuid = request.args.get("uuid",'')
        doc_mark_event = DocMarkEvent.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_event:
            res = success_res({
                "uuid": doc_mark_event.uuid,
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
                "doc_uuid": doc_mark_event.doc_uuid,
                "customer_uuid": doc_mark_event.customer_uuid,
                "parent_uuid": doc_mark_event.parent_uuid,
                "title": doc_mark_event.title,
                "event_class_uuid": doc_mark_event.event_class_uuid,
                "event_type_uuid": doc_mark_event.event_type_uuid,
                "create_by_uuid": doc_mark_event.create_by_uuid,
                "create_time": doc_mark_event.create_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_event.create_time else None,
                "update_by_uuid": doc_mark_event.update_by_uuid,
                "update_time": doc_mark_event.update_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_event.update_time else None,
                "add_time": doc_mark_event.add_time.strftime("%Y-%m-%d %H:%M:%S") if doc_mark_event.add_time else None
            })
        else:
            res = fail_res(msg="事件数据不存在")

    except Exception as e:
        print(str(e))
        res = fail_res({
            "uuid": '',
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
            "doc_uuid": "",
            "customer_uuid": "",
            "parent_uuid": "",
            "title": "",
            "event_class_uuid": "",
            "event_type_uuid": "",
            "create_by_uuid": "",
            "create_time": None,
            "update_by_uuid": "",
            "update_time": None,
            "add_time": None
        })

    return jsonify(res)


# 按doc_id查询
@blue_print.route('/get_doc_mark_event_by_doc_id', methods=['GET'])
def get_doc_mark_event_by_doc_id():
    try:
        doc_uuid = request.args.get("doc_uuid",'')
        doc_mark_event_list = DocMarkEvent.query.filter_by(doc_uuid=doc_uuid, valid=1).all()
        res = success_res(data=[{
            "uuid": i.uuid,
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
            "doc_uuid": i.doc_uuid,
            "customer_uuid": i.customer_uuid,
            "parent_uuid": i.parent_uuid,
            "title": i.title,
            "event_class_uuid": i.event_class_uuid,
            "event_type_uuid": i.event_type_uuid,
            "create_by_uuid": i.create_by_uuid,
            "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
            "update_by_uuid": i.update_by_uuid,
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
        doc_uuid = request.json.get("doc_uuid", None)
        customer_uuid = request.json.get("customer_uuid", None)
        parent_uuid = request.json.get("parent_uuid", None)
        title = request.json.get("title", "")
        event_class_uuid = request.json.get("event_class_uuid", None)
        event_type_uuid = request.json.get("event_type_uuid", None)
        create_by_uuid = request.json.get("create_by_uuid", None)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_by_uuid = request.json.get("update_by_uuid", None)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        add_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        place_insert_ids = []
        object_insert_ids = []
        subject_insert_ids = []
        time_tag_insert_ids = []

        if event_address:
            place_ids = DocMarkPlace.query.with_entities(DocMarkPlace.place_uuid).filter(
                DocMarkPlace.uuid.in_(event_address)).all()
            if place_ids:
                place_ids = [i[0] for i in place_ids]
                places = Entity.query.filter(Entity.uuid.in_(place_ids), Entity.valid == 1).all()
                if places:
                    for place in places:
                        doc_mark_place = DocMarkPlace.query.filter_by(place_uuid=place.uuid, valid=1).first()
                        if doc_mark_place:
                            place_insert_ids.append(str(doc_mark_place.uuid))
                    objects, subjects = [], []
                    if event_object or event_subject:
                        # object_id_list = event_object
                        # if event_subject:
                        #     object_id_list.extend(event_subject)
                        object_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_uuid).filter(
                            DocMarkEntity.uuid.in_(event_object)).all()
                        subject_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_uuid).filter(
                            DocMarkEntity.uuid.in_(event_subject)).all()
                        if object_ids or subject_ids:
                            object_ids = [str(i[0]) for i in object_ids]
                            subject_ids = [str(i[0]) for i in subject_ids]
                            objects = Entity.query.filter(Entity.uuid.in_(object_ids), Entity.valid == 1).all()
                            subjects = Entity.query.filter(Entity.uuid.in_(subject_ids), Entity.valid == 1).all()
                            if objects or subjects:
                                for object in objects:
                                    doc_mark_entity = DocMarkEntity.query.filter_by(entity_uuid=object.uuid, doc_uuid=doc_uuid,
                                                                                    valid=1).first()
                                    if doc_mark_entity:
                                        object_insert_ids.append(str(doc_mark_entity.uuid))
                                for subject in subjects:
                                    print(subject.uuid)
                                    doc_mark_entity = DocMarkEntity.query.filter_by(entity_uuid=subject.uuid,
                                                                                    doc_uuid=doc_uuid, valid=1).first()
                                    if doc_mark_entity:
                                        subject_insert_ids.append(str(doc_mark_entity.uuid))
                                if event_time:
                                    times = DocMarkTimeTag.query.filter(DocMarkTimeTag.uuid.in_(event_time)).all()
                                    if times:
                                        for time_tag in times:
                                            time_tag_insert_ids.append(str(time_tag.uuid))
                                        doc_mark_event = DocMarkEvent(uuid=uuid.uuid1(),event_id=event_id, event_desc=event_desc,
                                                                      event_subject=subject_insert_ids,
                                                                      event_predicate=event_predicate,
                                                                      event_object=object_insert_ids,
                                                                      event_time=time_tag_insert_ids,
                                                                      event_address=place_insert_ids,
                                                                      event_why=event_why,
                                                                      event_result=event_result,
                                                                      event_conduct=event_conduct,
                                                                      event_talk=event_talk, event_how=event_how,
                                                                      doc_uuid=doc_uuid,
                                                                      customer_uuid=customer_uuid, parent_uuid=parent_uuid,
                                                                      title=title,
                                                                      event_class_uuid=event_class_uuid,
                                                                      event_type_uuid=event_type_uuid,
                                                                      create_by_uuid=create_by_uuid, create_time=create_time,
                                                                      update_by_uuid=update_by_uuid, update_time=update_time,
                                                                      add_time=add_time,
                                                                      valid=1)
                                        db.session.add(doc_mark_event)
                                        db.session.commit()
                                        res = success_res(data={"uuid": doc_mark_event.uuid})
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
        uuid = request.json.get("uuid", None)
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
        doc_uuid = request.json.get("doc_uuid", None)
        customer_uuid = request.json.get("customer_uuid", None)
        parent_uuid = request.json.get("parent_uuid", None)
        title = request.json.get("title", "")
        event_class_uuid = request.json.get("event_class_uuid", None)
        event_type_uuid = request.json.get("event_type_uuid", None)
        create_by_uuid = request.json.get("create_by_uuid", None)
        create_time = request.json.get("create_time", None)
        update_by_uuid = request.json.get("update_by_uuid", None)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        add_time = request.json.get("add_time", None)

        doc_mark_event = DocMarkEvent.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_event:
            if event_id:
                doc_mark_event.event_id = event_id
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
            if doc_uuid:
                doc_mark_event.doc_uuid = doc_uuid
            if customer_uuid:
                doc_mark_event.customer_uuid = customer_uuid
            if parent_uuid:
                doc_mark_event.parent_uuid = parent_uuid
            if title:
                doc_mark_event.title = title
            if event_class_uuid:
                doc_mark_event.event_class_uuid = event_class_uuid
            if event_type_uuid:
                doc_mark_event.event_type_uuid = event_type_uuid
            if create_by_uuid:
                doc_mark_event.create_by_uuid = create_by_uuid
            if create_time:
                doc_mark_event.create_time = create_time
            if update_by_uuid:
                doc_mark_event.update_by_uuid = update_by_uuid
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
        uuid = request.json.get("uuid", 0)
        doc_mark_event = DocMarkEvent.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_event:
            doc_mark_event.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="事件数据不存在")

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
        event_time_tag_ids = DocMarkTimeTag.query.with_entities(DocMarkTimeTag.uuid).filter(and_(*conditions)).all()
        event_time_tag_ids = [i[0] for i in event_time_tag_ids]

        # 标记主宾语条件
        conditions = [DocMarkEntity.word.like("%{}%".format(search)),
                      DocMarkEntity.valid == 1]
        conditions = tuple(conditions)
        event_entity_ids = DocMarkEntity.query.with_entities(DocMarkEntity.uuid).filter(and_(*conditions)).all()
        event_entity_ids = [i[0] for i in event_entity_ids]

        # 标记地点条件
        conditions = [DocMarkPlace.word.like("%{}%".format(search)),
                      DocMarkPlace.valid == 1]
        conditions = tuple(conditions)
        event_place_ids = DocMarkPlace.query.with_entities(DocMarkPlace.uuid).filter(and_(*conditions)).all()
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
        doc_uuids = request.json.get('doc_uuids', [])
        start_date = request.json.get('start_date', '1900-01-01')
        end_date = request.json.get('end_date', '9999-12-31')
        res = get_event_list_from_docs(doc_uuids, start_date, end_date)
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


@blue_print.route('/get_doc_events_to_earth', methods=['GET'])
# @swag_from(get_doc_events_dict)
def get_doc_events_to_earth():
    try:
        doc_uuid = request.args.get("doc_uuid", '')
        doc_mark_event_list = DocMarkEvent.query.filter_by(doc_uuid=doc_uuid, valid=1).all()

        result = []
        for doc_mark_event in doc_mark_event_list:
            places = doc_mark_event.get_places()
            place_list = [{
                "word": i.word,
                "place_uuid": i.place_uuid,
                "place_lon": i.place_lon,
                "place_lat": i.place_lat
            } for i in places if i.place_lon and i.place_lat]
            if place_list:
                datetime = ""
                if doc_mark_event.event_time:
                    time_tag = DocMarkTimeTag.query.filter(DocMarkTimeTag.uuid.in_(doc_mark_event.event_time),
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
                # entity = Entity.query.filter_by(name=place, category_uuid="87d323a1-b233-4a82-9883-981da29d7b13", valid=1).first()
                entities = Entity.query.filter_by(name=place, valid=1).all()
                for entity in entities:
                    if entity.category_name() == PLACE_BASE_NAME:
                        doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=entity.uuid, valid=1).all() # multi
                        doc_mark_place_ids = [str(i.uuid) for i in doc_mark_places]
                        break

            elif place_type == "degrees":
                degrees = place_value
                if degrees.get("lon", None) and degrees.get("lat", None):
                    lon = degrees["lon"]
                    lat = degrees["lat"]
                    if lon.get("degrees",0) and lon.get("direction", 0) and lon.get("distance", 0) and lat.get("degrees",0) and lat.get("direction", 0) and lat.get("distance", 0):
                        lon = dfm_convert(lon.get("degrees"), lon.get("direction"), lon.get("distance", 0))
                        lat = dfm_convert(lat.get("degrees"), lat.get("direction"), lat.get("distance", 0))
                        # entity = Entity.query.filter_by(longitude=lon, latitude=lat, category_uuid="87d323a1-b233-4a82-9883-981da29d7b13", valid=1).first()
                        entities = Entity.query.filter_by(longitude=lon, latitude=lat, valid=1).all()
                        for entity in entities:
                            if entity.category_name() == PLACE_BASE_NAME:
                                doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=entity.uuid, valid=1).all()
                                doc_mark_place_ids = [str(i.uuid) for i in doc_mark_places]
                                break

            elif place_type == 'location':
                location = place_value
                if location.get("lon", None) and location.get("lat", None):
                    lon = location["lon"]
                    lat = location["lat"]
                    # entity = Entity.query.filter_by(longitude=lon, latitude=lat, category_uuid="87d323a1-b233-4a82-9883-981da29d7b13", valid=1).first()
                    entities = Entity.query.filter_by(longitude=lon, latitude=lat, valid=1).all()
                    for entity in entities:
                        if entity.category_name() == PLACE_BASE_NAME:
                            doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=entity.uuid, valid=1).all()
                            doc_mark_place_ids = [str(i.uuid) for i in doc_mark_places]

        object_list = request.json.get("object", [])
        doc_mark_entity_ids = []
        for object in object_list:
            if object.get("category_uuid", "") and object.get("entity", ""):
                category_uuid = object["category_uuid"]
                entity = object["entity"]
                entity_db = Entity.query.filter_by(category_uuid=category_uuid, name=entity, valid=1).first()
                if entity_db:
                    doc_mark_entities = DocMarkEntity.query.filter_by(entity_uuid=entity_db.uuid, valid=1).all()
                    doc_mark_entity_ids = [str(i.uuid) for i in doc_mark_entities]
                    print(doc_mark_entity_ids)

            if not object.get("category_uuid", None) and object.get("entity", ""):
                entity = object["entity"]
                entity_db = Entity.query.filter_by(name=entity, valid=1).first()
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
                condition_time.append(DocMarkEvent.event_time.op('@>')([time_tag_id]))
            condition_time = tuple(condition_time)

        if doc_mark_place_ids:
            for doc_mark_place_id in doc_mark_place_ids:
                condition_place.append(DocMarkEvent.event_address.op('@>')([doc_mark_place_id]))
            condition_place = tuple(condition_place)

        if doc_mark_entity_ids:
            for doc_mark_entity_id in doc_mark_entity_ids:
                condition_object.append(or_(DocMarkEvent.event_subject.op('@>')([doc_mark_entity_id]), DocMarkEvent.event_object.op('@>')([doc_mark_entity_id])))
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
            doc_mark_time_tag = DocMarkTimeTag.query.filter(DocMarkTimeTag.uuid.in_(doc_mark_event.event_time),
                                                            DocMarkTimeTag.time_type.in_([1, 2]),
                                                            DocMarkTimeTag.valid == 1).first()
            if doc_mark_time_tag:
                if doc_mark_time_tag.time_type == 1:
                    datetime.append(doc_mark_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S'))
                if doc_mark_time_tag.time_type == 2:
                    datetime.append(doc_mark_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S'))
                    datetime.append(doc_mark_time_tag.format_date_end.strftime('%Y-%m-%d %H:%M:%S'))

            place = []
            for doc_mark_place_id in doc_mark_event.event_address:
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
            subject_object = doc_mark_event.event_subject
            if doc_mark_event.event_object:
                subject_object.extend(doc_mark_event.event_object)
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
            event_list.append(event)
            if event_dict.get(timeline_key, []):
                event_dict[timeline_key].append(event)
            else:
                event_dict[timeline_key] = [event]
        event_list_entity = [sorted(i, key=lambda x: x.get('datetime', '')) for i in event_dict.values()]
        res = success_res(data={"event_list": event_list,"event_list_entity": event_list_entity})
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
                    '%Y-%m-%d %H:%M:%S') >= start_date and doc_mark_time_tag.format_date.strftime(
                '%Y-%m-%d %H:%M:%S') <= end_date:
                doc_mark_time_tag_ids.append(str(doc_mark_time_tag.uuid))

            elif doc_mark_time_tag.time_type == 2 and not (
                    end_date < doc_mark_time_tag.format_date.strftime(
                '%Y-%m-%d %H:%M:%S') or start_date > doc_mark_time_tag.format_date_end.strftime('%Y-%m-%d %H:%M:%S')):
                doc_mark_time_tag_ids.append(str(doc_mark_time_tag.uuid))
            else:
                pass
        doc_mark_time_tag_ids_set = set(doc_mark_time_tag_ids)
        doc_mark_events = DocMarkEvent.query.filter(DocMarkEvent.valid == 1, DocMarkEvent.event_time!=None,
                                                    DocMarkEvent.event_address!=None).all()
        event_list = []
        # event_dict = {}
        for doc_mark_event in doc_mark_events:
            if set(doc_mark_event.event_time) & doc_mark_time_tag_ids_set:
                time_id = list(set(doc_mark_event.event_time) & doc_mark_time_tag_ids_set)[0]
                datetime = [DocMarkTimeTag.query.filter_by(uuid=time_id, valid=1).first().format_date.strftime('%Y-%m-%d %H:%M:%S')]
                try:
                    datetime.append(DocMarkTimeTag.query.filter_by(uuid=time_id, valid=1).first().format_date_end.strftime('%Y-%m-%d %H:%M:%S'))
                except:
                    pass
                event_id = doc_mark_event.uuid
                place = []
                for item in doc_mark_event.event_address:
                    temp = {}
                    doc_mark_place = DocMarkPlace.query.filter_by(uuid=item, valid=1).first()
                    if doc_mark_place:
                        temp["word"] = doc_mark_place.word if doc_mark_place else None
                        temp["place_id"] = doc_mark_place.place_uuid
                        entity = Entity.query.filter_by(uuid=doc_mark_place.place_uuid, valid=1).first()
                        if entity:
                            temp["place_lon"] = entity.longitude
                            temp["place_lat"] = entity.latitude
                        place.append(temp)
                title = doc_mark_event.title
                subject_object = doc_mark_event.event_subject
                if doc_mark_event.event_object:
                    subject_object.extend(doc_mark_event.event_object)
                object = []
                for item in subject_object:
                    doc_mark_entity = DocMarkEntity.query.filter_by(uuid=item, valid=1).first()
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
                    '%Y-%m-%d %H:%M:%S') >= start_date and doc_mark_time_tag.format_date.strftime(
                    '%Y-%m-%d %H:%M:%S') <= end_date:
                doc_mark_time_tag_ids.append(str(doc_mark_time_tag.uuid))

            elif doc_mark_time_tag.time_type == 2 and not (
                    end_date < doc_mark_time_tag.format_date.strftime(
                '%Y-%m-%d %H:%M:%S') or start_date > doc_mark_time_tag.format_date_end.strftime('%Y-%m-%d %H:%M:%S')):
                doc_mark_time_tag_ids.append(str(doc_mark_time_tag.uuid))
            else:
                pass
        doc_mark_time_tag_ids_set = set(doc_mark_time_tag_ids)
        doc_mark_events = DocMarkEvent.query.filter(DocMarkEvent.valid == 1, DocMarkEvent.event_address!=None,
                                                    DocMarkEvent.event_time!=None).all()
        event_dict = {}
        for doc_mark_event in doc_mark_events:
            if set(doc_mark_event.event_time) & doc_mark_time_tag_ids_set:
                time_id = list(set(doc_mark_event.event_time) & doc_mark_time_tag_ids_set)[0]
                datetime = [DocMarkTimeTag.query.filter_by(uuid=time_id, valid=1).first().format_date.strftime('%Y-%m-%d %H:%M:%S')]
                try:
                    datetime.append(DocMarkTimeTag.query.filter_by(uuid=time_id, valid=1).first().format_date_end.strftime('%Y-%m-%d %H:%M:%S'))
                except:
                    pass
                event_id = doc_mark_event.uuid
                place = []
                for item in doc_mark_event.event_address:
                    temp = {}
                    doc_mark_place = DocMarkPlace.query.filter_by(uuid=item, valid=1).first()
                    if doc_mark_place:
                        temp["word"] = doc_mark_place.word if doc_mark_place else None
                        temp["place_id"] = doc_mark_place.place_uuid
                        entity = Entity.query.filter_by(uuid=doc_mark_place.place_uuid, valid=1).first()
                        if entity:
                            temp["place_lon"] = entity.longitude
                            temp["place_lat"] = entity.latitude
                        place.append(temp)
                title = doc_mark_event.title
                subject_object = doc_mark_event.event_subject
                if doc_mark_event.event_object:
                    subject_object.extend(doc_mark_event.event_object)
                object = []
                for item in subject_object:
                    doc_mark_entity = DocMarkEntity.query.filter_by(uuid=item, valid=1).first()
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
                    if DocMarkEntity.query.filter_by(uuid=id, valid=1).first():
                        event_subject_list.append(str(DocMarkEntity.query.filter_by(uuid=id, valid=1).first().uuid))
                    print(event_subject_list)
                if event_subject_list:
                    doc_mark_event.event_subject = event_subject_list


            event_object = doc_mark_event.event_object
            if isinstance(event_object, list):
                event_object_list = []
                for id in event_object:
                    if DocMarkEntity.query.filter_by(uuid=id, valid=1).first():
                        event_object_list.append(str(DocMarkEntity.query.filter_by(uuid=id, valid=1).first().uuid))
                if event_object_list:
                    doc_mark_event.event_object = event_object_list

            event_address = doc_mark_event.event_address
            event_address_list = []
            if isinstance(event_address, list):
                for id in event_address:
                    if DocMarkEntity.query.filter_by(uuid=id, valid=1).first():
                        event_address_list.append(str(DocMarkEntity.query.filter_by(uuid=id, valid=1).first().uuid))
                if event_address_list:
                    doc_mark_event.event_address = event_address_list

            event_time = doc_mark_event.event_time
            event_time_list = []
            if isinstance(event_time, list):
                for id in event_time:
                    if DocMarkTimeTag.query.filter_by(uuid=id, valid=1).first():
                        event_time_list.append(str(DocMarkTimeTag.query.filter_by(uuid=id, valid=1).first().uuid))
                if event_time_list:
                    doc_mark_event.event_time = event_time_list

        res = success_res()
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


@blue_print.route('/search_events_by_docId_pagination', methods=['GET'])
def search_events_by_docId_pagination():
    try:
        doc_uuid = request.args.get('uuid', None)
        page_size = request.args.get('page_size', 15)
        cur_page = request.args.get('cur_page', 1)

        pagination = DocMarkEvent.query.filter_by(doc_uuid=doc_uuid, valid=1).paginate(cur_page, page_size, False)
        data = [{
                "uuid": i.uuid,
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
                "doc_uuid": i.doc_uuid,
                "customer_uuid": i.customer_uuid,
                "parent_uuid": i.parent_uuid,
                "title": i.title,
                "event_class_uuid": i.event_class_uuid,
                "event_type_uuid": i.event_type_uuid,
                "create_by_uuid": i.create_by_uuid,
                "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
                "update_by_uuid": i.update_by_uuid,
                "update_time": i.update_time.strftime("%Y-%m-%d %H:%M:%S") if i.update_time else None,
                "add_time": i.add_time.strftime("%Y-%m-%d %H:%M:%S") if i.add_time else None,
                "_source": i._source
            } for i in pagination.items]
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


@blue_print.route('/get_advanced_search_of_events_pagination', methods=['POST'])
def get_advanced_search_of_events_pagination():
    try:
        event_class = request.json.get("event_class_uuid", [])  # 事件类型
        event_category = request.json.get("event_category_uuid", [])   # 具体类型
        start_time = request.json.get("start_time", "")
        end_time = request.json.get("end_time", "")
        title = request.json.get("title", "")
        page_size = request.json.get('page_size', 15)
        cur_page = request.json.get('cur_page', 1)

        time_tag_ids = []
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

        conditions = [DocMarkEvent.valid == 1]
        condition_time = []
        if time_tag_ids:
            for time_tag_id in time_tag_ids:
                condition_time.append(DocMarkEvent.event_time.op('@>')([time_tag_id]))
            condition_time = tuple(condition_time)

        if event_class:
            conditions.append(DocMarkEvent.event_class_uuid.in_(event_class) )
        if event_category:
            conditions.append(DocMarkEvent.event_type_uuid.in_(event_category))

        if title:
            conditions.append(DocMarkEvent.title.contains(title))
        conditions = tuple(conditions)

        pagination = DocMarkEvent.query.filter(and_(*conditions), or_(*condition_time)).order_by(
            DocMarkEvent.create_time.desc()).paginate(cur_page, page_size, False)

        data = [{
            "uuid": i.uuid,
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
            "doc_uuid": i.doc_uuid,
            "customer_uuid": i.customer_uuid,
            "parent_uuid": i.parent_uuid,
            "title": i.title,
            "event_class_uuid": i.event_class_uuid,
            "event_type_uuid": i.event_type_uuid,
            "create_by_uuid": i.create_by_uuid,
            "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
            "update_by_uuid": i.update_by_uuid,
            "update_time": i.update_time.strftime("%Y-%m-%d %H:%M:%S") if i.update_time else None,
            "add_time": i.add_time.strftime("%Y-%m-%d %H:%M:%S") if i.add_time else None,
            "_source": i._source
        } for i in pagination.items]
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


#根据开始时间、结束时间查询事件列表
@blue_print.route('/get_doc_mark_event_by_times', methods=['POST'])
# @swag_from(get_doc_events_dict)
def get_doc_mark_event_by_times():
    try:
        start_date = request.json.get('start_date', '1900-01-01')
        end_date = request.json.get('end_date', '9999-01-01')

        doc_mark_time_tags = DocMarkTimeTag.query.filter(
            and_(DocMarkTimeTag.valid == 1, DocMarkTimeTag.time_type.in_(['1', '2']))).all()
        doc_mark_time_tag_ids = []

        for doc_mark_time_tag in doc_mark_time_tags:
            if doc_mark_time_tag.time_type == 1 and doc_mark_time_tag.format_date.strftime(
                    '%Y-%m-%d %H:%M:%S') >= start_date and doc_mark_time_tag.format_date.strftime(
                '%Y-%m-%d %H:%M:%S') <= end_date:
                doc_mark_time_tag_ids.append(str(doc_mark_time_tag.uuid))

            elif doc_mark_time_tag.time_type == 2 and not (
                    end_date < doc_mark_time_tag.format_date.strftime(
                '%Y-%m-%d %H:%M:%S') or start_date > doc_mark_time_tag.format_date_end.strftime('%Y-%m-%d %H:%M:%S')):
                doc_mark_time_tag_ids.append(str(doc_mark_time_tag.uuid))
            else:
                pass
        doc_mark_time_tag_ids_set = set(doc_mark_time_tag_ids)
        doc_mark_events = DocMarkEvent.query.filter(DocMarkEvent.valid == 1, DocMarkEvent.event_time!=None,
                                                    DocMarkEvent.event_address!=None).all()
        event_list = []
        for i in doc_mark_events:
            if set(i.event_time) & doc_mark_time_tag_ids_set:
                event = {
                    "uuid": i.uuid,
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
                    "doc_uuid": i.doc_uuid,
                    "customer_uuid": i.customer_uuid,
                    "parent_uuid": i.parent_uuid,
                    "title": i.title,
                    "event_class_uuid": i.event_class_uuid,
                    "event_type_uuid": i.event_type_uuid,
                    "create_by_uuid": i.create_by_uuid,
                    "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
                    "update_by_uuid": i.update_by_uuid,
                    "update_time": i.update_time.strftime("%Y-%m-%d %H:%M:%S") if i.update_time else None,
                    "add_time": i.add_time.strftime("%Y-%m-%d %H:%M:%S") if i.add_time else None
                }
                event_list.append(event)
        res=success_res(data=event_list)



    except Exception as e:
        print(str(e))
        res =[]
    return jsonify(res)