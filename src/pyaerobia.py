from cookielib import CookieJar
from urllib import urlencode
from urllib2 import *
from urlparse import urljoin


from BeautifulSoup import BeautifulSoup

class Workout(object):

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return 'Workout(%(id)s, %(name)s)' % self.__dict__

class Aerobia(object):

    _CHEAT_HEADERS = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*'}

    def __init__(self, root='http://aerobia.ru/'):
        self.__root = root

    def _auth_url(self):
        return urljoin(self.__root, '/users/sign_in')

    def _workouts_url(self, user_id):
        return urljoin(
            self.__root,
            '/users/%(user_id)s/workouts?view=list' % locals())

    def _get_auth_token(self):
        request = Request(url = self._auth_url(), headers=self._CHEAT_HEADERS)
        response = urlopen(request)
        soup = BeautifulSoup(response.read())
        auth_token_tags = soup.findAll(attrs={'name': 'authenticity_token'})
        return auth_token_tags[0]['value']

    def _do_auth(self, user, password, token):
        self._cookie_jar = CookieJar()
        self._opener = \
            build_opener(HTTPCookieProcessor(self._cookie_jar), HTTPHandler())
        auth_request = Request(url = self._auth_url())
        data = urlencode({
            'user[email]': user,
            'user[password]': password,
            'authenticity_token': token})
        auth_request.add_data(data)
        response = self._opener.open(auth_request)
        assert response.getcode() / 100 == 2
        soup = BeautifulSoup(response.read())
        profile_tags = soup.findAll(name='li', attrs={'class': 'profile'})
        self._user_id = profile_tags[0].a['href'].split('/')[-1]

    def auth(self, user, password):
        token = self._get_auth_token()
        self._do_auth(user, password, token)

    def workout_list(self, user_id=None):
        user_id = user_id or self._user_id
        request = Request(
            url = self._workouts_url(user_id),
            headers=self._CHEAT_HEADERS)
        response = self._opener.open(request)
        soup = BeautifulSoup(response.read())
        tables = soup.findAll("table", attrs={'class': 'list'})
        workout_rows = tables[0].tbody.findAll("tr")

        workouts = []
        for tr in workout_rows:
            name_tds = tr.findAll('td', attrs={'class': 'title'})
            name = name_tds[0].div['title']
            id_refs = tr.findAll('a', attrs={'data-partial': 'workout'})
            id = id_refs[0]['href'].split('/')[-1]

            workouts.append(Workout(id, name))

        return workouts


