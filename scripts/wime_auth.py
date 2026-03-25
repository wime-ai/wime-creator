#!/usr/bin/env python3
"""
WIME OpenAPI 签名生成工具

签名流程 (两步 HMAC-SHA256):
1. sign_key = HMAC("ak-v1/{ak}/{timestamp}/{expiration}", sk)
2. signature = HMAC(canonical_request, sign_key)
3. Authorization = "ak-v1/{ak}/{timestamp}/{expiration}/{signature}"

canonical_request = "HTTPMethod:{method}\nCanonicalURI:{path}\nCanonicalQueryString:{params}\nCanonicalBody:{body}"
"""

import hashlib
import hmac
import json
import os
import time
import argparse
from typing import Dict, Optional

# 环境配置
# AK/SK 优先从环境变量 WIME_AK / WIME_SK 读取，未设置则为空（会在调用时报错提示）
ENVS = {
    "ol": {
        "base_url": os.environ.get("WIME_BASE_URL", "https://openapi.wime-ai.com"),
        "ak": os.environ.get("WIME_AK", ""),
        "sk": os.environ.get("WIME_SK", ""),
    },
}

DEFAULT_EXPIRE_SECONDS = 1800


def sha256_hmac(message: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def canonical_method(method: str) -> str:
    return "HTTPMethod:" + method


def canonical_url(url: str) -> str:
    return "CanonicalURI:" + url


def canonical_param(params: Optional[Dict[str, str]]) -> str:
    res = "CanonicalQueryString:"
    if not params:
        return res
    formatted = "&".join(f"{k}={v}" for k, v in params.items())
    return res + formatted


def canonical_body(body: Optional[str]) -> str:
    return "CanonicalBody:" + (body if body else "")


def sign(ak: str, sk: str, timestamp: int, expiration: int,
         method: str, uri_path: str,
         params: Optional[Dict[str, str]] = None,
         body: Optional[str] = None) -> str:
    """生成完整签名字符串"""
    cm = canonical_method(method)
    cu = canonical_url(uri_path)
    cp = canonical_param(params)
    cb = canonical_body(body)
    text = f"{cm}\n{cu}\n{cp}\n{cb}"

    sign_key_info = f"ak-v1/{ak}/{timestamp}/{expiration}"
    sign_key = sha256_hmac(sign_key_info, sk)
    sign_result = sha256_hmac(text, sign_key)
    return f"{sign_key_info}/{sign_result}"


def make_request_headers(env: str, method: str, uri_path: str,
                         params: Optional[Dict[str, str]] = None,
                         body_dict: Optional[dict] = None,
                         expire_seconds: int = DEFAULT_EXPIRE_SECONDS) -> dict:
    """生成请求所需的 headers 和 base_url

    body_dict 会被转为 sorted JSON (无空格) 用于签名。
    """
    config = ENVS[env]
    if not config["ak"] or not config["sk"]:
        raise ValueError(f"环境 '{env}' 的 AK/SK 未配置")

    ak, sk = config["ak"], config["sk"]
    timestamp = int(time.time())

    body_str = None
    if body_dict is not None:
        body_str = json.dumps(body_dict, separators=(',', ':'), sort_keys=True, ensure_ascii=False)

    auth = sign(ak, sk, timestamp, expire_seconds, method, uri_path, params, body_str)

    return {
        "base_url": config["base_url"],
        "Authorization": auth,
        # ⚠️ 发送请求时必须用 data=body_str.encode('utf-8')，不能用 json=body_dict
        # requests.post(json=) 的序列化与签名不一致会导致验签失败
        "body_str": body_str,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WIME OpenAPI 签名生成")
    parser.add_argument("--env", choices=["ol"], default="ol")
    parser.add_argument("--method", default="POST")
    parser.add_argument("--path", default="/openapi/wime/1_0/asset")
    parser.add_argument("--body", default="{}", help="JSON body string")
    parser.add_argument("--expire", type=int, default=DEFAULT_EXPIRE_SECONDS)
    args = parser.parse_args()

    body_dict = json.loads(args.body)
    result = make_request_headers(args.env, args.method, args.path, body_dict=body_dict, expire_seconds=args.expire)
    print(json.dumps(result, indent=2, ensure_ascii=False))
