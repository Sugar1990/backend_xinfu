# excel批量导入实体
@blue_print.route('import_entity_excel', methods=['POST'])
def import_entity_excel():
    file_list = request.files.getlist('file', None)
    for file_obj in file_list:
        filename = secure_filename(''.join(lazy_pinyin(file_obj.filename)))
        file_savepath = os.path.join(UPLOAD_PATH, filename)
        file_obj.save(file_savepath)

    data = xlrd.open_workbook(excel_file)
    table = data.sheet_by_index(0)

    entities = []
    # 实体名称	实体类型    实体别名    实体属性
    for row_index in range(1, table.nrows):
        try:
            row_value = table.row_values(row_index)

            category_id = EntityCategory.get_category_id(row_value[1].strip())
            if category_id:
                ex_name = row_value[0].strip()
                # 解析属性
                ex_props = {}
                for prop_str in row_value[3].strip().split('\n'):
                    if re.match('(.*)：(.*)', prop_str):
                        key, value = re.match('(.+?)：(.*)', prop_str).groups()
                        ex_props[key] = value
                # 解析别名
                ex_synonyms = []
                for synonym_str in row_value[2].strip().split('\n'):
                    if synonym_str:
                        ex_synonyms.append(synonym_str)

                entity = Entity.query.filter(or_(Entity.name == ex_name,
                                                 Entity.synonyms.has_key(ex_name),
                                                 Entity.name.in_(ex_synonyms),
                                                 Entity.synonyms.has_any(ex_props))).first()

                if entity:
                    print(entity)

        except:
            continue
