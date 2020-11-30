# -*- coding:utf-8 -*-
# @Author :MaYuhui
# work_location: Bei Jing
# @File : event_track.py 
# @Time : 2020/11/25 15:10


from flask import jsonify, request
from . import api_event_track as blue_print
from ..models import EventTrack
from .. import db
from .utils import success_res, fail_res
import uuid
import time


@blue_print.route('/get_event_track_names', methods=['GET'])
def get_event_track_names():
    try:
        event_tracks = EventTrack.query.filter_by(valid=1).all()
        res = success_res(data=[{
            "uuid": event_track.uuid,
            "title_name": event_track.title_name,
            "create_by_uuid": event_track.create_by_uuid,
            "create_time": event_track.create_time.strftime("%Y-%m-%d %H:%M:%S") if event_track.create_time else None,
            "update_by_uuid": event_track.update_by_uuid,
            "update_time": event_track.update_time.strftime("%Y-%m-%d %H:%M:%S") if event_track.update_time else None
        } for event_track in event_tracks])

    except Exception as e:
        print(str(e))
        res = []

    return jsonify(res)


@blue_print.route('/add_event_track_name', methods=['POST'])
def add_event_track_name():
    try:
        title_name = request.json.get('title_name')
        source = request.json.get("_source")
        create_by_uuid = request.json.get("customer_uuid", None)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_by_uuid = request.json.get("update_by_uuid", None)

        event_track = EventTrack.query.filter_by(title_name=title_name, valid=1).first()
        if event_track:
            res = fail_res(msg="录入事件的主题已存在!")
        else:
            event_track = EventTrack(uuid=uuid.uuid1(), title_name=title_name, valid=1, create_by_uuid=create_by_uuid,
                                    _source=source, create_time=create_time, update_time=update_time, update_by_uuid=update_by_uuid)
            db.session.add(event_track)
            db.session.commit()
            res = success_res(data={"uuid": event_track.uuid})

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/delete_event_track_by_id', methods=['POST'])
def delete_event_track_by_id():
    try:
        uuid = request.json.get("uuid", None)
        event_track = EventTrack.query.filter_by(uuid=uuid, valid=1).first()
        if event_track:
            event_track.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="录入事件的主题不存在！")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)