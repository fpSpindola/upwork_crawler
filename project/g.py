#!/usr/bin/env python2

import multiprocessing
import threading
import argparse
import logging
import time
import os
import sys
import random
import datetime
from queue import Empty
import requests
import psutil
from random import choice, randint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException, TimeoutException, ElementNotVisibleException
from selenium.webdriver.common.action_chains import ActionChains
from dashboard.models import Campaign, Proxy, db
from peewee import fn
from urllib.parse import urlparse
from multiprocessing import Queue
# from Queue import Empty


from xvfbwrapper import Xvfb
from selenium.webdriver.chrome.options import Options

daemon = None


class Client():

    def __init__(self, name, url, time_on_site, pages, traffic_source, 
                 settings, proxy, ua, ss, is_bounced, campaign_id, organic_engine):

        self.url = url
        self.time_on_site = time_on_site
        self.pages = pages
        self.traffic_source = traffic_source
        self.settings = settings
        self.organic_engine = organic_engine
        self.name = name
        self.logger = logging.getLogger(str(campaign_id))
        self.is_bounced = is_bounced

        # dcap = dict(DesiredCapabilities.PHANTOMJS)
        # dcap["phantomjs.page.settings.userAgent"] = ua
        opts = Options()
        opts.add_argument("user-agent={}".format(ua))
        # dcap["phantomjs.page.settings.browserName"] = 'Netscape'
        # platform
        # dcap["phantomjs.page.settings."] = 'Netscape'

        if proxy:
            self.proxy = proxy
            # service_args = [
                    # '--proxy={}:{}'.format(proxy.ip, proxy.port),
                    # '--proxy-type=http'
                    # ]
            opts.add_argument('--proxy-server={}:{}'.format(proxy.ip, proxy.port))
            # self.br = webdriver.PhantomJS(desired_capabilities=dcap, service_args=service_args,
                    # service_log_path=os.path.join('logs', 'ghostdriver.log'))
        # else:
            # self.br = webdriver.PhantomJS(desired_capabilities=dcap,
                    # service_log_path=os.path.join('logs', 'ghostdriver.log'))

        self.br = webdriver.Chrome(os.path.join(os.path.dirname(__file__), 'chromedriver'), chrome_options=opts)
        # self.br = webdriver.Chrome()
        self.br.implicitly_wait(20)
        self.br.set_page_load_timeout(90)
        self.br.set_script_timeout(60)

        self.logger.info("""starting client
                \ttime on site: {}
                \tpages to visit: {}
                \ttraffic source: {}
                \tproxy: {}
                \tuser agent: {}
                \tscreen size: {}
                \tis bounced: {}
                """.format(time_on_site, pages, traffic_source, proxy, ua, ss, is_bounced))

        if not self.url.startswith('http'):
            self.url = 'http://' + self.url
        self.netloc = urlparse(self.url).netloc
        if self.netloc.startswith('www'):
            self.netloc = self.netloc[4:]

        ss = ss.split('x')
        self.br.set_window_size(ss[0], ss[1])
        self.br.maximize_window()

    def run(self):
        # self.br.get('http://ifconfig.me/ip')
        # print 'ip: {}'.format(self.br.page_source)
        # return
        if self.to_site():
            if self.on_site():
                return True
        return False

    def open_url(self, url):
        self.br.get(url)
        time.sleep(1)
        if 'available' in self.br.current_url:
            self.br.get(url)
    

    def to_site(self):
        if self.traffic_source == 'organic':
            engines = {'google': ['', '', 'https://www.google.', '//h3[@class="r"]', 'pnnext'],
                       'yahoo': ['https://search.yahoo.com/', 'sbq', 'https://search.yahoo.', '//h3', 'next'],
                       'bing': ['https://www.bing.com/', 'b_searchbox', 'https://www.bing.', '//h2', 'sb_pagN'],
                       'aol': ['http://search.aol.com/', 'q', 'http://search.aol.', '//h3', 'gspPageNext']}
            e = engines[self.organic_engine]
            name = self.organic_engine
            if not self.settings[0]:
                self.logger.error('organic settings are empty')
                return False

            query = choice(self.settings)
            self.logger.debug('using {}, query: {}'.format(name, query))
            if name == 'google':
                query_url = 'https://www.google.com/search?q={}&ie=utf-8&oe=utf-8&aq=t'.format(query)
                query_url = query_url.replace(' ', '+')
                self.logger.debug('query_url: {}'.format(query_url))
                self.open_url(query_url)
            elif name == 'aol':
                self.open_url(e[0])
                time.sleep(2)
                inputq = self.br.find_element_by_name(e[1])
                ActionChains(self.br).move_to_element(inputq).send_keys(query, Keys.RETURN).perform()
                results = self.br.find_elements_by_xpath(e[3])
                if not results:
                    try:
                        self.br.find_element_by_class_name('csbb').click()
                    except:
                        pass
            else:
                self.open_url(e[0])
                time.sleep(2)
                self.br.find_element_by_class_name(e[1]).send_keys(query, Keys.RETURN)
            time.sleep(1)

            if not self.br.current_url.startswith(e[2]):
                if self.br.current_url == 'about:blank':
                    # self.proxy.delete_instance()
                    self.logger.error('Cannot open {} through proxy {}, aborting'.format(name, self.proxy))
                    return False
                self.logger.error('loading url "{}" instead of {}, aborting'.format(self.br.current_url, name))
                return False

            results = None
            found = False
            page_counter = 0
            while not found:
                results = self.br.find_elements_by_xpath(e[3])
                if not results:
                    raise WebDriverException('something wrong, see screenshot')

                for result in results:
                    try:
                        a = result.find_element_by_xpath('.//a')
                    except:
                        continue
                    link = a.get_attribute('href')
                    if self.netloc in link:
                        found = True
                        self.logger.debug(u'url found, header: {}'.format(a.text))
                        a.click()
                        break
                if page_counter == 4 and not found:
                    self.logger.error('URL {} not found'.format(self.url))
                    return False
                if not found:
                    self.logger.debug('cannot find url on page {}'.format(page_counter))
                    if page_counter == 0:
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
                        if not os.path.exists('screenshots'):
                            os.makedirs('screenshots')
                        scr_path = os.path.join('screenshots', 'error_screenshot_' + timestamp + '.png')
                        self.br.save_screenshot(scr_path.replace(':', '_'))
                        self.logger.debug('see screenshot')
                    page_counter += 1
                    time.sleep(1)
                    if name == 'aol':
                        span = self.br.find_element_by_class_name(e[4])
                        span.find_element_by_xpath('.//a').click()
                    elif name == 'google':
                        self.br.find_element_by_id(e[4]).click()
                    else:
                        self.br.find_element_by_class_name(e[4]).click()
                    time.sleep(1)
            if len(self.br.window_handles) > 1:
                site_tab = self.br.window_handles[1]
                self.br.close() # close engine tab
                self.br.switch_to_window(site_tab)

        elif self.traffic_source == 'direct':
            self.open_url(self.url)
            time.sleep(1)
            if not self.url in self.br.current_url:
                self.logger.error('loading url "{}" instead of site url, aborting'.format(self.br.current_url))
                return False

        elif self.traffic_source == 'social':
            if not self.settings[0]:
                self.logger.error('social settings are empty')
                return False
            post = choice(self.settings).strip().split('|')
            post = [p.strip() for p in post]
            self.logger.debug('post: {}'.format(post))
            if post[0] == 'FB':
                post_found = False
                self.open_url(post[1])
                time.sleep(1)
                if not 'facebook' in self.br.current_url:
                    self.logger.error('cannot open facebook')
                    return False
                for article in self.br.find_elements_by_class_name('userContentWrapper'):
                    if article.find_element_by_class_name('userContent').text.startswith(post[2]):
                        post_found = True
                        link_found = False
                        self.logger.info('post found')
                        for a in article.find_elements_by_xpath('.//a'):
                            href = a.get_attribute('href')
                            if href and self.netloc in href:
                                link_found = True
                                self.logger.info('link found')
                                try:
                                    a.click()
                                except:
                                    a.click()
                                time.sleep(3)
                                self.br.switch_to_window(self.br.window_handles[1])
                                # close other tabs
                                cwh = self.br.current_window_handle
                                for tab in self.br.window_handles:
                                    if cwh != tab:
                                        self.br.switch_to_window(tab)
                                        self.br.close()
                                self.br.switch_to_window(cwh)
                                return True
                        if not link_found:
                            self.logger.error('cannot find link to site in post {}'.format(post))
                            return False
                if not post_found:
                    self.logger.error('cannot find post {}'.format(post))
                    return False
            elif post[0] == 'TW':
                self.open_url(post[1])
                time.sleep(1)
                if not 'twitter' in self.br.current_url:
                    self.logger.error('cannot open twitter')
                    return False
                link_found = False
                tweet = self.br.find_element_by_class_name('tweet-text')
                a = tweet.find_element_by_xpath('.//a')
                self.logger.info('url in twitter post: {}'.format(a.get_attribute('href')))
                a.click()
                time.sleep(3)
                self.br.switch_to_window(self.br.window_handles[1])
                # close other tabs
                cwh = self.br.current_window_handle
                for tab in self.br.window_handles:
                    if cwh != tab:
                        self.br.switch_to_window(tab)
                        self.br.close()
                self.br.switch_to_window(cwh)
                return True


        elif self.traffic_source == 'referral':
            if not self.settings[0]:
                self.logger.error('referrer settings are empty')
                return False
            self.open_url(choice(self.settings))
            time.sleep(3)
            link_found = False
            for a in self.br.find_elements_by_xpath('//a'):
                href = a.get_attribute('href')
                if href and self.netloc in href:
                    link_found = True
                    a.click()
                    return True
            if not link_found:
                self.logger.info('cannot find url on referrer site')
                return False

        elif self.traffic_source == 'email':
            self.logger.debug('email url {}'.format(self.settings))
            self.open_url(self.settings)

        return True


    def on_site(self):
        # close other tabs
        cwh = self.br.current_window_handle
        for tab in self.br.window_handles:
            if cwh != tab:
                self.br.switch_to_window(tab)
                self.br.close()
        self.br.switch_to_window(cwh)

        if self.br.current_url == 'about:blank':
            # self.proxy.delete_instance()
            self.logger.error('Cannot open page through proxy {}, aborting'.format(self.proxy))
            return False

        # wait on site
        average_time_on_page = self.time_on_site / self.pages        

        # main page
        time_on_page = average_time_on_page + randint(-10, 10)
        if time_on_page < 5:
            time_on_page = 5
        self.logger.debug('current url: {}'.format(self.br.current_url))
        self.logger.debug('waiting, {} seconds'.format(time_on_page))
        h = 100
        while time_on_page > 0:
            self.br.execute_script('window.scrollTo(0, {});'.format(h))
            h += 150
            time.sleep(5)
            time_on_page -= 5

        if self.is_bounced:
            return True

        self.pages -= 1

        for n in range(self.pages):
            possible_pages = []
            for a in self.br.find_elements_by_xpath('//a'):
                href = a.get_attribute('href')
                if href and self.netloc in href:
                    possible_pages.append(a)
            try:
                possible_pages.remove(self.br.current_url)
            except ValueError:
                pass
            if not possible_pages:
                self.logger.warning('cannot find any links on page')
                self.logger.debug('current title: {}'.format(self.br.title))
                return
            page = choice(possible_pages)
            href = page.get_attribute('href')
            self.logger.debug('loading page {}'.format(href))
            try:
                page.click()
            except ElementNotVisibleException:
                self.open_url(href)
            except WebDriverException:
                self.open_url(href)
            if 'not available' in self.br.title:
                self.open_url(href)
            
            # close other tabs
            cwh = self.br.current_window_handle
            for tab in self.br.window_handles:
                if cwh != tab:
                    self.br.switch_to_window(tab)
                    self.br.close()
            self.br.switch_to_window(cwh)

            time_on_page = average_time_on_page + randint(-10, 10)
            if time_on_page < 5:
                time_on_page = 5
            self.logger.debug('waiting, {} seconds'.format(time_on_page))
            h = 100
            while time_on_page > 0:
                self.br.execute_script('window.scrollTo(0, {});'.format(h))
                h += 150
                time.sleep(5)
                time_on_page -= 5

        return True


    def stop(self):
        self.br.quit()
        self.logger.info('stop client')


