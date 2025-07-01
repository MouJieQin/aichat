// src/utils/jsonLoader.ts
const cacheMap = new Map<string, any>();
/**
 * 读取本地JSON文件内容（单例模式，确保只读取一次）
 * @param filePath - JSON文件路径（相对于public目录）
 * @returns JSON内容对象
 */
export async function loadJsonFile(filePath: string): Promise<any> {
    // 如果已经缓存了数据，直接返回
    if (cacheMap.has(filePath)) {
        return cacheMap.get(filePath);
    }
    try {
        // 使用fetch API读取public目录下的JSON文件
        const response = await fetch(filePath);

        // 检查响应状态
        if (!response.ok) {
            throw new Error(`Failed to load JSON file: ${response.statusText}`);
        }

        // 解析JSON并缓存结果
        const data = await response.json();
        cacheMap.set(filePath, data);
        return data;
    } catch (error) {
        console.error('Error loading JSON file:', error);
        return undefined
        // throw error;
    }
}