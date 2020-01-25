# 项目描述
本项目用于获取 CordCloud SSR 订阅链接然后转为 SS 链接，写入到指定的文件中，同时将文件上传到指定的腾讯 COS 地址。

# 解决的问题
1. 有些时候你的订阅被墙了，或者订阅本身不稳定挂了
2. 你的 Mac 在使用 ClashX 而你的机场并不提供 SS 以外的订阅类型
3. 对于不同倍率的节点做了区分，倍率低于 3 的自动加入到测试列表，倍率高于 2 的可以自己选择

# 配置文件
config-template.json 仅仅用作举例，自己的配置需要重命名为 config.json

## 举例
config.json
```json
{
    "rule_url": "https://raw.githubusercontent.com/Hackl0us/SS-Rule-Snippet/master/LAZY_RULES/clash.yaml",
    "url": "https://www.cordcord.xyz/link/f6NPtV0Kr3woDPTm?mu=0",
    "append_name": [
        "vmessBDW"
    ],
    "china_city_list": [
        "上海",
        "徐州",
        "深圳",
        "北京"
    ],
    "input_name": "template.yaml",
    "output_name": "config.yaml",
    "upload_key": "CordCloud/MuGpOzidudPurlyNEW.yaml",
    "cos_bucket": "xxxx",
    "cos_secret_id": "xxx",
    "cos_secret_key": "xxxx",
    "cos_region": "ap-xxx"
}
```

## 含义

| 配置名          | 含义                                                         | 备注 |
| --------------- | ------------------------------------------------------------ | ---- |
| rule_url        | 分流规则订阅地址                                             |      |
| url             | SS 订阅地址（或者是 plain 的SSR）                            |      |
| append_name     | 如果你在模版文件中自定义了节点，可以在这里加进去             |      |
| china_city_list | 中国的节点，有些订阅可能会有回国节点，过滤掉回国节点防止自动测速选择国内节点 |      |
| input_name      | 模版文件在本地存储的文件名                                   |      |
| output_name     | 转换后的本地文件名                                           |      |
| upload_key      | 上传到 COS，在 COS 中 的文件名                               |      |
| cos_bucket      | COS bucket 桶名字                                            |      |
| cos_secret_id   | COS 密钥信息                                                 |      |
| cos_secret_key  | COS 密钥信息                                                 |      |
| cos_region      | COS 地区信息                                                 |      |

# 推荐用法
在自己的 VPS 上利用定时任务触发该脚本。通过 COS 更新本地的订阅