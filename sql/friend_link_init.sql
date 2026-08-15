CREATE TABLE IF NOT EXISTS `blog_friend_link` (
  `link_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '友链ID',
  `link_name` varchar(100) NOT NULL COMMENT '网站名称',
  `link_url` varchar(500) NOT NULL COMMENT '网站地址',
  `link_desc` varchar(500) DEFAULT '' COMMENT '网站描述',
  `order_num` int(4) DEFAULT '0' COMMENT '显示顺序',
  `status` char(1) DEFAULT '1' COMMENT '状态（0隐藏 1显示）',
  `create_by` varchar(64) DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(64) DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`link_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='友情链接表';