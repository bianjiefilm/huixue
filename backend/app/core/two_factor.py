"""
二次验证（2FA）系统
提供TOTP、短信、邮箱等多种二次验证方式
"""
import hashlib
import hmac
import time
import base64
import secrets
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TwoFactorAuth:
    """二次验证管理器"""

    def __init__(self):
        self.secret_length = 32  # TOTP密钥长度

    def generate_totp_secret(self, user_id: int) -> str:
        """
        为用户生成TOTP密钥

        Args:
            user_id: 用户ID

        Returns:
            str: base64编码的密钥
        """
        # 生成随机密钥
        secret_bytes = secrets.token_bytes(self.secret_length)

        # 使用用户ID作为salt进行混淆
        salt = str(user_id).encode('utf-8')
        secret_bytes = hmac.new(salt, secret_bytes, hashlib.sha256).digest()

        return base64.b64encode(secret_bytes).decode('utf-8')

    def generate_totp_code(self, secret: str, time_window: int = 30) -> str:
        """
        生成TOTP验证码

        Args:
            secret: base64编码的密钥
            time_window: 时间窗口（秒）

        Returns:
            str: 6位数字验证码
        """
        try:
            # 解码密钥
            key = base64.b64decode(secret)

            # 计算时间步长
            current_time = int(time.time() // time_window)

            # 转换为8字节大端格式
            time_bytes = current_time.to_bytes(8, 'big')

            # HMAC-SHA1
            hmac_hash = hmac.new(key, time_bytes, hashlib.sha1).digest()

            # 动态截断
            offset = hmac_hash[-1] & 0x0f
            code_bytes = hmac_hash[offset:offset + 4]
            code_int = int.from_bytes(code_bytes, 'big')

            # 生成6位数字
            code = str(code_int % 10**6).zfill(6)

            return code

        except Exception as e:
            logger.error(f"生成TOTP验证码失败: {e}")
            return ""

    def verify_totp_code(self, secret: str, code: str, time_window: int = 30, tolerance: int = 1) -> bool:
        """
        验证TOTP验证码

        Args:
            secret: base64编码的密钥
            code: 用户输入的验证码
            time_window: 时间窗口
            tolerance: 容忍的时间窗口数量（前后）

        Returns:
            bool: 验证码是否有效
        """
        if not code or len(code) != 6 or not code.isdigit():
            return False

        # 检查当前时间窗口和前后tolerance个窗口
        current_time = int(time.time() // time_window)

        for i in range(-tolerance, tolerance + 1):
            check_time = current_time + i
            expected_code = self.generate_totp_code(secret, time_window)

            # 手动计算指定时间的验证码
            try:
                key = base64.b64decode(secret)
                time_bytes = check_time.to_bytes(8, 'big')
                hmac_hash = hmac.new(key, time_bytes, hashlib.sha1).digest()

                offset = hmac_hash[-1] & 0x0f
                code_bytes = hmac_hash[offset:offset + 4]
                code_int = int.from_bytes(code_bytes, 'big')
                expected_code = str(code_int % 10**6).zfill(6)

                if expected_code == code:
                    return True

            except Exception as e:
                logger.error(f"验证TOTP时出错: {e}")
                continue

        return False

    def send_sms_code(self, phone_number: str, code: str) -> bool:
        """
        发送短信验证码（模拟实现）

        Args:
            phone_number: 手机号
            code: 验证码

        Returns:
            bool: 发送是否成功
        """
        # TODO: 集成真实的短信服务，如阿里云SMS、腾讯云SMS等
        logger.info(f"模拟发送短信验证码到 {phone_number}: {code}")

        # 在实际项目中，这里应该调用真实的短信API
        # 示例：
        # try:
        #     sms_client = AliyunSMSClient(access_key, secret_key)
        #     response = sms_client.send_sms(phone_number, template_code, {"code": code})
        #     return response.success
        # except Exception as e:
        #     logger.error(f"发送短信失败: {e}")
        #     return False

        return True  # 模拟成功

    def send_email_code(self, email: str, code: str) -> bool:
        """
        发送邮箱验证码（模拟实现）

        Args:
            email: 邮箱地址
            code: 验证码

        Returns:
            bool: 发送是否成功
        """
        # TODO: 集成真实的邮件服务，如SendGrid、AWS SES等
        logger.info(f"模拟发送邮件验证码到 {email}: {code}")

        # 在实际项目中，这里应该调用真实的邮件API
        # 示例：
        # try:
        #     email_client = SendGridClient(api_key)
        #     message = Mail(
        #         from_email='noreply@example.com',
        #         to_emails=email,
        #         subject='验证码',
        #         html_content=f'您的验证码是: <strong>{code}</strong>'
        #     )
        #     response = email_client.send(message)
        #     return response.status_code == 202
        # except Exception as e:
        #     logger.error(f"发送邮件失败: {e}")
        #     return False

        return True  # 模拟成功

    def generate_backup_codes(self, user_id: int, count: int = 10) -> list:
        """
        生成备用验证码

        Args:
            user_id: 用户ID
            count: 生成数量

        Returns:
            list: 备用验证码列表
        """
        codes = []
        for i in range(count):
            # 使用用户ID和序号生成唯一码
            seed = f"{user_id}:{i}:{secrets.token_hex(8)}"
            code = hashlib.sha256(seed.encode()).hexdigest()[:10].upper()
            codes.append(code)

        return codes

    def verify_backup_code(self, user_id: int, code: str, stored_codes: list) -> tuple:
        """
        验证备用验证码

        Args:
            user_id: 用户ID
            code: 输入的验证码
            stored_codes: 存储的备用验证码列表

        Returns:
            tuple: (是否有效, 剩余验证码列表)
        """
        code = code.upper()

        if code in stored_codes:
            # 移除已使用的验证码
            remaining_codes = [c for c in stored_codes if c != code]
            return True, remaining_codes

        return False, stored_codes

# 全局2FA实例
two_factor_auth = TwoFactorAuth()

def get_two_factor_auth() -> TwoFactorAuth:
    """获取2FA实例"""
    return two_factor_auth

# 便捷函数
def generate_totp_secret(user_id: int) -> str:
    """生成TOTP密钥"""
    return two_factor_auth.generate_totp_secret(user_id)

def generate_totp_code(secret: str) -> str:
    """生成TOTP验证码"""
    return two_factor_auth.generate_totp_code(secret)

def verify_totp_code(secret: str, code: str) -> bool:
    """验证TOTP验证码"""
    return two_factor_auth.verify_totp_code(secret, code)

def send_sms_code(phone: str, code: str) -> bool:
    """发送短信验证码"""
    return two_factor_auth.send_sms_code(phone, code)

def send_email_code(email: str, code: str) -> bool:
    """发送邮箱验证码"""
    return two_factor_auth.send_email_code(email, code)

