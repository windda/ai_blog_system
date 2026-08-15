CREATE TABLE IF NOT EXISTS `blog_notice` (
  `notice_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '通知ID',
  `receive_user_id` bigint(20) NOT NULL COMMENT '接收用户ID',
  `article_id` bigint(20) DEFAULT NULL COMMENT '关联文章ID',
  `notice_type` varchar(20) NOT NULL COMMENT '通知类型（like/comment/collect）',
  `message` varchar(500) NOT NULL COMMENT '通知内容',
  `is_read` char(1) DEFAULT '0' COMMENT '是否已读（0未读 1已读）',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '通知时间',
  PRIMARY KEY (`notice_id`),
  KEY `idx_receive_user` (`receive_user_id`, `is_read`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站内通知表';