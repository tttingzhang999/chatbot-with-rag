# AWS 部署故障排查指南

本文档记录 HR Chatbot 系统部署到 AWS 时遇到的实际问题和解决方案。

**部署日期**: 2025-12-02
**版本**: v0.6.0
**架构**: Frontend (App Runner) → API Gateway → Backend Lambda → Bedrock

---

## 目录

1. [Lambda 部署问题](#lambda-部署问题)
2. [App Runner 部署问题](#app-runner-部署问题)
3. [架构兼容性问题](#架构兼容性问题)
4. [最佳实践总结](#最佳实践总结)

---

## Lambda 部署问题

### 问题 1: Lambda 文件权限错误

**症状**:
```
PermissionError: [Errno 13] Permission denied: '/var/task/backend_handler.py'
```

**原因**:
Lambda 容器中的文件权限不正确，导致 Python 无法读取 handler 文件。

**解决方案**:
在 Dockerfile 中添加 chmod 命令修复文件权限：

```dockerfile
# 在 Dockerfile.backend 中添加
COPY lambda_handlers/backend_handler.py ./

# Fix file permissions for Lambda
RUN chmod -R 755 /var/task

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
```

**文件**: `Dockerfile.backend:44`

---

### 问题 2: Lambda 写入文件到只读文件系统

**症状**:
```
OSError: [Errno 30] Read-only file system: 'uploads'
```

**原因**:
Lambda 的 `/var/task` 目录是只读的，应用在启动时尝试创建 `uploads` 目录失败。

**解决方案**:
修改代码，在文件系统只读时自动使用 `/tmp` 目录：

```python
# src/api/routes/upload.py
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
# Only create directory if filesystem is writable (not Lambda)
try:
    UPLOAD_DIR.mkdir(exist_ok=True)
except OSError:
    # Lambda has read-only filesystem, use /tmp instead
    UPLOAD_DIR = Path("/tmp/uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)
```

**文件**: `src/api/routes/upload.py:22-29`

**注意**: Lambda 的 `/tmp` 目录有 512 MB 限制，且不会在调用之间持久化。

---

### 问题 3: 数据库连接失败导致 Lambda 无法启动

**症状**:
```
ArgumentError: Could not parse SQLAlchemy URL from given URL string
```

**原因**:
Lambda 环境变量中缺少 `DATABASE_URL`，导致 SQLAlchemy 初始化失败。

**解决方案**:
为测试环境添加占位符 `DATABASE_URL`：

```bash
aws lambda update-function-configuration \
    --function-name hr-chatbot-backend \
    --region ap-northeast-1 \
    --environment "Variables={
        ENABLE_RAG=false,
        DEBUG=false,
        DATABASE_URL=postgresql://placeholder:placeholder@localhost/placeholder
    }"
```

**替代方案**:
修改代码让数据库连接延迟初始化，避免在导入时立即连接数据库。

---

### 问题 4: Lambda 初始化超时

**症状**:
```
INIT_REPORT Init Duration: 9999.48 ms Phase: init Status: timeout
```

**原因**:
Lambda 冷启动时间过长，通常是由于依赖包过多或数据库连接超时。

**解决方案**:
1. 减少依赖包大小
2. 使用 Lambda 层（Layers）存储大型依赖
3. 延迟初始化数据库连接
4. 增加 Lambda 超时时间和内存

```bash
aws lambda update-function-configuration \
    --function-name hr-chatbot-backend \
    --timeout 30 \
    --memory-size 1024
```

---

## App Runner 部署问题

### 问题 5: App Runner 健康检查失败，无应用日志

**症状**:
```
Health check failed on protocol `TCP` [Port: '7860']
No application logs available
```

**根本原因**:
**架构不匹配** - 在 Apple M2 (ARM64) 上构建的镜像无法在 App Runner (x86_64) 上运行。

**诊断过程**:
1. 本地测试镜像可以正常运行 ✅
2. App Runner 健康检查失败 ❌
3. 没有任何应用日志 ❌ (说明容器根本没有启动)

**解决方案**:
使用 `--platform linux/amd64` 构建 x86_64 架构镜像：

```bash
# 错误的构建方式（在 M2 Mac 上）
docker build -f Dockerfile.frontend -t hr-chatbot-frontend:latest .
# 结果: arm64 镜像 → App Runner 无法运行

# 正确的构建方式
docker build --platform linux/amd64 -f Dockerfile.frontend -t hr-chatbot-frontend:v0.6.0 .
# 结果: amd64 镜像 → App Runner 可以运行
```

**验证镜像架构**:
```bash
docker image inspect <image-name> --format '{{.Architecture}}'
# 应该输出: amd64
```

**参考文档**:
- [AWS App Runner Health Check Failed - Stack Overflow](https://stackoverflow.com/questions/69322032/aws-app-runner-create-failed-on-health-check)
- [AWS App Runner Troubleshooting](https://docs.aws.amazon.com/apprunner/latest/dg/troubleshooting.html)

---

### 问题 6: App Runner PORT 环境变量冲突

**症状**:
尝试使用 `GRADIO_PORT=7860` 但应用没有在正确端口监听。

**原因**:
App Runner 自动设置 `PORT` 环境变量（默认 8080），但应用使用自定义的 `GRADIO_PORT`。

**两种解决方案**:

**方案 A - 让应用读取 PORT 环境变量**:
```python
# frontend_entrypoint.py
import os
port = int(os.getenv("PORT", settings.GRADIO_PORT))

demo.launch(
    server_name=settings.GRADIO_HOST,
    server_port=port,  # 使用 PORT 环境变量
)
```

**方案 B - 明确指定端口（推荐）**:
```bash
# App Runner 配置
{
  "ImageConfiguration": {
    "Port": "7860",  # 明确指定端口
    "RuntimeEnvironmentVariables": {
      "GRADIO_PORT": "7860"  # 应用使用的端口
    }
  }
}
```

本项目采用方案 B，保持代码简洁。

**参考**: [AWS App Runner Environment Variables](https://docs.aws.amazon.com/apprunner/latest/dg/env-variable.html)

---

### 问题 7: App Runner 健康检查超时设置过短

**症状**:
应用启动需要 5-10 秒，但健康检查只等待 2 秒就超时。

**解决方案**:
调整健康检查配置：

```bash
aws apprunner update-service \
    --service-arn <service-arn> \
    --health-check-configuration '{
        "Protocol": "TCP",
        "Interval": 10,
        "Timeout": 10,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 3
    }'
```

**配置说明**:
- `Timeout`: 10 秒（原来 2 秒）- 给应用足够启动时间
- `Interval`: 10 秒（原来 5 秒）- 检查间隔
- `UnhealthyThreshold`: 3（原来 5）- 失败 3 次才标记为不健康

---

### 问题 8: Dockerfile CMD 导致启动缓慢

**症状**:
使用 `uv run` 启动应用时，每次都重新检查依赖，导致启动慢。

**原因**:
```dockerfile
# 慢的方式
CMD ["uv", "run", "python", "frontend_entrypoint.py"]
# uv run 会重新检查依赖，耗时 10+ 秒
```

**解决方案**:
直接使用虚拟环境中的 Python：

```dockerfile
# 快的方式
CMD [".venv/bin/python", "frontend_entrypoint.py"]
# 直接运行，2-5 秒启动
```

**文件**: `Dockerfile.frontend:34`

---

## 架构兼容性问题

### 问题 9: 多平台镜像格式不兼容

**症状**:
```
The image manifest, config or layer media type for the source image is not supported
```

**原因**:
Docker 默认构建多平台镜像（OCI format），Lambda 不支持此格式。

**解决方案**:
使用 `--provenance=false` 禁用多平台 manifest：

```bash
docker build --platform linux/amd64 \
    --provenance=false \
    -f Dockerfile.backend \
    -t hr-chatbot-backend:v0.6.0 .
```

**检查镜像格式**:
```bash
aws ecr describe-images \
    --repository-name <repo-name> \
    --image-ids imageTag=<tag> \
    --query 'imageDetails[0].imageManifestMediaType'

# Lambda 支持: application/vnd.docker.distribution.manifest.v2+json
# Lambda 不支持: application/vnd.oci.image.index.v1+json
```

---

### 问题 10: 在 Apple Silicon Mac 上构建镜像

**最佳实践**:

```bash
# ✅ 正确：明确指定平台和格式
docker build --platform linux/amd64 \
    --provenance=false \
    --output type=docker \
    -f Dockerfile \
    -t <image-name> .

# ❌ 错误：使用默认平台
docker build -f Dockerfile -t <image-name> .
# 结果: ARM64 镜像，无法在 AWS 上运行
```

**验证清单**:
```bash
# 1. 检查架构
docker image inspect <image> --format '{{.Architecture}}'
# 必须是: amd64

# 2. 本地测试（模拟 x86_64 环境）
docker run --platform linux/amd64 -p 8080:8080 <image>

# 3. 推送到 ECR 并部署
docker push <ecr-uri>
```

---

## 最佳实践总结

### Docker 镜像构建

#### Backend (Lambda)
```bash
docker build --platform linux/amd64 \
    --provenance=false \
    --output type=docker \
    -f Dockerfile.backend \
    -t hr-chatbot-backend:v0.6.0 .
```

**关键点**:
- `--platform linux/amd64`: Lambda 只支持 x86_64
- `--provenance=false`: 避免多平台 manifest
- `--output type=docker`: 使用 Docker 格式

#### Frontend (App Runner)
```bash
docker build --platform linux/amd64 \
    -f Dockerfile.frontend \
    -t hr-chatbot-frontend:v0.6.0 .
```

**关键点**:
- App Runner 也只支持 x86_64
- 不需要 `--provenance=false`（App Runner 兼容性更好）

---

### Lambda 配置

**环境变量**:
```bash
DATABASE_URL=postgresql://placeholder:placeholder@localhost/placeholder
ENABLE_RAG=false
DEBUG=false
```

**资源配置**:
- Memory: 1024 MB（推荐）
- Timeout: 30 seconds
- Ephemeral Storage: 512 MB（默认）

**IAM Permissions**:
- `AWSLambdaBasicExecutionRole` - CloudWatch Logs
- `AmazonBedrockFullAccess` - Bedrock API 调用
- `SecretsManagerReadWrite` - 读取数据库凭证（可选）

---

### App Runner 配置

**镜像配置**:
```json
{
  "Port": "7860",
  "RuntimeEnvironmentVariables": {
    "BACKEND_API_URL": "https://<api-id>.execute-api.ap-northeast-1.amazonaws.com",
    "GRADIO_HOST": "0.0.0.0",
    "GRADIO_PORT": "7860",
    "DATABASE_URL": "postgresql://placeholder:placeholder@localhost/placeholder"
  }
}
```

**健康检查配置**:
```json
{
  "Protocol": "TCP",
  "Interval": 10,
  "Timeout": 10,
  "HealthyThreshold": 1,
  "UnhealthyThreshold": 3
}
```

**实例配置**:
- CPU: 1 vCPU
- Memory: 2 GB

---

### 部署前检查清单

#### 镜像验证
- [ ] 架构是 `amd64`（使用 `docker image inspect`）
- [ ] 本地可以运行（使用 `--platform linux/amd64`）
- [ ] 镜像已推送到 ECR
- [ ] ECR 镜像格式正确（Lambda 需要检查 manifest type）

#### Lambda 验证
- [ ] Handler 路径正确
- [ ] 环境变量已设置
- [ ] IAM Role 权限正确
- [ ] 文件权限正确（chmod 755）
- [ ] /tmp 目录用于临时文件

#### App Runner 验证
- [ ] 端口配置正确（7860）
- [ ] 健康检查超时足够（10 秒）
- [ ] 环境变量包含 `BACKEND_API_URL`
- [ ] IAM Role 可以访问 ECR

#### 连通性测试
- [ ] Backend `/health` 返回 200
- [ ] Frontend 页面可以访问
- [ ] Frontend 可以调用 Backend API
- [ ] Bedrock API 调用成功（如果使用）

---

### 故障排查步骤

#### Lambda 无法启动

1. **检查 CloudWatch Logs**:
```bash
aws logs tail /aws/lambda/<function-name> --follow --region ap-northeast-1
```

2. **常见错误**:
- 文件权限 → 添加 `chmod -R 755`
- 依赖缺失 → 检查 Dockerfile 安装步骤
- 环境变量 → 检查 `DATABASE_URL` 等必需变量
- 超时 → 增加 timeout 和 memory

#### App Runner 健康检查失败

1. **检查部署日志**:
   - AWS Console → App Runner → Service → Logs

2. **如果没有 Application Logs**:
   - ✅ 镜像架构：必须是 amd64
   - ✅ 镜像格式：检查是否能在 x86_64 上运行
   - ✅ 端口配置：确保应用监听正确端口

3. **如果有 Application Logs 但启动失败**:
   - 检查应用错误日志
   - 检查环境变量
   - 检查依赖是否完整

4. **健康检查超时**:
   - 增加 Timeout（10 秒）
   - 检查应用启动时间
   - 优化 Dockerfile（避免运行时安装依赖）

---

## 常见命令参考

### 检查镜像架构
```bash
docker image inspect <image-name> --format '{{.Architecture}}'
```

### 本地测试 amd64 镜像
```bash
docker run --platform linux/amd64 -p 8080:8080 <image-name>
```

### 查看 Lambda 日志
```bash
aws logs tail /aws/lambda/<function-name> --since 5m --region ap-northeast-1
```

### 更新 Lambda 环境变量
```bash
aws lambda update-function-configuration \
    --function-name <function-name> \
    --environment "Variables={KEY=VALUE}" \
    --region ap-northeast-1
```

### 更新 App Runner 服务
```bash
aws apprunner update-service \
    --service-arn <service-arn> \
    --source-configuration file://config.json \
    --region ap-northeast-1
```

---

## 参考资源

### AWS 官方文档
- [Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [App Runner Troubleshooting](https://docs.aws.amazon.com/apprunner/latest/dg/troubleshooting.html)
- [App Runner Environment Variables](https://docs.aws.amazon.com/apprunner/latest/dg/env-variable.html)
- [App Runner Health Checks](https://docs.aws.amazon.com/apprunner/latest/dg/manage-configure-healthcheck.html)

### 社区资源
- [AWS App Runner Health Check Failed - Stack Overflow](https://stackoverflow.com/questions/69322032/aws-app-runner-create-failed-on-health-check)
- [AWS App Runner Health Check Fails Despite Successful Local Testing](https://stackoverflow.com/questions/77865613/aws-app-runner-health-check-fails-despite-successful-local-testing)

### 项目文档
- [AWS 部署指南](./aws_deployment_guide.md) - 完整部署步骤
- [本地开发指南](./local_development.md) - 本地测试
- [架构文档](./architecture.md) - 系统架构

---

**最后更新**: 2025-12-02
**维护者**: Ting Zhang

**部署成功案例**:
- Backend: Lambda + API Gateway ✅
- Frontend: App Runner ✅
- 架构: Apple M2 → amd64 镜像 → AWS 部署 ✅
