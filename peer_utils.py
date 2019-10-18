import MySQLdb


class DB:
    conn = None

    def __init__(self):
        self.connect()

    def connect(self):
        self.conn = MySQLdb.connect(host='futurebass.mysql.pythonanywhere-services.com', user='futurebass',
                                    password='pivotrulez1234567891011121315', database='futurebass$peer_ids',
                                    use_unicode=True, charset='utf8')

    def query(self, sql, params: tuple = None):
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
        return cursor


class PeerStorage:
    peers: dict  # of dicts
    forbidden_genres_key = 'forbidden_genres'
    # str forbidden_genres: rap,rock,pop,etc
    db = DB()

    def __init__(self):
        cursor = self.db.query("""SELECT * FROM peers;""")
        self.db.conn.commit()
        self.peers = dict()
        peers_tuple = cursor.fetchall()
        for peer in peers_tuple:
            self.peers[int(peer[0])] = {self.forbidden_genres_key: peer[1]}

    def __getitem__(self, item):
        try:
            return self.peers[item]
        except KeyError:
            self.__init__()
            try:
                return self.peers[item]
            except KeyError:
                self.insert_peer(item)
                return self.peers[item]

    def _check_peer_exists(self, peer_id: int) -> bool:
        return peer_id in self.peers.keys()

    def insert_peer(self, peer_id: int, forbidden_genres='rap'):
        if not self._check_peer_exists(peer_id):
            self.peers[peer_id] = {self.forbidden_genres_key: forbidden_genres}
            self.db.query("""INSERT INTO peers(peer_id, forbidden_genres) VALUES (%s, %s)""", (peer_id,
                                                                                               forbidden_genres))
            self.db.conn.commit()
            print('current dict state is: ', self.peers)

    def edit_peer(self, peer_id: int, forbidden_genres):
        if self._check_peer_exists(peer_id):
            self.peers[peer_id][self.forbidden_genres_key] = forbidden_genres
            self.db.query("""UPDATE peers SET forbidden_genres=%s WHERE peer_id=%s""",
                          (forbidden_genres, peer_id))
            self.db.conn.commit()
        else:
            self.insert_peer(peer_id, forbidden_genres)
        print('current dict state is: ', self.peers)


peer_storage = PeerStorage()
