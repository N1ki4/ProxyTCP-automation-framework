import re
import json

grid = {
    'user_1': 'http://35.217.54.189:4444/wd/hub',
    'user_2': 'http://35.217.18.62:4444/wd/hub',
    'user_3': 'http://127.0.0.1:4444/wd/hub',
}
proxy = 'socks5://35.217.25.199:1080'
proxy_enable = False
url = 'https://receipt1.seiko-cybertime.jp/'
url2 = 'chrome://version'
tag = re.compile(r'(https|http)://(.*)\.').search(url)[2]


if __name__ == "__main__":
    from selenium import webdriver

    # chrome
    chrome_options = webdriver.ChromeOptions()
    chrome_options.capabilities['goog:loggingPrefs'] = { 'browser':'ALL' }  #!
    
    chrome_options.add_argument("--ignore-certificate-errors")
    
    chrome_local_state_prefs = {
    "browser": {
        "enabled_labs_experiments": [
            "legacy-tls-enforced@1",
        ],
        }
    }
    chrome_options.add_experimental_option("localState", chrome_local_state_prefs)
    if proxy_enable is True:
        chrome_options.add_argument(f"--proxy-server={proxy}")
    
    remote_params = {
        "command_executor": grid['user_1'],
        "options": chrome_options,
    }

    driver = webdriver.Remote(**remote_params)
    driver.get(url)
    driver.save_screenshot(f'{tag}.png')
    # print messages
    output = driver.get_log('browser')
    with open('requestresult.json', 'w') as f:
        json.dump(output, f)

    # timings = driver.execute_script("return window.performance.getEntries();")
    # for entry in timings:
    #     print("_________________________________")
    #     for k, v in entry.items():
    #         print(f'"{k}": "{v}"')
    driver.quit()
