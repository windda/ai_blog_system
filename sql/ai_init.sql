-- ============================================================
-- AI 多轮对话记忆模块 — 数据库建表脚本（Tier4 主线）
-- 
-- 用途：创建 AI 会话和消息存储表
-- 执行方式：在项目数据库中运行此脚本
-- ============================================================

CREATE TABLE IF NOT EXISTS bowl_ai_session (
    session_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '会话ID',
    user_id INT NOT NULL COMMENT '用户ID（关联 sys_user.user_id）',
    title VARCHAR(200) COMMENT '会话标题',
    model VARCHAR(50) DEFAULT 'deepseek-chat' COMMENT 'AI 模型名称',
    message_count INT DEFAULT 0 COMMENT '消息总数',
    total_tokens INT DEFAULT 0 COMMENT '累计消耗 token 数',
    summary_content TEXT COMMENT '远期消息压缩摘要',
    status CHAR(1) DEFAULT '1' COMMENT '状态：1=活跃 0=归档',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_ai_session_user (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 对话会话表';

CREATE TABLE IF NOT EXISTS bowl_ai_message (
    message_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '消息ID',
    session_id INT NOT NULL COMMENT '会话ID',
    seq INT NOT NULL COMMENT '消息序号（会话内递增）',
    role VARCHAR(10) NOT NULL COMMENT '角色：user/assistant/system',
    content TEXT NOT NULL COMMENT '消息内容',
    token_count INT DEFAULT 0 COMMENT '本条消息 token 估算数',
    is_compressed CHAR(1) DEFAULT '0' COMMENT '是否已被压缩：0=原文 1=已压缩',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_ai_msg_session_seq (session_id, seq),
    CONSTRAINT fk_ai_msg_session FOREIGN KEY (session_id) REFERENCES bowl_ai_session(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 对话消息表';