# -*- coding:utf-8 -*-
# @Author :MaYuhui
# work_location: Bei Jing
# @File : entity_dict.py 
# @Time : 2020/9/21 10:29


get_all_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [{
        "name": "cur_page",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "current page"
    },
    {
        "name": "page_size",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "page_size"
    },
    {
        "name": "category_id",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "category_id of entity"
    }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Getting all entity"
        }
    }
}

insert_entity_dict = {
    "swagger": "2.0",
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [{
        "name": "category_id, name,props, synonyms, summary",
        "in": "body",
        #"required": "true",
        "schema":{
            "required":"category_id, name,",
            "properties":{
                "category_id":{"type": "integer"},
                "name":{"type": "string"},
                "props":{
                        "type": "object",
                        "items": {"type": "string"}},
                "synonyms":{
                        "type": "array",
                        "items": {"type": "string"}},
                "summary": {"type": "string"}
                }
            }
        }],
    "responses":{
        "500":
            {"description": "Error !"},
        "200":{
            "description": "Adding one entity",
             "schema":{
                "properties":{
                    "category_id":{
                        "type": "integer",
                        "description": "category_id of entity"
                    },
                    "name":{
                        "type": "string",
                        "description": "name of entity",
                        "default": ""
                    },
                    "props":{
                        "type": "object",
                        "items": {"type": "string"},
                        "description": "props of entity"
                    },
                    "synonyms":{
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "synonyms of entity"
                    },
                    "summary":{
                        "type": "string",
                        "description": "summary of entity",
                        "default": ""
                    }
                }
            }
        }
    }
}

update_entity_dict = {
    "swagger": "2.0",
    "tags": [{
        "name": "entity"
        }],
    "parameters": [{
            "name": "id, category_id, name,props, synonyms, summary",
            "in": "body",
            #"required": "true",
            "descriptions": "id of entity, name of entity",
            "schema":{
                "required":"id,category_id, name",
                "properties":{
                    "id":{"type": "integer"},
                    "category_id":{"type": "integer"},
                    "name":{"type": "string"},
                    "props":{
                        "type": "object",
                        "items": {"type": "string"}},
                    "synonyms":{
                        "type": "array",
                        "items": {"type": "string"}},
                    "summary": {"type": "string"}
                    }
                }
        }],
    "responses": {
          "500":
              {"description": "Error !"},
          "200":
              {"description": "Modifying one entity"}
            }
}

delete_entity_dict = {
    "tags": [
        {
            "name": "entity"
        }],
    "parameters": [{
        "name": "id, synonyms",
        "in": "body",
        "required": "true",
        "schema":{
            "required":"id",
            "properties":{
                "id":{
                "type": "integer"}
            }}
    }],
    "responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Deleting one entity"}
        }
}

delete_entity_by_ids_dict ={
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [{
        "name": "ids",
        "in": "body",
        "required": "true",
        "schema":{
            "required":"ids",
            "properties":{
                "ids":{
                    "type": "array",
                    "items":{
                        "type": "integer"}
                }
            }}
    }],
    "responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Deleting multi entity"}
        }
}

add_synonyms_dict = {
    "swagger": "2.0",
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [{
        "name": "id, synonyms",
        "in": "body",
        "required": "true",
        "schema":{
            "required":"id, synonyms",
            "properties":{
                "id":{"type": "integer"},
                "synonyms":{
                        "type": "array",
                        "items": {"type": "string"}}
                }
            }
        }],
    "responses":{
        "500":
            {"description": "Error !"},
        "200":{
            "description": "Adding one entity",
             "schema":{
                "properties":{
                    "id":{
                        "type": "integer",
                        "description": "id of entity"
                    },
                    "synonyms":{
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "synonyms of entity"
                    }
                }
            }
        }
    }
}

delete_synonyms_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [{
        "name": "id, synonyms",
        "in": "body",
        "required": "true",
        "schema": {
            "required": "id, synonyms",
            "properties": {
                "id": {
                    "type": "integer"},
                "synonyms": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }}
    }],
    "responses": {
        "500":
            {"description": "Error !"},
        "200":
            {"description": "delete synonyms"}
    }
}

get_linking_entity_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [
        {
            "name": "search",
            "in": "query",
            "type": "string",
            "required": "true",
            "description": "search"
        },
        {
            "name": "category_id",
            "in": "query",
            "type": "integer",
            "required": "true",
            "description": "category_id"
        }],

    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting linking entity"}
    }
}

get_top_list_es_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [
        {
            "name": "search",
            "in": "query",
            "type": "string",
            "required": "true",
            "description": "search"
        },
        {
            "name": "category_id",
            "in": "query",
            "type": "integer",
            "required": "true",
            "description": "category_id"
        }],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting top list"
        }
    }
}

get_search_panigation_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [{
        "name": "cur_page",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "current page"
    },
    {
        "name": "search",
        "in": "query",
        "type": "string",
        # "required": "true",
        "description": "search"
    },
    {
        "name": "page_size",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "page_size"
    },
    {
        "name": "category_id",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "category_id of entity"
    }],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting search panigation"
        }
    }
}


get_entity_data_es_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [
        {
            "name": "search",
            "in": "query",
            "type": "string",
            "required": "true",
            "description": "entity data"
        }],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting entity data by entity_name"}
    }
}

get_entity_info_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [
        {
            "name": "id",
            "in": "query",
            "type": "integer",
            "required": "true",
            "description": "id of entity"
        }],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting entity info by id"}
    }
}

get_entity_data_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [
        {
            "name": "search",
            "in": "query",
            "type": "string",
            "required": "true",
            "description": "search of entity"
        }],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting entity data by search"}
    }
}

get_top_list_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [
        {
            "name": "search",
            "in": "query",
            "type": "string",
            # "required": "true",
            "description": "search"
        },
        {
            "name": "category_id",
            "in": "query",
            "type": "integer",
            "required": "true",
            "description": "category_id of entity"
        }],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting top list"
        }
    }
}

get_search_panigation_pg_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [{
        "name": "cur_page",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "current page"
    },
    {
        "name": "search",
        "in": "query",
        "type": "string",
        # "required": "true",
        "description": "search"
    },
    {
        "name": "page_size",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "page_size"
    }],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting all panigation pg"
        }
    }
}

download_entity_excel_example_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting all panigation pg"
        }
    }
}

import_entity_excel_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [{
            "name": "file",
            "in": "body",
            "required": "true",
            "schema":{
                "required":"file",
                "properties":{
                    "file":{
                    "type": "array",
                        "items":{"type": "file"}
                    }
                }
            }
        }],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "Getting all panigation pg"
        }
    }
}

import_entity_excel_straightly_dict = {
    "tags": [
        {
            "name": "entity"
        }
    ],
    "parameters": [{
            "name": "file",
            "in": "body",
            "required": "true",
            "schema":{
                "required":"file",
                "properties":{
                    "file":{
                    "type": "array",
                        "items":{"type": "file"}
                    }
                }
            }
        }],
    "responses": {
        "500": {"description": "Error !"},
        "200": {
            "description": "import_entity_excel_straightly"
        }
    }
}




