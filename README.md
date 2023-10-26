# tok715

开发代号: TOK715

## 1. 系统构架

```mermaid
flowchart TB
    node_mic(用户: 麦克风)
    node_speaker(用户: 扬声器)
    node_voicerecog_main("模块: tok715-voicerecog")
    node_speechloud_main("模块: tok715-speechloud")
    node_vectorstor_main("模块: tok715-vectorstor")
    node_ai_service_main("模块: tok715-ai-service")
    node_mindignite_main("模块: tok715-mindignite")
    node_danmucolle_main("模块: tok715-danmucolle")
    node_aliyun_nls(阿里云: 语音识别服务)
    node_aliyun_tts(阿里云: 语音合成服务)
    node_bilibili_stream(哔哩哔哩: 直播间)
    node_redis_queue_input(Redis 队列: 用户输入)
    node_redis_queue_output(Redis 队列: 模型输出)

    subgraph MySQL
        node_mysql_messages(表: messages)
    end
    subgraph Milvus
        node_milvus_messages(表: messages)
    end

    node_mic --> node_voicerecog_main <--> node_aliyun_nls
    node_voicerecog_main --> node_redis_queue_input
    node_redis_queue_input --> node_vectorstor_main -- 原始数据 --> node_mysql_messages
    node_vectorstor_main <-- 向量化 --> node_ai_service_main
    node_vectorstor_main -- 向量数据 --> node_milvus_messages
    node_milvus_messages -- 向量数据 --> node_mindignite_main
    node_mysql_messages -- 原始数据 --> node_mindignite_main
    node_mindignite_main <-- 推理 --> node_ai_service_main
    node_mindignite_main --> node_redis_queue_output --> node_speechloud_main
    node_speechloud_main <--> node_aliyun_tts
    node_speechloud_main --> node_speaker
    node_bilibili_stream --> node_danmucolle_main --> node_redis_queue_input
```

## 2. 依赖

* 最新最好的英伟达显卡
* **python > 3.10**
* **ffmpeg**, 用来捕捉麦克风数据流
* **poetry**, 用来管理 python 依赖

## 3. 模块

### 3.1 语音识别模块: `voicerecog`

**功能**

* 使用 `ffmpeg` 捕捉麦克风数据流
* 传输数据流到阿里云语音识别服务
* 使用 `redis` 发布识别结果到 `自然语言输入` 主题

**编码格式**

阿里云语音识别服务要求编码格式为 `pcm_s16le, 16khz, mono`

### 3.2 AI 服务模块: `ai-service`

**功能**

* 监听 HTTP 端口
* 提供 `向量化` 服务
* 提供 `推理` 服务

### 3.3 存储处理模块: `vectorstor`

**功能**

* 监听 `redis` `自然语言输入` 主题
* 存储到 `MySQL`
* 向量化 (调用 `ai-service`) 并存储到 `Milvus`

### 3.4 思维触发模块: `mindignite`

### 3.5 语音合成模块: `speechloud`

### 3.6 弹幕收集模块: `danmucolle`

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
# 使用模块：voicerecog
user:
  id: owner
  display_name: 主人
  group: owner

# redis 配置
# 更多参数，翻阅 https://redis-py.readthedocs.io/en/stable/connections.html
# 使用模块: voicerecog
redis:
  host: '127.0.0.1'
  port: 6379

# 数据库配置
# 使用模块: vectorstor
database:
  url: 'mysql+pymysql://root:root@localhost:3306/tok715'
  # 更多参数，翻阅 https://docs.sqlalchemy.org/en/20/core/engines.html
  echo: true

# milvus 配置
# 使用模块: vectorstor
milvus:
  alias: "default"
  host: 'localhost'
  port: '19530'

# 阿里云 服务配置
# 使用模块: voicerecog
aliyun:
  # 阿里云语音识别
  nls:
    endpoint: wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1
    app_key: xxxxx
    access_key_id: xxxxx
    access_key_secret: xxxxx

# AI 服务配置
# 使用模块: ai-service (server 字段)
# 使用模块: vectorstor (address 字段)
ai_service:
  address: 127.0.0.1:9891

  server:
    host: '127.0.0.1'
    port: 9891

    models:
      generation: 'CausalLM/14B'
      embeddings: 'intfloat/multilingual-e5-large'
```

## 6. 许可证

TOK715 Developers, MIT License
