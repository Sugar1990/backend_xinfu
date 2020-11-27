# -*- coding: UTF-8 -*-
import json
import time
from flask import jsonify, request
from . import api_event_point as blue_print
from ..models import EventClass, EventPoint, Entity, EventTrack
from ..models import EventCategory
from .. import db
from .utils import success_res, fail_res
import uuid
from sqlalchemy import create_engine, MetaData, Table, or_,and_

@blue_print.route('/add_event_points', methods=['POST'])
def add_event_points():
    try:
        title_uuid = request.json.get('title_uuid', None)
        entity_name = request.json.get('entity_name', '')
        end_time = request.json.get('end_time', '')
        details = request.json.get('details', [])
        _source = request.json.get('_source', "")
        for detail in details:
            entity = Entity.query.filter_by(name=entity_name, valid=1).first()
            if not entity:
                entity = Entity(uuid=uuid.uuid1(), name=entity_name, category_uuid=title_uuid,
                                longitude=detail.get("longitude"), latitude=detail.get("latitude"),
                                create_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                update_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                _source=_source, valid=1)
                db.session.add(entity)
                db.session.commit()
            event_point = EventPoint.query.filter_by(title_uuid=title_uuid, entity_uuid=entity.uuid,
                                                     end_time=end_time, event_name=detail.get("event_name"),
                                                     event_desc=detail.get("event_desc"), valid=1).first()
            if event_point:
                pass
            else:
                event_point = EventPoint(uuid=uuid.uuid1(), title_uuid=title_uuid,
                                         entity_uuid=entity.uuid,
                                         source=detail.get("source"),
                                         event_name=detail.get("event_name"), event_desc=detail.get("event_desc"),
                                         longitude=detail.get("longitude"), latitude=detail.get("latitude"),
                                         event_time=detail.get("event_time"),
                                         create_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                         update_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                         create_by_uuid=detail.get("create_by_uuid"),
                                         update_by_uuid=detail.get("update_by_uuid"),
                                         end_time=end_time, _source=_source, valid=1)
                db.session.add(event_point)
        db.session.commit()
        res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)

@blue_print.route('/search_during_time_event_point', methods=['POST'])
def search_during_time_event_point():
    try:
        start_time = request.json.get('start_time', '1900-01-01 00:00:00')
        end_time = request.json.get('end_time', '9999-01-01 00:00:00')

        event_points = EventPoint.query.filter(and_(EventPoint.valid == 1, EventPoint.event_time >= start_time, EventPoint.event_time <= end_time)).order_by(
            EventPoint.event_time.asc()).all()

        entity_same = {}
        for event_point in event_points:
            event_track = EventTrack.query.filter_by(uuid=event_point.title_uuid, valid=1).first()
            entity = Entity.query.filter_by(uuid=event_point.entity_uuid, valid=1).first()
            if entity.name not in entity_same.keys():
                entity_same[entity.name] = {
                    "event_tract_uuid": event_track.uuid,
                    "event_track_title_name": event_track.title_name,
                    "entity_name": entity.name,
                    "end_time": event_point.end_time,
                    "details":[]
                }

            entity_same[entity.name].get("details").append({
                "event_point_description": event_point.event_desc,
                "event_point_event_name": event_point.event_name,
                "entity_lon": entity.longitude,
                "entity_lat": entity.latitude,
                "source": event_point.source,
                "event_point_event_time": event_point.event_time

            })
        res = success_res(data=entity_same)

    except Exception as e:
        print(str(e))
        res = fail_res(data={})
    return jsonify(res)

