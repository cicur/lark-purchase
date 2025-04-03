import json

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.authen.v1 import *

from selenium import webdriver
from authlib.integrations.requests_client import OAuth2Session
import yaml
import time, os
import tb

def get_user_access_token(client_id, client_secret, scope):
    client = OAuth2Session(client_id, client_secret, scope=scope,redirect_uri='http://localhost/')
    auth_endpoint = 'https://accounts.feishu.cn/open-apis/authen/v1/authorize'
    uri, state = client.create_authorization_url(auth_endpoint)

    driver = webdriver.Edge()
    lark_cookies_path = 'lark_cookies.json'
    if os.path.exists(lark_cookies_path):
        tb.login(driver, lark_cookies_path)
        cookies_flag = True
    else:
        cookies_flag = False
    driver.get(uri)
    while True:
        print("等待用户授权...")
        time.sleep(5)
        if not cookies_flag and driver.current_url.startswith(auth_endpoint):
            tb.save_cookies(driver, lark_cookies_path)
            cookies_flag = True
        if driver.current_url.startswith("http://localhost"):
            break
    auth_response = driver.current_url
    driver.quit()

    client = OAuth2Session(client_id, client_secret, state=state,redirect_uri='http://localhost/')
    token_endpoint = 'https://open.feishu.cn/open-apis/authen/v2/oauth/token'
    token = client.fetch_token(token_endpoint, authorization_response=auth_response, grant_type='authorization_code')
    return token

# SDK 使用说明: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/python--sdk/preparations-before-development

def lark_get_user_info(client, access_token):
    # 构造请求对象
    request: GetUserInfoRequest = GetUserInfoRequest.builder() \
        .build()

    # 发起请求
    option = lark.RequestOption.builder().user_access_token(access_token).build()
    response: GetUserInfoResponse = client.authen.v1.user_info.get(request, option)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.authen.v1.user_info.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return response.data

def lark_add_records(client, item_list, app_token, table_id, access_token, userinfo):
    # 处理数据
    records = []
    timestamp = int(time.time())*1000
    for item in item_list:
        item["付款状态"] = "未发"
        item['申请人'] = [{'id': userinfo['open_id']}]
        item['电话'] = userinfo['mobile']
        item['日期'] = timestamp
        records.append(AppTableRecord.builder().fields(item).build())

    # 构造请求对象
    request: BatchCreateAppTableRecordRequest = BatchCreateAppTableRecordRequest.builder() \
        .app_token(app_token) \
        .table_id(table_id) \
        .user_id_type("open_id") \
        .request_body(BatchCreateAppTableRecordRequestBody.builder()
                      .records(records)
                      .build()) \
        .build()

    # 发起请求
    option = lark.RequestOption.builder().user_access_token(access_token).build()
    response: BatchCreateAppTableRecordResponse = client.bitable.v1.app_table_record.batch_create(request, option)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table_record.batch_create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))

def main():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    tb_item_list = tb.tb()

    token = get_user_access_token(config['client_id'], config['client_secret'], 'base:record:create')
    # 创建client
    client = lark.Client.builder() \
        .enable_set_token(True) \
        .log_level(lark.LogLevel.INFO) \
        .build()

    user = lark_get_user_info(client, token['access_token'])
    userinfo = {'open_id': user.open_id, 'mobile': config.get('user_mobile',user.mobile)}
    lark_add_records(client, tb_item_list, config['app_token'], config['table_id'],token['access_token'], userinfo)

if __name__ == "__main__":
    main()