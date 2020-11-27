# -*- coding:utf-8 -*-
# author: Scandium
# work_location: Bei Jing
import os
from sqlalchemy.dialects.postgresql import JSONB
import re
from . import db
from .conf import PLACE_BASE_NAME, LOCAL_SOURCE


class Entity(db.Model):
    __tablename__ = 'entity'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.Text)
    synonyms = db.Column(JSONB)
    props = db.Column(JSONB)
    category_uuid = db.Column(db.String)
    summary = db.Column(db.Text)
    valid = db.Column(db.Integer)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    create_time = db.Column(db.TIMESTAMP)
    update_time = db.Column(db.TIMESTAMP)

    def category_name(self):
        conf = EntityCategory.query.filter_by(uuid=self.category_uuid).first()
        return conf.name if conf else ""

    @staticmethod
    def get_category_id(entity_uuid):
        conf = Entity.query.filter_by(uuid=entity_uuid).first()
        return conf.category_uuid if conf else -1

    @staticmethod
    def get_location_of_entity(entity_uuid):
        entity = Entity.query.filter_by(uuid=entity_uuid).first()
        if entity:
            if entity.longitude and entity.longitude:
                return {"lon": float(format(entity.longitude,".5f")), "lat": float(format(entity.latitude,".5f"))}
            else:
                return {}
        else:
            return {}

    @staticmethod
    def get_location_of_entity_name(entity_name):
        entity = Entity.query.filter_by(name=entity_name).first()
        if entity:
            if entity.longitude and entity.longitude:
                return {"lon": float(format(entity.longitude,".5f")), "lat": float(format(entity.latitude,".5f"))}
            else:
                return {}
        else:
            return {}

    def get_yc_mark_category(self):
        mark_category = "ner"
        if self.category_uuid == EntityCategory.get_category_id(PLACE_BASE_NAME):
            mark_category = "place"
        elif EntityCategory.get_category_type(self.category_uuid) == 2:
            mark_category = "concept"
        return mark_category

    def __repr__(self):
        return '<Entity %r>' % self.name


class Document(db.Model):
    __tablename__ = 'document'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.Text)
    category = db.Column(db.Text)
    savepath = db.Column(db.Text)
    content = db.Column(db.JSON)
    catalog_uuid = db.Column(db.String)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    permission_id = db.Column(db.Integer)
    status = db.Column(db.Integer)
    keywords = db.Column(db.JSON)
    md5 = db.Column(db.String)
    is_favorite = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    html_path = db.Column(db.String)
    valid = db.Column(db.Integer)

    def category_name(self):
        conf = EntityCategory.query.filter_by(uuid=self.category_uuid).first()
        return conf.name if conf else "未知"

    def get_power(self):
        if self.permission_id:
            return Permission.get_power(self.permission_id)
        return 0

    def get_full_path(self):
        return Catalog.get_full_path(self.catalog_uuid)

    def get_status_name(self):
        return "上传处理中" if self.status == 0 else "未标注" if self.status == 1 else "已标注" if self.status == 2 else ""

    def __repr__(self):
        return '<Document %r>' % self.name


class DocumentRecords(db.Model):
    __tablename__ = 'document_records'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    doc_uuid = db.Column(db.String)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    operate_type = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)

    def __repr__(self):
        return '<DocumentRecords %r>' % self.doc_uuid


class Customer(db.Model):
    __tablename__ = 'customer'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    username = db.Column(db.Text)
    pwd = db.Column(db.Text)
    permission_id = db.Column(db.Integer)
    valid = db.Column(db.Integer)
    token = db.Column(db.String)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    # mark_doc_ids = db.Column(db.JSON)
    power_score = db.Column(db.Float)
    troop_number = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_time = db.Column(db.TIMESTAMP)

    @staticmethod
    def get_username_by_id(uuid):
        uname = ""
        if uuid:
            cus = Customer.query.filter_by(uuid=uuid).first()
            if cus:
                uname = cus.username
        return uname

    def get_power(self):
        if self.permission_id:
            return Permission.get_power(self.permission_id)
        return 0

    def __repr__(self):
        return '<Customer %r>' % self.username


