from flask import Flask, redirect, url_for, request, Response, render_template, g, Response
from flask import flash
from models import db, Campaign, Proxy
from forms import Campaign_form
from functools import wraps
import urllib
# import urlparse
import os
from json import dumps
# from urllib import urlencode, unquote
# from urlparse import urlparse, parse_qsl, ParseResult


app = Flask(__name__)
app.secret_key = 'KikoikiLolpolo@1'
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')
db.create_tables([Campaign, Proxy], True)
USERNAME = 'boostga'
PASSWORD = '@002120159--'


def check_auth(username, password):
    return username == USERNAME and password == PASSWORD


def authenticate():
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials.', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@requires_auth
def main():
    campaigns = Campaign.select()
    return render_template('active.jade', campaigns=campaigns)


@app.route('/new', methods=['GET', 'POST'])
@requires_auth
def new():
    form = Campaign_form()
    if form.validate_on_submit():
        params = {
                'utm_source': form.e_cs.data,
                'utm_medium': form.e_cm.data,
                'utm_term': form.e_ct.data,
                'utm_content': form.e_cc.data,
                'utm_campaign': form.e_cn.data}
        order = ['utm_source', 'utm_medium', 'utm_term', 'utm_content', 'utm_campaign']
        queryString  = "&".join([item+'='+urllib.quote_plus(params[item]) for item in order])
        url = form.url.data
        if url[-1] != '/':
            url = url + '/' 
        email_url = url + '?' + queryString
        campaign = Campaign.create(
                name=form.name.data,
                active=form.active.data,
                url=form.url.data,
                time_on_site_min=form.time_on_site_min.data,
                time_on_site_max=form.time_on_site_max.data,
                pages_min=form.pages_min.data,
                pages_max=form.pages_max.data,
                visits_per_day_min=form.visits_per_day_min.data,
                visits_per_day_max=form.visits_per_day_max.data,
                length_from=form.length_from.data,
                length_to=form.length_to.data,
                bounce_rate=form.bounce_rate.data,
                organic_source=form.organic_source.data,
                direct_source=form.direct_source.data,
                social_source=form.social_source.data,
                email_source=form.email_source.data,
                referral_source=form.referral_source.data,
                organic_google=form.organic_google.data,
                organic_yahoo=form.organic_yahoo.data,
                organic_bing=form.organic_bing.data,
                organic_aol=form.organic_aol.data,
                organic_keywords=form.organic_keywords.data,
                referral_settings=form.referral_settings.data,
                social_settings=form.social_settings.data,
                e_cs=form.e_cs.data,
                e_cm=form.e_cm.data,
                e_ct=form.e_ct.data,
                e_cc=form.e_cc.data,
                e_cn=form.e_cn.data,
                email_url=email_url,
                use_proxy_list=form.use_proxy_list.data,
                use_proxy_api=form.use_proxy_api.data,
                proxy_api_url=form.proxy_api_url.data,
                reused_proxy=form.reused_proxy.data,
                ua_safari=form.ua_safari.data,
                ua_firefox=form.ua_firefox.data,
                ua_ie=form.ua_ie.data,
                ua_opera=form.ua_opera.data,
                ua_chrome=form.ua_chrome.data,
                ua_iphone=form.ua_iphone.data,
                ua_ipad=form.ua_ipad.data,
                ua_android=form.ua_android.data,
                ua_win=form.ua_win.data,
                ua_mac=form.ua_mac.data,
                ua_linux=form.ua_linux.data
                )
        if form.proxy.data:
            campaign.proxy_filename=form.proxy.data.filename
            campaign.save()
            proxies = form.proxy.data.read().splitlines()
            data_source = []
            for proxy in proxies:
                p = proxy.split(':')
                data_source.append({'ip': p[0], 'port': p[1], 'campaign': campaign, 'from_list': True})
            with db.atomic():
                for idx in range(0, len(data_source), 100):
                    Proxy.insert_many(data_source[idx:idx+100]).execute()
        return redirect(url_for('main'))
    # print form.errors
    return render_template('new.jade', form=form)


