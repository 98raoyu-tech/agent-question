"""
认证路由

提供飞书 OAuth2 登录、Token 管理和统一认证中心功能。
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from ..middleware.auth import auth_middleware, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["认证中心"])


# ==================== 配置 ====================

class FeishuConfig:
    """飞书 OAuth2 配置"""
    APP_ID: str = os.getenv("FEISHU_APP_ID", "")
    APP_SECRET: str = os.getenv("FEISHU_APP_SECRET", "")
    REDIRECT_URI: str = os.getenv("FEISHU_REDIRECT_URI", "http://localhost:9000/api/v1/auth/callback")
    
    # 飞书 API 端点
    AUTHORIZE_URL: str = "https://open.feishu.cn/open-apis/authen/v1/authorize"
    ACCESS_TOKEN_URL: str = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"
    USER_INFO_URL: str = "https://open.feishu.cn/open-apis/authen/v1/user_info"
    APP_ACCESS_TOKEN_URL: str = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"


feishu_config = FeishuConfig()


# ==================== 数据模型 ====================

class LoginResponse(BaseModel):
    """登录响应"""
    token: str = Field(description="JWT Token")
    user: dict = Field(description="用户信息")
    expires_in: int = Field(description="Token 过期时间（秒）")


class TokenRefreshRequest(BaseModel):
    """Token 刷新请求"""
    token: str = Field(description="当前 Token")


class TokenVerifyResponse(BaseModel):
    """Token 验证响应"""
    valid: bool = Field(description="是否有效")
    user: Optional[dict] = Field(default=None, description="用户信息")
    expires_at: Optional[str] = Field(default=None, description="过期时间")


class UserResponse(BaseModel):
    """用户信息响应"""
    user_id: str = Field(description="用户 ID")
    name: str = Field(description="用户名")
    email: Optional[str] = Field(default=None, description="邮箱")
    avatar: Optional[str] = Field(default=None, description="头像")
    feishu_user_id: Optional[str] = Field(default=None, description="飞书用户 ID")
    tenant_key: Optional[str] = Field(default=None, description="租户 Key")


# ==================== 存储 ====================

# TODO: 替换为数据库存储
_user_store: dict[str, dict] = {}
_app_access_token_cache: dict[str, str] = {}


# ==================== 飞书 API 工具函数 ====================

async def get_app_access_token() -> str:
    """获取飞书 App Access Token

    Returns:
        App Access Token
    """
    # 检查缓存
    if "app_access_token" in _app_access_token_cache:
        return _app_access_token_cache["app_access_token"]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            feishu_config.APP_ACCESS_TOKEN_URL,
            json={
                "app_id": feishu_config.APP_ID,
                "app_secret": feishu_config.APP_SECRET,
            }
        )
        
        if response.status_code != 200:
            logger.error(f"获取 App Access Token 失败: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取飞书 App Access Token 失败"
            )
        
        data = response.json()
        if data.get("code") != 0:
            logger.error(f"获取 App Access Token 失败: {data}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取飞书 App Access Token 失败: {data.get('msg')}"
            )
        
        token = data.get("app_access_token")
        expire = data.get("expire", 7200)
        
        # 缓存 Token（提前 5 分钟过期）
        _app_access_token_cache["app_access_token"] = token
        _app_access_token_cache["expire_at"] = datetime.now(timezone.utc) + timedelta(seconds=expire - 300)
        
        return token


async def get_user_access_token(code: str) -> dict:
    """使用授权码获取用户 Access Token

    Args:
        code: 飞书授权码

    Returns:
        包含 access_token 和用户信息的字典
    """
    app_token = await get_app_access_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            feishu_config.ACCESS_TOKEN_URL,
            headers={
                "Authorization": f"Bearer {app_token}",
                "Content-Type": "application/json",
            },
            json={
                "grant_type": "authorization_code",
                "code": code,
            }
        )
        
        if response.status_code != 200:
            logger.error(f"获取用户 Token 失败: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取用户 Token 失败"
            )
        
        data = response.json()
        if data.get("code") != 0:
            logger.error(f"获取用户 Token 失败: {data}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"获取用户 Token 失败: {data.get('msg')}"
            )
        
        return data.get("data", {})


async def get_feishu_user_info(access_token: str) -> dict:
    """获取飞书用户信息

    Args:
        access_token: 用户 Access Token

    Returns:
        用户信息字典
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            feishu_config.USER_INFO_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
            }
        )
        
        if response.status_code != 200:
            logger.error(f"获取用户信息失败: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取用户信息失败"
            )
        
        data = response.json()
        if data.get("code") != 0:
            logger.error(f"获取用户信息失败: {data}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"获取用户信息失败: {data.get('msg')}"
            )
        
        return data.get("data", {})


