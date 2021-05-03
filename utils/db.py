from copy import deepcopy
from datetime import datetime
from itertools import chain
from sqlalchemy import bindparam, create_engine, text, select, and_, or_, tuple_
from sqlalchemy.dialects import mysql


def execute_sql(engine, sql, params=None):
    with engine.connect() as conn:

        print('params=', params)
        try:
            if params:
                query = text(sql).bindparams(values=params)
            else:
                query = text(sql)
            print(query)
            conn.execute(query.execution_options(autocommit=True))
        except:
            raise
        finally:
            conn.close()


def get_db_records(engine, sql, params=None):
    with engine.connect() as conn:
        try:
            if params:
                query = text(sql).bindparams(values=params)
            else:
                query = text(sql)
            results = conn.execute(query).fetchall()
            results_as_dicts = [{k: v for (k, v) in r.items()}
                                for r in results]
        except:
            raise
        finally:
            conn.close()

    return results_as_dicts


def get_db_records_by_pair_of_keys(engine, table, records, keys):
    select_columns = [table.c.id] + \
        [c for c in table.columns if c.name in keys]

    inner_conditions = [and_(
        *[(c == r[c.name]) for c in table.columns if c.name in keys]) for r in records]
    stmt = select(select_columns).where(
        or_(*inner_conditions)).select_from(table)

    # key_tuples = (c for c in table.columns if c.name in keys)
    # inner_tuples = [tuple(v for k, v in r.items() if k in keys) for r in records]
    # stmt = select(select_columns).where(
    #     tuple_(*key_tuples).in_(inner_tuples)).select_from(table)

    print(stmt.compile(compile_kwargs={"literal_binds": True}))

    with engine.connect() as conn:
        try:
            results = conn.execute(stmt, records).fetchall()
            results_as_dicts = [{k: v for (k, v) in r.items()}
                                for r in results]
        except:
            raise
        finally:
            conn.close()

    return results_as_dicts


