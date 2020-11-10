# -*- coding: UTF-8 -*-
import os
from . import api_sync_offline as blue_print
from ..models import Customer, db

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session


@blue_print.route('/sync_offline', methods=['GET'])
def sync_offline():
    try:
        # todo 改为request请求
        OFFLINE_PG_USER_NAME = os.getenv('OFFLINE_PG_USER_NAME', 'postgres')
        OFFLINE_PG_USER_PASSWORD = os.getenv('OFFLINE_PG_USER_PASSWORD', 'postgres')
        OFFLINE_PG_DB_SERVER_IP = os.getenv('OFFLINE_PG_DB_SERVER_IP', '192.168.2.159')
        OFFLINE_PG_DB_PORT = os.getenv('OFFLINE_PG_DB_PORT', '5432')
        OFFLINE_PG_DB_NAME = os.getenv('OFFLINE_PG_DB_NAME', 'offline_tagging_system_for_sync')

        # 建立动态数据库的链接
        offline_postgres = 'postgresql://%s:%s@%s:%s/%s' % (
            OFFLINE_PG_USER_NAME, OFFLINE_PG_USER_PASSWORD, OFFLINE_PG_DB_SERVER_IP,
            OFFLINE_PG_DB_PORT,
            OFFLINE_PG_DB_NAME)
        engine = create_engine(offline_postgres)
        # 定义模型类继承父类及数据连接会话
        DBsession = sessionmaker(bind=engine)  # 类似于游标
        dbsession = scoped_session(DBsession)
        Base = declarative_base()  # 定义一个给其他类继承的父类

        # md = MetaData(bind=engine)  # 元数据: 主要是指数据库表结构、关联等信息

        # 定义模型类
        class OfflineCustomer(Base):  # 自动加载表结构
            # __table__ = Table('customer', md, autoload=True)
            __tablename__ = 'customer'
            uuid = db.Column(db.String, primary_key=True)
            username = db.Column(db.Text)
            pwd = db.Column(db.Text)
            permission_id = db.Column(db.Integer)
            valid = db.Column(db.Integer)
            token = db.Column(db.String)
            _source = db.Column(db.String)
            power_score = db.Column(db.Float)
            troop_number = db.Column(db.String)

            def __repr__(self):
                return '<Customer %r>' % self.username

        # offline所有uuid/troop_number，唯一性（去重）判断
        uuids_and_troop_in_offline = dbsession.query(OfflineCustomer).with_entities(OfflineCustomer.uuid, OfflineCustomer.troop_number).all()
        uuids_in_offline = [i[0] for i in uuids_and_troop_in_offline]

        # online所有uuid/troop_number，唯一性（去重）判断
        uuids_and_troop_in_online = Customer.query.with_entities(Customer.uuid, Customer.troop_number).all()
        uuids_in_online = [i[0] for i in uuids_and_troop_in_online]

        # 记录uuid变化----customer_uuid_dict_trans
        online_dict_trans = {}
        customer_uuid_dict_trans = {}

        for i in uuids_and_troop_in_online:
            if i[1] not in online_dict_trans.keys():
                online_dict_trans[i[1]] = i[0]  # [{"troop_number": "uuid"}]

        for offline_customer in uuids_and_troop_in_offline:
            # offtroop存在, {"offuuid": "onuuid"}, offtroop不存在, {"offuuid": "offuuid"}
            customer_uuid_dict_trans[offline_customer[0]] = online_dict_trans[
                offline_customer[1]] if online_dict_trans.get(offline_customer[1], "") else offline_customer[0]

        # offline-online：计算是否有要插入的数据
        offline_uuids = list(set(uuids_in_offline).difference(set(uuids_in_online)))

        # 如果有要插入的数据
        if offline_uuids:
            offline_customers = dbsession.query(OfflineCustomer).filter(OfflineCustomer.uuid.in_(offline_uuids)).all()
            sync_customers = [Customer(uuid=i.uuid,
                                       username=i.username,
                                       pwd=i.pwd,
                                       permission_id=i.permission_id,
                                       valid=i.valid,
                                       token=i.token,
                                       _source=i._source,
                                       power_score=i.power_score,
                                       troop_number=i.troop_number) for i in offline_customers]
            db.session.add_all(sync_customers)
            db.session.commit()

    except Exception as e:
        print(str(e))
        if dbsession:
            dbsession.close()

    return "success"
