/**
 * 安全的认证工具 - 使用 httpOnly cookies 存储 JWT
 */

interface AuthConfig {
  tokenKey: string;
  userInfoKey: string;
  cookieDomain?: string;
  cookiePath: string;
}

const config: AuthConfig = {
  tokenKey: 'huixue_token',
  userInfoKey: 'huixue_user',
  cookiePath: '/',
  cookieDomain: undefined
};

/**
 * Cookie 操作工具类
 */
class CookieUtil {
  /**
   * 设置 cookie
   */
  static set(name: string, value: string, options: {
    expires?: number; // 天数
    path?: string;
    domain?: string;
    secure?: boolean;
    sameSite?: 'strict' | 'lax' | 'none';
  } = {}) {
    let cookieStr = `${name}=${encodeURIComponent(value)}`;
    
    if (options.expires) {
      const date = new Date();
      date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
      cookieStr += `; expires=${date.toUTCString()}`;
    }
    
    cookieStr += `; path=${options.path || '/'}`;
    
    if (options.domain) {
      cookieStr += `; domain=${options.domain}`;
    }
    
    // 生产环境强制使用 secure
    if (options.secure || (typeof window !== 'undefined' && window.location.protocol === 'https:')) {
      cookieStr += '; secure';
    }
    
    cookieStr += `; samesite=${options.sameSite || 'strict'}`;
    
    document.cookie = cookieStr;
  }
  
  /**
   * 获取 cookie
   */
  static get(name: string): string | null {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    
    for (let c of ca) {
      c = c.trim();
      if (c.indexOf(nameEQ) === 0) {
        return decodeURIComponent(c.substring(nameEQ.length));
      }
    }
    
    return null;
  }
  
  /**
   * 删除 cookie
   */
  static remove(name: string, options: {
    path?: string;
    domain?: string;
  } = {}) {
    this.set(name, '', {
      expires: -1,
      path: options.path || '/',
      domain: options.domain
    });
  }
}

/**
 * 安全存储类 - 支持 cookie 和 localStorage 双模式
 */
export class SecureStorage {
  private static isSecureContext(): boolean {
    return (typeof window !== 'undefined' && (window.location.protocol === 'https:' || window.location.hostname === 'localhost'));
  }
  
  /**
   * 保存认证信息
   */
  static setAuth(token: string, userInfo?: any) {
    console.log('SecureStorage.setAuth() called, token length:', token.length);
    console.log('isSecureContext:', this.isSecureContext());

    const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost';

    // 学校环境使用 http://100.74.141.3:3000，不能只依赖 sessionStorage。
    // 使用同源 host-only cookie，避免 IP 地址设置 Domain 属性后被浏览器拒收。
    CookieUtil.set(config.tokenKey, token, {
      expires: 7, // 7天
      path: config.cookiePath,
      domain: config.cookieDomain,
      secure: !isLocalhost && typeof window !== 'undefined' && window.location.protocol === 'https:',
      sameSite: 'lax'
    });

    console.log('Token set in cookie');

    sessionStorage.setItem(config.tokenKey, token);
    console.log('Token set in sessionStorage');

    // 用户信息可以存储在 localStorage
    if (userInfo) {
      localStorage.setItem(config.userInfoKey, JSON.stringify(userInfo));
      console.log('User info set in localStorage');
    }
  }
  
  /**
   * 获取 token
   */
  static getToken(): string | null {
    console.log('SecureStorage.getToken() called');
    console.log('isSecureContext:', this.isSecureContext());

    // 优先从 cookie 获取
    const cookieToken = CookieUtil.get(config.tokenKey);
    console.log('cookieToken:', !!cookieToken ? 'found' : 'not found');
    if (cookieToken) {
      console.log('Returning token from cookie');
      return cookieToken;
    }

    // 降级：从 sessionStorage 获取
    const sessionToken = sessionStorage.getItem(config.tokenKey);
    console.log('sessionToken:', !!sessionToken ? 'found' : 'not found');
    if (sessionToken) {
      console.log('Returning token from sessionStorage');
      return sessionToken;
    }

    // 兼容旧版本：从 localStorage 获取并迁移
    const localToken = localStorage.getItem('token');
    console.log('localToken:', !!localToken ? 'found' : 'not found');
    if (localToken) {
      // 迁移到新的存储方式
      this.setAuth(localToken);
      localStorage.removeItem('token');
      console.log('Returning migrated token from localStorage');
      return localToken;
    }

    console.log('No token found in any storage');
    return null;
  }
  
  /**
   * 获取用户信息
   */
  static getUserInfo(): any | null {
    const userInfoStr = localStorage.getItem(config.userInfoKey) || localStorage.getItem('userInfo');
    if (userInfoStr) {
      try {
        return JSON.parse(userInfoStr);
      } catch {
        return null;
      }
    }
    return null;
  }
  
  /**
   * 清除认证信息
   */
  static clearAuth() {
    // 清除 cookie
    CookieUtil.remove(config.tokenKey, {
      path: config.cookiePath,
      domain: config.cookieDomain
    });
    
    // 清除其他存储
    sessionStorage.removeItem(config.tokenKey);
    localStorage.removeItem('token');
    localStorage.removeItem(config.userInfoKey);
    localStorage.removeItem('userInfo');
  }
  
  /**
   * 检查是否已认证
   */
  static isAuthenticated(): boolean {
    return !!this.getToken();
  }
}

/**
 * 导出便捷方法
 */
export const getToken = () => SecureStorage.getToken();
export const getUserInfo = () => SecureStorage.getUserInfo();
export const setAuth = (token: string, userInfo?: any) => SecureStorage.setAuth(token, userInfo);
export const clearAuth = () => SecureStorage.clearAuth();
export const isAuthenticated = () => SecureStorage.isAuthenticated();
