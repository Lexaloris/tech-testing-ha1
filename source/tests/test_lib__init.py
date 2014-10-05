#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import mock
from source import lib


class LibInitTestCase(unittest.TestCase):
    #to_unicode(val, errors='strict')
        #positive_tests
    def test_to_unicode_isinstance(self):
        val = 'val'
        self.assertEquals(val, lib.to_unicode(val))

    def test_to_unicode_else(self):
        val = 'значение'
        errors = 'ignore'
        self.assertEquals(val.decode('utf8', errors), lib.to_unicode(val, errors))

    #to_str(val, errors='strict')
        #positive_tests
    def test_to_str_isinstance(self):
        val = 'val'
        self.assertEquals(val.encode('utf8'), lib.to_str(val))

    def test_to_str_else(self):
        val = 'значение'
        self.assertEquals(val, lib.to_str(val))

    #get_counters(content)
        #positive_tests
    def test_get_counters_match(self):
        import rstr
        content = ''

        for counter_name, regexp in lib.COUNTER_TYPES:
            content += rstr.xeger(regexp)

        self.assertEquals(len(lib.COUNTER_TYPES), len(lib.get_counters(content)))

    def test_get_counters_else(self):
        content = ''

        self.assertEquals(0, len(lib.get_counters(content)))

    #check_for_meta(content, url)
        #positive_tests
    def test_check_for_meta_not_result(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head></head>
                <body></body>
            </html>
        """
        url = 'url'

        self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_not_content(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta charset="UTF-8" />
                </head>
                <body></body>
            </html>
        """
        url = 'url'

        self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_not_http_equiv(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta name="refresh" content="content" />
                </head>
                <body></body>
            </html>
        """
        url = 'url'

        self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_not_refresh(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                </head>
                <body></body>
            </html>
        """
        url = 'url'

        self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_len_splitted_not_equals_2(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta http-equiv="ReFresh" content="5" />
                </head>
                <body></body>
            </html>
        """
        url = 'url'

        self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta_not_search_url(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=">
                </head>
                <body></body>
            </html>
        """
        url = 'url'

        self.assertEquals(None, lib.check_for_meta(content, url))

    def test_check_for_meta(self):
        url = 'http://url.ru'
        redirect_url = 'http://redirect-url.ru'
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=""" + redirect_url + """">
                </head>
                <body></body>
            </html>
        """
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
        useragent = 'useragent'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=redirect_url)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals((content, redirect_url), lib.make_pycurl_request(url, timeout))
                self.assertEquals((content, redirect_url), lib.make_pycurl_request(url, timeout, useragent))

    def test_make_pycurl_request_none(self):
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
                self.assertEquals((content, None), lib.make_pycurl_request(url, timeout))
                self.assertEquals((content, None), lib.make_pycurl_request(url, timeout, useragent))

    #get_url(url, timeout, user_agent=None)
        #positive_tests
    def test_get_url_not_redirect(self):
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'http://odnoklassniki.ru/redirect-url/st.redirect'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, new_redirect_url])):
            redirect_url, redirect_type, return_content = lib.get_url(url, timeout)

        self.assertEquals(None, redirect_url)
        self.assertEquals(None, redirect_type)
        self.assertEquals(content, return_content)

    def test_get_url_redirect_http(self):
        from source.lib import REDIRECT_HTTP
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'http://redirect-url.ru'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, new_redirect_url])):
            redirect_url, redirect_type, return_content = lib.get_url(url, timeout)

        self.assertEquals(new_redirect_url, redirect_url)
        self.assertEquals(REDIRECT_HTTP, redirect_type)
        self.assertEquals(content, return_content)

    def test_get_url_redirect_http_market(self):
        from source.lib import REDIRECT_HTTP
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'market://redirect-url.ru'
        new_redirect_url_without_market = 'http://play.google.com/store/apps/redirect-url.ru'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, new_redirect_url])):
            redirect_url, redirect_type, return_content = lib.get_url(url, timeout)

        self.assertEquals(new_redirect_url_without_market, redirect_url)
        self.assertEquals(REDIRECT_HTTP, redirect_type)
        self.assertEquals(content, return_content)

    def test_get_url_redirect_meta_none(self):
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, None])):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=None)):
                redirect_url, redirect_type, return_content = lib.get_url(url, timeout)

        self.assertEquals(None, redirect_url)
        self.assertEquals(None, redirect_type)
        self.assertEquals(content, return_content)

    def test_get_url_redirect_meta(self):
        from source.lib import REDIRECT_META
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'http://redirect-url.ru'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, None])):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=new_redirect_url)):
                redirect_url, redirect_type, return_content = lib.get_url(url, timeout)

        self.assertEquals(new_redirect_url, redirect_url)
        self.assertEquals(REDIRECT_META, redirect_type)
        self.assertEquals(content, return_content)

    def test_get_url_redirect_meta_market(self):
        from source.lib import REDIRECT_META
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'market://redirect-url.ru'
        new_redirect_url_without_market = 'http://play.google.com/store/apps/redirect-url.ru'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, None])):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=new_redirect_url)):
                redirect_url, redirect_type, return_content = lib.get_url(url, timeout)

        self.assertEquals(new_redirect_url_without_market, redirect_url)
        self.assertEquals(REDIRECT_META, redirect_type)
        self.assertEquals(content, return_content)

        #negative_tests
    def test_get_url_value_error(self):
        url = 'http://url.ru'
        timeout = 30
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            redirect_url, redirect_type, content = lib.get_url(url, timeout)

        self.assertEquals(url, redirect_url)
        self.assertEquals('ERROR', redirect_type)
        self.assertEquals(None, content)

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
        url = 'https://netloc.com/path with%20space.php;qs=qs1 qs2'
        return_url = 'https://netloc.com/path%20with%20space.php;qs=qs1+qs2'

        self.assertEquals(return_url, lib.prepare_url(url))