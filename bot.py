import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
from config import TOKEN, GROUP_ID, ADMIN_IDS
from database import init_db
from words import WORDS, LOCATIONS
 
PHOTO_WELCOME     = 'photo-237196588_457239029'
PHOTO_INSTRUCTION = 'photo-237196588_457239030'
PHOTO_RULES       = 'photo-237196588_457239031'
PHOTO_LOCATIONS   = 'photo-237196588_457239032'
PHOTO_THANKS      = 'photo-237196588_457239033'
 
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
 
def send(user_id, message, keyboard=None, attachment=None):
    params = {'user_id': user_id, 'message': message, 'random_id': 0}
    if keyboard:
        params['keyboard'] = keyboard.get_keyboard()
    if attachment:
        params['attachment'] = attachment
    vk.messages.send(**params)
 
def get_player(user_id):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    conn.close()
    return player
 
def create_player(user_id):
    user_info = vk.users.get(user_ids=user_id)[0]
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO players (user_id, first_name, last_name) VALUES (?, ?, ?)',
              (user_id, user_info['first_name'], user_info['last_name']))
    conn.commit()
    conn.close()
 
def update_player(user_id, **kwargs):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    for key, value in kwargs.items():
        c.execute(f'UPDATE players SET {key} = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
    conn.close()
 
def get_word_status(user_id, word_id):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('SELECT status FROM word_progress WHERE user_id = ? AND word_id = ?', (user_id, word_id))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 'open'
 
def set_word_status(user_id, word_id, status):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO word_progress (user_id, word_id, status) VALUES (?, ?, ?)',
              (user_id, word_id, status))
    conn.commit()
    conn.close()
 
def get_next_coupon():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('SELECT number FROM coupons WHERE is_used = 0 ORDER BY number LIMIT 1')
    row = c.fetchone()
    if row:
        c.execute('UPDATE coupons SET is_used = 1 WHERE number = ?', (row[0],))
        conn.commit()
    conn.close()
    return row[0] if row else None
 
def get_next_prize():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('SELECT number FROM prizes WHERE is_used = 0 ORDER BY number LIMIT 1')
    row = c.fetchone()
    if row:
        c.execute('UPDATE prizes SET is_used = 1 WHERE number = ?', (row[0],))
        conn.commit()
    conn.close()
    return row[0] if row else None
 
def keyboard_start():
    kb = VkKeyboard(one_time=True)
    kb.add_button('Участвую', color=VkKeyboardColor.POSITIVE)
    return kb
 
def keyboard_instruction():
    kb = VkKeyboard(one_time=True)
    kb.add_button('Далее', color=VkKeyboardColor.POSITIVE)
    return kb
 
def keyboard_rules():
    kb = VkKeyboard(one_time=True)
    kb.add_button('Я согласен с правилами', color=VkKeyboardColor.POSITIVE)
    return kb
 