# ==================== 路由处理函数 ====================

@router.get(
    "/login",
    summary="飞书登录",
    description="重定向到飞书授权页面",
)
async def feishu_login():
    """飞书登录

    重定向用户到飞书授权页面。

    Returns:
        重定向响应
    """
    if not feishu_config.APP_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="飞书 APP_ID 未配置"
        )
    
    # 构建授权 URL
    authorize_url = (
        f"{feishu_config.AUTHORIZE_URL}"
        f"?app_id={feishu_config.APP_ID}"
        f"&redirect_uri={feishu_config.REDIRECT_URI}"
        f"&response_type=code"
        f"&state=feishu_login"
    )
    
    return RedirectResponse(url=authorize_url)


@router.get(
    "/callback",
    summary="飞书回调",
    description="处理飞书 OAuth2 回调，获取用户信息并签发 Token",
)
async def feishu_callback(
    code: str = Query(description="飞书授权码"),
    state: Optional[str] = Query(default=None, description="状态参数"),
):
    """飞书 OAuth2 回调

    处理飞书授权回调，获取用户信息，签发 JWT Token。

    Args:
        code: 飞书授权码
        state: 状态参数

    Returns:
        重定向到前端，携带 Token
    """
    try:
        # 1. 使用授权码获取用户 Token
        token_data = await get_user_access_token(code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="获取用户 Token 失败"
            )
        
        # 2. 获取用户信息
        user_info = await get_feishu_user_info(access_token)
        
        # 3. 构建用户数据
        user_id = user_info.get("user_id", "")
        user_data = {
            "user_id": user_id,
            "name": user_info.get("name", ""),
            "email": user_info.get("email", ""),
            "avatar": user_info.get("avatar_url", ""),
            "feishu_user_id": user_id,
            "tenant_key": user_info.get("tenant_key", ""),
            "open_id": user_info.get("open_id", ""),
        }
        
        # 4. 存储用户（TODO: 替换为数据库）
        _user_store[user_id] = user_data
        
        # 5. 签发 JWT Token
        jwt_token = auth_middleware.create_access_token(
            data={
                "sub": user_id,
                "name": user_data["name"],
                "email": user_data["email"],
                "feishu_user_id": user_id,
            }
        )
        
        # 6. 重定向到前端，携带 Token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        redirect_url = f"{frontend_url}/auth/callback?token={jwt_token}&user_id={user_id}"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"飞书登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"飞书登录失败: {str(e)}"
        )


@router.get(
    "/login-url",
    summary="获取登录 URL",
    description="获取飞书授权登录 URL（供前端使用）",
)
async def get_login_url():
    """获取飞书登录 URL

    Returns:
        飞书授权 URL
    """
    if not feishu_config.APP_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="飞书 APP_ID 未配置"
        )
    
    authorize_url = (
        f"{feishu_config.AUTHORIZE_URL}"
        f"?app_id={feishu_config.APP_ID}"
        f"&redirect_uri={feishu_config.REDIRECT_URI}"
        f"&response_type=code"
        f"&state=feishu_login"
    )
    
    return {"url": authorize_url}


