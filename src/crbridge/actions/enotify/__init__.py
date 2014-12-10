#!/usr/bin/python
######################################################################
# Cloud Routes Bridge
# -------------------------------------------------------------------
# Actions Module
######################################################################

import jinja2
import syslog
import time

def action(**kwarg):
    ''' This method is called to action a reaction '''
    # This method can be used for legacy reactions that have
    # a different function based on true/false
    if "false" in kwarg['jdata']['check']['status']:
        return false(kwarg['redata'], kwarg['jdata'],
            kwarg['rdb'], kwarg['r_server'], kwarg['config'])
    if "true" in kwarg['jdata']['check']['status']:
        return true(kwarg['redata'], kwarg['jdata'],
            kwarg['rdb'], kwarg['r_server'], kwarg['config'])


def false(redata, jdata, rdb, r_server, config):
    ''' This method will be called when a monitor has false '''
    run = True
    # Check for Trigger
    if redata['trigger'] > jdata['failcount']:
        run = False

    # Check for lastrun
    checktime = time.time() - float(redata['lastrun'])
    if checktime < redata['frequency'] or checktime < 900:
        run = False

    if run:
        result = emailNotify(redata, jdata, "false.msg", config)
        if result:
            line = "enotify: Sent %s email notification for monitor %s" % (
                jdata['check']['status'], jdata['cid'])
            syslog.syslog(syslog.LOG_INFO, line)
            return True
        else:
            line = "enotify: False to send %s email notification for monitor %s" % (jdata['check']['status'], jdata['cid'])
            syslog.syslog(syslog.LOG_ERR, line)
            return False
    else:
        line = "enotify: Skipping %s email notification for monitor %s" % (
            jdata['check']['status'], jdata['cid'])
        syslog.syslog(syslog.LOG_ERR, line)
        return None


def true(redata, jdata, rdb, r_server, config):
    ''' This method will be called when a monitor has passed '''
    run = True
    if "true" in jdata['check']['prev_status']:
        run = False

    if "send_true" in redata['data']:
        if redata['data']['send_true'] == "False":
            run = False

    if run:
        result = emailNotify(redata, jdata, "true.msg", config)
        if result:
            line = "enotify: Sent %s email notification for monitor %s" % (
                jdata['check']['status'], jdata['cid'])
            syslog.syslog(syslog.LOG_INFO, line)
            return True
        else:
            line = "enotify: False to send %s email notification for monitor %s" % (jdata['check']['status'], jdata['cid'])
            syslog.syslog(syslog.LOG_ERR, line)
            return False
    else:
        line = "enotify: Skipping %s email notification for monitor %s" % (
            jdata['check']['status'], jdata['cid'])
        syslog.syslog(syslog.LOG_INFO, line)
        return None


def emailNotify(redata, jdata, tfile, config):
    '''
    This method will be called to notify a user via email of status changes
    '''
    import requests
    import json

    data = {}
    templateLoader = jinja2.FileSystemLoader(
        searchpath="/data/crbridge/templates/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(tfile)

    data['name'] = jdata['name']
    msg = template.render(data)

    mandrill_data = {
        "key": config['mandrill_api_key'],
        "message": {
            "text": msg,
            "from_email": "noreply@runbook.io",
            "from_name" : "Runbook Notifications",
            "subject" : "Monitor Alerts",
            "to" : [
                { "email": redata['data']['email'] }
            ]
        },
        "async" : True
    }

    payload = json.dumps(mandrill_data)
    url = config['mandrill_api_url'] + "/messages/send.json"
    try:
        result = requests.post(url=url, data=payload, timeout=1.0, verify=True)
    except:
        return False
    if result.status_code >= 200 and result.status_code <= 299:
      return True
    else:
      line = "enotify: Got status code %d from mandrill for monitor %s" % (
            result.status_code, jdata['cid'])
      return False
