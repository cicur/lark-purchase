from selenium import webdriver
import requests
import os, time, json

def save_cookies(driver, cookies_path):
    cookies_list = driver.get_cookies()
    cookies_dict = {cookie['name']:cookie['value'] for cookie in cookies_list}
    cookies_json = json.dumps(cookies_dict)  # 转换成字符串保存
    with open(cookies_path, 'w') as f:
        f.write(cookies_json)
    print('cookies保存成功！'+cookies_path)
    driver.quit()
    return cookies_dict

def lcsc_login(url, title):
    driver = webdriver.Edge()
    driver.get(url)
    while True:
        print('等待用户登录...')
        time.sleep(5)
        if driver.title == title:
            break
    return driver

def get_items(cart):
    currently_product_list = cart.get("currentlyProductList", [])   # 现货
    is_need_product_list = cart.get("isNeedProductList", [])        # 订货
    product_list = currently_product_list + is_need_product_list    # 合并

    item_list = [{'采购内容':product['productModel'], '购买链接':'https://item.szlcsc.com/'+str(product['productId'])+'.html',
                  '型号':'无', '单价':product['productDiscountPrice'] or product['productConsultPrice'], '个数':product['productOrderNumber']} \
                 for product in product_list]

    return item_list

def lcsc():
    # cart_url = 'https://cart.szlcsc.com/cart/display.html'
    cart_login_url = 'https://passport.jlc.com/login?redirectUrl=http%3A%2F%2Fcart.szlcsc.com%2Fcart%2Fdisplay.html'
    cart_api_url = 'https://cart-api.szlcsc.com/cart/display'
    cart_title ='我的购物车-立创商城'
    lcsc_cookies_path = 'lcsc_cookies.json'
    if os.path.exists(lcsc_cookies_path):
        with open(lcsc_cookies_path, 'r') as f:
            cookies_dict = json.load(f)
    else:
        cookies_dict = save_cookies(lcsc_login(cart_login_url, cart_title), lcsc_cookies_path)
    cart_json = requests.get(cart_api_url, cookies=cookies_dict).json()
    if cart_json['code'] != 200 and cart_json['msg'] is not None:
        print(str(cart_json['code'])+cart_json['msg'])
        item_list = []
    else:
        item_list = get_items(cart_json['result']['shoppingCartVO']['rmbCnShoppingCart'])

    return item_list

if __name__ == "__main__":
    lcsc()