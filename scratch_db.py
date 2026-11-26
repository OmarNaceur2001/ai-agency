import sqlite3, json
conn = sqlite3.connect(r'D:\ai-agency-tools\flowise\data\database.sqlite')
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])
for t in tables:
    tname = t[0]
    try:
        cols = c.execute(f'PRAGMA table_info({tname})').fetchall()
        colnames = [col[1] for col in cols]
        print(f'\n{tname} columns: {colnames}')
        rows = c.execute(f'SELECT * FROM {tname} LIMIT 2').fetchall()
        if rows:
            print(f'  {len(rows)} row(s)')
            for r in rows:
                row_str = str(r)
                # Mask anything that looks like a password hash
                if 'password' in str(colnames).lower() or 'credential' in str(colnames).lower():
                    print(f'  [row hidden - contains sensitive columns]')
                else:
                    print(f'  {row_str[:400]}')
        else:
            print('  (empty)')
    except Exception as e:
        print(f'  Error: {e}')
conn.close()
