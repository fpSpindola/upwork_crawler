from peewee import *


db = SqliteDatabase('../main.db')


class Campaign(Model):
    class Meta:
        database = db

    # general settings
    id = PrimaryKeyField()
    name = CharField()
    active = BooleanField()
    url = CharField()
    time_on_site_min = IntegerField()
    time_on_site_max = IntegerField()
    pages_min = IntegerField()
    pages_max = IntegerField()
    visits_per_day_min = IntegerField()
    visits_per_day_max = IntegerField()
    length_from = DateField()
    length_to = DateField()
    bounce_rate = IntegerField()
    
    # traffic settings
    organic_source = IntegerField()
    direct_source = IntegerField()
    social_source = IntegerField()
    referral_source = IntegerField()
    email_source = IntegerField()

    organic_google = IntegerField()
    organic_yahoo = IntegerField()
    organic_bing = IntegerField()
    organic_aol = IntegerField()
    organic_keywords = CharField()

    referral_settings = CharField()
    social_settings = CharField()
    e_cs = CharField()
    e_cm = CharField()
    e_ct = CharField()
    e_cc = CharField()
    e_cn = CharField()
    email_url = CharField(null=True)
    
    use_proxy_list = BooleanField()
    use_proxy_api = BooleanField()
    proxy_api_url = CharField()
    proxy_filename = CharField(null=True)
    reused_proxy = IntegerField()

    ua_safari = BooleanField()
    ua_firefox = BooleanField()
    ua_ie = BooleanField()
    ua_opera = BooleanField()
    ua_chrome = BooleanField()
    ua_iphone = BooleanField()
    ua_ipad = BooleanField()
    ua_android = BooleanField()
    ua_win = BooleanField()
    ua_mac = BooleanField()
    ua_linux = BooleanField()

    state = BooleanField(default=False)


class Proxy(Model):
    class Meta:
        database = db
    
    ip = CharField()
    port = CharField()
    from_list = BooleanField()
    used = BooleanField(default=False)
    campaign = ForeignKeyField(Campaign, related_name='proxy')

    def __repr__(self):
        return self.ip + ':' + self.port
