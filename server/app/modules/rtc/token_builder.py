# -*- coding: utf-8 -*-
"""
声网 Agora AccessToken2（007 版）最小实现
=========================================

按 Agora 官方 DynamicKey/AccessToken2 + Packer 的字段顺序实现，仅覆盖 RTC 频道鉴权，
不引入第三方依赖、不包含 RTM / 流媒体等其它服务。

安全说明：
- 签名密钥只在服务端用 AGORA_APP_CERTIFICATE 计算，证书本身绝不下发客户端；
- salt 用 secrets 生成（非可预测随机数）；
- token 有效期由调用方控制，默认 1 小时。
"""
import base64
import hmac
import secrets
import struct
import time
import zlib
from collections import OrderedDict
from hashlib import sha256

TOKEN_VERSION = "007"

SERVICE_TYPE_RTC = 1
RTC_PRIVILEGE_JOIN_CHANNEL = 1
RTC_PRIVILEGE_PUBLISH_AUDIO = 2
RTC_PRIVILEGE_PUBLISH_VIDEO = 3
RTC_PRIVILEGE_PUBLISH_DATA = 4


def _pack_uint16(x) -> bytes:
    return struct.pack("<H", int(x))


def _pack_uint32(x) -> bytes:
    return struct.pack("<I", int(x))


def _pack_string(data) -> bytes:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return _pack_uint16(len(data)) + data


def _pack_map_uint32(m: dict) -> bytes:
    """按 key 升序打包 uint16→uint32 映射（官方实现要求顺序稳定）"""
    items = OrderedDict(sorted(m.items(), key=lambda kv: int(kv[0])))
    body = b"".join(_pack_uint16(k) + _pack_uint32(v) for k, v in items.items())
    return _pack_uint16(len(items)) + body


def is_valid_app_key(value: str) -> bool:
    """Agora 的 App ID / App Certificate 均为 32 位十六进制字符串"""
    if not value or len(value) != 32:
        return False
    try:
        bytes.fromhex(value)
    except (TypeError, ValueError):
        return False
    return True


def build_rtc_token(app_id: str, app_certificate: str, channel_name: str,
                    uid: int, expire: int = 3600, issue_ts: int = 0) -> str:
    """
    生成 RTC 频道 token。

    :param channel_name: 频道名（调用方需保证 1~64 字节、仅字母数字下划线连字符）
    :param uid:          用户 uid（0 表示「任意用户」；本项目始终传真实 uid）
    :param expire:       token 有效期（秒）
    :param issue_ts:     签发时间戳（0 = 当前时间，测试可指定）
    """
    if not is_valid_app_key(app_id) or not is_valid_app_key(app_certificate):
        raise ValueError("APP ID / APP Certificate 必须是 32 位十六进制字符串")
    if not channel_name:
        raise ValueError("频道名不能为空")

    issued = int(issue_ts or time.time())
    salt = secrets.SystemRandom().randint(1, 99999999)
    expire = int(expire)
    expire_ts = issued + expire

    # 1) RTC service：服务类型 + 权限表 + 频道名 + uid
    privileges = {
        RTC_PRIVILEGE_JOIN_CHANNEL: expire_ts,
        RTC_PRIVILEGE_PUBLISH_AUDIO: expire_ts,
        RTC_PRIVILEGE_PUBLISH_VIDEO: expire_ts,
        RTC_PRIVILEGE_PUBLISH_DATA: expire_ts,
    }
    service_payload = (
        _pack_uint16(SERVICE_TYPE_RTC)
        + _pack_map_uint32(privileges)
        + _pack_string(channel_name)
        + _pack_string(b"" if int(uid) == 0 else str(int(uid)))
    )

    # 2) 签名密钥：HMAC(issue_ts, cert) → HMAC(salt, 上一步结果)
    signing_key = hmac.new(_pack_uint32(issued), app_certificate.encode("utf-8"), sha256).digest()
    signing_key = hmac.new(_pack_uint32(salt), signing_key, sha256).digest()

    # 3) 待签名内容（服务端可用同一份证书复算校验）
    signing_info = (
        _pack_string(app_id)
        + _pack_uint32(issued)
        + _pack_uint32(expire)
        + _pack_uint32(salt)
        + _pack_uint16(1)            # service 数量
        + service_payload
    )
    signature = hmac.new(signing_key, signing_info, sha256).digest()

    # 4) 007 + base64(zlib(signature + signing_info))
    content = _pack_string(signature) + signing_info
    return TOKEN_VERSION + base64.b64encode(zlib.compress(content)).decode("utf-8")
