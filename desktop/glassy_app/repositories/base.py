"""Base repository with shared CRUD helpers.

Repositories own all SQL. Services never build SQL strings and the UI never
touches a repository directly, which keeps the query surface in one layer.
"""

from ..core.models import now_iso


class BaseRepository:
    table = ""
    columns = ()

    def __init__(self, db):
        self.db = db

    def _insert(self, data):
        data = dict(data)
        data.setdefault("created_at", now_iso())
        data["updated_at"] = now_iso()
        keys = [k for k in data if k in self.columns]
        placeholders = ", ".join("?" for _ in keys)
        sql = (
            f"INSERT INTO {self.table} ({', '.join(keys)}) "
            f"VALUES ({placeholders})"
        )
        return self.db.insert(sql, [data[k] for k in keys])

    def _update(self, row_id, data):
        data = {k: v for k, v in dict(data).items() if k in self.columns}
        data["updated_at"] = now_iso()
        assignments = ", ".join(f"{k}=?" for k in data)
        sql = f"UPDATE {self.table} SET {assignments} WHERE id=?"
        self.db.execute(sql, [*data.values(), row_id])
        return row_id

    def get(self, row_id):
        return self.db.query_one(
            f"SELECT * FROM {self.table} WHERE id=?", (row_id,)
        )

    def all(self, order_by="id"):
        return self.db.query(f"SELECT * FROM {self.table} ORDER BY {order_by}")

    def count(self):
        row = self.db.query_one(f"SELECT COUNT(*) AS n FROM {self.table}")
        return row["n"] if row else 0

    def delete(self, row_id):
        self.db.execute(f"DELETE FROM {self.table} WHERE id=?", (row_id,))
        return row_id
