"""
认证中间件

基于JWT Token的身份验证，支持token提取、验证和创建。
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


# JWT配置
SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


class AuthMiddleware:
    """JWT认证中间件"""

    def __init__(self, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM):
        """初始化认证中间件

        Args:
            secret_key: JWT密钥
            algorithm: 加密算法
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.security = HTTPBearer(auto_error=False)

    def extract_token(self, request: Request) -> Optional[str]:
        """从请求头提取token

        Args:
            request: FastAPI请求对象

        Returns:
            提取到的token字符串，未找到则返回None
        """
        # 从Authorization头提取
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]

        # 从查询参数提取（用于WebSocket等场景）
        return request.query_params.get("token")

    def verify_token(self, token: str) -> dict:
        """验证JWT token

        Args:
            token: JWT token字符串

        Returns:
            解码后的payload字典

        Raises:
            HTTPException: token无效或已过期
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期",
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"无效的Token: {str(e)}",
            )

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """创建JWT access token

        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量，默认使用配置值

        Returns:
            编码后的JWT token字符串
        """
        to_encode = data.copy()

        # 设置过期时间
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})

        # 编码并返回token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt


# 全局认证中间件实例
auth_middleware = AuthMiddleware()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> dict:
    """获取当前认证用户的FastAPI依赖注入函数

    用于路由保护，验证请求中的JWT token并返回用户信息。

    Args:
        credentials: HTTP Bearer认证凭据

    Returns:
        当前用户信息字典

    Raises:
        HTTPException: 未提供认证信息或token无效
    """
    # 检查是否提供了认证凭据
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证token
    payload = auth_middleware.verify_token(credentials.credentials)

    # 检查用户ID是否存在
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token: 缺少用户标识",
        )

    return payload
