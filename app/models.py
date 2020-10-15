import os
from sqlalchemy.dialects.postgresql import JSONB

from . import db
from .conf import PLACE_BASE_NAME


class Entity(db.Model):
    __tablename__ = 'entity'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    synonyms = db.Column(JSONB)
    props = db.Column(JSONB)
    category_id = db.Column(db.Integer)
    summary = db.Column(db.Text)
    valid = db.Column(db.Integer)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)

    def category_name(self):
        conf = EntityCategory.query.filter_by(id=self.category_id).first()
        return conf.name if conf else ""

    def get_yc_mark_category(self):
        mark_category = "ner"
        if self.category_id == EntityCategory.get_category_id(PLACE_BASE_NAME):
            mark_category = "place"
        elif EntityCategory.get_category_type(self.category_id) == 2:
            mark_category = "concept"
        return mark_category

    def __repr__(self):
        return '<Entity %r>' % self.name


class Document(db.Model):
    __tablename__ = 'document'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    category = db.Column(db.Text)
    savepath = db.Column(db.Text)
    content = db.Column(db.JSON)
    catalog_id = db.Column(db.Integer)
    create_by = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    permission_id = db.Column(db.Integer)
    status = db.Column(db.Integer)
    keywords = db.Column(db.JSON)
    md5 = db.Column(db.String)
    is_favorite = db.Column(db.Integer)

    def category_name(self):
        conf = EntityCategory.query.filter_by(id=self.category_id).first()
        return conf.name if conf else "未知"

    def get_power(self):
        if self.permission_id:
            return Permission.get_power(self.permission_id)
        return 0

    def get_full_path(self):
        return Catalog.get_full_path(self.catalog_id)

    def get_status_name(self):
        return "上传处理中" if self.status == 0 else "未标注" if self.status == 1 else "已标注" if self.status == 2 else ""

    def __repr__(self):
        return '<Document %r>' % self.name


class DocumentRecords(db.Model):
    __tablename__ = 'document_records'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer)
    create_by = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    operate_type = db.Column(db.Integer)

    def __repr__(self):
        return '<DocumentRecords %r>' % self.doc_id


class Customer(db.Model):
    __tablename__ = 'customer'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text)
    pwd = db.Column(db.Text)
    permission_id = db.Column(db.Integer)
    valid = db.Column(db.Integer)
    token = db.Column(db.String)

    @staticmethod
    def get_username_by_id(id):
        uname = ""
        if id:
            cus = Customer.query.filter_by(id=id).first()
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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    parent_id = db.Column(db.Integer)
    create_by = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    tagging_tabs = db.Column(db.JSON)

    @staticmethod
    def get_name_by_id(catalog_id):
        catalog = Catalog.query.filter_by(id=catalog_id).first()
        return catalog.name if catalog else ""

    @staticmethod
    def get_full_path(catalog_id):
        catalog = Catalog.query.filter_by(id=catalog_id).first()
        if catalog:
            return os.path.join(Catalog.get_full_path(catalog.parent_id), catalog.name)
        else:
            return ""

    @staticmethod
    def get_ancestorn_catalog(catalog_id):
        cur_catalog = Catalog.query.filter_by(id=catalog_id).first()
        if cur_catalog:
            if cur_catalog.parent_id == 0:
                return cur_catalog
            else:
                parent_catalog = Catalog.query.filter_by(id=cur_catalog.parent_id).first()
                if parent_catalog:
                    if not parent_catalog.parent_id:
                        return parent_catalog
                    else:
                        return Catalog.get_ancestorn_catalog(parent_catalog.id)
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
        doc = Document.query.filter_by(id=doc_id).first()
        cus = Customer.query.filter_by(id=customer_id).first()
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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    valid = db.Column(db.Integer)  # 取值0或1，0表示已删除，1表示正常
    type = db.Column(db.Integer)  # 1：实体（地名、国家、人物...）；2：概念（条约公约、战略、战法...）

    @staticmethod
    def get_category_name(id):
        category = EntityCategory.query.filter_by(id=id).first()
        return category.name if category else ""

    @staticmethod
    def get_category_type(id):
        category = EntityCategory.query.filter_by(id=id).first()
        return category.type if category else 0

    @staticmethod
    def get_category_id(name):
        category = EntityCategory.query.filter_by(name=name).first()
        return category.id if category else 0

    def __repr__(self):
        return '<EntityCategory %r>' % self.name


# hanzhonghe add in 200826:
class EventCategory(db.Model):
    __tablename__ = 'event_category'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    event_class_id = db.Column(db.Integer)  # connect to EventClass.id, not null
    valid = db.Column(db.Integer)

    def __repr__(self):
        return '<EventCategory %r>' % self.name


# hanzhonghe add in 200826:
class EventClass(db.Model):
    __tablename__ = 'event_class'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    valid = db.Column(db.Integer)

    @staticmethod
    def get_classname(id):
        event_class = EventClass.query.filter_by(id=id).first()
        return event_class.name if event_class else ""

    def __repr__(self):
        return '<EventClass %r>' % self.name


