# -*- coding: utf-8 -*-

from cookielib import CookieJar
from datetime import datetime, timedelta
import re
from urllib import urlencode
from urllib2 import *
from urlparse import urljoin

from BeautifulSoup import BeautifulSoup


class Workout(object):

    def __init__(self, id, name, date, duration, length):
        self.id = id
        self.name = name
        self.date = date
        self.duration = duration
        self.length = length

    def __repr__(self):
        return (('Workout(' +
                 '%(id)s, %(name)s, %(date)s, %(duration)s, %(length)s' +
                 ')') % self.__dict__).encode('utf-8')


class Aerobia(object):

    _CHEAT_HEADERS = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*'}

    def __init__(self, root='http://aerobia.ru/'):
        self.__root = root

    def _auth_url(self):
        return urljoin(self.__root, '/users/sign_in')

    def _workouts_url(self, user_id, page=None):
        base = urljoin(
            self.__root,
            '/users/%(user_id)s/workouts?view=list' % locals())
        if page is not None:
            return base + '&page=' + str(page)
        else:
            return base

    def _export_url(self, workout_id, fmt):
        return urljoin(
            self.__root,
            "/export/workouts/%(workout_id)s/%(fmt)s" % locals())

    def _get_auth_token(self):
        request = Request(url=self._auth_url(), headers=self._CHEAT_HEADERS)
        response = urlopen(request)
        soup = BeautifulSoup(response.read())
        auth_token_tags = soup.findAll(attrs={'name': 'authenticity_token'})
        return auth_token_tags[0]['value']

    def _do_auth(self, user, password, token):
        self._cookie_jar = CookieJar()
        self._opener = \
            build_opener(HTTPCookieProcessor(self._cookie_jar), HTTPHandler())
        auth_request = Request(url=self._auth_url())
        data = urlencode({
            'user[email]': user,
            'user[password]': password,
            'authenticity_token': token})
        auth_request.add_data(data)
        response = self._opener.open(auth_request)
        assert response.getcode() / 100 == 2
        soup = BeautifulSoup(response.read())
        profile_tags = soup.findAll(name='li', attrs={'class': 'profile'})
        self._user_id = profile_tags[0].a['href'].split('/')[-1].split('?')[0]

    def _flatten_strings(self, tag):
        contents = []
        for child in tag.contents:
            if isinstance(child, basestring):
                contents.append(child)
            else:
                contents.extend(self._flatten_strings(child))
        return contents

    def _month_num(self, month):
        months = [u'январь', u'февраль',
                  u'марта', u'апрель', u'мая',
                  u'июня', u'июля', u'август',
                  u'сентябрь', u'октябрь', u'ноябрь',
                  u'декабрь']
        prefix = month.strip('.')
        for i in xrange(len(months)):
            if months[i].startswith(prefix):
                return i + 1
        raise Exception(month + "is not legal month name")

    def auth(self, user, password):
        token = self._get_auth_token()
        self._do_auth(user, password, token)

    def workout_list(self, user_id=None):
        return list(self.workout_iterator(user_id))

    def workout_iterator(self, user_id=None):
        page = 0
        while True:
            current_page_workouts = self._workout_page(page, user_id)
            if not len(current_page_workouts):
                return
            for w in current_page_workouts:
                yield w
            page += 1

    def _workout_page(self, page, user_id=None):
        user_id = user_id or self._user_id
        request = Request(
            url=self._workouts_url(user_id, page),
            headers=self._CHEAT_HEADERS)
        response = self._opener.open(request)
        soup = BeautifulSoup(response.read())
        tables = soup.findAll("table", attrs={'class': 'list'})
        if not len(tables):  # TODO: check this is really empty page
            return []
        workout_rows = tables[0].tbody.findAll("tr")

        workouts = []
        for tr in workout_rows:
            name_tds = tr.findAll('td', attrs={'class': 'title'})
            name = (name_tds[0].string or name_tds[0].div['title']).strip()

            id_refs = tr.findAll('a', attrs={'data-partial': 'workout'})
            id = id_refs[0]['href'].split('/')[-1].split('?')[0]

            datetime_spans = tr.findAll('span', attrs={'class': 'datetime'})
            datetime_str = \
                ''.join(self._flatten_strings(datetime_spans[0])).strip()
            datetime_re = re.compile(r'(\d+)\s+(\S+)\s+(\d+)\D+(\d+)\:(\d+)')
            [d, M, y, h, m] = datetime_re.match(datetime_str).groups()
            month = self._month_num(M)
            date = datetime(int(y), month, int(d), int(h), int(m))

            duration_td = tr.findAll('td')[-1]
            duration_str = duration_td.string
            duration_re = re.compile(r'((\d+)\D+)?(\d+)\D+(\d+)')
            [_, d_h, d_m, d_s] = duration_re.match(duration_str).groups()
            duration = timedelta(
                hours=int(d_h or 0),
                minutes=int(d_m),
                seconds=int(d_s))

            length_tds = tr.findAll(lambda el: (el.string or '').count(u'км'))
            length_str = length_tds[0].string
            length_re = re.compile(r'([0-9.]+).*')
            length = float(length_re.match(length_str).group(1))

            workout = Workout(id, name, date, duration, length)
            workouts.append(workout)

        return workouts

    def export_workout(self, workout_id, fmt='tcx'):
        response = self._opener.open(self._export_url(workout_id, fmt))
        return response.read()
