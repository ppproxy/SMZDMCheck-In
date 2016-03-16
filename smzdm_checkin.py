#! /usr/bin/python3
# -*- coding: utf-8 -*-

import urllib.parse
import urllib.request
import re
import json
from smtplib import SMTP
from email.mime.text import MIMEText
import configparser
import datetime

## Load config
config = configparser.RawConfigParser()
config.read('config.ini')

default_config = config['DEFAULT']
smzdm_config = config['smzdm']
mail_config = config['mail']

OK_message = default_config['OK_message']
smzdm_username = smzdm_config['userName']
smzdm_pw = smzdm_config['passwd']

## global checkin status
g_write_date = ''
g_cookie = ''
g_has_checkin = False
g_checkin_num = ''
g_checkin_url = ''

def getStatus():
    global g_write_date, g_cookie, g_has_checkin, g_checkin_num, g_checkin_url
    status = configparser.RawConfigParser()
    status.read('status.ini')
    section = status['DEFAULT']
    g_write_date = section['write_date']
    g_cookie = section['cookie']
    g_has_checkin = section['has_checkin'] in ['True', 'true', 'yes', '1']
    g_checkin_num = section['checkin_num']
    g_checkin_url = section['checkin_url']

def updateStatus(write_date=None, cookie=None, has_checkin=None, checkin_num=None, checkin_url=None):
    global g_write_date, g_cookie, g_has_checkin, g_checkin_num, g_checkin_url
    if write_date:
        g_write_date = write_date
    if cookie:
        g_cookie = cookie
    if has_checkin:
        g_has_checkin = has_checkin
    if checkin_num:
        g_checkin_num = checkin_num
    if checkin_url:
        g_checkin_url = checkin_url

def saveStatus():
    global g_write_date, g_cookie, g_has_checkin, g_checkin_num, g_checkin_url
    status = configparser.RawConfigParser()
    status['DEFAULT'] = {'write_date': g_write_date,
                         'cookie': g_cookie,
                         'has_checkin': g_has_checkin,
                         'checkin_num': g_checkin_num,
                         'checkin_url': g_checkin_url}
    with open('status.ini', 'w') as statusfile:
        status.write(statusfile)

def login():
    '''Log in and get Cookie'''

    global g_cookie
    cookie_set = set()
    login_url = 'https://zhiyou.smzdm.com/user/login/ajax_check'
    login_header = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
                  'Origin': 'https://zhiyou.smzdm.com',
                  'Referer': 'https://zhiyou.smzdm.com/user/login/window',
                  'X-Requested-With': 'XMLHttpRequest'}
    login_data = {'username': smzdm_username,
                  'password': smzdm_pw,
                  'rememberme': '1',
                  'captcha': '',
                  'redirect_url': 'http://www.smzdm.com'}

    data = urllib.parse.urlencode(login_data).encode('ascii')
    login_req = urllib.request.Request(login_url, data, login_header)

    with urllib.request.urlopen(login_req) as response:
        resp_header = response.info()
        cookie_lines = resp_header.get_all('Set-Cookie')
        for cookie_line in cookie_lines:
            cookie = cookie_line.split(';', 1)[0]
            if cookie.split('=', 1)[1] == 'deleted':
                continue
            else:
                if cookie not in cookie_set:
                    cookie_set.add(cookie)

    cookies = '; '.join(cookie_set)
    g_cookie = cookies
    return (True, cookies)

def getUserStatus(cookie):
    '''Before login, get user info and checkin_url'''

    checkin_url = ''
    prev_checkin_num = -1
    has_checkin = False

    user_url = 'http://zhiyou.smzdm.com/user/info/jsonp_get_current?callback=jQuery111008130632126703858_1452430586564&_=1452430586565'
    user_header = {'Referer': 'http://www.smzdm.com/',
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
                   'Cookie': cookie}
    user_req = urllib.request.Request(user_url, None, user_header)

    # regular expression
    p = re.compile('^[a-zA-Z0-9_]*\((.*)\)$')
    with urllib.request.urlopen(user_req) as response:
        user_info = response.read().decode('utf-8')
        # parse json object
        matchs = p.findall(user_info)
        if len(matchs) == 0:
            pass
        else:
            checkin = json.loads(matchs[0])['checkin']
            has_checkin = checkin['has_checkin']
            checkin_num = checkin['daily_checkin_num']
            checkin_url = checkin['set_checkin_url']
    return (has_checkin, checkin_num, checkin_url)

def checkin(checkin_url, cookie):
    '''send checkin request only'''

    checkin_num = -1
    checkin_header = {'Referer': 'http://www.smzdm.com/',
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
                   'Cookie': cookie}
    checkin_req = urllib.request.Request(checkin_url, None, checkin_header)

    with urllib.request.urlopen(checkin_req) as response:
        resp_body = response.read()
        resp_status = response.getcode()
        #TODO status analyse
        status = json.loads(resp_body.decode('utf-8'))
        checkin_num = status['data']['checkin_num']
    return checkin_num

def sendMail(checkin_num=-1, message=''):
    '''Send mail'''

    me = mail_config['from']
    to = mail_config['to']
    passwd = mail_config['passwd']
    smtp_server = mail_config['smtp_server']
    smtp_port = mail_config['smtp_port']

    if (len(message) == 0):
        message = OK_message
    msg = MIMEText(message)

    msg['Subject'] = 'SMZDM 连续签到 %s 天' % str(checkin_num)
    msg['From'] = me
    msg['To'] = to

    s = SMTP(smtp_server, smtp_port)
    s.starttls()
    s.login(me, passwd)
    s.send_message(msg)
    s.quit()

def initialize():
    getStatus()

def tryCheckin():
    '''Try checkin'''

    global g_write_date, g_cookie, g_has_checkin, g_checkin_num, g_checkin_url

    today = str(datetime.date.today())
    if len(g_write_date) != 0 and not today > g_write_date and g_has_checkin:
        return True
    else:
        # status out of date
        if len(g_cookie) == 0:
            status, g_cookie = login()
        #TODO what if cookie out of date
        a, b, g_checkin_url = getUserStatus(g_cookie)
        checkin(g_checkin_url, g_cookie)
        g_has_checkin, g_checkin_num, g_checkin_url = getUserStatus(g_cookie)
        if g_has_checkin:
            # checkin success
            sendMail(g_checkin_num, '')
            updateStatus(write_date=today)
            saveStatus()
        return g_has_checkin

if __name__ == "__main__":
    message = 'Error throwned:\n'
    initialize()
    try:
        checkedIn = tryCheckin()
    except urllib.error.URLError as e:
        message += e
    except Exception as e:
        message += e
    finally:
        if not checkedIn:
            sendMail(-1, message)
            # pass
