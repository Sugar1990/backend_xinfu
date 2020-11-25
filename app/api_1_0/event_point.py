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


@blue_print.route('/add_event_points', methods=['POST'])
def add_event_points():
    try:
        title_uuid = request.json.get('title_uuid', None)
        entity_name = request.json.get('entity_name', '')
        end_time = request.json.get('end_time', '')
        details = request.json.get('details', [])
        _source = request.json.get('_source')
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


