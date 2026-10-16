SET NAMES utf8mb4;
-- ============================================================
-- 个人博客管理系统 - 种子初始化数据
-- 
-- 用途：项目首次部署时自动加载演示数据
-- 包含：管理员账号、示例文章、评论、分类、标签
-- 加载方式：docker-compose up 时自动执行
-- ============================================================

-- ============================================================
-- 1. 确保管理员账号存在（admin / admin123）
-- ============================================================
-- 如果 admin 已存在则跳过（ON DUPLICATE KEY UPDATE）
INSERT INTO sys_user (user_id, dept_id, user_name, nick_name, password, email, phonenumber, sex, status, del_flag, login_ip, login_date, create_by, create_time, update_by, update_time, remark)
VALUES (1, 103, 'admin', '管理员', '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2', 'admin@blog.com', '13800000000', '0', '0', '0', '127.0.0.1', NOW(), 'admin', NOW(), '', NOW(), '系统管理员')
ON DUPLICATE KEY UPDATE nick_name=VALUES(nick_name);

-- ============================================================
-- 2. 博客分类数据
-- ============================================================
INSERT INTO blog_category (category_name, order_num, status, create_by, create_time, remark) VALUES
('技术分享', 1, '0', 'admin', NOW(), '技术类文章'),
('生活随笔', 2, '0', 'admin', NOW(), '生活记录'),
('项目实战', 3, '0', 'admin', NOW(), '实战项目经验'),
('前端技术', 4, '0', 'admin', NOW(), '前端相关'),
('后端开发', 5, '0', 'admin', NOW(), '后端技术')
ON DUPLICATE KEY UPDATE category_name=VALUES(category_name);

-- ============================================================
-- 3. 博客标签数据
-- ============================================================
INSERT INTO blog_tag (tag_name, order_num, create_by, create_time) VALUES
('Python', 1, 'admin', NOW()),
('Flask', 2, 'admin', NOW()),
('Vue', 3, 'admin', NOW()),
('MySQL', 4, 'admin', NOW()),
('Redis', 5, 'admin', NOW()),
('Docker', 6, 'admin', NOW()),
('JavaScript', 7, 'admin', NOW()),
('CSS', 8, 'admin', NOW())
ON DUPLICATE KEY UPDATE tag_name=VALUES(tag_name);

-- ============================================================
-- 4. 示例文章（含 Markdown/HTML 内容）
-- ============================================================
INSERT INTO blog_article (article_id, title, content, summary, cover_image, category_id, author_id, status, is_top, view_count, like_count, create_by, create_time, update_by, update_time, remark) VALUES
-- 文章1：技术类
(1, 'Flask + Vue 全栈博客开发实战',
'<h2>项目概述</h2><p>本文记录从零搭建一个完整的个人博客系统，使用 Flask 3.0 作为后端框架，Vue 2 + ElementUI 作为前端。</p><h2>技术栈</h2><ul><li>后端：Flask 3.0 + SQLAlchemy 2.0 + JWT</li><li>前端：Vue 2.x + ElementUI + ECharts</li><li>数据库：MySQL 8.0</li><li>缓存：Redis 7.0</li><li>部署：Docker + Nginx</li></ul><h2>核心功能</h2><p>1. RBAC 权限控制（用户→角色→菜单）</p><p>2. 文章管理（发布/草稿/置顶）</p><p>3. 评论审核（先审后发）</p><p>4. 数据仪表盘（ECharts 可视化）</p><p>5. 前台博客展示</p><h2>技术特性</h2><p>本项目包含以下技术特性：全局异常处理、Redis 缓存策略、SQL 聚合查询优化、Docker 跨平台部署、JWT 无状态认证。</p>',
'从零搭建一个完整的 Flask + Vue 个人博客系统，涵盖后端架构、前端开发、权限控制、部署上线全过程。',
NULL, 1, 1, '1', '1', 128, 5, 'admin', '2026-06-10 10:00:00', 'admin', '2026-06-10 10:00:00', ''),

-- 文章2：生活类
(2, '程序员的日常：代码与生活',
'<h2>清晨</h2><p>一杯咖啡，打开 VS Code，开始新的一天。</p><h2>上午</h2><p>解决了一个让我头疼两天的 bug，原来是一个拼写错误。积累经验：</p><ul><li>善用 IDE 的拼写检查</li><li>Code Review 很重要</li><li>写单元测试能提前发现问题</li></ul><h2>下午</h2><p>学习了 Redis ZSet 的用法，发现可以用来做排行榜功能，很有意思。</p><h2>晚上</h2><p>看了一篇关于系统设计的文章，受益匪浅。程序员要保持学习的习惯。</p>',
'记录程序员一天的日常工作和学习，分享调试 bug 的经验和 Redis ZSet 的用法。',
NULL, 2, 1, '1', '0', 89, 3, 'admin', '2026-06-11 14:30:00', 'admin', '2026-06-11 14:30:00', ''),

