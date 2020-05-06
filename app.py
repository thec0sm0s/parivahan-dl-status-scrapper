from lxml import html, etree
from pprint import pprint
import json
import requests


class WrongDLOrDOB(Exception):

    pass


class InvalidCaptcha(Exception):

    pass


class UnExpectedResponse(Exception):

    pass


BASE_URL = "https://parivahan.gov.in"
FORM_URL = BASE_URL + "/rcdlstatus/?pur_cd=101"


def get_captcha(captcha_src):
    html.open_in_browser(html.fromstring(f"<img src='{captcha_src}' />"))
    return input("Enter the captcha displayed in browser: ")


def write_json(data):
    with open("dl.json", "w") as file:
        json.dump(data, file, indent=4)


def get_viewstate_from_tree(t):
    return t.xpath('//*[@id="j_id1:javax.faces.ViewState:0"]/text()')[0]


def get_viewstate(session, data):
    res = session.post(FORM_URL, data=data)
    _tree = etree.fromstring(res.content)
    return get_viewstate_from_tree(_tree)


def fill_form_and_parse(dl_number, dob):
    session = requests.Session()
    page = session.get(FORM_URL)
    tree = html.fromstring(page.content)

    captcha_src = BASE_URL + tree.xpath('//*[@id="form_rcdl:j_idt34:j_idt41"]')[0].attrib["src"]
    captcha = get_captcha(captcha_src)

    viewstate = tree.xpath('//*[@id="j_id1:javax.faces.ViewState:0"]')[0].attrib["value"]
    _ = {
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source: form_rcdl': 'tf_dlNO',
        'javax.faces.partial.execute': 'form_rcdl:tf_dlNO',
        'javax.faces.partial.render': 'form_rcdl:tf_dlNO',
        'javax.faces.behavior.event': 'valueChange',
        'javax.faces.partial.event': 'change',
        'form_rcdl': 'form_rcdl',
        'form_rcdl: tf_dlNO': dl_number,
        'form_rcdl: tf_dob_input': '',
        'form_rcdl: j_idt34:CaptchaID': '',
        'javax.faces.ViewState': viewstate}
    viewstate = get_viewstate(session, _)

    _ = {
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'form_rcdl:tf_dob',
        'javax.faces.partial.execute': 'form_rcdl:tf_dob',
        'javax.faces.partial.render': 'form_rcdl:tf_dob',
        'javax.faces.behavior.event': 'valueChange',
        'javax.faces.partial.event': 'change',
        'form_rcdl:tf_dob_input': dob,
        'javax.faces.ViewState': viewstate}
    try:
        viewstate = get_viewstate(session, _)
    except IndexError:
        raise WrongDLOrDOB

    _ = {
        'form_rcdl': 'form_rcdl',
        'form_rcdl:tf_dlNO': dl_number,
        'form_rcdl:tf_dob_input': dob,
        'form_rcdl:j_idt37:CaptchaID': captcha,
        'javax.faces.ViewState': viewstate,
        'javax.faces.source': 'form_rcdl:j_idt37:CaptchaID',
        'javax.faces.partial.event': 'blur',
        'javax.faces.partial.execute': 'form_rcdl:j_idt37:CaptchaID',
        'javax.faces.partial.render': 'form_rcdl:j_idt37:CaptchaID',
        'CLIENT_BEHAVIOR_RENDERING_MODE': 'OBSTRUSIVE',
        'javax.faces.behavior.event': 'blur',
        'javax.faces.partial.ajax': 'true'}
    try:
        viewstate = get_viewstate(session, _)
    except IndexError:
        raise InvalidCaptcha

    _ = {
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'form_rcdl:j_idt50',
        'javax.faces.partial.execute': '@all',
        'javax.faces.partial.render': 'form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl',
        'form_rcdl:j_idt46': 'form_rcdl:j_idt46',
        'form_rcdl': 'form_rcdl',
        'form_rcdl:tf_dlNO': dl_number,
        'form_rcdl:tf_dob_input': dob,
        'form_rcdl:j_idt37:CaptchaID': captcha,
        'javax.faces.ViewState': viewstate}

    res = session.post(FORM_URL, data=_)
    __tree = etree.fromstring(res.content)

    if __tree.xpath('//changes/extensions'):
        raise InvalidCaptcha
    if __tree.xpath('//changes/eval'):
        raise WrongDLOrDOB

    __html = html.fromstring(__tree.xpath('//update[@id="form_rcdl:rcdl_pnl"]')[0].text)

    try:
        table1 = __html.xpath('//*[@id="form_rcdl:j_idt118"]/table[1]')[0]
    except IndexError:
        raise UnExpectedResponse
    else:
        tr = table1.xpath('//table[1]')[0].xpath('//tbody')[0].xpath('//tr')

    __data = {
        "dl_number": dl_number,
        "current_status": tr[0].getchildren()[-1].text_content(),
        "holder_name": " ".join(tr[1].getchildren()[-1].text_content().split()),
        "date_of_issue": tr[2].getchildren()[-1].text_content(),
        "last_transaction_at": tr[3].getchildren()[-1].text_content(),
        "old_or_new_dl_number": tr[4].getchildren()[-1].text_content(),
        "non_transport": {
            "from": tr[5].getchildren()[1].text_content().split()[-1],
            "to": tr[5].getchildren()[-1].text_content().split()[-1]
        },
        "transport": {
            "from": tr[6].getchildren()[1].text_content().split()[-1],
            "to": tr[6].getchildren()[-1].text_content().split()[-1]
        },
        "hazardous_valid_till": tr[7].getchildren()[1].text_content(),
        "hill_valid_till": tr[7].getchildren()[-1].text_content(),
        "cov_category": tr[9].getchildren()[0].text_content(),
        "class_of_vehicle": tr[9].getchildren()[1].text_content(),
        "cov_issue_date": tr[9].getchildren()[2].text_content()
    }

    write_json(__data)
    session.close()
    return __data


def run(dl_number, dob):
    while True:
        try:
            dl_json = fill_form_and_parse(dl_number, dob)
        except InvalidCaptcha:
            pass
        else:
            return dl_json


def get_stdin():
    return input("Enter the DL number [DL-XXXXXXXXXXXXX]: "), input("Enter the Date of birth: [DD-MM-YYYY]: ")


if __name__ == "__main__":
    while True:
        try:
            sdtin = get_stdin()
            _ = run(*sdtin)
        except WrongDLOrDOB:
            print("!! Either DL number or the date of birth is incorrect.")
        except UnExpectedResponse:
            print("!! Re-check and verify DL Number, DOB and Captcha.")
        except IndexError:
            print("!! Internal Error. Retrying for same DL number and DOB.")
        else:
            print(f"--- Details of Driving License: {_['dl_number']} --- ", end=str())
            write_json(_)
            print(f"Written to > dl.json ---")
            pprint(_, indent=4)
            break
