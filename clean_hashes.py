import sqlite3
conn = sqlite3.connect('data_storage/knowledge_base.db')
cur = conn.cursor()
cur.execute("DELETE FROM users WHERE password_hash NOT LIKE '$2%'")
print('Deleted rows:', cur.rowcount)
conn.commit()
conn.close()