-- 文章3：项目实战类
(3, '如何用 Docker 部署 Flask 项目',
'<h2>为什么用 Docker</h2><p>Docker 能解决"在我电脑上可以运行"的经典问题。通过容器化部署，确保开发、测试、生产环境一致。</p><h2>Dockerfile 编写</h2><pre><code>FROM python:3.10-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD ["python", "app.py"]</code></pre><h2>Docker Compose</h2><p>使用 docker-compose.yml 编排多个服务：</p><ul><li>MySQL 8.0 数据库</li><li>Redis 7 缓存</li><li>Flask 后端</li><li>Nginx 前端</li></ul><h2>优化技巧</h2><p>1. 使用 .dockerignore 减小构建上下文</p><p>2. 多阶段构建减轻镜像体积</p><p>3. 健康检查保证服务可用</p>',
'详细介绍如何使用 Docker 和 Docker Compose 部署 Flask 项目，含 Dockerfile 编写、环境变量管理、健康检查配置等实用技巧。',
NULL, 3, 1, '1', '0', 76, 2, 'admin', '2026-06-12 09:15:00', 'admin', '2026-06-12 09:15:00', ''),

-- 文章4：Redis 缓存实战
(4, 'Redis 在博客系统中的应用',
'<h2>场景 1：用户登录态存储</h2><p>JWT Token 只作为一个凭证 ID，真正的用户信息存 Redis。好处：</p><ul><li>可以随时踢人（删 Redis key 即可）</li><li>Session 集中管理，多台后端共享登录态</li><li>设置过期时间自动清理</li></ul><h2>场景 2：文章列表缓存</h2><p>公开文章列表是读多写少的场景，使用 Redis 缓存：</p><pre><code># 查询时先看缓存\ncached = redis.get("blog:article:pub_list")\nif cached:\n    return json.loads(cached)\n# 查数据库后写入缓存\nredis.setex("blog:article:pub_list", 300, data)</code></pre><h2>场景 3：热门文章排行</h2><p>使用 Redis ZSet 实现：</p><pre><code># 文章被访问时 +1\nredis.zincrby("blog:hot_articles", 1, article_id)\n# 取热门 Top 5\nredis.zrevrange("blog:hot_articles", 0, 4)</code></pre><h2>缓存一致性</h2><p>新增/修改/删除文章时自动清除缓存，保证数据一致性。</p>',
'详细介绍 Redis 在博客系统中的三种应用场景：Token 存储、文章缓存、热门排行 ZSet。',
NULL, 1, 1, '1', '1', 156, 8, 'admin', '2026-06-13 16:20:00', 'admin', '2026-06-13 16:20:00', ''),

-- 文章5：测试环境测试用
(5, '测试文章 - 请忽略',
'<p>这是一篇测试文章，用于验证博客系统的各项功能。</p>',
'测试用文章，验证系统功能。',
NULL, 5, 1, '0', '0', 5, 0, 'admin', '2026-06-14 20:00:00', 'admin', '2026-06-14 20:00:00', '草稿状态')
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- ============================================================
-- 5. 示例评论数据
-- ============================================================
INSERT INTO blog_comment (article_id, content, author_name, author_email, user_id, status, create_time) VALUES
(1, '写得非常好，学习了！请问 JWT 过期时间一般设置多久比较合理？', '小明', 'xiaoming@test.com', NULL, '1', '2026-06-10 11:00:00'),
(1, '同问，另外 Flask 3.0 和 2.x 有什么区别吗？', '张三', 'zhangsan@test.com', NULL, '1', '2026-06-10 11:30:00'),
(2, '程序员的日常太真实了，哈哈！' , '李四', 'lisi@test.com', NULL, '1', '2026-06-11 15:00:00'),
(3, 'Docker 部署确实方便，我之前也在用。建议补充一下 docker-compose 中 healthcheck 的用法。', '王五', 'wangwu@test.com', NULL, '1', '2026-06-12 10:00:00'),
(3, '多阶段构建的镜像真的小很多，我试过从 800MB 降到 200MB', '赵六', 'zhaoliu@test.com', NULL, '1', '2026-06-12 12:00:00'),
(4, 'Redis ZSet 做排行榜这个想法很赞！方便说一下如何处理冷启动（没有历史数据）的问题吗？', '小红', 'xiaohong@test.com', NULL, '1', '2026-06-13 17:00:00'),
(4, 'ZINCRBY 这个命令学到了，之前只知道用 SET/GET', '小明', 'xiaoming@test.com', NULL, '0', '2026-06-13 18:00:00')
ON DUPLICATE KEY UPDATE content=VALUES(content);

-- ============================================================
-- 6. 全文搜索性能优化索引（建议在数据量 > 1万条时执行）
-- ============================================================
-- MySQL 5.6+ InnoDB 支持 FULLTEXT，中文需 ngram parser（5.7.6+）
-- 不使用 FULLTEXT 时，当前 LIKE 查询在 10万条以内性能可接受
