from wtforms import *
from wtforms.fields.html5 import DateField
from flask_wtf import Form
import datetime


class Campaign_form(Form):
    active = BooleanField('Active', default=True)
    name = TextField('Name', default='New Campaign') 
    url = TextField('URL', default='http://example.com/')
    time_on_site_min = IntegerField('Time on site', default=30)
    time_on_site_max = IntegerField(default=60)
    pages_min = IntegerField('Pages to visit', default=3)
    pages_max = IntegerField(default=7)
    visits_per_day_min = IntegerField('Visites per day', default=250)
    visits_per_day_max = IntegerField(default=400)
    length_from = DateField('Start date', default=datetime.date.today())
    length_to = DateField('End date', default=datetime.date.today() + datetime.timedelta(days=10))
    bounce_rate = IntegerField('Bounce rate', default=20)

    organic_source = IntegerField('Organic', default=40)
    direct_source = IntegerField('Direct', default=30)
    social_source = IntegerField('Social', default=5)
    referral_source = IntegerField('Referral', default=10)
    email_source = IntegerField('Email', default=15)

    organic_google = IntegerField('Google', default=40)
    organic_yahoo = IntegerField('Yahoo', default=20)
    organic_bing = IntegerField('Bing', default=25)
    organic_aol = IntegerField('Aol', default=15)
    organic_keywords = TextAreaField('Organic Traffic Keyword Settings', [validators.Optional()])

    referral_settings = TextAreaField('Referral Settings', [validators.Optional()])
    social_settings = TextAreaField('Social Settings', [validators.Optional()])
    e_cs = TextField('Source')
    e_cm = TextField('Medium')
    e_ct = TextField('Term')
    e_cc = TextField('Content')
    e_cn = TextField('Name')

    use_proxy_list = BooleanField('Use proxy list', default=False)
    use_proxy_api = BooleanField('Use proxy API', default=False)
    proxy_api_url = TextAreaField('Proxy API url', default='https://kingproxies.com/api/v2/proxies.txt?key=0efdb4557a2037d9a1a4db19db4914&protocols=http&alive=1')
    proxy = FileField('Proxy settings', [validators.Optional()])
    reused_proxy = IntegerField('Reused proxies', default=5)

    ua_safari = BooleanField(default=True)
    ua_firefox = BooleanField(default=True)
    ua_ie = BooleanField(default=True)
    ua_opera = BooleanField(default=True)
    ua_chrome = BooleanField(default=True)
    ua_iphone = BooleanField(default=True)
    ua_ipad = BooleanField(default=True)
    ua_android = BooleanField(default=True)
    ua_win = BooleanField(default=True)
    ua_mac = BooleanField(default=True)
    ua_linux = BooleanField(default=True)
