#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from app.models import Permission, Customer


def get_leader_ids():
    leader_ids = []
    permission = Permission.query.filter(Permission.power>=90, Permission.valid==1).all()
    permission_ids = [i.id for i in permission]

    if permission_ids:
        leaders = Customer.query.filter(Customer.permission_id.in_(permission_ids), Customer.valid==1).all()
        leader_ids = [i.id for i in leaders]

    return leader_ids