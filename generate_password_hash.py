#!/usr/bin/env python3
"""
生成测试用户密码哈希的辅助脚本
用于生成 TEST_DATA.sql 中的正确 bcrypt 密码哈希
"""
import bcrypt

# 测试密码（统一为 "123456"）
password = "123456"

# 生成 bcrypt 哈希
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("=" * 60)
print("测试用户密码哈希生成器")
print("=" * 60)
print(f"\n密码: {password}")
print(f"哈希值: {password_hash}")
print("\n" + "=" * 60)
print("使用方法：")
print("1. 将上述哈希值复制到 TEST_DATA.sql 中")
print("2. 替换所有用户记录的 password_hash 字段")
print("=" * 60)
