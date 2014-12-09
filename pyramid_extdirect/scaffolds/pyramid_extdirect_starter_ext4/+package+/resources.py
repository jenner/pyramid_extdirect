import traceback
from pyramid_extdirect import extdirect_method
from .models import *

class UsersController(object):

    __extdirect_settings__ = {
        'default_action_name': 'Users',
    }

    def __init__(self, request):
        self.request = request
        self.image_handler = self.request.registry.image_handler

    # method_name is optional -- to make sure we comply
    # with both, python and ExtJS naming conventions
    # we expose the method in camel-case for ExtJS
    @extdirect_method(method_name='loadAll')
    def load_all(self, params):
        limit = params.get('limit', 25)
        offset = params.get('start', 0)
        sort_by = params.get('sort', 'name')
        reverse_order = params.get('dir', 'DESC').upper() == 'DESC'
        users = get_all(limit, offset, sort_by, reverse_order)
        return dict(
            total=get_count(),
            users=get_all(limit, offset, sort_by, reverse_order)
        )

    @extdirect_method(accepts_files=True)
    def edit(self, data):
        """ edit is called in form submits when creating/updating a user """
        ret = None
        is_new = data['isNew'] == 'true'
        try:
            ret = None
            if is_new:
                ret = self.create(data)
            else:
                ret = self.update(data)
            return dict(success=True, msg="User {}".format('created' if is_new else 'updated'), user=ret)
        except Exception as e:
            return dict(success=False, msg="Could not save user: {}".format(str(e)))

    def create(self, data):
        user = add_user(User(data['name'], data['title_id'], data['description']))
        if type(data['picture']) is not unicode:
            user.picture = self.image_handler.put(user, data['picture'])
        else:
            user.picture = None
        return update_user(user)

    def update(self, data):
        uid = int(data['id'])
        user = get_user(uid)
        user.name = data['name']
        user.title_id = data['title_id']
        user.description = data['description']
        if type(data['picture']) is not unicode:
            user.picture = self.image_handler.put(user, data['picture'])
        else:
            user.picture = None
        return update_user(user)

    @extdirect_method()
    def remove(self, user_id):
        user = get_user(user_id)
        return remove_user(user)

@extdirect_method(action='Utils', method_name='getTitles')
def get_titles(data):
    """ return a list of titles, optionally filtered
        by a prefix
    """
    prefix = data.get('query', '')
    ret = TITLES
    if prefix:
        prefix = prefix.lower()
        ret = [title for title in TITLES if title.lower().startswith(prefix)]
    return [dict(id=idx, title=title) for (idx, title) in enumerate(ret)]
