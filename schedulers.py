"""
该模块为任务执行模块，包含下述任务
1. 邮件发送任务
2. 缓存清理任务
3. 异步日志收集
"""

from concurrent.futures import ThreadPoolExecutor
