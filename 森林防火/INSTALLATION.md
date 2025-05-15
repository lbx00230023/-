# 森林防火预测监测系统安装指南

## 系统要求
- Python 3.6 或更高版本
- Pip 包管理器
- 虚拟环境工具 (venv)

## 安装步骤

### 1. 克隆或下载项目代码

```bash
git clone <仓库地址>
cd 森林防火预测监测系统
```

### 2. 创建并激活虚拟环境

#### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 创建环境变量文件

在项目根目录创建 `.env` 文件，内容如下:

```
# 应用配置
SECRET_KEY=dev_secret_key_change_in_production
JWT_SECRET_KEY=jwt_secret_key_change_in_production

# 数据库配置（默认使用SQLite）
DATABASE_URI=sqlite:///forest_fire.db

# 服务配置
DEBUG=True
HOST=0.0.0.0
PORT=5000
```

在生产环境中，请更改 `SECRET_KEY` 和 `JWT_SECRET_KEY` 为强随机字符串。

### 5. 创建目录结构

确保项目有以下目录结构:

```
static/
  css/
  js/
templates/
```

如果没有，请创建这些目录。

### 6. 运行应用

```bash
python app.py
```

应用将在 http://localhost:5000 上运行。

### 7. 初始管理员账户

首次访问系统时，需要注册一个用户账户。然后可以使用 SQLite 数据库管理工具手动将该用户角色改为 'admin'，例如:

```sql
UPDATE user SET role = 'admin' WHERE username = '您的用户名';
```

然后就可以登录并使用管理员功能了。

## 生产环境部署

对于生产环境，建议:

1. 使用 Gunicorn 或 uWSGI 作为 WSGI 服务器
2. 使用 Nginx 作为反向代理
3. 使用 MySQL 或 PostgreSQL 而不是 SQLite
4. 设置更强的密钥
5. 关闭调试模式

### 使用 Gunicorn 部署示例

1. 安装 Gunicorn:
```bash
pip install gunicorn
```

2. 启动应用:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 使用 Docker 部署

也可以考虑使用 Docker 来部署该应用。在项目根目录创建 `Dockerfile` 和 `docker-compose.yml` 文件，然后通过 Docker Compose 启动服务。 