def generate_record_key(record, keys, separator="|"):
    tmp = list()
    for k in keys:
        v = record[k]
        if isinstance(v, datetime):
            tmp.append(v.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            tmp.append(str(v))

    record_key = separator.join(tmp)
    return record_key


def generate_id_lookups(records, keys, separator="|"):
    lookups = {generate_record_key(r, keys): r.get("id") for r in records}
    return lookups


def generate_lookup_dict(records, keys, separator="|"):
    print('Generating lookup dictionary')
    lookups = {generate_record_key(
        r, keys): {k: v for k, v in r.items() if k not in keys} for r in records}

    return lookups


def custom_mysql_upsert(engine, table, records, key_fields, exclude_fields_on_update=[], op='upsert'):
    """
    This method developed to overcome https://dev.mysql.com/doc/refman/8.0/en/insert-on-duplicate.html
    Which causing a lot of garbage autoincrement
    - Currently support multiple keys / composite keys
    - Support only auto increment primary key column named `id`
    """
    table_name = table.name
    # list_of_keys = [(r[key_field], ) for r in records]

    # 1st: Find any existing record on target by unique/natural key and separate new record
    # [{"id": 1, "key1": "value_key1", "key2": "value_key2", "field1": "value1"}, ...]
    print("Find any existing record on target by unique/natural key")
    existing_records = get_db_records_by_pair_of_keys(
        engine=engine,
        table=table,
        records=records,
        keys=key_fields
    )
    print(existing_records)
    # Generate lookup_ids from existing records
    # {value_key1|value_key2": 1, ...}
    existing_lookup_ids = generate_id_lookups(existing_records, key_fields)

    insert_records = list()
    update_records = list()
    for r in records:
        record_key = generate_record_key(r, key_fields)
        id = existing_lookup_ids.get(record_key)

        if id:
            update_record = deepcopy(r)
            update_record.update({"_id": id, "id": id, })
            update_records.append(update_record)
        else:
            # print(record_key, existing_lookup_ids, r)
            # for k, v in r.items():
            #     print(v, type(v))
            insert_records.append(r)
    n_insert_records = len(insert_records)
    n_update_records = len(update_records)

    # # At this point, we got all the existing records based on incoming
    # # 2nd: Now, let's insert non exist records
    if n_insert_records > 0 and op in ('insert', 'upsert', ):
        print(f"Inserting non exist: {n_insert_records} records")
        with engine.connect() as conn:
            try:
                insert_stmt = mysql.insert(table).values(insert_records)
                conn.execute(insert_stmt)

            except Exception as e:
                raise e
            finally:
                conn.close()

    # # 3rd: Then, we update existing records
    if n_update_records > 0 and op in ('update', 'upsert', ):
        print(f"Update existing: {n_update_records} records")
        updatable_fields = {k for k in chain(*update_records)
                            if k not in exclude_fields_on_update
                            and k not in ('_id', 'id', )}
        # print('----DEBUG---')
        # print(updatable_fields)
        # for u in update_records[:5]:
        #     print(u)
        # print('----DEBUG---')
        with engine.connect() as conn:
            try:
                stmt = table.update().\
                    where(table.c.id == bindparam('_id')).\
                    values({c: bindparam(c) for c in updatable_fields})
                # print(stmt.compile(compile_kwargs={"literal_binds": True}))
                conn.execute(stmt, update_records)

                """
                Basically we re constructing this
                connection.execute(stmt, [
                    {'user_id': '12345', 'user_name': 'John', '_id': '12345'},
                    {'user_id': '11223', 'user_name': 'Andy', '_id': '11223'}
                ])
                """

            except Exception as e:
                raise e
            finally:
                conn.close()


def mysql_upsert(engine, table, records, exclude_fields):
    """
    WARNING!
    This method generates a lot of garbage autoincrement IDs
    https://dev.mysql.com/doc/refman/8.0/en/insert-on-duplicate.html
    Here is a simple explanation. MySQL attempts to do the insert first.
    This is when the id gets auto incremented. Once increment, it stays.
    Then the duplicate is detected and the update happens.
    But the value gets missed.
    """
    updatable_fields = {k for k in chain(*records)}
    with engine.connect() as conn:
        try:
            insert_stmt = mysql.insert(table).values(records)
            update_data = {col.name: col for col in insert_stmt.inserted
                           if col.name not in exclude_fields
                           and col.name in updatable_fields}
            update_stmt = insert_stmt.on_duplicate_key_update(update_data)
            conn.execute(update_stmt)

        except Exception as e:
            raise e
        finally:
            conn.close()


def sql_lookup(engine, sql, records, key_fields, default={}, preformat=False):
    enriched_records = deepcopy(records)
    with engine.connect() as conn:
        try:
            # If npt preformatted e.g no SQL.format()
            if not preformat:
                values = list()
                for r in records:
                    value = tuple([r[key] for key in key_fields])
                    if not any(map(lambda x: x is None, value)):
                        values.append(value)

                print(tuple(set(values)))

            if (not preformat) and (len(values) > 0):
                query = text(sql).bindparams(values=tuple(set(values)))
                results = conn.execute(query).fetchall()
                results_as_dicts = [{k: v for (k, v) in r.items()}
                                    for r in results]
                lookup_dict = generate_lookup_dict(results_as_dicts, key_fields)
            elif preformat:
                query = text(sql)
                results = conn.execute(query).fetchall()
                results_as_dicts = [{k: v for (k, v) in r.items()}
                                    for r in results]
                lookup_dict = generate_lookup_dict(results_as_dicts, key_fields)
                # print('lookup_dict')
                # print(lookup_dict)
            else:
                lookup_dict = {}

            for r in enriched_records:
                record_key = generate_record_key(r, key_fields)
                found = lookup_dict.get(record_key, default)
                
                # print('record_key', record_key, found)
                
                r.update(found)
        except:
            raise
        finally:
            conn.close()

    return enriched_records
