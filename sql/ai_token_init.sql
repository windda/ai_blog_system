CREATE TABLE IF NOT EXISTS `ai_token_record` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `session_id` bigint(20) DEFAULT NULL COMMENT '会话ID',
  `prompt_tokens` int(11) DEFAULT 0 COMMENT '提示Token数',
  `completion_tokens` int(11) DEFAULT 0 COMMENT '回复Token数',
  `total_tokens` int(11) DEFAULT 0 COMMENT '总Token数',
  `model` varchar(50) DEFAULT '' COMMENT '模型名称',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '调用时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_time` (`user_id`, `create_time`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Token消耗统计表';