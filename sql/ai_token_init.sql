CREATE TABLE IF NOT EXISTS `ai_token_record` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `session_id` bigint(20) DEFAULT NULL COMMENT '会话ID',
  `prompt_tokens` int(11) DEFAULT 0 COMMENT '提示Token数',
  `completion_tokens` int(11) DEFAULT 0 COMMENT '回复Token数',
  `total_tokens` int(11) DEFAULT 0 COMMENT '总Token数',
  `ai_type` varchar(32) DEFAULT 'llm' COMMENT '能力类型：llm / asr',
  `input_tokens` int(11) DEFAULT 0 COMMENT '输入token数',
  `output_tokens` int(11) DEFAULT 0 COMMENT '输出token数',
  `model` varchar(50) DEFAULT '' COMMENT '模型名称',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '调用时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_time` (`user_id`, `create_time`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Token消耗统计表';

CREATE TABLE IF NOT EXISTS `ai_provider_call_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `provider` varchar(50) DEFAULT '' COMMENT '服务商名称',
  `model` varchar(50) DEFAULT '' COMMENT '模型名称',
  `ai_type` varchar(32) DEFAULT 'llm' COMMENT '能力类型：llm / asr',
  `success` tinyint(1) DEFAULT 0 COMMENT '是否成功：1成功 0失败',
  `error_category` varchar(32) DEFAULT '' COMMENT '失败原因分类：timeout/429/500/auth/network/http_xxx/exception',
  `error_message` varchar(500) DEFAULT '' COMMENT '失败详情',
  `latency_ms` int(11) DEFAULT 0 COMMENT '耗时（毫秒）',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  PRIMARY KEY (`id`),
  KEY `idx_provider_time` (`provider`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 服务商调用日志表（容灾切换 + 成功率统计）';