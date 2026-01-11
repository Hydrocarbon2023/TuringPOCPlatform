-- 项目数据库初始化脚本
-- 用于首次创建数据库和用户

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS poc_platform 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 2. 创建用户（如果不存在）
-- 注意：MySQL 8.0+ 需要使用 CREATE USER IF NOT EXISTS
-- MySQL 5.7 需要使用 GRANT ... IDENTIFIED BY 语法
CREATE USER IF NOT EXISTS 'poc_user'@'localhost' IDENTIFIED BY 'nucifera';

-- 3. 授予权限
GRANT ALL PRIVILEGES ON poc_platform.* TO 'poc_user'@'localhost';

-- 4. 刷新权限
FLUSH PRIVILEGES;

-- 使用数据库
USE poc_platform;

-- 说明：
-- 1. 执行此脚本需要 root 权限
-- 2. 执行方式：mysql -u root -p < INIT_DATABASE.sql
-- 3. 执行后，运行 setup.sh 或手动执行数据库迁移
