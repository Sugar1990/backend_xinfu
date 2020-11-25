#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from flask import jsonify, request
import time

from sqlalchemy import or_, and_, extract

from . import api_schedule as blue_print
from ..models import Schedule
from .. import db
from .utils import success_res, fail_res
import uuid


@blue_print.route('/insert_schedule', methods=['POST'])
def insert_schedule():
    try:
        description = request.json.get("description", "")
        start_time = request.json.get("start_time", None)
        end_time = request.json.get("end_time", None)
        customer_uuid = request.json.get("customer_uuid", None)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        remind_time = request.json.get("remind_time", None)
        _source = request.json.get("_source", "")
        cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cur_day = time.strftime("%Y-%m-%d", time.localtime())

        if remind_time < cur_time:
            res = fail_res(msg="提醒时间无效！")
        else:
            schedule = Schedule.query.filter_by(description=description, customer_uuid=customer_uuid,
                                                start_time=start_time, end_time=end_time, valid=1).first()
            if schedule:
                res = fail_res(msg="日程已存在")
            else:
                flag = False
                schedule = Schedule(uuid=uuid.uuid1(), description=description, customer_uuid=customer_uuid,
                                    start_time=start_time, end_time=end_time, create_time=create_time,
                                    update_time=update_time, remind_time=remind_time, _source=_source, valid=1)

                if remind_time.split(' ')[0] == cur_day:
                    flag = True
                db.session.add(schedule)
                db.session.commit()
                res = success_res(data=flag)
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg=str(e))

    return jsonify(res)


@blue_print.route('/get_schedules_according_to_remind_time', methods=['GET'])
def get_schedules_according_to_remind_time():
    try:
        cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cur_day = time.strftime("%Y-%m-%d", time.localtime())
        schedules = Schedule.query.filter(or_(Schedule.remind_time >= cur_time, Schedule.start_time > cur_time),
                                          Schedule.valid == 1).all()
        year = cur_day.split('-')[0]
        month = cur_day.split('-')[1]
        day = cur_day.split('-')[2]
        schedule_records = [{
            "uuid": i.uuid,
            "description": i.description,
            "start_time": i.start_time.strftime("%Y-%m-%d %H:%M:%S") if i.start_time else None,
            "end_time": i.end_time.strftime("%Y-%m-%d %H:%M:%S") if i.end_time else None,
            "remind_time": i.remind_time.strftime("%Y-%m-%d %H:%M:%S") if i.remind_time else None
        } for i in schedules]
        res = {
            "year": year,
            "month": month,
            "day": day,
            "Schedule": schedule_records
        }
        res = success_res(data=res)
    except Exception as e:
        print(str(e))
        res = fail_res(msg=str(e))

    return jsonify(res)


@blue_print.route('/get_schedule_by_customer_uuid', methods=['POST'])
def get_event_categories_by_classid():
    try:
        customer_uuid = request.json.get('customer_uuid', None)

        schedule = Schedule.query.filter_by(customer_uuid=customer_uuid, valid=1).first()

        cur_day = time.strftime("%Y-%m-%d", time.localtime())
        year = cur_day.split('-')[0]
        month = cur_day.split('-')[1]
        day = cur_day.split('-')[2]
        schedule_records = [{
            "uuid": i.uuid,
            "description": i.description,
            "start_time": i.start_time.strftime("%Y-%m-%d %H:%M:%S") if i.start_time else None,
            "end_time": i.end_time.strftime("%Y-%m-%d %H:%M:%S") if i.end_time else None,
            "remind_time": i.remind_time.strftime("%Y-%m-%d %H:%M:%S") if i.remind_time else None
        } for i in schedule]
        res = {
            "year": year,
            "month": month,
            "day": day,
            "Schedule": schedule_records
        }
        res = success_res(data=res)
    except Exception as e:
        print(str(e))
        return jsonify(fail_res())
    return jsonify(res)


@blue_print.route('/delete_schedule', methods=['POST'])
def delete_schedule():
    try:
        uuid = request.json.get("uuid", None)
        customer_uuid = request.json.get("customer_uuid", None)
        schedule = Schedule.query.filter_by(uuid=uuid, customer_uuid=customer_uuid, valid=1).first()
        if schedule:
            for uni_schedule in schedule:
                uni_schedule.valid = 0
            db.session.commit()
            res = success_res()
        else:
            res = fail_res(msg="日程未找到")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg=str(e))
    return jsonify(res)
