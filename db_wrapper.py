from psycopg2.extras import RealDictCursor
import psycopg2

class NeonDB:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=()):
        # Replace SQLite placeholders (?) with Postgres ones (%s)
        # Note: This is a simple replacement. If '?' appears in strings, it might break.
        # Given the app simplicity, this is likely fine.
        query = query.replace('?', '%s')
        
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(query, params)
            return cur
        except Exception as e:
            self.conn.rollback()
            raise e

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
