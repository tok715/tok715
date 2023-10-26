# tok715

开发代号: TOK715

```mermaid
---
title: 系统构架
---
flowchart TB
    node_mic(麦克风)

    subgraph 阿里云
        direction TB
        node_aliyun_nls(语音识别服务)
    end

    subgraph TOK715
        direction TB
        node_voicerecog_main("语音识别模块
        voicerecog")
        node_vectorstor_main("存储处理模块
        vectorstor")
        node_ai_service_main("AI 服务模块
        ai-service")
    end

    subgraph 基础服务
        direction TB
        subgraph Redis
            node_redis_queue(队列: 用户输入)
        end
        subgraph MySQL
            node_mysql_messages(表: messages)
        end
        subgraph Milvus
            node_milvus_messages(表: messages)
        end
    end

    node_mic --> node_voicerecog_main <--> node_aliyun_nls
    node_voicerecog_main --> node_redis_queue
    node_redis_queue --> node_vectorstor_main --> node_mysql_messages
    node_vectorstor_main <-- 向量化 --> node_ai_service_main
    node_vectorstor_main --> node_milvus_messages
```

## 1. 依赖

* `NVIDIA CUDA`, 使用 GPU 加速
* `ffmpeg`, 捕捉麦克风数据流
* `poetry`, 管理 Python 依赖

## 2. 模块

### 2.1 `tok715-voicerecog` 语音识别模块

**功能**

* 使用 `ffmpeg` 捕捉麦克风数据流
* 传输数据流到阿里云语音识别服务
* 使用 `redis` 发布识别结果到 `自然语言输入` 主题

**编码格式**

阿里云语音识别服务要求编码格式为 `pcm_s16le, 16khz, mono`

### 2.2 `tok715-vectorstor`: 存储处理模块

**功能**

* 监听 `redis` `自然语言输入` 主题
* 存储到 `MySQL`
* 向量化 (调用 `ai-service`) 并存储到 `Milvus`

### 2.2 `tok715-ai-service`: AI 服务模块

**功能**

* 监听 HTTP 端口
* 提供 `向量化` 和 `推理` 服务

## 3. Redis PUB/SUB 主题

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

## 4. 配置文件

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

    model: 'CausalLM/14B'
```

## 5. 许可证

TOK715 Developers, MIT License
