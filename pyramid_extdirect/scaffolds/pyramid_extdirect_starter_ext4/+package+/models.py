from operator import attrgetter
# fake container for users
USERS = dict()

def get_user(user_id):
    global USERS
    return USERS.get(user_id, None)

def add_user(user):
    global USERS
    if not user.id:
        user.id = len(USERS) + 1
    USERS[user.id] = user
    return user

def remove_user(user):
    global USERS
    USERS.pop(user.id)
    return user

def update_user(user):
    global USERS
    USERS[user.id] = user
    return user

def get_all(limit=25, offset=0, order_by='id', reverse_sort=False):
    ret = sorted(USERS.values(), key=attrgetter(order_by))
    if reverse_sort:
        ret = list(reversed(ret))
    return ret[offset:limit]

def get_count():
    return len(USERS)

def bootstrap():
    """ add some users to our "DB" """
    add_user(User('John Doe', 'Dr'))
    add_user(User('Hans Dampf', 'Mr'))
    add_user(User('Igor Stroh', TITLES[35]))

class User(object):

    def __init__(self, name, title=None, description=None):
        self.name = name
        if title not in TITLES:
            title = 'Mr'
        self.title_id = TITLES.index(title)
        self.description = description
        self.picture = None
        self.id = None

    @property
    def title(self):
        return TITLES[self.title_id]

    @title.setter
    def set_title(self, title):
        old = self.title_id
        if title in TITLES:
            self.title_id = TITLES.index(title)

    def json_repr(self):
        ret = self.__dict__
        ret['title'] = TITLES[ret['title_id']]
        return ret

TITLES = (
    'Mr',
    'Mrs',
    'Miss',
    'Ms',
    'Dr',
    'Professor',
    'The Rt Revd Dr',
    'The Most Revd',
    'The Rt Revd',
    'The Revd Canon',
    'The Revd',
    'The Rt Revd Professor',
    'The Ven',
    'The Most Revd Dr',
    'Rabbi',
    'Canon',
    'Dame',
    'Chief',
    'Sister',
    'Reverend',
    'Major',
    'Other',
    'Cllr',
    'Sir',
    'Rt Hon Lord',
    'Rt Hon',
    'The Lord ',
    'Viscount',
    'Viscountess',
    'Baroness',
    'Captain',
    'Master',
    'Very Revd',
    'Lady',
    'MP',
    'King of Kings and Lord of Lords',
    'Conquering Lion of the Tribe of Judah',
    'Elect of God and Light of this World',
    'His Own Divine Majesty',
    'First Ancient King of Creation',
    'King Alpha',
    'Queen Omega',
    'Beginning with Our End and First with Our Last',
    'Protector of All Human Faith',
    'Ruler of the Universe',
    'Dude',
    'Mx (gender-netural)',
    'His Holiness',
    'Her Holiness',
)