@app.route('/c/<id>', methods=['GET', 'POST'])
@requires_auth
def change_campaign(id):
    campaign = Campaign.select().where(Campaign.id == id).get()
    form = Campaign_form(
            name=campaign.name,
            active=campaign.active,
            url=campaign.url,
            time_on_site_min=campaign.time_on_site_min,
            time_on_site_max=campaign.time_on_site_max,
            pages_min=campaign.pages_min,
            pages_max=campaign.pages_max,
            visits_per_day_min=campaign.visits_per_day_min,
            visits_per_day_max=campaign.visits_per_day_max,
            length_from=campaign.length_from,
            length_to=campaign.length_to,
            bounce_rate=campaign.bounce_rate,
            organic_source=campaign.organic_source,
            direct_source=campaign.direct_source,
            social_source=campaign.social_source,
            email_source=campaign.email_source,
            referral_source=campaign.referral_source,
            organic_google=campaign.organic_google,
            organic_yahoo=campaign.organic_yahoo,
            organic_bing=campaign.organic_bing,
            organic_aol=campaign.organic_aol,
            organic_keywords=campaign.organic_keywords,
            referral_settings=campaign.referral_settings,
            social_settings=campaign.social_settings,
            e_cs=campaign.e_cs,
            e_cm=campaign.e_cm,
            e_ct=campaign.e_ct,
            e_cc=campaign.e_cc,
            e_cn=campaign.e_cn,
            use_proxy_list=campaign.use_proxy_list,
            use_proxy_api=campaign.use_proxy_api,
            proxy_api_url=campaign.proxy_api_url,
            reused_proxy=campaign.reused_proxy,
            ua_safari=campaign.ua_safari,
            ua_firefox=campaign.ua_firefox,
            ua_ie=campaign.ua_ie,
            ua_opera=campaign.ua_opera,
            ua_chrome=campaign.ua_chrome,
            ua_iphone=campaign.ua_iphone,
            ua_ipad=campaign.ua_ipad,
            ua_android=campaign.ua_android,
            ua_win=campaign.ua_win,
            ua_mac=campaign.ua_mac,
            ua_linux=campaign.ua_linux
            )
    if form.validate_on_submit():
        params = {
                'utm_source': form.e_cs.data,
                'utm_medium': form.e_cm.data,
                'utm_term': form.e_ct.data,
                'utm_content': form.e_cc.data,
                'utm_campaign': form.e_cn.data}
        order = ['utm_source', 'utm_medium', 'utm_term', 'utm_content', 'utm_campaign']
        queryString  = "&".join([item+'='+urllib.quote_plus(params[item]) for item in order])
        url = form.url.data
        if url[-1] != '/':
            url = url + '/' 
        email_url = url + '?' + queryString
        campaign.name=form.name.data
        campaign.active=form.active.data
        campaign.url=form.url.data
        campaign.time_on_site_min=form.time_on_site_min.data
        campaign.time_on_site_max=form.time_on_site_max.data
        campaign.pages_min=form.pages_min.data
        campaign.pages_max=form.pages_max.data
        campaign.visits_per_day_min=form.visits_per_day_min.data
        campaign.visits_per_day_max=form.visits_per_day_max.data
        campaign.length_from=form.length_from.data
        campaign.length_to=form.length_to.data
        campaign.bounce_rate=form.bounce_rate.data
        campaign.organic_source=form.organic_source.data
        campaign.direct_source=form.direct_source.data
        campaign.social_source=form.social_source.data
        campaign.email_source=form.email_source.data
        campaign.referral_source=form.referral_source.data
        campaign.organic_google=form.organic_google.data
        campaign.organic_yahoo=form.organic_yahoo.data
        campaign.organic_bing=form.organic_bing.data
        campaign.organic_aol=form.organic_aol.data
        campaign.organic_keywords=form.organic_keywords.data
        campaign.referral_settings=form.referral_settings.data
        campaign.social_settings=form.social_settings.data
        campaign.e_cs=form.e_cs.data
        campaign.e_cm=form.e_cm.data
        campaign.e_ct=form.e_ct.data
        campaign.e_cc=form.e_cc.data
        campaign.e_cn=form.e_cn.data
        campaign.email_url=email_url
        campaign.use_proxy_list=form.use_proxy_list.data
        campaign.use_proxy_api=form.use_proxy_api.data
        campaign.proxy_api_url=form.proxy_api_url.data
        campaign.reused_proxy=form.reused_proxy.data
        campaign.proxy_filename=form.proxy.data.filename
        campaign.ua_safari=form.ua_safari.data
        campaign.ua_firefox=form.ua_firefox.data
        campaign.ua_ie=form.ua_ie.data
        campaign.ua_opera=form.ua_opera.data
        campaign.ua_chrome=form.ua_chrome.data
        campaign.ua_iphone=form.ua_iphone.data
        campaign.ua_ipad=form.ua_ipad.data
        campaign.ua_android=form.ua_android.data
        campaign.ua_win=form.ua_win.data
        campaign.ua_mac=form.ua_mac.data
        campaign.ua_linux=form.ua_linux.data
        campaign.save()
        if form.proxy.data:
            campaign.proxy_filename=form.proxy.data.filename
            campaign.save()
            proxies = form.proxy.data.read().splitlines()
            data_source = []
            for proxy in proxies:
                p = proxy.split(':')
                data_source.append({'ip': p[0], 'port': p[1], 'campaign': campaign, 'from_list': True})
            with db.atomic():
                for idx in range(0, len(data_source), 100):
                    Proxy.insert_many(data_source[idx:idx+100]).execute()
        return redirect(url_for('main'))
    return render_template('change.jade', form=form, filename=campaign.proxy_filename, campaign=campaign)


@app.route('/r/<id>')
@requires_auth
def remove_campaign(id):
    Campaign.select().where(Campaign.id == id).get().delete_instance()
    return redirect(url_for('main'))


@app.route('/p/<id>')
@requires_auth
def show_proxies(id):
    proxies = Campaign.select().where(Campaign.id == id).get().proxy
    proxies = [p.ip + ':' + p.port + '  \t' + str(p.used) for p in proxies]
    return Response('\n'.join(proxies), mimetype='text/plain')


@app.route('/rp/<id>')
@requires_auth
def remove_proxies(id):
    proxies = Campaign.select().where(Campaign.id == id).get().proxy
    for proxy in proxies:
        proxy.delete_instance()
    return 'Proxies have been deleted.'


@app.route('/logs')
@requires_auth
def logs():
    with open('/home/filipe/Desktop/project/logs/main.log') as f:
        return Response(f.read(), mimetype='text/plain')


@app.route('/rmlog/<id>')
@requires_auth
def remove_log(id):
    log_file = '../logs/{}.log'.format(id)
    if os.path.isfile(log_file):
        os.remove(log_file)
        return 'Log has been deleted.'
    else:
        return 'There is no log file for this campaign.'


@app.route('/log/<id>')
@requires_auth
def log(id):
    # id = Campaign.select().where(Campaign.id == id).get().id
    try:
        with open('../logs/{}.log'.format(str(id))) as f:
            return Response(f.read(), mimetype='text/plain')
    except IOError:
        return ''


@app.before_request
def before_request():
    g.db = db
    g.db.connect()


@app.after_request
def after_request(response):
    g.db.close()
    return response


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ))


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=58019)
    app.run(host='0.0.0.0', debug=True, port=58019)

