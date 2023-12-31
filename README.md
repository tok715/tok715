# tok715

开发代号: TOK715

## 1. 系统构架

```mermaid
flowchart TB
    node_mic(用户: 麦克风)
    node_speaker(用户: 扬声器)
    node_audiotouch_main("模块: tok715-audiotouch")
    node_inputdirec_main("模块: tok715-inputdirec")
    node_ai_service_main("模块: tok715-ai-service")
    node_corepsyche_main("模块: tok715-corepsyche")
    node_danmucolle_main("模块: tok715-danmucolle")
    node_aliyun_nls(阿里云: 语音识别/合成服务)
    node_bilibili_stream(哔哩哔哩: 直播间)
    node_redis_queue(Redis 队列)
    node_mysql_messages(MySQL 数据库)
    node_milvus_messages(Milvus 向量数据库)
    node_mic --> node_audiotouch_main
    node_audiotouch_main --> node_speaker
    node_audiotouch_main <--> node_aliyun_nls
    node_audiotouch_main -- 用户输入 --> node_redis_queue
    node_redis_queue -- 模型输出 --> node_audiotouch_main
    node_inputdirec_main -- 用户输入 --> node_redis_queue
    node_bilibili_stream --> node_danmucolle_main -- 用户输入 --> node_redis_queue
    node_redis_queue -- 用户输入 --> node_corepsyche_main
    node_corepsyche_main -- 模型输出 --> node_redis_queue
    node_corepsyche_main <-- 原始数据 --> node_mysql_messages
    node_corepsyche_main <-- 向量化 --> node_ai_service_main
    node_corepsyche_main <-- 推理 --> node_ai_service_main
    node_corepsyche_main <-- 向量数据 --> node_milvus_messages
```

## 2. 依赖

* 尽可能高端的英伟达显卡
* **python > 3.10**
* **ffmpeg**, 用来捕捉麦克风数据流
* **poetry**, 用来管理 python 依赖

## 3. 模块

### 3.1 音频交互模块: `audiotouch`

* 输入
    * 使用 `ffmpeg` 捕捉麦克风数据流
    * 传输数据流到阿里云语音识别服务
    * 使用 `redis` 发布识别结果到 `自然语言输入` 主题
* 输出
    * 使用 `redis` 订阅 `模型输出` 主题
    * 适用 阿里云语音合成服务 将输出结果转换为语音
    * 使用 `ffplay` 播放语音合成结果

**输入格式**

阿里云语音识别服务要求编码格式为 `pcm_s16le, 16khz, mono`

### 3.2 AI 服务模块: `ai-service`

* 监听 HTTP 端口
* 提供 `向量计算` 接口
* 提供 `推理` 接口

**接口调用方法**

```
POST /invoke
```

**接口定义: 向量计算**

请求:

```json
{
  "method": "embeddings",
  "args": {
    "input_texts": [
      "早上好中国我有草履虫",
      "早上好中国我有冰淇淋"
    ]
  }
}
```

返回:

```json
{
  "result": {
    "vectors": [
      [],
      []
    ]
  }
}
```

**接口定义: 生成**

请求:

```json
{
  "method": "chat",
  "args": {
    "query": "",
    "system": "",
    "history": [
      [
        "你好",
        "你好"
      ]
    ]
  }
}
```

返回:

```json
{
  "result": {
    "response": "我是小可爱",
    "history": [
      [
        "你好",
        "你好"
      ]
    ]
  }
}
```

### 3.3 核心思维模块: `corepsyche`

### 3.4 弹幕收集模块: `danmucolle`

## 4. Redis PUB/SUB 队列

**自然语言输入**

`tok715:nl-input:USER_GROUP:USER_ID`

```json
{
  "ts": 1698240603702,
  "content": "坐在驶进乡间小路的摇晃公交车里，他回想起了过去唯一次和祖母交谈。",
  "user": {
    "id": "owner",
    "display_name": "主人",
    "group": "owner"
  }
}
```

## 5. 配置文件

```yaml
# tok715.yml

# 用户身份
# 使用模块：audiotouch
user:
  id: owner
  display_name: 主人
  group: owner

# redis 配置
# 更多参数，翻阅 https://redis-py.readthedocs.io/en/stable/connections.html
# 使用模块: audiotouch, corepsyche, danmucolle
redis:
  host: '127.0.0.1'
  port: 6379

# 数据库配置
# 使用模块: corepsyche
database:
  url: 'mysql+pymysql://root:root@localhost:3306/tok715'
  # 更多参数，翻阅 https://docs.sqlalchemy.org/en/20/core/engines.html
  echo: true

# milvus 配置
# 使用模块: corepsyche
milvus:
  alias: "default"
  host: 'localhost'
  port: '19530'

# 阿里云 服务配置
# 使用模块: audiotouch
aliyun:
  # 阿里云语音识别
  nls:
    endpoint: wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1
    app_key: xxxxx
    access_key_id: xxxxx
    access_key_secret: xxxxx

# AI 服务配置
# 客户端使用 url 字段调用
# 服务端使用 server 字段配置
# 使用模块: corepsyche
ai_service:
  url: http://127.0.0.1:9891/invoke

  server:
    host: '127.0.0.1'
    port: 9891
```

## 6. 许可证

TOK715 Developers, MIT License
