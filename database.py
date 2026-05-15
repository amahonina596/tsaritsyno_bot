import sqlite3

def init_db():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        score INTEGER DEFAULT 0,
        state TEXT DEFAULT 'start',
        current_word_id INTEGER DEFAULT NULL,
        attempts_left INTEGER DEFAULT 2,
        got_sticker INTEGER DEFAULT 0,
        got_coupon INTEGER DEFAULT 0,
        coupon_number INTEGER DEFAULT NULL,
        got_prize INTEGER DEFAULT 0,
        prize_number INTEGER DEFAULT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS word_progress (
        user_id INTEGER,
        word_id INTEGER,
        status TEXT DEFAULT 'open',
        PRIMARY KEY (user_id, word_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS coupons (
        number INTEGER PRIMARY KEY,
        is_used INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS prizes (
        number INTEGER PRIMARY KEY,
        is_used INTEGER DEFAULT 0
    )''')

    for i in range(1, 51):
        c.execute('INSERT OR IGNORE INTO coupons (number) VALUES (?)', (i,))

    for i in range(1, 21):
        c.execute('INSERT OR IGNORE INTO prizes (number) VALUES (?)', (i,))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("База данных создана успешно!")