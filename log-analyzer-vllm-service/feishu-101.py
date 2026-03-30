import requests # 这玩意和fastapi打架的，是同步，需要换成异步，即httpx
import json

webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/d5c30596-7942-4932-8728-d83716aaaa27"

# 构造请求数据 - 飞书规定的格式，text表示字；at表示@
data = {
    "msg_type": "post",
    "content": {
        "post": {
            "zh_cn": {
                "title": "大哥大姐新年好",
                "content": [
                    [{
                        "tag": "text",
                        "text": "2026 22：02：00"
                    },
                    {
                        "tag": "a",
                        "text": "点击进行更多操作",
                        "href": "http://www.baidu.com/"
                    },
                    {
                        "tag": "text",
                        "text": "\n"
                    },
                    # @所有人
                    {
                        "tag": "at",
                        "user_id": "all"
                    }]
                ]
            }
        }
    }
}

# 设置请求头
headers = {
    "Content-Type": "application/json"
}

try:
    # 发送 POST 请求
    response = requests.post(
        url=webhook_url,
        data=json.dumps(data),
        headers=headers
    )

    # 输出响应结果
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)

except requests.exceptions.RequestException as e:
    print("请求失败:", e)
