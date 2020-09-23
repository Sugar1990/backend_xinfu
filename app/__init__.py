# from flasgger import Swagger
# from flasgger import Swagger
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_cors import CORS
import os
import threading
# from flasgger import Swagger

lock = threading.Lock()

db = SQLAlchemy(session_options={'autocommit': False})

# 5.3.1升级依赖包后修改语法，注释
cache_config = {'CACHE_TYPE': 'filesystem', 'CACHE_DIR': '/data/cache'}


def create_app(config_name):
    app = Flask(__name__, static_folder=os.path.join(os.getcwd(), 'static'), static_url_path='/static')
    # Swagger(app)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    CORS(app)
    # 5.3.1升级依赖包后修改语法，注释
    # Cache(app, config=cache_config, with_jinja2_ext=False)

    db.init_app(app)

    from .api_1_0 import api_entity as api_1_0_entity_blueprint
    app.register_blueprint(api_1_0_entity_blueprint, url_prefix='/entity')

    from .api_1_0 import api_document as api_1_0_docment_blueprint
    app.register_blueprint(api_1_0_docment_blueprint, url_prefix='/doc')

    from .api_1_0 import api_customer as api_1_0_customer_blueprint
    app.register_blueprint(api_1_0_customer_blueprint, url_prefix='/customer')

    from .api_1_0 import api_catalog as api_1_0_catalog_blueprint
    app.register_blueprint(api_1_0_catalog_blueprint, url_prefix='/catalog')

    from .api_1_0 import api_entity_category as api_1_0_entity_category_blueprint
    app.register_blueprint(api_1_0_entity_category_blueprint, url_prefix='/entity_category')

    from .api_1_0 import api_event_category as api_1_0_event_category_blueprint
    app.register_blueprint(api_1_0_event_category_blueprint, url_prefix='/event_category')

    from .api_1_0 import api_event_class as api_1_0_event_class_blueprint
    app.register_blueprint(api_1_0_event_class_blueprint, url_prefix='/event_class')

    from .api_1_0 import api_relation_category as api_1_0_relation_category_blueprint
    app.register_blueprint(api_1_0_relation_category_blueprint, url_prefix='/relation_category')

    from .api_1_0 import api_event as api_1_0_event_blueprint
    app.register_blueprint(api_1_0_event_blueprint, url_prefix='/event')

    from .api_1_0 import api_permission as api_1_0_permission_blueprint
    app.register_blueprint(api_1_0_permission_blueprint, url_prefix='/permission')

    from .api_1_0 import api_initial as api_1_0_initial_blueprint
    app.register_blueprint(api_1_0_initial_blueprint, url_prefix='/initial')

    from .api_1_0 import api_document_records as api_1_0_document_records_blueprint
    app.register_blueprint(api_1_0_document_records_blueprint, url_prefix='/doc_records')

    from .api_1_0 import api_place as api_1_0_place_blueprint
    app.register_blueprint(api_1_0_place_blueprint, url_prefix='/place')

    return app
