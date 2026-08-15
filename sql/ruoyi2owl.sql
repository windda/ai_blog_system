
-- 删除 quartz 表（python 无quartz，使用apscheduler替代）
DROP TABLE IF EXISTS QRTZ_FIRED_TRIGGERS;
DROP TABLE IF EXISTS QRTZ_PAUSED_TRIGGER_GRPS;
DROP TABLE IF EXISTS QRTZ_SCHEDULER_STATE;
DROP TABLE IF EXISTS QRTZ_LOCKS;
DROP TABLE IF EXISTS QRTZ_SIMPLE_TRIGGERS;
DROP TABLE IF EXISTS QRTZ_SIMPROP_TRIGGERS;
DROP TABLE IF EXISTS QRTZ_CRON_TRIGGERS;
DROP TABLE IF EXISTS QRTZ_BLOB_TRIGGERS;
DROP TABLE IF EXISTS QRTZ_TRIGGERS;
DROP TABLE IF EXISTS QRTZ_JOB_DETAILS;
DROP TABLE IF EXISTS QRTZ_CALENDARS;

-- 删除 ruoyi 定时任务 数据
-- 新增 owl 定时任务 数据
delete from sys_job where job_id in (1, 2, 3);
insert into sys_job values(1, '系统默认（无参）', 'DEFAULT', 'owl_apscheduler.task.owl_task.no_args()',        '0/10 * * * * ?', '3', '1', '1', 'admin', sysdate(), '', null, '');
insert into sys_job values(2, '系统默认（有参）', 'DEFAULT', 'owl_apscheduler.task.owl_task.one_args(\'1\')',  '0/15 * * * * ?', '3', '1', '1', 'admin', sysdate(), '', null, '');
insert into sys_job values(3, '系统默认（多参）', 'DEFAULT', 'owl_apscheduler.task.owl_task.multiply_args(\'1\',\'2\')',  '0/20 * * * * ?', '3', '1', '1', 'admin', sysdate(), '', null, '');

-- 隐藏 ruoyi 数据监控 菜单（python 无druid连接池）
update sys_menu set status = '1', visible = '1' where menu_id = '111';

-- 隐藏 ruoyi 代码生成 菜单（待定）
update sys_menu set status = '1', visible = '1' where menu_id = '112';

-- 隐藏 ruoyi 系统接口 菜单（待定）
update sys_menu set status = '1', visible = '1' where menu_id = '117';



