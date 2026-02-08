# 情侣任务奖励系统 (LoveTask) 设计文档

## 1. 项目概述
这是一个专为情侣设计的 Web 应用程序，旨在通过游戏化的任务和奖励机制增进互动。用户可以通过完成预设任务获得虚拟货币（积分），并使用积分为现实生活中的愿望或物品进行兑换。

## 2. 技术架构
考虑到易部署、数据隐私和轻量级需求，推荐使用以下技术栈：

- **后端**: Python (FastAPI) - 高性能，开发效率高，适合构建 RESTful API。
- **数据库**: SQLite - 轻量级文件数据库，无需安装额外服务，数据易于备份和迁移（完美契合“不能只存在浏览器缓存”且“易于部署”的需求）。
- **前端**: HTML5 + TailwindCSS + JavaScript (Vue.js CDN 或 Jinja2 模板) - 响应式设计，适配手机和电脑浏览器。
- **部署**: Docker 或 直接 Python 运行。支持 Linux 机器端口映射访问。

## 3. 核心功能模块

### 3.1 经济系统
- **虚拟货币**: 定义一个货币单位（如“金币”、“爱心值”）。
- **汇率系统**: 可配置 1 金币 = X 人民币（仅作参考，用于价值锚定）。
- **钱包**: 每个用户拥有独立的余额。

### 3.2 任务系统 (Tasks)
支持多种任务类型：
- **每日任务 (Daily)**: 每天重置。支持“连续打卡”奖励（Streak Bonus）和“中断惩罚”（Penalty）。
- **单次任务 (One-time)**: 完成一次后结束，或需重新发布。
- **周期任务**: 每周/每月特定时间刷新。
- **审批机制**: 任务完成可以设置为“自动确认”或“需对方审批”。

### 3.3 奖励系统 (Rewards)
- **商品上架**: 上架现实生活中的物品或服务（如“洗碗券”、“周末大餐”、“买个包”）。
- **库存管理**: 可限制兑换次数（如“限量版”）。
- **兑换流程**: 用户消耗金币兑换 -> 扣除余额 -> 生成兑换记录 -> 对方确认/执行 -> 标记为已交付。

### 3.4 数据统计
- **流水记录**: 所有的金币获取和消耗都有据可查。
- **图表展示**: 只有数据持久化存储才能支持历史趋势查看。

## 4. 数据库模型设计 (Draft)

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    balance REAL DEFAULT 0,  -- 当前余额
    partner_id INTEGER       -- 绑定伴侣
);

-- 任务表
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    reward_amount REAL NOT NULL, -- 奖励金额
    type TEXT,                   -- 'daily', 'one_time', 'weekly'
    penalty_amount REAL DEFAULT 0, -- 未完成惩罚
    needs_approval BOOLEAN DEFAULT 0, -- 是否需要审批
    is_active BOOLEAN DEFAULT 1
);

-- 任务执行记录
CREATE TABLE task_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    task_id INTEGER,
    status TEXT, -- 'pending_approval', 'completed', 'failed'
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 商品表
CREATE TABLE rewards (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    cost REAL NOT NULL,
    stock INTEGER DEFAULT -1, -- -1 表示无限
    is_active BOOLEAN DEFAULT 1
);

-- 兑换记录
CREATE TABLE redemptions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    reward_id INTEGER,
    cost_snapshot REAL, -- 兑换时的价格
    status TEXT, -- 'pending_delivery', 'delivered'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 资金流水
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    amount REAL, -- 正数为收入，负数为支出
    type TEXT, -- 'task_reward', 'redemption', 'penalty', 'manual_adjustment'
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 5. 部署方案
- 项目将包含一个 `start.sh` 或 `Dockerfile`。
- 所有的状态数据保存在服务器端的 `love_task.db` 文件中。
- 用户通过 `http://<服务器IP>:<端口>` 访问，只要 Linux 机器有公网 IP 或做了内网穿透/端口映射即可。
