import MySQLdb


def put_info_for_peer(data_object: dict):
    conn = MySQLdb.connect(host='futurebass.mysql.pythonanywhere-services.com', user='futurebass',
                           password='pivotrulez1234567891011121315', database='futurebass$peer_ids',
                           use_unicode=True, charset='utf8')

    try:
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO operations_queue VALUES (NULL, %s);""", (str(data_object),))  # comma means tuple
        conn.commit()
    finally:
        conn.close()