class Catalog(db.Model):
    __tablename__ = 'catalog'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.Text)
    parent_uuid = db.Column(db.String)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    tagging_tabs = db.Column(db.JSON)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    sort = db.Column(db.Integer)

    @staticmethod
    def get_name_by_id(catalog_uuid):
        catalog = Catalog.query.filter_by(uuid=catalog_uuid).first()
        return catalog.name if catalog else ""

    @staticmethod
    def get_full_path(catalog_uuid):
        catalog = Catalog.query.filter_by(uuid=catalog_uuid).first()
        if catalog:
            return os.path.join(Catalog.get_full_path(catalog.parent_uuid), catalog.name)
        else:
            return ""

    @staticmethod
    def get_ancestorn_catalog(catalog_uuid):
        cur_catalog = Catalog.query.filter_by(uuid=catalog_uuid).first()
        if cur_catalog:
            if cur_catalog.parent_uuid == "":
                return cur_catalog
            else:
                parent_catalog = Catalog.query.filter_by(uuid=cur_catalog.parent_uuid).first()
                if parent_catalog:
                    if not parent_catalog.parent_uuid:
                        return parent_catalog
                    else:
                        return Catalog.get_ancestorn_catalog(parent_catalog.uuid)
                else:
                    return None

    def __repr__(self):
        return '<Catalog %r>' % self.name


class Permission(db.Model):
    __tablename__ = "permission"
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    power = db.Column(db.Integer)
    valid = db.Column(db.Integer)  # 取值0或1，0表示已删除，1表示正常

    @staticmethod
    def get_power(permission_id):
        power = 0
        if permission_id:
            permission = Permission.query.filter_by(id=permission_id).first()
            power = permission.power if permission else 0
        return power

    @staticmethod
    def judge_power(customer_id, doc_id):
        doc = Document.query.filter_by(uuid=doc_id).first()
        cus = Customer.query.filter_by(uuid=customer_id).first()
        doc_power = doc.get_power() if doc else 0
        cus_power = cus.get_power() if cus else 0
        if cus_power and doc_power <= cus_power:
            return True
        else:
            return False

    def __repr__(self):
        return '<Permission %r>' % self.name


# hanzhonghe add in 200826:
class EntityCategory(db.Model):
    __tablename__ = 'entity_category'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.Text)
    valid = db.Column(db.Integer)  # 取值0或1，0表示已删除，1表示正常
    type = db.Column(db.Integer)  # 1：实体（地名、国家、人物...）；2：概念（条约公约、战略、战法...）
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    create_time = db.Column(db.TIMESTAMP)
    update_time = db.Column(db.TIMESTAMP)

    @staticmethod
    def get_category_name(uuid):
        category = EntityCategory.query.filter_by(uuid=uuid).first()
        return category.name if category else ""

    @staticmethod
    def get_category_type(uuid):
        category = EntityCategory.query.filter_by(uuid=uuid).first()
        return category.type if category else 0

    @staticmethod
    def get_category_id(name):
        category = EntityCategory.query.filter_by(name=name).first()
        return category.uuid if category else ""

    def __repr__(self):
        return '<EntityCategory %r>' % self.name


# hanzhonghe add in 200826:
class EventCategory(db.Model):
    __tablename__ = 'event_category'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.Text)
    event_class_uuid = db.Column(db.String)
    valid = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    create_time = db.Column(db.TIMESTAMP)
    update_time = db.Column(db.TIMESTAMP)

    def __repr__(self):
        return '<EventCategory %r>' % self.name


# hanzhonghe add in 200826:
class EventClass(db.Model):
    __tablename__ = 'event_class'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.Text)
    valid = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    create_time = db.Column(db.TIMESTAMP)
    update_time = db.Column(db.TIMESTAMP)

    @staticmethod
    def get_classname(uuid):
        event_class = EventClass.query.filter_by(uuid=uuid).first()
        return event_class.name if event_class else ""

    def __repr__(self):
        return '<EventClass %r>' % self.name


# hanzhonghe add in 200826:
class RelationCategory(db.Model):
    __tablename__ = 'relation_category'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    source_entity_category_uuids = db.Column(db.JSON)  # NOTE: not null
    target_entity_category_uuids = db.Column(db.JSON)
    relation_name = db.Column(db.Text)
    valid = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    create_time = db.Column(db.TIMESTAMP)
    update_time = db.Column(db.TIMESTAMP)

    def source_entity_category(self):
        source_entity_categories = []
        for uuid in self.source_entity_category_uuids:
            source_entity_categories.append(EntityCategory.get_category_name(uuid))
        return source_entity_categories

    def target_entity_category(self):
        target_entity_categories = []
        for uuid in self.target_entity_category_uuids:
            target_entity_categories.append(EntityCategory.get_category_name(uuid))
        return target_entity_categories

    def __repr__(self):
        return '<RelationCategory %r>' % self.relation_name


class DocMarkComment(db.Model):
    __tablename__ = 'doc_mark_comment'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    doc_uuid = db.Column(db.String)
    name = db.Column(db.Text)
    position = db.Column(db.String)
    comment = db.Column(db.String)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    valid = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    appear_index_in_text = db.Column(JSONB)
    locate_position = db.Column(JSONB)

    def __repr__(self):
        return '<DocMarkComment %r>' % self.name


