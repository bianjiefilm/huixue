/**
 * Mock数据工具函数
 */

/**
 * 生成指定范围内的随机数
 * @param min 最小值（包含）
 * @param max 最大值（包含）
 * @returns 随机整数
 */
export const getRandomNumber = (min: number, max: number): number => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

/**
 * 生成随机ID
 * @param prefix ID前缀，默认为空
 * @returns 随机ID字符串
 */
export const getRandomId = (prefix: string = ''): string => {
  return prefix + Math.random().toString(36).substring(2, 10);
};

/**
 * 从数组中随机选择一个元素
 * @param array 源数组
 * @returns 随机选中的元素
 */
export const getRandomElement = <T>(array: T[]): T => {
  return array[getRandomNumber(0, array.length - 1)];
};

/**
 * 从数组中随机选择多个元素
 * @param array 源数组
 * @param count 选择的元素数量
 * @returns 随机选中的元素数组
 */
export const getRandomElements = <T>(array: T[], count: number): T[] => {
  if (count >= array.length) return [...array];
  
  const result: T[] = [];
  const copyArray = [...array];
  
  for (let i = 0; i < count; i++) {
    const randomIndex = getRandomNumber(0, copyArray.length - 1);
    result.push(copyArray[randomIndex]);
    copyArray.splice(randomIndex, 1);
  }
  
  return result;
};

/**
 * 生成随机日期字符串
 * @param startYear 开始年份
 * @param endYear 结束年份
 * @returns 随机日期字符串，格式：YYYY-MM-DD HH:MM:SS
 */
export const getRandomDate = (startYear: number = 2020, endYear: number = 2023): string => {
  const year = getRandomNumber(startYear, endYear);
  const month = getRandomNumber(1, 12).toString().padStart(2, '0');
  const day = getRandomNumber(1, 28).toString().padStart(2, '0');
  const hour = getRandomNumber(0, 23).toString().padStart(2, '0');
  const minute = getRandomNumber(0, 59).toString().padStart(2, '0');
  const second = getRandomNumber(0, 59).toString().padStart(2, '0');
  
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
};

/**
 * 生成随机布尔值
 * @param trueProb true的概率，范围0-1，默认0.5
 * @returns 随机布尔值
 */
export const getRandomBoolean = (trueProb: number = 0.5): boolean => {
  return Math.random() < trueProb;
};

/**
 * 从URL中解析查询参数
 * @param url URL字符串
 * @returns 包含查询参数的对象
 */
export const getUrlParams = (url: string): Record<string, string> => {
  const params: Record<string, string> = {};
  const queryString = url.split('?')[1];
  
  if (!queryString) return params;
  
  const paramPairs = queryString.split('&');
  
  for (const pair of paramPairs) {
    const [key, value] = pair.split('=');
    params[key] = decodeURIComponent(value || '');
  }
  
  return params;
}; 