from flask import Blueprint

api_entity = Blueprint('entity', __name__)
api_catalog = Blueprint('catalog', __name__)
api_document = Blueprint('document', __name__)
api_customer = Blueprint('customer', __name__)
api_entity_category = Blueprint('entity_category', __name__)
api_event_category = Blueprint('event_category', __name__)
api_event_class = Blueprint('event_class', __name__)
api_relation_category = Blueprint('relation_category', __name__)
api_event = Blueprint('event', __name__)
api_permission = Blueprint('permission', __name__)
api_initial = Blueprint('initial', __name__)
api_document_records = Blueprint('document_records', __name__)
api_place = Blueprint('place', __name__)
api_doc_mark_comment = Blueprint('doc_mark_comment', __name__)
api_doc_mark_entity = Blueprint('doc_mark_entity', __name__)
api_doc_mark_event = Blueprint('doc_mark_event', __name__)
api_doc_mark_place = Blueprint('doc_mark_place', __name__)
api_doc_mark_time_tag = Blueprint('doc_mark_time_tag', __name__)
api_doc_mark_mind = Blueprint('doc_mark_mind', __name__)
api_doc_mark_relation_property= Blueprint('doc_mark_relation_property', __name__)
api_doc_mark_advise= Blueprint('doc_mark_advise', __name__)

from . import document
from . import entity
from . import catalog
from . import customer
from . import entity_category
from . import event_category
from . import event_class
from . import relation_category
from . import event
from . import permission
from . import initial
from . import document_records
from . import place
from . import doc_mark_comment
from . import doc_mark_entity
from . import doc_mark_event
from . import doc_mark_place
from . import doc_mark_time_tag
from . import doc_mark_mind
from . import doc_mark_relation_property
from . import doc_mark_advise