class DocMarkAdvise(db.Model):
    __tablename__ = 'doc_mark_advise'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    doc_uuid = db.Column(db.String)
    mark_uuid = db.Column(db.String)
    type = db.Column(db.Integer)
    content = db.Column(db.Text)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    valid = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)

    def __repr__(self):
        return '<DocMarkAdvise %r>' % self.content


class DocMarkEntity(db.Model):
    __tablename__ = 'doc_mark_entity'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    doc_uuid = db.Column(db.String)
    word = db.Column(db.String)
    entity_uuid = db.Column(db.String)
    source = db.Column(db.Integer)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    appear_text = db.Column(db.String)
    appear_index_in_text = db.Column(db.JSON)
    valid = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    position = db.Column(JSONB)

    def __repr__(self):
        return '<DocMarkEntity %r>' % self.word


class DocMarkEvent(db.Model):
    __tablename__ = 'doc_mark_event'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    event_id = db.Column(db.String)
    event_desc = db.Column(db.String)
    event_subject = db.Column(db.JSON)
    event_predicate = db.Column(db.String)
    event_object = db.Column(db.JSON)
    event_time = db.Column(db.JSON)
    event_address = db.Column(db.JSON)
    event_why = db.Column(db.String)
    event_result = db.Column(db.String)
    event_conduct = db.Column(db.String)
    event_talk = db.Column(db.String)
    event_how = db.Column(db.String)
    doc_uuid = db.Column(db.String)
    customer_uuid = db.Column(db.String)
    parent_uuid = db.Column(db.String)
    title = db.Column(db.String)
    event_class_uuid = db.Column(db.String)
    event_type_uuid = db.Column(db.String)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    add_time = db.Column(db.TIMESTAMP)
    valid = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    position = db.Column(JSONB)

    def get_subject_entity_names(self):
        subject_entity_names = []
        if self.event_subject:
            doc_mark_entities = DocMarkEntity.query.filter(DocMarkEntity.uuid.in_(self.event_subject)).all()
            doc_mark_entities_entity_uuids = [i.entity_uuid for i in doc_mark_entities]
            if doc_mark_entities_entity_uuids:
                entities = Entity.query.filter(Entity.uuid.in_(doc_mark_entities_entity_uuids)).all()
                subject_entity_names = [i.name for i in entities]
        return subject_entity_names

    def get_object_entity_names(self):
        object_entity_names = []
        if self.event_object:
            doc_mark_entities = DocMarkEntity.query.filter(DocMarkEntity.uuid.in_(self.event_object)).all()
            doc_mark_entities_entity_uuids = [i.entity_uuid for i in doc_mark_entities]
            if doc_mark_entities_entity_uuids:
                entities = Entity.query.filter(Entity.uuid.in_(doc_mark_entities_entity_uuids)).all()
                object_entity_names = [i.name for i in entities]
        return object_entity_names

    def get_places(self):
        places = []
        if self.event_address:
            places = DocMarkPlace.query.filter(DocMarkPlace.uuid.in_(self.event_address)).all()
        return places

    def __repr__(self):
        return '<DocMarkEvent %r>' % self.uuid


class DocMarkPlace(db.Model):
    __tablename__ = 'doc_mark_place'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    doc_uuid = db.Column(db.String)
    word = db.Column(db.Text)
    type = db.Column(db.Integer)
    place_uuid = db.Column(db.String)
    direction = db.Column(db.Text)
    place_lon = db.Column(db.Text)
    place_lat = db.Column(db.Text)
    height = db.Column(db.Text)
    unit = db.Column(db.Text)
    dms = db.Column(db.JSON)
    distance = db.Column(db.Integer)
    relation = db.Column(db.Text)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.DateTime)
    update_by_uuid = db.Column(db.String)
    update_time = db.Column(db.DateTime)
    valid = db.Column(db.Integer)
    entity_or_sys = db.Column(db.Integer)
    appear_index_in_text = db.Column(db.JSON)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    word_count = db.Column(db.String)
    word_sentence = db.Column(db.String)
    source_type = db.Column(db.Integer)
    position = db.Column(JSONB)
    def __repr__(self):
        return '<DocMarkPlace %r>' % self.uuid


class DocMarkTimeTag(db.Model):
    __tablename__ = 'doc_mark_time_tag'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    doc_uuid = db.Column(db.String)
    word = db.Column(db.Text)
    format_date = db.Column(db.DateTime)
    format_date_end = db.Column(db.DateTime)
    mark_position = db.Column(db.Text)
    time_type = db.Column(db.Integer)
    reserve_fields = db.Column(db.Text)
    valid = db.Column(db.Integer)
    arab_time = db.Column(db.Text)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    appear_index_in_text = db.Column(db.JSON)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    position = db.Column(JSONB)

    def __repr__(self):
        return '<DocMarkTimeTag %r>' % self.uuid


