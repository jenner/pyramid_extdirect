from pyramid_extdirect import extdirect_method
from .models import *

class UsersController(object):

    __extdirect_settings__ = {
        'default_action_name': 'Users',
    }

    def __init__(self, request):
        self.request = request

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

    @extdirect_method()
    def create(self, data):
        user = User(data['name'], data['title'], data['description'])
        return add_user(user)

    @extdirect_method()
    def update(self, data):
        user = get_user(data['id'])
        user.name = data['name']
        title_id = TITLES.index(data['title'])
        user.title_id = title_id
        user.description = data['description']
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
