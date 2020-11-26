#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from flask import jsonify, request
import time

from sqlalchemy import or_, and_, extract, func, text

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
        _source = request.json.get("_source")
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
        customer_uuid = request.args.get("customer_uuid", None)
        cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cur_day = time.strftime("%Y-%m-%d", time.localtime())
        schedules = Schedule.query.filter(or_(Schedule.remind_time >= cur_time, Schedule.start_time > cur_time),
                                          Schedule.valid == 1, Schedule.customer_uuid == customer_uuid).all()
        schedules_records = [i for i in schedules if i.remind_time.strftime("%Y-%m-%d") == cur_day]

        sche_dict = {}
        dict_in_result = {}
        final_result = []
        for i in schedules_records:
            cur_start_time = i.start_time.strftime("%Y-%m-%d")
            year = cur_start_time.split('-')[0]
            month = cur_start_time.split('-')[1]
            day = cur_start_time.split('-')[2]
            if not sche_dict.get(cur_start_time):
                sche_dict[cur_start_time] = []
                temp = {
                    "uuid": i.uuid,
                    "description": i.description,
                    "start_time": i.start_time.strftime("%Y-%m-%d %H:%M:%S") if i.start_time else None,
                    "end_time": i.end_time.strftime("%Y-%m-%d %H:%M:%S") if i.end_time else None,
                    "remind_time": i.remind_time.strftime("%Y-%m-%d %H:%M:%S") if i.remind_time else None
                }
                sche_dict[cur_start_time].append(temp)
                dict_in_result["year"] = year
                dict_in_result["month"] = month
                dict_in_result["day"] = day
                dict_in_result["schedule"] = sche_dict[cur_start_time]
            else:
                temp = {
                    "uuid": i.uuid,
                    "description": i.description,
                    "start_time": i.start_time.strftime("%Y-%m-%d %H:%M:%S") if i.start_time else None,
                    "end_time": i.end_time.strftime("%Y-%m-%d %H:%M:%S") if i.end_time else None,
                    "remind_time": i.remind_time.strftime("%Y-%m-%d %H:%M:%S") if i.remind_time else None
                }
                sche_dict[cur_start_time].append(temp)
                dict_in_result["year"] = year
                dict_in_result["month"] = month
                dict_in_result["day"] = day
                dict_in_result["schedule"] = sche_dict[cur_start_time]

        for key, value in sche_dict.items():
            temp_dict = {}
            year = key.split('-')[0]
            month = key.split('-')[1]
            day = key.split('-')[2]
            temp_dict["year"] = year
            temp_dict["month"] = month
            temp_dict["day"] = day
            temp_dict["schedules"] = value
            final_result.append(temp_dict)

        res = success_res(data=final_result)
    except Exception as e:
        print(str(e))
        res = fail_res(msg=str(e))

    return jsonify(res)


@blue_print.route('/get_schedule_by_customer_uuid', methods=['GET'])
def get_schedule_by_customer_uuid():
    try:
        customer_uuid = request.args.get('customer_uuid', None)
        schedule = Schedule.query.filter_by(customer_uuid=customer_uuid, valid=1).all()
        sche_dict = {}
        dict_in_result = {}
        final_result = []
        for i in schedule:
            cur_start_time = i.start_time.strftime("%Y-%m-%d")
            year = cur_start_time.split('-')[0]
            month = cur_start_time.split('-')[1]
            day = cur_start_time.split('-')[2]
            if not sche_dict.get(cur_start_time):
                sche_dict[cur_start_time] = []
                temp = {
                    "uuid": i.uuid,
                    "description": i.description,
                    "start_time": i.start_time.strftime("%Y-%m-%d %H:%M:%S") if i.start_time else None,
                    "end_time": i.end_time.strftime("%Y-%m-%d %H:%M:%S") if i.end_time else None,
                    "remind_time": i.remind_time.strftime("%Y-%m-%d %H:%M:%S") if i.remind_time else None
                }
                sche_dict[cur_start_time].append(temp)
                dict_in_result["year"] = year
                dict_in_result["month"] = month
                dict_in_result["day"] = day
                dict_in_result["schedule"] = sche_dict[cur_start_time]
            else:
                temp = {
                    "uuid": i.uuid,
                    "description": i.description,
                    "start_time": i.start_time.strftime("%Y-%m-%d %H:%M:%S") if i.start_time else None,
                    "end_time": i.end_time.strftime("%Y-%m-%d %H:%M:%S") if i.end_time else None,
                    "remind_time": i.remind_time.strftime("%Y-%m-%d %H:%M:%S") if i.remind_time else None
                }
                sche_dict[cur_start_time].append(temp)
                dict_in_result["year"] = year
                dict_in_result["month"] = month
                dict_in_result["day"] = day
                dict_in_result["schedule"] = sche_dict[cur_start_time]

        for key, value in sche_dict.items():
            temp_dict = {}
            year = key.split('-')[0]
            month = key.split('-')[1]
            day = key.split('-')[2]
            temp_dict["year"] = year
            temp_dict["month"] = month
            temp_dict["day"] = day
            temp_dict["schedules"] = value

            final_result.append(temp_dict)

        res = success_res(data=final_result)
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
            schedule.valid = 0
            db.session.commit()
            res = success_res()
        else:
            res = fail_res(msg="日程未找到")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg=str(e))
    return jsonify(res)
