from selenium import webdriver
# import csv
import os
import time
import json


def browser_init():  # 浏览器初始化
    options = webdriver.EdgeOptions()
    options.set_capability('ms:edgeOptions', {'perfLoggingPrefs':{'enableNetwork':True, 'enablePage':False}})
    options.set_capability('ms:loggingPrefs', {'performance':'ALL'})
    driver = webdriver.Edge(options=options)
    return driver

def first_login(url, driver, title):
    driver.get(url)
    while True:
        print("等待打开登录后的页面...")
        time.sleep(5)
        if driver.title == title:
            break

def save_cookies(driver, cookies_path):
    cookies_list = driver.get_cookies()
    cookies_json = json.dumps(cookies_list)  # 转换成字符串保存

    with open(cookies_path, 'w') as f:
        f.write(cookies_json)
    print('cookies保存成功！'+cookies_path)

def login(driver, cookies_path):
    driver.get('about:blank')
    with open(cookies_path, 'r') as f:
        cookies_list = json.load(f)
        for cookie in cookies_list:
            # del cookie['domain']
            # driver.add_cookie(cookie)
            driver.execute_cdp_cmd('Network.setCookie', cookie)

def get_xhr_logs(driver, filter_str):
    log_xhr_id_array = []
    log_list = driver.get_log('performance')
    for log in log_list:
        message_ = log['message']
        try:
            log = json.loads(message_)['message']
                    # 去掉静态js、css等，仅保留xhr请求
            if log['params']['type'].upper() == "XHR" and log['params']['request']['url'].startswith(filter_str):
                log_xhr_id_array.append(log['params']['requestId'])

        except:
            pass
    return log_xhr_id_array

def get_item(data,seller_id):
    item_keys = data['hierarchy']['structure']['itemGroup_i_'+seller_id]
    item_list = []
    for item in item_keys:
        model = ', '.join(list(data['data'][item]['fields']['sku']['skuMap'].values())) if len(data['data'][item]['fields']['sku']['skuMap']) else '无'
        # item_list.append({'name':data['data'][item]['fields']['title'],'link':data['data'][item]['fields']['outerUrl'].replace("&from=cart&","&"),'model': model, 'u_price':data['data'][item]['fields']['pay']['now'], 'quantity':data['data'][item]['fields']['quantity']})
        item_list.append({'采购内容':data['data'][item]['fields']['title'],'购买链接':data['data'][item]['fields']['outerUrl'].replace("&from=cart&","&"),'型号': model, '单价':data['data'][item]['fields']['pay']['now']/100.0, '个数':data['data'][item]['fields']['quantity']})
    return item_list

def get_cart(url, driver):
    driver.get(url)
    time.sleep(5)
    request_id = get_xhr_logs(driver, 'https://h5api.m.taobao.com/h5/mtop.trade.query.bag')
    for rid in request_id:
        content = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': rid})
        try:
            body = json.loads(content['body'])
            item_list = get_item(body['data'], '2658592015')
            # with open('cart_items.csv', 'w') as cf:
            #     fieldnames = ['采购内容', '购买链接', '型号', '单价', '个数']
            #     writer = csv.DictWriter(cf, fieldnames=fieldnames)
            #     writer.writeheader()
            #     for item in item_list:
            #         writer.writerow(item)
            # print('csv保存成功！')
            return item_list
        except Exception as e:
            print(e)
        # with open('body.json', 'w', encoding='UTF-8') as bf:
        #     bf.write(content['body'])


def tb():
    cart_url = "https://cart.taobao.com/cart.htm"
    cart_title = '淘宝网 - 我的购物车'
    tb_cookies_path = 'taobao_cookies.json'
    driver = browser_init()
    if os.path.exists(tb_cookies_path):
        login(driver, tb_cookies_path)
    else:
        first_login(cart_url, driver, cart_title)
        save_cookies(driver, tb_cookies_path)
    time.sleep(2)
    # first_login(cart_url, driver)
    item_list = get_cart(cart_url, driver)

    driver.quit()
    return item_list

if __name__ == "__main__":
    tb()