def keyboard_locations():
    kb = VkKeyboard(one_time=False)
    kb.add_button('Большой дворец', color=VkKeyboardColor.PRIMARY)
    kb.add_button('Хлебный дом', color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button('Первый оранжерейный корпус', color=VkKeyboardColor.PRIMARY)
    kb.add_button('Третий кавалерский корпус', color=VkKeyboardColor.PRIMARY)
    return kb
 
def keyboard_back():
    kb = VkKeyboard(one_time=False)
    kb.add_button('⬅ К локациям', color=VkKeyboardColor.SECONDARY)
    return kb
 
def keyboard_i_am_here():
    kb = VkKeyboard(one_time=True)
    kb.add_button('Я на месте', color=VkKeyboardColor.POSITIVE)
    return kb
 
def keyboard_prize_confirm():
    kb = VkKeyboard(one_time=True)
    kb.add_button('Приз получен', color=VkKeyboardColor.POSITIVE)
    return kb
 
def handle_message(user_id, text):
    player = get_player(user_id)
    if player is None:
        create_player(user_id)
        player = get_player(user_id)
 
    state = player[4]
    score = player[3]
 
    # --- СТАРТ ---
    if text.lower() in ['начать', 'start', '/start', 'привет'] or state == 'start':
        update_player(user_id, state='rules')
        send(user_id,
             'Здравствуйте, дорогой посетитель!\n\nДобро пожаловать в игру музея ГМЗ «Царицыно».\nНажмите кнопку ниже, чтобы начать.',
             keyboard_start(),
             attachment=PHOTO_WELCOME)
        return
 
    # --- УЧАСТВУЮ -> показываем инструкцию ---
    if text == 'Участвую':
        instruction_text = (
            'С величайшею радостию в сердце уведомляем Вас о правилах нашей игры.\n\n'
            'Во дворце и других строениях найти можно пятьдесят карточек, на коих начертаны слова и цифры '
            '(к примеру, «Белка – 13»). В настоящем чате после выбора локации надлежит вписывать названия '
            'и номера найденных карточек. Бот принимает только правильные сочетания.\n\n'
            'Отыскать следует как можно больше карточек. По окончании поисков возвратитесь в главное фойе '
            'музея и покажите администраторам, чего достигли. Собравшие 10, 40 или 50 карточек получат '
            'вознаграждение за старания.\n\n'
            'Покорнейше просим соблюдать следующие установления:\n'
            '1. Дабы узреть карточки, не потребуется ни трогать экспонаты (кроме тактильных макетов, '
            'на коих имеется особый знак), ни отворять двери в закрытые помещения: карточки размещены на видных местах.\n'
            '2. Забирать карточки с собою не следует — довольно отправить обнаруженные на них слова и числа '
            'в чат, а сами карточки оставить для иных ищущих.\n'
            '3. Возвратиться не позднее 23 часов 30 минут.'
        )
        send(user_id, instruction_text, keyboard_instruction(), attachment=PHOTO_INSTRUCTION)
        update_player(user_id, state='awaiting_rules')
        return
 
    # --- ДАЛЕЕ -> показываем правила (награды) ---
    if text == 'Далее' and state == 'awaiting_rules':
        rules_text = (
            'О наградах за усердие:\n\n'
            'Если собрано 10 карточек — стикерпак музея нашего.\n'
            'Если собрано 40 карточек — купон на один напиток в кофейне «17 75».\n'
            'Если собраны все 50 карточек — особые дары: пригласительные на концерт для двух человек '
            'или книга-путеводитель по Царицыну.\n\n'
            'Купоны предусмотрены для первых 50 участников, собравших надлежащее количество карточек; '
            'один из особых даров — для первых 20 участников.\n\n'
            'Желаем незабываемого времяпрепровождения в стенах нашего музея и успеха в поисках!'
        )
        send(user_id, rules_text, keyboard_rules(), attachment=PHOTO_RULES)
        update_player(user_id, state='awaiting_agree')
        return
 
    # --- СОГЛАСЕН С ПРАВИЛАМИ ---
    if text == 'Я согласен с правилами':
        send(user_id, 'Я сейчас здесь:', keyboard_locations(), attachment=PHOTO_LOCATIONS)
        update_player(user_id, state='locations')
        return
 
    # --- ВОЗВРАТ К ЛОКАЦИЯМ ---
    if text == '⬅ К локациям':
        update_player(user_id, state='locations', current_word_id=None, attempts_left=2)
        send(user_id, 'Я сейчас здесь:', keyboard_locations(), attachment=PHOTO_LOCATIONS)
        return
 
    # --- Я НА МЕСТЕ ---
    if text == 'Я на месте' and state == 'prize_waiting':
        update_player(user_id, state='prize_confirm')
        send(user_id, 'Подтвердите получение приза у волонтёра и нажмите кнопку ниже.', keyboard_prize_confirm())
        return
 
    # --- ПРИЗ ПОЛУЧЕН ---
    if text == 'Приз получен' and state == 'prize_confirm':
        update_player(user_id, state='done')
        send(user_id,
             'Спасибо, что приняли участие в нашем квесте!\n\n'
             'Благодарим Анну Махонину, студентку Центрального университета, '
             'за разработку данного бота.\n\n'
             'Подписывайтесь на нашу группу ВКонтакте: https://vk.com/tsaritsynomuseum',
             attachment=PHOTO_THANKS)
        return
 
    # --- ЛОКАЦИИ ---
    location_map = {
        'Большой дворец': 'big_palace',
        'Хлебный дом': 'bread_house',
        'Первый оранжерейный корпус': 'greenhouse',
        'Третий кавалерский корпус': 'cavalier',
    }
 
    if text in location_map:
        location_key = location_map[text]
        location_name = LOCATIONS[location_key]
        update_player(user_id, state=f'answer_{location_key}', current_word_id=None, attempts_left=2)
        send(user_id,
             f'📍 {location_name}\n\nВведите слово и цифру с найденной карточки (например: Белка 13)\n\nДля возврата к выбору локации нажмите кнопку ниже.',
             keyboard_back())
        return
 
    # --- ОТВЕТ НА КАРТОЧКУ ---
    for loc_key in LOCATIONS.keys():
        if state == f'answer_{loc_key}':
            attempts_left = player[6]
            parts = text.strip().rsplit(None, 1)
            if len(parts) != 2:
                send(user_id, 'Пожалуйста, введите слово и цифру через пробел.\nНапример: Белка 13')
                return
            word_part = parts[0].strip()
            num_part = parts[1].strip()
            try:
                answer_num = int(num_part)
            except ValueError:
                send(user_id, 'Последний символ должен быть числом.\nНапример: Белка 13')
                return
            word_obj = next(
                (w for w in WORDS if w['location'] == loc_key
                 and w['text'].lower().strip() == word_part.lower().strip()
                 and w['answer'] == answer_num), None)
            if word_obj is None:
                attempts_left -= 1
                if attempts_left > 0:
                    update_player(user_id, attempts_left=attempts_left)
                    send(user_id, f'Неверно. Осталось попыток: {attempts_left}\n\nПроверьте слово и цифру и попробуйте ещё раз.')
                else:
                    update_player(user_id, attempts_left=2)
                    send(user_id, 'Попытки исчерпаны. Попробуйте найти другую карточку или переключитесь на другую локацию.', keyboard_back())
                return
            status = get_word_status(user_id, word_obj['id'])
            if status == 'correct':
                send(user_id, f'Карточка «{word_obj["text"]}» уже была найдена ранее! Попробуйте другую.')
                return
            set_word_status(user_id, word_obj['id'], 'correct')
            new_score = score + 1
            update_player(user_id, score=new_score, attempts_left=2)
            send(user_id, f'Верно! Найдено {new_score} из 50.')
            check_milestones(user_id, new_score, player)
            return
 
    # --- ЕСЛИ НИЧЕГО НЕ ПОДОШЛО ---
    send(user_id, 'Я сейчас здесь:', keyboard_locations(), attachment=PHOTO_LOCATIONS)
 
 
def check_milestones(user_id, score, player):
    got_sticker = player[7]
    got_coupon = player[8]
    got_prize = player[10]
 
    if score >= 10 and not got_sticker:
        update_player(user_id, got_sticker=1)
        send(user_id,
             'Вы – настоящий искатель!\n\n'
             'Вы собрали правильно 10 карточек. Для получения стикерпака в подарок '
             'нужно подойти до конца игры в Подземное пространство Большого дворца '
             'и показать это сообщение.')
 
    if score >= 40 and not got_coupon:
        coupon_number = get_next_coupon()
        if coupon_number:
            update_player(user_id, got_coupon=1, coupon_number=coupon_number)
            send(user_id,
                 f'Вы – опытный следопыт!\n\nВы собрали 40 карточек. Подойдите к администратору '
                 f'в Подземное пространство Большого дворца и покажите это сообщение.\n\n'
                 f'Купон №{coupon_number} на один напиток в кофейне «17 75».\n\n'
                 f'Полученный купон пожалуйста не теряйте.\n'
                 f'Важно: количество купонов ограничено и напиток можно забрать до конца игры.')
 
    if score >= 50 and not got_prize:
        prize_number = get_next_prize()
        if prize_number:
            update_player(user_id, got_prize=1, prize_number=prize_number, state='prize_waiting')
            send(user_id,
                 f'Ура! Вы – истинный исследователь нашего музея!\n\n'
                 f'Вы собрали правильно все 50 карточек.\n\n'
                 f'Получите главный приз №{prize_number} у волонтёра в Подземном '
                 f'пространстве Большого дворца, показав это сообщение.\n\n'
                 f'Когда будете у волонтёра — нажмите кнопку ниже.',
                 keyboard_i_am_here())
 
 
if __name__ == '__main__':
    init_db()
    print('Бот запущен!')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            handle_message(event.user_id, event.text)