class Daemon():

    def __init__(self, nodebug):

        if not os.path.exists('logs'):
            os.makedirs('logs')

        self.setup_logger('main', os.path.join('logs', 'main.log'))
        logger = logging.getLogger('main')

        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('peewee').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)

        logger.info('bot started')

        db.init('main.db')

        with open('user_agents') as f:
            self.uas = f.read().splitlines()

        self.screen_sizes = ['1366x768', '1920x1080', '1280x800', '1440x900', '1280x1024']

    def setup_logger(self, logger_name, log_file, level=logging.DEBUG):
        l = logging.getLogger(logger_name)
        fmt = logging.Formatter('[%(asctime)s] [%(levelname)8s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        if len(l.handlers) > 0:
            for handler in l.handlers:
                if not isinstance(handler, logging.FileHandler) and not isinstance(handler, logging.StreamHandler):
                    fileHandler = logging.FileHandler(log_file, mode='a')
                    fileHandler.setFormatter(fmt)
                    streamHandler = logging.StreamHandler()
                    streamHandler.setFormatter(fmt)

                    l.setLevel(level)
                    l.addHandler(fileHandler)
                    l.addHandler(streamHandler) 
        else:
            fileHandler = logging.FileHandler(log_file, mode='a')
            fileHandler.setFormatter(fmt)
            streamHandler = logging.StreamHandler()
            streamHandler.setFormatter(fmt)

            l.setLevel(level)
            l.addHandler(fileHandler)
            l.addHandler(streamHandler) 


    def run(self):
        # loop that picks active && date && not started campaings and starts them

        with Xvfb(width=1920, height=1080) as xvfb:
            while True:
                main_logger = logging.getLogger('main')
                try:
                    db.connect()
                    date = datetime.date.today()
                    for campaign in Campaign.select().where(
                            (Campaign.active == True) &
                            ((Campaign.length_from <= date) & (Campaign.length_to >= date)) &
                            (Campaign.state == False)):
                        campaign.state = True
                        campaign.save()
                        self.setup_logger(str(campaign.id), os.path.join('logs', str(campaign.id) + '.log'))
                        logger = logging.getLogger(str(campaign.id))
                        logger.info('campaign started!')
                        thread = threading.Thread(target = self.campaign, args = (campaign, ))
                        thread.daemon = True
                        thread.start()
                    db.close()
                    time.sleep(15)
                except KeyboardInterrupt:
                    db.connect()
                    for campaign in Campaign.select():
                        campaign.state = False
                        campaign.save()
                    db.close()
                    main_logger.info('stop')
                    exit(0)

    def campaign(self, campaign):
        # spawns client and sets timer for itself

        try:
            logger = logging.getLogger(str(campaign.id))
            db.connect()
            try:
                campaign = Campaign.select().where(Campaign.id == campaign.id).get()
            except:
                campaign.state = False
                campaign.save()
                logger.info('Campaign {} is not active.'.format(campaign.name))
                return

            # check if it is still active and date
            date = datetime.date.today()
            if campaign.active == False or date < campaign.length_from or date > campaign.length_to:
                campaign.state = False
                campaign.save()
                logger.info('Campaign {} is not active.'.format(campaign.name))
                return

            # let's determine settings for this instance 
            time_on_site = randint(campaign.time_on_site_min, campaign.time_on_site_max)
            pages = randint(campaign.pages_min, campaign.pages_max)
            is_bounced = False
            if float(campaign.bounce_rate) / 100 > random.random():
                is_bounced = True

            traffic_source = weighted_choice([
                ('organic', campaign.organic_source),
                ('direct', campaign.direct_source),
                ('social', campaign.social_source),
                ('referral', campaign.referral_source),
                ('email', campaign.email_source)]) 

            organic_engine = None

            if traffic_source == 'organic':
                organic_engine = weighted_choice([
                    ('google', campaign.organic_google),
                    ('yahoo', campaign.organic_yahoo),
                    ('bing', campaign.organic_bing),
                    ('aol', campaign.organic_aol)]) 
                settings = campaign.organic_keywords.split('\n')
            elif traffic_source == 'direct':
                settings = None
            elif traffic_source == 'social':
                settings = campaign.social_settings.split('\n')
            elif traffic_source == 'referral':
                settings = campaign.referral_settings.split('\n')
            elif traffic_source == 'email':
                settings = campaign.email_url

            proxy = None
            if campaign.use_proxy_list or campaign.use_proxy_api:
                try:
                    if campaign.use_proxy_list and campaign.use_proxy_api:
                        proxy = Proxy.select().where(Proxy.used == False).order_by(fn.Random()).limit(1).get()
                    else:
                        if campaign.use_proxy_list and not campaign.use_proxy_api:
                            from_list = True
                        elif not campaign.use_proxy_list and campaign.use_proxy_api:
                            from_list = False
                        proxy = Proxy.select().where(
                                Proxy.used == False, 
                                Proxy.from_list == from_list).order_by(fn.Random()).limit(1).get()
                except:
                    if campaign.use_proxy_api:
                        logger.info('cannot find any proxies, let\'s download them')
                        resp = requests.get(campaign.proxy_api_url)
                        if resp.status_code == 200:
                            proxies = resp.text.splitlines()
                            data_source = []
                            for proxy in proxies:
                                p = proxy.split(':')
                                data_source.append({'ip': p[0], 'port': p[1], 'campaign': campaign, 'from_list': False})
                            with db.atomic():
                                for idx in range(0, len(data_source), 100):
                                    Proxy.insert_many(data_source[idx:idx+100]).execute()
                        try:
                            proxy = Proxy.select().where(Proxy.used == False).order_by(fn.Random()).limit(1).get()
                            logger.info('proxies succesfully downloaded')
                        except:
                            logger.warning('cannot download proxies')
                            # logger.error('cannot download proxies, campaign deactivated')
                            # campaign.active = False
                            # campaign.state = False
                            # campaign.save()
                            # return

                # if not proxy:
                    # logger.error('Campaign must use proxy but there are no proxies. Campaign deactivated.')
                    # campaign.active = False
                    # campaign.state = False
                    # campaign.save()
                    # return
                if proxy:
                    if campaign.reused_proxy / 100 < random.random():
                        proxy.used = True
                        proxy.save()

            platforms = []
            if campaign.ua_win:
                platforms.append('Win')
            if campaign.ua_linux:
                platforms.append('Linux')
            if campaign.ua_mac:
                platforms.append('Mac')
            if traffic_source != 'organic':
                if campaign.ua_ipad:
                    platforms.append('iPad')
                if campaign.ua_iphone:
                    platforms.append('iPhone')
                if campaign.ua_android:
                    platforms.append('Android')
            
            browsers = []

            if campaign.ua_safari:
                browsers.append('Safari')
            if campaign.ua_firefox:
                browsers.append('Firefox')
            # if campaign.ua_ie:
                # browsers.append('MSIE')
            # if campaign.ua_opera:
                # browsers.append('Opera')
            if campaign.ua_chrome:
                browsers.append('Chrome')

            try:
                p = choice(platforms)
            except IndexError:
                logger.error('you need to select at least one platform')
                p = None
            try:
                b = choice(browsers)
            except IndexError:
                b = None

            ps = []
            if b == 'Safari' and 'Mac' in platforms:
                for ua in self.uas:
                    if b in ua and not 'Chrome' in ua and not 'iPhone' in ua and not 'iPad' in ua:
                        ps.append(ua)
            elif b == 'MSIE' and 'Win' in platforms:
                for ua in self.uas:
                    if b in ua and 'Win' in ua:
                        ps.append(ua)
            elif b == 'Opera':
                for ua in self.uas:
                    if b in ua:
                        if 'Linux' in ua and 'Linux' in platforms:
                            ps.append(ua)
                        if 'Win' in ua and 'Win' in platforms:
                            ps.append(ua)
                
            if b != 'Safari' and b != 'Opera' and b != 'MSIE':
                if p == 'iPad' or p == 'iPhone' or p == 'Android':
                    for ua in self.uas:
                        if p in ua:
                            ps.append(ua)
                else:
                    for ua in self.uas:
                        if p in ua and b in ua:
                            ps.append(ua)

            ua = choice(ps)

            if 'iPad' in ua:
                ss = '768x1024'
            elif 'iPhone' in ua:
                ss = '750x1334'
            elif 'Android' in ua:
                ss = '540x960'
            else:
                ss = choice(self.screen_sizes)

            q = multiprocessing.Queue()
            p = multiprocessing.Process(target=self.run_client, args=(q, logger, campaign.name, campaign.url,
                time_on_site, pages, traffic_source, settings, proxy, ua, ss, is_bounced, campaign.id,
                organic_engine))

            p.start()
            p.join(1200) # timeout is 20m
            if p.is_alive():
                logger.error('client does not respond, let\'s kill it')
                kill_proc_tree(p.pid)
                # p.terminate()
                p.join()
            try:
                failure = q.get(False)
            except Empty:
                failure = True

            if failure:
                next_run_in = randint(5, 30)
                logger.debug('failure, next run in {} seconds'.format(next_run_in))
                threading.Timer(next_run_in, self.campaign, args=[campaign]).start()
            else:
                next_run_in = 86400 / randint(campaign.visits_per_day_min, campaign.visits_per_day_max)
                logger.debug('next run in {} seconds'.format(next_run_in))
                threading.Timer(next_run_in, self.campaign, args=[campaign]).start()
            db.close()

        except:
            db.connect()
            campaign.state = False
            campaign.save()
            db.close()
            if logger:
                logger.exception('')
            next_run_in = randint(5, 30)
            logger.debug('error in code, next run in {} seconds'.format(next_run_in))
            threading.Timer(next_run_in, self.campaign, args=[campaign]).start()


    def run_client(self, q, logger, name, url, tos, pages, ts, settings, proxy, ua, ss, ib, cid, oe):
        client = Client(name, url, tos, pages, ts, settings, proxy, ua, ss, ib, cid, organic_engine=oe) 

        failure = False
        try:
            if not client.run():
                failure = True
            client.stop()

        except TimeoutException:
            failure = True
            # client.proxy.delete_instance()
            logger.error('proxy {} is not responding'.format(client.proxy))
            client.stop()
            
        except WebDriverException:
            failure = True
            logger.exception('')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
            if not os.path.exists('screenshots'):
                os.makedirs('screenshots')
            scr_path = os.path.join('screenshots', 'error_screenshot_' + timestamp + '.png')
            client.br.save_screenshot(scr_path.replace(':', '_'))
            client.stop()

        except KeyboardInterrupt:
            client.stop()
            logger.info('stop')
            exit(0)

        except Exception as e:
            failure = True
            logger.exception('')
            client.stop()

        q.put(failure)


def weighted_choice(choices):
   total = sum(w for c, w in choices)
   r = random.uniform(0, total)
   upto = 0
   for c, w in choices:
      if upto + w >= r:
         return c
      upto += w
   assert False, "Shouldn't get here"


def kill_proc_tree(pid, including_parent=True):    
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children, timeout=5)
    if including_parent:
        parent.kill()
        parent.wait(5)


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument('--nodebug', action='store_true')
    args = parser.parse_args()
    daemon = Daemon(args.nodebug)
    daemon.run()
