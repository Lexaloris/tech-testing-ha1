#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import mock
from source import lib


class LibInitTestCase(unittest.TestCase):
    #to_unicode(val, errors='strict')
        #positive_tests
    def test_to_unicode_isinstance(self):
        val = u'val'
        self.assertTrue(isinstance(lib.to_unicode(val), unicode))

    def test_to_unicode_else(self):
        val = 'значение'
        errors = 'ignore'
        self.assertTrue(isinstance(lib.to_unicode(val, errors), unicode))

    #to_str(val, errors='strict')
        #positive_tests
    def test_to_str_isinstance(self):
        val = u'val'
        self.assertTrue(isinstance(lib.to_str(val), str))

    def test_to_str_else(self):
        val = 'значение'
        self.assertTrue(isinstance(lib.to_str(val), str))

    #get_counters(content)
        #positive_tests
    def test_get_counters_match(self):
        content = 'http://google-analytics.com/ga.js'

        self.assertEquals(1, len(lib.get_counters(content)))

    def test_get_counters_else(self):
        content = ''

        self.assertEquals(0, len(lib.get_counters(content)))

    #check_for_meta(content, url)
        #positive_tests
    def test_check_for_meta_not_result(self):
        content = "not meta"
        url = 'url'

        with mock.patch('source.lib.BeautifulSoup.find', mock.Mock(return_value=None)):
            self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_not_content(self):
        content = "meta: not content"
        url = 'url'
        result = mock.MagicMock()

        with mock.patch('source.lib.BeautifulSoup.find', mock.Mock(return_value=result)):
            self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_not_http_equiv(self):
        content = "meta: name = refresh content=content"
        url = 'url'
        result = mock.MagicMock()
        result.attrs = {
            'content': 'content',
            'name': 'refresh',
        }

        with mock.patch('source.lib.BeautifulSoup.find', mock.Mock(return_value=result)):
            self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_not_refresh(self):
        content = "meta: http-equiv=Content-Type content=content"
        url = 'url'
        result = mock.MagicMock()
        result.attrs = {
            'content': 'content',
            'http-equiv': 'Content-Type',
        }

        with mock.patch('source.lib.BeautifulSoup.find', mock.Mock(return_value=result)):
            self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_len_splitted_not_equals_2(self):
        content = '<meta http-equiv="ReFresh" content="content">'
        url = 'url'

        self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_not_search_url(self):
        content = '<meta http-equiv="refresh" content="content; url=">'
        url = 'url'

        self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta(self):
        content = '<meta http-equiv="refresh" content="content; url=redirect_url">'
        url = 'http://url.ru'
        redirect_url = 'http://redirect-url.ru'

        with mock.patch('source.lib.to_unicode', mock.Mock(return_value=redirect_url)):
            self.assertEquals(lib.urljoin(url, redirect_url), lib.check_for_meta(content, url))

    #fix_market_url(url)
        #positive_tests
    def test_fix_market_url_fixed_bug(self):
        url = 'market://apps-url'
        return_url = 'http://play.google.com/store/apps/apps-url'

        self.assertEquals(return_url, lib.fix_market_url(url))

    def test_fix_market_url_not_market(self):
        url = 'http://apps-url'

        self.assertEquals(url, lib.fix_market_url(url))

    #make_pycurl_request(url, timeout, useragent=None)
        #positive_tests
    def test_make_pycurl_request_redirect_url(self):
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        redirect_url = 'http://redirect-url.ru'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=redirect_url)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals((content, redirect_url), lib.make_pycurl_request(url, timeout))

    def test_make_pycurl_request_redirect_url_useragent(self):
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        redirect_url = 'http://redirect-url.ru'
        useragent = 'useragent'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=redirect_url)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals((content, redirect_url), lib.make_pycurl_request(url, timeout, useragent))

    def test_make_pycurl_request_none(self):
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=None)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals((content, None), lib.make_pycurl_request(url, timeout))

    def test_make_pycurl_request_none_useragent(self):
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        useragent = 'useragent'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=None)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals((content, None), lib.make_pycurl_request(url, timeout, useragent))

    #get_url(url, timeout, user_agent=None)
        #positive_tests
    def test_get_url_not_redirect(self):
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'http://odnoklassniki.ru/redirect-url/st.redirect'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, new_redirect_url])):
            self.assertEquals((None, None, content), lib.get_url(url, timeout))

    def test_get_url_redirect_http(self):
        from source.lib import REDIRECT_HTTP
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'http://redirect-url.ru'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, new_redirect_url])):
            self.assertEquals((new_redirect_url, REDIRECT_HTTP, content), lib.get_url(url, timeout))

    def test_get_url_redirect_http_market(self):
        from source.lib import REDIRECT_HTTP
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'market://redirect-url.ru'
        new_redirect_url_without_market = 'http://play.google.com/store/apps/redirect-url.ru'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, new_redirect_url])):
            self.assertEquals((new_redirect_url_without_market, REDIRECT_HTTP, content), lib.get_url(url, timeout))

    def test_get_url_redirect_meta_none(self):
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, None])):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=None)):
                self.assertEquals((None, None, content), lib.get_url(url, timeout))

    def test_get_url_redirect_meta(self):
        from source.lib import REDIRECT_META
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'http://redirect-url.ru'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, None])):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=new_redirect_url)):
                self.assertEquals((new_redirect_url, REDIRECT_META, content), lib.get_url(url, timeout))

    def test_get_url_redirect_meta_market(self):
        from source.lib import REDIRECT_META
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'market://redirect-url.ru'
        new_redirect_url_without_market = 'http://play.google.com/store/apps/redirect-url.ru'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, None])):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=new_redirect_url)):
                self.assertEquals((new_redirect_url_without_market, REDIRECT_META, content), lib.get_url(url, timeout))

        #negative_tests
    def test_get_url_value_error(self):
        url = 'http://url.ru'
        timeout = 30
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            self.assertEquals((url, 'ERROR', None), lib.get_url(url, timeout))

    #get_redirect_history(url, timeout, max_redirects=30, user_agent=None)
        #positive_tests
    def test_get_redirect_history_ok_url(self):
        url = 'https://www.odnoklassniki.ru/'
        timeout = 30
        with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
            history_types, history_urls, counters = lib.get_redirect_history(url, timeout)

        self.assertEquals([], history_types)
        self.assertEquals([url], history_urls)
        self.assertEquals([], counters)

    def test_get_redirect_history_mm_url(self):
        url = 'https://my.mail.ru/apps/'
        timeout = 30
        with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
            history_types, history_urls, counters = lib.get_redirect_history(url, timeout)

        self.assertEquals([], history_types)
        self.assertEquals([url], history_urls)
        self.assertEquals([], counters)

    def test_get_redirect_history_not_redirect_url(self):
        url = 'http://url.ru'
        timeout = 30
        with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[None, None, None])):
                history_types, history_urls, counters = lib.get_redirect_history(url, timeout)

        self.assertEquals([], history_types)
        self.assertEquals([url], history_urls)
        self.assertEquals([], counters)

    def test_get_redirect_history_not_redirect_url_content(self):
        url = 'http://url.ru'
        timeout = 30
        counters = 'counters'
        with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[None, None, 'content'])):
                with mock.patch('source.lib.get_counters', mock.Mock(return_value=counters)):
                    history_types, history_urls, return_counters = lib.get_redirect_history(url, timeout)

        self.assertEquals([], history_types)
        self.assertEquals([url], history_urls)
        self.assertEquals(counters, return_counters)

    def test_get_redirect_history_redirect_type_error(self):
        url = 'http://url.ru'
        timeout = 30
        redirect_url = 'http://redirect-url.ru'
        redirect_type_error = 'ERROR'
        with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[redirect_url, redirect_type_error, None])):
                history_types, history_urls, counters = lib.get_redirect_history(url, timeout)

        self.assertEquals([redirect_type_error], history_types)
        self.assertEquals([url, redirect_url], history_urls)
        self.assertEquals([], counters)

    def test_get_redirect_history_redirect_type_error_content(self):
        url = 'http://url.ru'
        timeout = 30
        redirect_url = 'http://redirect-url.ru'
        redirect_type_error = 'ERROR'
        counters = 'counters'
        with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[redirect_url, redirect_type_error, 'content'])):
                with mock.patch('source.lib.get_counters', mock.Mock(return_value=counters)):
                    history_types, history_urls, return_counters = lib.get_redirect_history(url, timeout)

        self.assertEquals([redirect_type_error], history_types)
        self.assertEquals([url, redirect_url], history_urls)
        self.assertEquals(counters, return_counters)

    def test_get_redirect_history_redirect_repeat(self):
        url = 'http://url.ru'
        timeout = 30
        redirect_url = 'http://redirect-url.ru'
        redirect_type = 'redirect_type'
        with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[redirect_url, redirect_type, None])):
                    history_types, history_urls, return_counters = lib.get_redirect_history(url, timeout)

        self.assertEquals([redirect_type, redirect_type], history_types)
        self.assertEquals([url, redirect_url, redirect_url], history_urls)
        self.assertEquals([], return_counters)

    def test_get_redirect_history_redirect_repeat_content(self):
        url = 'http://url.ru'
        timeout = 30
        redirect_url = 'http://redirect-url.ru'
        redirect_type = 'redirect_type'
        counters = 'counters'
        with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[redirect_url, redirect_type, 'content'])):
                with mock.patch('source.lib.get_counters', mock.Mock(return_value=counters)):
                    history_types, history_urls, return_counters = lib.get_redirect_history(url, timeout)

        self.assertEquals([redirect_type, redirect_type], history_types)
        self.assertEquals([url, redirect_url, redirect_url], history_urls)
        self.assertEquals(counters, return_counters)

    #prepare_url(url)
        #positive_tests
    def test_prepare_url_none(self):
        url = None

        self.assertEquals(url, lib.prepare_url(url))

    def test_prepare_url(self):
        url = 'http://url.ru'
        with mock.patch('source.lib.urlparse', mock.Mock(return_value=[mock.MagicMock()] * 6)) as urlparse:
            with mock.patch('source.lib.quote', mock.Mock()) as quote:
                with mock.patch('source.lib.quote_plus', mock.Mock()) as quote_plus:
                    lib.prepare_url(url)
        urlparse.assert_called_once()
        quote.assert_called_once()
        quote_plus.assert_called_once()
