# tok715

开发代号: TOK715

## 依赖

* `ffmpeg`, 使用 `ffmpeg` 捕捉麦克风数据流
* `poetry`, 使用 `poetry` 管理 Python 依赖

## 组件

### `tok715-voicerecog`: 语音识别模块

**功能**

* 使用 `ffmpeg` 捕捉麦克风数据流
* 传输数据流到阿里云语音识别服务
* 使用 `redis` 发布识别结果到 `自然语言输入` 主题

**编码格式**

阿里云识别服务要求编码格式为 `pcm_s16le`，采样率为 `16000`，单声道。

### `tok715-vectorstor`: 存储和预处理模块

## Redis PUB/SUB 主题

**自然语言输入**

`tok715:nl-input:USER_GROUP:USER_ID`

```json
{
  "ts": 1698240603702,
  "text": "坐在驶进乡间小路的摇晃公交车里，他回想起了过去唯一次和祖母交谈。",
  "user": {
    "id": "owner",
    "name": "主人",
    "group": "owner"
  }
}
```

## 配置文件

```yaml
# tok715.yml

# 用户身份
# 使用模块：voicerecog
user:
  id: owner
  group: owner
  name: 主人

# redis 配置
# 更多参数，翻阅 https://redis-py.readthedocs.io/en/stable/connections.html
# 使用模块: voicerecog
redis:
  host: '127.0.0.1'
  port: 6379

# 阿里云 服务配置
# 使用模块: voicerecog
aliyun:
  # 阿里云语音识别
  nls:
    endpoint: wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1
    app_key: xxxxx
    access_key_id: xxxxx
    access_key_secret: xxxxx
```

## 许可证

TOK715 Developers, MIT License