# hanzhonghe add in 200826:
class RelationCategory(db.Model):
    __tablename__ = 'relation_category'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    source_entity_category_id = db.Column(db.Integer)  # NOTE: not null
    target_entity_category_id = db.Column(db.Integer)  # NOTE: not null
    relation_name = db.Column(db.Text)
    valid = db.Column(db.Integer)

    def source_entity_category(self):
        return EntityCategory.get_category_name(self.source_entity_category_id)

    def target_entity_category(self):
        return EntityCategory.get_category_name(self.target_entity_category_id)

    def __repr__(self):
        return '<RelationCategory %r>' % self.relation_name


class DocMarkComment(db.Model):
    __tablename__ = 'doc_mark_comment'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer)
    name = db.Column(db.Text)
    position = db.Column(db.String)
    comment = db.Column(db.String)
    create_by = db.Column(db.Integer)
    create_time = db.Column(db.TIMESTAMP)
    update_by = db.Column(db.Integer)
    update_time = db.Column(db.TIMESTAMP)
    valid = db.Column(db.Integer)

    def __repr__(self):
        return '<DocMarkComment %r>' % self.name


class DocMarkEntity(db.Model):
    __tablename__ = 'doc_mark_entity'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer)
    word = db.Column(db.String)
    entity_id = db.Column(db.Integer)
    source = db.Column(db.Integer)
    create_by = db.Column(db.Integer)
    create_time = db.Column(db.TIMESTAMP)
    update_by = db.Column(db.Integer)
    update_time = db.Column(db.TIMESTAMP)
    paragraph_index = db.Column(db.Integer)
    appear_text = db.Column(db.String)
    appear_index_in_text = db.Column(db.Integer)
    valid = db.Column(db.Integer)

    def __repr__(self):
        return '<DocMarkEntity %r>' % self.word


class DocMarkEvent(db.Model):
    __tablename__ = 'doc_mark_event'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String)
    event_desc = db.Column(db.String)
    event_subject = db.Column(db.String)
    event_predicate = db.Column(db.String)
    event_object = db.Column(db.String)
    event_time = db.Column(db.String)
    event_address = db.Column(db.String)
    event_why = db.Column(db.String)
    event_result = db.Column(db.String)
    event_conduct = db.Column(db.String)
    event_talk = db.Column(db.String)
    event_how = db.Column(db.String)
    doc_id = db.Column(db.Integer)
    customer_id = db.Column(db.Integer)
    parent_id = db.Column(db.Integer)
    title = db.Column(db.String)
    event_class_id = db.Column(db.Integer)
    event_type_id = db.Column(db.Integer)
    create_by = db.Column(db.Integer)
    create_time = db.Column(db.TIMESTAMP)
    update_by = db.Column(db.Integer)
    update_time = db.Column(db.TIMESTAMP)
    add_time = db.Column(db.TIMESTAMP)
    valid = db.Column(db.Integer)

    def __repr__(self):
        return '<DocMarkEvent %r>' % self.title


class DocMarkPlace(db.Model):
    __tablename__ = 'doc_mark_place'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer)
    word = db.Column(db.Text)
    type = db.Column(db.Integer)
    place_id = db.Column(db.Integer)
    direction = db.Column(db.Text)
    place_lon = db.Column(db.Text)
    place_lat = db.Column(db.Text)
    height = db.Column(db.Text)
    unit = db.Column(db.Text)
    dms = db.Column(db.JSON)
    distance = db.Column(db.Integer)
    relation = db.Column(db.Text)
    create_by = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    update_by = db.Column(db.Integer)
    update_time = db.Column(db.DateTime)
    valid = db.Column(db.Integer)
    entity_or_sys = db.Column(db.Integer)

    def __repr__(self):
        return '<DocumentRecords %r>' % self.doc_id


class DocMarkTimeTag(db.Model):
    __tablename__ = 'doc_mark_time_tag'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer)
    word = db.Column(db.Text)
    format_date = db.Column(db.DateTime)
    format_date_end = db.Column(db.DateTime)
    mark_position = db.Column(db.Text)
    time_type = db.Column(db.Text)
    reserve_fields = db.Column(db.Text)
    valid = db.Column(db.Integer)
    arab_time = db.Column(db.Text)
    update_by = db.Column(db.Integer)
    update_time = db.Column(db.DateTime)

    def __repr__(self):
        return '<DocumentRecords %r>' % self.doc_id


class DocMarkRelationProperty(db.Model):
    __tablename__ = 'doc_mark_relation_property'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer)
    nid = db.Column(db.Text)
    relation_id = db.Column(db.Integer)
    relation_name = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    start_type = db.Column(db.Text)
    end_time = db.Column(db.DateTime)
    end_type = db.Column(db.Text)
    valid = db.Column(db.Integer)

    def __repr__(self):
        return '<DocMarkRelationProperty %r>' % self.id


class DocMarkMind(db.Model):
    __tablename__ = 'doc_mark_mind'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    parent_id = db.Column(db.Integer)
    doc_id = db.Column(db.Integer)
    valid = db.Column(db.Integer)

    def __repr__(self):
        return '<DocMarkMind %r>' % self.id