@router.post(
    "/login/token",
    response_model=LoginResponse,
    summary="Token 登录",
    description="使用已有 Token 登录（供子系统调用）",
)
async def login_with_token(
    token: str = Query(description="飞书 User Access Token"),
):
    """使用 Token 登录

    子系统可以使用飞书 User Access Token 换取本系统的 JWT Token。

    Args:
        token: 飞书 User Access Token

    Returns:
        JWT Token 和用户信息
    """
    try:
        # 获取用户信息
        user_info = await get_feishu_user_info(token)
        user_id = user_info.get("user_id", "")
        
        # 构建用户数据
        user_data = {
            "user_id": user_id,
            "name": user_info.get("name", ""),
            "email": user_info.get("email", ""),
            "avatar": user_info.get("avatar_url", ""),
            "feishu_user_id": user_id,
        }
        
        # 存储用户
        _user_store[user_id] = user_data
        
        # 签发 JWT Token
        jwt_token = auth_middleware.create_access_token(
            data={
                "sub": user_id,
                "name": user_data["name"],
                "email": user_data["email"],
                "feishu_user_id": user_id,
            }
        )
        
        return LoginResponse(
            token=jwt_token,
            user=user_data,
            expires_in=1800,  # 30 分钟
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token 登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token 登录失败: {str(e)}"
        )


@router.post(
    "/token/refresh",
    response_model=LoginResponse,
    summary="刷新 Token",
    description="刷新 JWT Token",
)
async def refresh_token(
    current_user: dict = Depends(get_current_user),
):
    """刷新 Token

    使用当前有效的 Token 换取新 Token。

    Args:
        current_user: 当前用户信息

    Returns:
        新的 JWT Token 和用户信息
    """
    user_id = current_user.get("sub")
    user_data = _user_store.get(user_id, {})
    
    # 签发新 Token
    new_token = auth_middleware.create_access_token(
        data={
            "sub": user_id,
            "name": current_user.get("name", ""),
            "email": current_user.get("email", ""),
            "feishu_user_id": current_user.get("feishu_user_id", ""),
        }
    )
    
    return LoginResponse(
        token=new_token,
        user=user_data,
        expires_in=1800,
    )


@router.get(
    "/verify",
    response_model=TokenVerifyResponse,
    summary="验证 Token",
    description="验证 Token 是否有效（供子系统调用）",
)
async def verify_token(
    current_user: dict = Depends(get_current_user),
):
    """验证 Token

    子系统可以调用此接口验证 Token 是否有效。

    Args:
        current_user: 当前用户信息

    Returns:
        Token 验证结果
    """
    user_id = current_user.get("sub")
    user_data = _user_store.get(user_id, {})
    
    return TokenVerifyResponse(
        valid=True,
        user=user_data,
        expires_at=current_user.get("exp"),
    )


@router.get(
    "/user-info",
    response_model=UserResponse,
    summary="获取用户信息",
    description="获取当前登录用户信息",
)
async def get_user_info(
    current_user: dict = Depends(get_current_user),
):
    """获取用户信息

    Args:
        current_user: 当前用户信息

    Returns:
        用户信息
    """
    user_id = current_user.get("sub")
    user_data = _user_store.get(user_id, {})
    
    return UserResponse(
        user_id=user_id,
        name=user_data.get("name", current_user.get("name", "")),
        email=user_data.get("email", current_user.get("email", "")),
        avatar=user_data.get("avatar", ""),
        feishu_user_id=user_data.get("feishu_user_id", ""),
        tenant_key=user_data.get("tenant_key", ""),
    )


@router.post(
    "/logout",
    summary="登出",
    description="用户登出",
)
async def logout(
    current_user: dict = Depends(get_current_user),
):
    """登出

    Args:
        current_user: 当前用户信息

    Returns:
        登出结果
    """
    # TODO: 将 Token 加入黑名单（需要 Redis 支持）
    return {"message": "登出成功"}
