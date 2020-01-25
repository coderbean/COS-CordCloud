import base64
import urllib.request
import os
import codecs
import json
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def parse(ssr_rul):
    ssr = ssr_rul.strip()

    if ssr.startswith('ssr://'):
        base64_encode_str = ssr[6:]
        return parse_ssr(base64_encode_str)
    return "", ""


def parse_ssr(base64_encode_str):
    decode_str = base64_decode(base64_encode_str)
    parts = decode_str.split(':')
    if len(parts) != 6:
        print('不能解析SSR链接: %s' % base64_encode_str)
        return ""

    server = parts[0]
    port = parts[1]
    protocol = parts[2]
    method = parts[3]
    obfs = parts[4]
    password_and_params = parts[5]

    password_and_params = password_and_params.split("/?")

    password_encode_str = password_and_params[0]
    password = base64_decode(password_encode_str)
    params = password_and_params[1]

    param_parts = params.split('&')
    param_dic = {}
    for part in param_parts:
        key_and_value = part.split('=')
        param_dic[key_and_value[0]] = key_and_value[1]

    obfsparam = base64_decode(param_dic['obfsparam'])
    protoparam = base64_decode(param_dic['obfsparam'])
    remarks = base64_decode(param_dic['remarks'])
    group = base64_decode(param_dic['group'])
    # print('server: %s, port: %s, 协议: %s, 加密方法: %s, 密码: %s, 混淆: %s, 混淆参数: %s, 协议参数: %s, 备注: %s, 分组: %s'
    #       % (server, port, protocol, method, password, obfs, obfsparam, protoparam, remarks, group))
    if remarks[:2] in config['china_city_list']:
        remarks = '[国内]' + remarks
    yml = '''- {{ name: "{0}", type: ss, server: {1}, port: {2}, cipher: {3}, password: "{4}" }}'''
    return yml.format(remarks, server, port, method, password), remarks


def fill_padding(base64_encode_str):
    need_padding = len(base64_encode_str) % 4 != 0

    if need_padding:
        missing_padding = 4 - need_padding
        base64_encode_str += '=' * missing_padding
    return base64_encode_str


def base64_decode(base64_encode_str):
    base64_encode_str = fill_padding(base64_encode_str)
    return base64.urlsafe_b64decode(base64_encode_str).decode('utf-8')


def base64_2_str(b64_string):
    b64_string += "=" * ((4 - len(b64_string) % 4) % 4)
    return str(base64.b64decode(b64_string), encoding="utf-8")


def update(intput_name, output_name, name_list, yaml_list):
    switcher = False
    rule_switcher = False
    custom_rule_switcher = False
    is_first_line = False
    with codecs.open(intput_name, 'r', encoding='utf-8') as fi, \
            codecs.open(output_name, 'w', encoding='utf-8') as fo:
        for line in fi:
            if is_first_line:
                # fo.write(update_time + '\n')
                is_first_line = False
                continue
            if line.startswith(
                    '''- { name: "Proxy", type: select, proxies:'''):
                proxy_list = list()
                proxy_list.append("auto")
                for name in name_list:
                    if ('倍率:0.' not in name
                            and not name.endswith('(倍率:1)')) or '[国内]' in name:
                        proxy_list.append(name)
                newline = '''- {{ name: "Proxy", type: select, proxies: {} }}\n'''.format(
                    proxy_list)
                fo.write(newline.replace("'", '"'))
                continue
            if line.startswith(
                    '''- { name: "auto", type: url-test, proxies:'''):
                url_test_list = config['append_name']
                for name in name_list:
                    if ('倍率:0.' in name or name.endswith('(倍率:1.')
                            or '(倍率:2' in name
                            ) or '(倍率:2' in name and '[国内]' not in name:
                        url_test_list.append(name)
                newline = '''- {{ name: "auto", type: url-test, proxies: {}, url: "http://www.gstatic.com/generate_204", interval: 300 }}\n'''.format(
                    url_test_list)
                fo.write(newline.replace("'", '"'))
                continue
            if line == "## auto changed by py3 begin ##\n":
                switcher = True
                fo.write(line)
            if line == "Rule:\n":
                rule_switcher = True
                fo.write(rule_str_part_1)
            if rule_switcher and line == "# 自定义规则\n":
                custom_rule_switcher = True
            if line == "## 您可以在此处插入您补充的自定义规则\n":
                custom_rule_switcher = False
                fo.write(line)
                fo.write(rule_str_part_2)
            if rule_switcher and custom_rule_switcher:
                fo.write(line)
            if line == "## auto changed by py3 end ##\n":
                switcher = False
                new_line = ""
                for ss in yaml_list:
                    new_line = new_line + ss + '\n'
                fo.write(new_line)
            if not switcher and not rule_switcher:
                fo.write(line)


def init_COS(config):
    secret_id = config['cos_secret_id']      # 替换为用户的 secretId
    secret_key = config['cos_secret_key']      # 替换为用户的 secretKey
    region = config['cos_region']     # 替换为用户的 Region
    token = None                # 使用临时密钥需要传入 Token，默认为空，可不填
    scheme = 'https'            # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
    config = CosConfig(Region=region, SecretId=secret_id,
                       SecretKey=secret_key, Token=token, Scheme=scheme)
    # 2. 获取客户端对象
    client = CosS3Client(config)
    return client


def download_template(config, client):
    # 获取文件到本地
    response = client.get_object(
        Bucket=config['cos_bucket'],
        Key=config['input_name'],
    )
    response['Body'].get_stream_to_file(config['input_name'])


def get_config():
    f = open('config.json', 'r')
    text = f.read()
    f.close()
    config = json.loads(text)
    return config


def upload_file(client, config):
    # 根据文件大小自动选择简单上传或分块上传，分块上传具备断点续传功能。
    response = client.upload_file(
        Bucket=config['cos_bucket'],
        LocalFilePath=config['output_name'],
        Key=config['upload_key'],
        PartSize=1,
        MAXThread=10,
        EnableMD5=False
    )
    print(response['ETag'])


if __name__ == '__main__':
    config = get_config()
    client = init_COS(config)
    download_template(config, client)

    # 更新 cordcould 规则 ，同时更新 https://github.com/Hackl0us/SS-Rule-Snippet 规则
    rule_url = config['rule_url']
    rule_f = urllib.request.urlopen(rule_url)
    rule_raw = rule_f.read().decode('utf-8')
    rule_str = rule_raw[rule_raw.find('Rule:\n'):]
    rule_str_part_1 = rule_str[:rule_str.find('# 自定义规则\n')]
    rule_str_part_2 = rule_str[rule_str.find('## 您可以在此处插入您补充的自定义规则\n') +
                               len("## 您可以在此处插入您补充的自定义规则\n"):]
    update_time = rule_raw[:rule_raw.find('\n')]
    url = config['url']
    yaml_list = list()
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
    }
    req = urllib.request.Request(url=url, headers=headers)
    f = urllib.request.urlopen(req)
    b64_string = f.read().decode('utf-8')
    result = base64_2_str(b64_string)

    ssr_url_list = result.split("\n")
    name_list = list()
    name_list.extend(config['append_name'])
    for ssr_url in ssr_url_list:
        tmp, name = parse(ssr_url)
        if len(tmp) > 0:
            yaml_list.append(tmp)
            name_list.append(name)

    input_name = config['input_name']
    output_name = config['output_name']
    update(input_name, output_name, name_list, yaml_list)
    upload_file(client, config)
