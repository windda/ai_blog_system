SET NAMES utf8mb4;
-- ============================================================
-- 个人博客管理系统 - 博客/AI 模块建表脚本
--
-- 用途：创建博客业务表 + AI 对话表
-- 说明：由 SQLAlchemy 模型（owl_blog/domain/po.py、owl_ai/domain/po.py）
--       生成，补齐项目早期缺失的核心博客表建表语句
-- 执行顺序：先导入 ry_20230706.sql（若依 sys_* 表），再导入本脚本，
--           最后导入 init_seed.sql（种子数据）
-- ============================================================

CREATE TABLE IF NOT EXISTS `blog_article` (
  `article_id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_general_ci NOT NULL,
  `content` longtext COLLATE utf8mb4_general_ci,
  `summary` varchar(500) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `cover_image` varchar(500) COLLATE utf8mb4_general_ci DEFAULT '',
  `category_id` bigint DEFAULT NULL,
  `author_id` bigint DEFAULT NULL,
  `status` char(1) COLLATE utf8mb4_general_ci DEFAULT '0',
  `is_top` char(1) COLLATE utf8mb4_general_ci DEFAULT 'N',
  `view_count` int DEFAULT '0',
  `like_count` int DEFAULT '0',
  `create_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT '',
  `create_time` datetime DEFAULT NULL,
  `update_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT '',
  `update_time` datetime DEFAULT NULL,
  `remark` varchar(500) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`article_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='博客文章表';

CREATE TABLE IF NOT EXISTS `blog_article_collect` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `article_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='文章收藏记录表';

CREATE TABLE IF NOT EXISTS `blog_article_like` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `article_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='文章点赞记录表';

CREATE TABLE IF NOT EXISTS `blog_article_tag` (
  `article_id` bigint NOT NULL,
  `tag_id` bigint NOT NULL,
  PRIMARY KEY (`article_id`,`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='博客文章标签关联表';

CREATE TABLE IF NOT EXISTS `blog_category` (
  `category_id` bigint NOT NULL AUTO_INCREMENT,
  `category_name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `order_num` int DEFAULT '0',
  `status` char(1) COLLATE utf8mb4_general_ci DEFAULT '0',
  `create_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT '',
  `create_time` datetime DEFAULT NULL,
  `update_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT '',
  `update_time` datetime DEFAULT NULL,
  `remark` varchar(500) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='博客分类表';

CREATE TABLE IF NOT EXISTS `blog_column` (
  `column_id` bigint NOT NULL AUTO_INCREMENT,
  `column_name` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `description` varchar(500) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `cover_image` varchar(500) COLLATE utf8mb4_general_ci DEFAULT '',
  `author_id` bigint NOT NULL,
  `status` char(1) COLLATE utf8mb4_general_ci DEFAULT '0',
  `order_num` int DEFAULT '0',
  `create_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT '',
  `create_time` datetime DEFAULT NULL,
  `update_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT '',
  `update_time` datetime DEFAULT NULL,
  `remark` varchar(500) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`column_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='博客专栏表';

CREATE TABLE IF NOT EXISTS `blog_comment` (
  `comment_id` bigint NOT NULL AUTO_INCREMENT,
  `article_id` bigint NOT NULL,
  `parent_id` bigint DEFAULT '0',
  `content` text COLLATE utf8mb4_general_ci,
  `author_name` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `author_email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `user_id` bigint DEFAULT NULL,
  `status` char(1) COLLATE utf8mb4_general_ci DEFAULT '0',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`comment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='博客评论表';

CREATE TABLE IF NOT EXISTS `blog_friend_link` (
  `link_id` bigint NOT NULL AUTO_INCREMENT,
  `link_name` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `link_url` varchar(500) COLLATE utf8mb4_general_ci NOT NULL,
  `link_desc` varchar(500) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `order_num` int DEFAULT NULL,
  `status` char(1) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `create_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `remark` varchar(500) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`link_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='友情链接表';

CREATE TABLE IF NOT EXISTS `blog_notice` (
  `notice_id` bigint NOT NULL AUTO_INCREMENT,
  `receive_user_id` bigint NOT NULL,
  `article_id` bigint DEFAULT NULL,
  `notice_type` varchar(20) COLLATE utf8mb4_general_ci NOT NULL,
  `message` varchar(500) COLLATE utf8mb4_general_ci NOT NULL,
  `is_read` char(1) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`notice_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='站内通知表';

CREATE TABLE IF NOT EXISTS `blog_tag` (
  `tag_id` bigint NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `order_num` int DEFAULT '0',
  `create_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT '',
  `create_time` datetime DEFAULT NULL,
  `update_by` varchar(64) COLLATE utf8mb4_general_ci DEFAULT '',
  `update_time` datetime DEFAULT NULL,
  `remark` varchar(500) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='博客标签表';

CREATE TABLE IF NOT EXISTS `blog_view_history` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `article_id` bigint NOT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='用户浏览历史表';

CREATE TABLE IF NOT EXISTS `bowl_ai_message` (
  `message_id` bigint NOT NULL AUTO_INCREMENT,
  `session_id` bigint NOT NULL COMMENT '会话ID',
  `seq` int NOT NULL COMMENT '消息序号',
  `role` varchar(20) COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色（user/assistant/system）',
  `content` longtext COLLATE utf8mb4_general_ci COMMENT '消息内容',
  `token_count` int DEFAULT NULL COMMENT 'Token估算数',
  `is_compressed` char(1) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否已压缩',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='AI 对话消息表';

CREATE TABLE IF NOT EXISTS `bowl_ai_session` (
  `session_id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `title` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '会话标题',
  `model` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '模型名称',
  `message_count` int DEFAULT NULL COMMENT '消息数量',
  `total_tokens` int DEFAULT NULL COMMENT '累计Token数',
  `summary_content` text COLLATE utf8mb4_general_ci COMMENT '远期摘要',
  `status` char(1) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '状态',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='AI 对话会话表';

CREATE TABLE IF NOT EXISTS `ai_token_record` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `session_id` bigint DEFAULT NULL COMMENT '会话ID',
  `prompt_tokens` int DEFAULT NULL COMMENT '提示Token数',
  `completion_tokens` int DEFAULT NULL COMMENT '回复Token数',
  `total_tokens` int DEFAULT NULL COMMENT '总Token数',
  `model` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '模型名称',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='AI Token 消耗统计表';

