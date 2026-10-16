SET NAMES utf8mb4;
-- ============================================================
-- 个人博客管理系统 - 面试演示数据
--
-- 用途：补齐普通用户 + 普通用户文章，用于演示 RBAC 数据隔离
-- 说明：所有普通用户密码均为 admin123
-- 执行顺序：在 blog_init.sql 之后、可选
-- ============================================================

-- ============================================================
-- 1. 普通用户（zhangsan / lisi / wangwu，密码 admin123）
-- ============================================================
INSERT INTO sys_user (user_id, dept_id, user_name, nick_name, user_type, email, phonenumber, sex, avatar, password, status, del_flag, login_ip, login_date, create_by, create_time, update_by, update_time, remark) VALUES
(3, 103, 'zhangsan', '张三', '00', 'zhangsan@blog.com', '13800000001', '0', '', '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2', '0', '0', '127.0.0.1', NULL, 'admin', NOW(), '', NULL, '普通用户-张三'),
(4, 103, 'lisi', '李四', '00', 'lisi@blog.com', '13800000002', '0', '', '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2', '0', '0', '127.0.0.1', NULL, 'admin', NOW(), '', NULL, '普通用户-李四'),
(5, 103, 'wangwu', '王五', '00', 'wangwu@blog.com', '13800000003', '0', '', '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2', '0', '0', '127.0.0.1', NULL, 'admin', NOW(), '', NULL, '普通用户-王五')
ON DUPLICATE KEY UPDATE nick_name=VALUES(nick_name);

-- ============================================================
-- 2. 用户-角色关联（普通用户 -> common 角色 role_id=2）
-- ============================================================
INSERT IGNORE INTO sys_user_role (user_id, role_id) VALUES
(3, 2), (4, 2), (5, 2);

-- ============================================================
-- 3. common 角色关联博客菜单
--    文章/评论：完整权限；分类/标签：只读（增删改仅管理员）
-- ============================================================
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(2, 2000),  -- 博客管理目录
(2, 2001),  -- 文章管理
(2, 2002),  -- 文章新增
(2, 2003),  -- 文章修改
(2, 2004),  -- 文章删除
(2, 2010),  -- 评论管理
(2, 2011),  -- 评论审核
(2, 2012),  -- 评论删除
(2, 2020),  -- 分类管理（只读）
(2, 2021),  -- 分类查询
(2, 2030),  -- 标签管理（只读）
(2, 2031);  -- 标签查询

-- ============================================================
-- 4. 普通用户自己的文章（用于演示数据隔离）
--    zhangsan 2 篇已发布，lisi 1 篇已发布，wangwu 1 篇草稿
-- ============================================================
INSERT INTO blog_article (article_id, title, content, summary, cover_image, category_id, author_id, status, is_top, view_count, like_count, create_by, create_time, update_by, update_time, remark) VALUES
(6, 'Python 异步编程从入门到实践',
'<h2>为什么需要异步</h2><p>在处理大量 IO 操作时，同步方式会阻塞线程，异步可以大幅提升并发性能。</p><h2>asyncio 核心概念</h2><ul><li>事件循环 event loop</li><li>协程 coroutine</li><li>await 关键字</li></ul><h2>一个简单例子</h2><pre><code>import asyncio\n\nasync def main():\n    await asyncio.sleep(1)\n    print("done")\n\nasyncio.run(main())</code></pre><h2>总结</h2><p>异步适合 IO 密集型场景，CPU 密集型应使用多进程。</p>',
'介绍 Python asyncio 的核心概念、await 语法以及适用场景。',
'', 1, 3, '1', '0', 45, 3, 'zhangsan', NOW(), 'zhangsan', NOW(), ''),
(7, '我的全栈学习路线分享',
'<h2>第一阶段：打好基础</h2><p>掌握 HTML/CSS/JavaScript，以及 Python 基础语法。</p><h2>第二阶段：前后端框架</h2><ul><li>前端：Vue 2 + ElementUI</li><li>后端：Flask + SQLAlchemy</li></ul><h2>第三阶段：工程化</h2><p>学习 Docker 部署、Git 版本控制、CI/CD 流水线。</p>',
'分享个人从零到全栈的学习路线与阶段规划。',
'', 1, 3, '1', '0', 32, 2, 'zhangsan', NOW(), 'zhangsan', NOW(), ''),
(8, '前端性能优化的几个实用技巧',
'<h2>资源加载优化</h2><p>使用懒加载、代码分割、CDN 加速减少首屏时间。</p><h2>渲染优化</h2><ul><li>减少重排重绘</li><li>使用虚拟列表</li><li>合理使用缓存</li></ul><h2>网络优化</h2><p>开启 gzip、使用 HTTP/2、合并请求。</p>',
'总结前端性能优化的常见手段与实战经验。',
'', 4, 4, '1', '0', 28, 1, 'lisi', NOW(), 'lisi', NOW(), ''),
(9, '关于生活与编程的思考（草稿）',
'<p>这是一篇还未完成的草稿文章，用于演示草稿状态。</p>',
'草稿状态的演示文章。',
'', 2, 5, '0', '0', 0, 0, 'wangwu', NOW(), 'wangwu', NOW(), '草稿-未完成')
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- ============================================================
-- 5. 点赞记录（与各文章 like_count 对齐，保证"点赞数=点赞列表条数"）
-- ============================================================
DELETE FROM blog_article_like;

INSERT INTO blog_article_like (article_id, user_id, create_time) VALUES
(1, 1, NOW()), (1, 2, NOW()), (1, 3, NOW()), (1, 4, NOW()), (1, 5, NOW()),
(2, 2, NOW()), (2, 3, NOW()), (2, 4, NOW()),
(3, 1, NOW()), (3, 5, NOW()),
(4, 1, NOW()), (4, 2, NOW()), (4, 3, NOW()), (4, 4, NOW()), (4, 5, NOW()),
(6, 1, NOW()), (6, 2, NOW()), (6, 3, NOW()),
(7, 4, NOW()), (7, 5, NOW()),
(8, 1, NOW());

-- 修正文章4 点赞数（init_seed.sql 中 like_count=8，但仅5个用户，对齐为5）
UPDATE blog_article SET like_count = 5 WHERE article_id = 4;

