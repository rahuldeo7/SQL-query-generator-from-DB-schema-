def simplify_schema(raw_schema: dict) -> dict:
    """
    Converts raw JSON schema to simplified reference dictionary for GPT.
    """
    tables = {}
    primary_keys = {}
    foreign_keys = {}

    for table_name, columns in raw_schema.items():
        tables[table_name] = []
        primary_keys[table_name] = []

        for col in columns:
            col_name = col.get("name")
            tables[table_name].append(col_name)

            # Primary key
            if str(col.get("isPrimaryKey", "false")).lower() == "true":
                primary_keys[table_name].append(col_name)

            # Foreign key
            fk = col.get("foreignKeys")
            if fk:
                foreign_keys[f"{table_name}.{col_name}"] = f"{fk['foreign_Table_Name']}.{fk['foreign_Column']}"

    return {
        "tables": tables,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys
    }