class DocMarkRelationProperty(db.Model):
    __tablename__ = 'doc_mark_relation_property'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    doc_uuid = db.Column(db.String)
    nid = db.Column(db.Text)
    relation_uuid = db.Column(db.String)
    relation_name = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    start_type = db.Column(db.Text)
    end_time = db.Column(db.DateTime)
    end_type = db.Column(db.Text)
    source_entity_uuid = db.Column(db.String)
    target_entity_uuid = db.Column(db.String)
    valid = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    create_by_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    position = db.Column(JSONB)

    def __repr__(self):
        return '<DocMarkRelationProperty %r>' % self.uuid


class DocMarkMind(db.Model):
    __tablename__ = 'doc_mark_mind'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.Text)
    parent_uuid = db.Column(db.String)
    doc_uuid = db.Column(db.String)
    valid = db.Column(db.Integer)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    create_time = db.Column(db.TIMESTAMP)
    update_time = db.Column(db.TIMESTAMP)
    position = db.Column(JSONB)

    def __repr__(self):
        return '<DocMarkMind %r>' % self.uuid


class Schedule(db.Model):
    __tablename__ = 'schedule'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    description = db.Column(db.String)
    start_time = db.Column(db.TIMESTAMP)
    end_time = db.Column(db.TIMESTAMP)
    customer_uuid = db.Column(db.String)
    create_time = db.Column(db.TIMESTAMP)
    update_time = db.Column(db.TIMESTAMP)
    remind_time = db.Column(db.TIMESTAMP)
    _source = db.Column(db.String, default = LOCAL_SOURCE)
    valid = db.Column(db.Integer)

    def __repr__(self):
        return '<Schedule %r>' % self.uuid


class EventTrack(db.Model):
    __tablename__ = 'event_track'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    title_name = db.Column(db.String)
    _source = db.Column(db.String, default=LOCAL_SOURCE)
    valid = db.Column(db.Integer)
    create_time = db.Column(db.TIMESTAMP)
    create_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)

    def __repr__(self):
        return '<Schedule %r>' % self.title_name


class EventPoint(db.Model):
    __tablename__ = 'event_point'
    __table_args__ = {"schema": "public"}
    uuid = db.Column(db.String, primary_key=True)
    title_uuid = db.Column(db.String)
    source = db.Column(db.String)
    event_name = db.Column(db.String)
    event_desc = db.Column(db.Text)
    entity_uuid = db.Column(db.String)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    event_time = db.Column(db.TIMESTAMP)
    create_time = db.Column(db.TIMESTAMP)
    create_by_uuid = db.Column(db.String)
    update_time = db.Column(db.TIMESTAMP)
    update_by_uuid = db.Column(db.String)
    end_time = db.Column(db.String)
    _source = db.Column(db.String, default=LOCAL_SOURCE)
    valid = db.Column(db.Integer)

    def __repr__(self):
        return '<EventPoint %r>' % self.event_name

class SyncRecords(db.Model):
    __tablename__ = 'sync_records'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    system_name = db.Column(db.String)
    sync_time = db.Column(db.TIMESTAMP)

    def __repr__(self):
        return '<SyncRecords %r>' % self.system_name


class Es_controller():
    # def __init__(self):
    #     Es_controller =
    def dfm_to_location(self,deggrees):
        lon = deggrees["lon"]
        lat = deggrees["lat"]
        lon_num  =  self.dfm_convert(lon['degree'],lon["minute"],lon["second"])
        lat_num  =  self.dfm_convert(lat['degree'],lat["minute"],lat["second"])
        return {"lon":lon_num , "lat": lat_num}

    @staticmethod
    def dfm_convert(du,fen,miao):
        out_location = int(du) + int(fen)/60 + int(miao)/3600
        return float(format(out_location,".5f"))

    @staticmethod
    def hight_convert(hight):
        dict_of_hight = {
            "千米":1000,
            "米":1,
            "公里":1000,
            "海里":1852,
            "里":500,
            "丈":3.333,
            "码":0.914,
            "英里":1609.344
        }
        str_num_hight = re.findall('(\d+)',hight)[0]
        num_hight = int(str_num_hight)
        unit_hight =hight.split(str_num_hight)[1]
        return num_hight * dict_of_hight.get(unit_hight,0)

    @staticmethod
    def place_convert(place_name):
        location_output = Entity.get_location_of_entity_name(place_name)
        return location_output


import re


def find_int_in_str(string):
    str_to_num = re.findall('(\d+)', string)[0]
    return int(str_to_num)


def find_dfm(dfm_string):
    d_ = find_int_in_str(dfm_string.split("°")[0])
    f_ = find_int_in_str(dfm_string.split("°")[1])
    return d_ + f_/60


# Es_controller.hight_convert('100千米')
#
# Es_controller.dfm_convert(12,11,11)