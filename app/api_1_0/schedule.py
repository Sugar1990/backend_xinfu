#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from flask import jsonify, request
import time
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

        schedule = Schedule.query.filter_by(description=description, customer_uuid=customer_uuid,
                                            start_time=start_time, end_time=end_time).first()

        if schedule:
            res = fail_res(msg="日程已存在")
        else:
            schedule = Schedule(uuid=uuid.uuid1(), description=description, customer_uuid=customer_uuid,
                                start_time=start_time, end_time=end_time, create_time=create_time,
                                update_time=update_time, remind_time=remind_time, _source=_source)
            db.session.add(schedule)
            db.session.commit()
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg=str(e))

    return jsonify(res)


