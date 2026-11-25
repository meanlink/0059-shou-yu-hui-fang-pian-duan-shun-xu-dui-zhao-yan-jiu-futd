# 手语回放 · 片段顺序对照研究

冻结匿名回放试教记录，在同一水平内置换估计顺序效应，总结下一版教材编辑决定。

**模拟客户**　山堤手语夜校，两个水平班和三位课程编辑

**现有流程**　手语老师用表格对比复看分数。不同水平混算，学员误看不对版本时仍算样本，结论写在各自备课本。

**业务交接**　课件编辑定义片段次序，试教员收匿名分数，复核员冻结和计算，编辑部据结果决定留用或调整。

## 一日工作剧本

1. 18:00 查看 SR-12「问路课回放动词」以及词组优先、情境优先两列。
2. 18:10 对照 匿名学员 N-2 所在班与实际版本。错版会拦截，不更改试教分组。
3. 18:30 检查初学和续学的两臂记录，每格至少两人。
4. 18:45 复核员冻结匿名答题记录。worker 在组内打乱版本标签。
5. 18:46 预览相差 12 分，双侧精确置换 p 为 0.0556。
6. 19:00 签编辑决定暂缓改版，等待下一轮验证。
7. 19:05 查阅员确认意见来源已绑定 SR-12 的冻结结果。

## 算法和演示边界

在每个水平班内维持原版本 A/B 人数，枚举全部可能对照名单组合。效应为按组人数加权的 B 均分减 A 均分。精确双侧 p 取绝对效应不小于观测结果的置换比例。

试教轮次限定每班最多八个匿名分配码，确保全枚举可完成。p 大于 0.05 时可决定延后或保留，不能批准切换。

## 快速启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

- 前端浏览器地址为 `http://127.0.0.1:18453`。
- FastAPI 文档地址为 `http://127.0.0.1:19453/docs`。
- PostgreSQL 本地端口为 `17953`。后端与后台 worker 共用数据库事务和 Redis 健康探测。
- 开发 HTML、CSS、ES modules 后运行 `docker compose up -d --build frontend`。Python 代码修改后运行 `docker compose up -d --build backend worker`。
- `SEED_DEMO` 控制自动填充。可改三项宿主端口、`DEMO_PASSWORD`、`JWT_SECRET`、`POSTGRES_PASSWORD`。持久卷保存业务数据和队列状态。停机并保留数据使用 `docker compose down`。
- 技术栈为 Python 3.11、FastAPI、PostgreSQL 16、Redis 7、Nginx 与原生浏览器 JS。后端业务模块、SQL 迁移都在 `backend/`。界面和交互在 `frontend/`。

| 账号 | 密码 | 典型权限 |
|---|---|---|
| operator@demo.local | Demo2026! | 登记已分配试教成绩 |
| reviewer@demo.local | Demo2026! | 冻结对照、批准课件编辑决定 |
| viewer@demo.local | Demo2026! | 查阅记录和经计算的指标 |

共享角色和任务状态枚举分别位于 `backend/core.py` 的 `ROLES`、`JOB_STATES` 和 `frontend/base.js` 的 `roles`、`jobStates`。数据库检查约束与服务状态以相应 SQL 和模块为准。

许可证见 LICENSE。
