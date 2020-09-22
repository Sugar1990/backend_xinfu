upload_doc_dict = {
    "tags": [
        {
            "name": "document"
        }
    ],
    "parameters":[
        {
            "name": "catalog_id",
            "in": "formData",
            "type": "integer",
            "required": "true",
            "description": "id of catalog"
        },
        {
            "name": "uid",
            "in": "formData",
            "type": "integer",
            "required": "true",
            "description": "id of customer"
        },
        {
            "name": "file",
            "in": "formData",
            "required": "true",
            "type": "array",
            "items":{"type": "file"},
            "description": "filepath of docs"
        }
    ],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Upload !"}
        }
}

get_doc_realpath_dict = {
    "tags": [
        {
            "name": "document"
        }
    ],
    "parameters":[
        {
            "name": "doc_id",
            "in": "query",
            "type": "integer",
            "required": "true",
            "description": "id of doc"
        }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Getting path of doc !"}
        }
}

get_content_dict = {
    "tags": [
        {
            "name": "document"
        }
    ],
    "parameters":[
        {
            "name": "doc_id",
            "in": "query",
            "type": "integer",
            "required": "true",
            "description": "id of doc"
        }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Getting content of doc !"}
        }
}

modify_doc_info_dict = {
    "tags": [
        {
            "name": "document"
        }
    ],
    "parameters": [{
        "name": "body",
        "in": "body",
        "required": "true",
        "descriptions": "id of doc, name of doc and status of doc",
        "schema":{
            "required":"doc_id, name, status",
            "properties":{
                "doc_id":{
                    "type": "integer"},
                "name":{
                    "type": "string"},
                "status":{
                    "type": "integer"}
                }
            }
    }],
"responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Modifying one doc !"}
        }
}

del_doc_dict = {
    "tags": [
        {
            "name": "document"
        }
    ],
    "parameters": [{
        "name": "body",
        "in": "body",
        "required": "true",
        "descriptions": "ids of doc, id of customer",
        "schema":{
            "required":"doc_ids, customer_id",
            "properties":{
                "doc_ids":{
                    "type": "array",
                    "items":{
                        "type": "integer"}},
                "customer_id":{
                    "type": "integer"}
                }
            }
    }],
"responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Delete docs !"}
        }
}

get_upload_history_dict = {
"tags": [
        {
            "name": "document"
        }
    ],
    "parameters": [
        {
        "name": "cur_page",
        "in": "query",
        "type":"integer",
        "required": "true",
        "descriptions": "current page"},
        {
        "name": "page_size",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "page size"
        },
        {
        "name": "customer_id",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "id of customer"
        }
    ],
"responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Get upload history !"}
        }
}

get_info_dict = {
"tags": [
        {
            "name": "document"
        }
    ],
    "parameters": [
        {
        "name": "doc_id",
        "in": "query",
        "type": "integer",
        "required": "true",
        "descriptions": "id of doc"}
    ],
"responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Get doc info !"}
        }
}

get_entity_in_list_pagination_dict = {
    "tags": [
        {
            "name": "document"
        }
    ],
    "parameters": [
        {
        "name": "search",
        "in": "query",
        "type":"string",
        "required": "true",
        "descriptions": "item for filtering docs"},
        {
        "name": "customer_id",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "id of customer"
        },
        {
        "name": "cur_page",
        "in": "query",
        "type":"integer",
        "required": "true",
        "descriptions": "current page"},
        {
        "name": "page_size",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "page size"
        }
    ],
"responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Get entity pagination !"}
        }
}

judge_doc_permission_dict = {
    "tags": [
        {
            "name": "document"
        }
    ],
    "parameters": [
        {
        "name": "customer_id",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "id of customer"
        },
        {
        "name": "doc_id",
        "in": "query",
        "type":"integer",
        "required": "true",
        "descriptions": "id of doc"}
    ],
"responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Get doc pagination !"}
        }
}

get_search_panigation_dict = {
"tags": [
        {
            "name": "document"
        }
    ],
    "parameters": [
        {
        "name": "customer_id",
        "in": "query",
        "type": "integer",
        "default": 0,
        "required": "true",
        "description": "id of customer"
        },
        {
        "name": "search",
        "in": "query",
        "type":"string",
        "required": "true",
        "descriptions": "item for filtering docs"},
        {
        "name": "search_type",
        "in": "query",
        "type": "string",
        "required": "true",
        "description": "search type"
        },
        {
        "name": "page_size",
        "in": "query",
        "type": "integer",
        "default": 10,
        "required": "true",
        "description": "page size"
        },
        {
        "name": "cur_page",
        "in": "query",
        "type":"integer",
        "default": 1,
        "required": "true",
        "descriptions": "current page"}
    ],
"responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Get doc pagination !"}
        }
}

search_advanced_dict = {
    "tags": [
        {
            "name": "document"
        }
    ],
    "parameters": [{
        "name": "body",
        "in": "body",
        "required": "true",
        "schema":{
            "required":"start_date, end_date, dates, places, customer_id, entities,"
                       " keywords, event_categories, notes, doc_type, content",
            "properties":{
                "start_date":{
                    "type": "string"},
                "end_date":{
                    "type": "string"},
                # "dates": {
                #     "type":"array",
                #     "items":{
                #             "properties":{
                #                 "date_type":{
                #                     "type": "string",
                #                     "enum":{"date","time_range","time_period"}
                #                 },
                #                 "value":{
                #                     "type":"array",
                #                     "items":{
                #                         "type": "string"}
                #                 }
                #             }
                #     }},
                "places":{
                    "schema": {
                        "$ref": "#/definitions/places"
                    }},
                "customer_id":{
                    "type": "integer"},
                "entities":{
                    "type": "array",
                    "items":{
                        "type": "string"}},
                "event_categories":{
                    "type": "array",
                    "items":{
                        "properties":{
                            "event_class":{"type":"integer"},
                            "event_category_id":{"type":"integer"}
                        }}},
                "notes":{
                    "type": "array",
                    "items":{
                        "type": "string"}},
                "doc_type":{
                    "type": "integer"},
                "content":{
                    "type": "string"}}}
    }],
    "responses": {
      "500":
          {"description": "Error !"},
      "200":
          {"description": "Get search results"}
        }}

get_latest_upload_file_tagging_url = {
    "tags": [
        {
            "name": "document"
        }
    ],
    "parameters":[
    {
        "name": "uid",
        "in": "query",
        "type": "integer",
        "required": "true",
        "description": "id of customer"
    }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Getting latest_upload_file_tagging_url"
        }
    }
}

