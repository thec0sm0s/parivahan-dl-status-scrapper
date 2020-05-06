# Parivahan Sewa DL Status Scrapper

A Python CLI scrapper for https://parivahan.gov.in/rcdlstatus/?pur_cd=101 which parses and returns the Driving License details in JSON form and saves it to the disc in project root with `dl.json` name.


### Entry Point

Override the default `app.get_captcha(captcha_src)`. For now it displays the captcha in your browser which needs to be entered manually.

Use `python app.py` to start the application.

- Enter the DL number [DL-XXXXXXXXXXXXX]
- Enter the Date of birth: [DD-MM-YYYY]
