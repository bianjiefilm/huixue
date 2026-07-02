import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  esbuild: {
    tsconfigRaw: {
      compilerOptions: {
        noImplicitAny: false,
        strict: false,
        skipLibCheck: true
      }
    }
  },
  base: '/',
  define: {
    global: "globalThis",
    process: { env: {} }
  },
  plugins: [
    vue(),
    vueJsx(),
    // 暂时禁用vueDevTools，可能导致页面卡死
    // vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // 添加vue的别名，以支持运行时编译
      'vue': 'vue/dist/vue.esm-bundler.js'
    },
  },
  worker: {
    format: 'es'
  },
  server: {
    port: 3000,
    proxy: {
      // 注意：代理规则按顺序匹配，更具体的规则应该放在前面
      // 关键修复：将 /api/v1/environments/proxy 路径直接代理到后端，避免 Vite 拦截并注入脚本
      '/api/v1/environments/proxy': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        credentials: 'include',
        // 不重写路径，直接转发
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // 确保 referer 头被保留
            if (req.headers.referer) {
              proxyReq.setHeader('referer', req.headers.referer);
            }
          });
        }
      },
      // 代理Superset的API请求（从iframe发出的特定Superset API路径）
      // Superset的API路径通常是：/api/v1/database/, /api/v1/chart/, /api/v1/dashboard/, /api/v1/dataset/等
      // 我们的后端API路径是：/api/v1/classrooms/, /api/v1/environments/等
      // 关键修复：检查请求是否来自iframe（通过referer或URL参数）
      '/api/v1/database': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        credentials: 'include',
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            const referer = req.headers.referer || '';
            const url = req.url || '';
            // 如果referer包含environments/proxy，或者URL包含training_id/user_id参数，说明是来自iframe的Superset请求
            const isFromIframe = referer.includes('environments/proxy') || 
                                 url.includes('training_id') || 
                                 url.includes('user_id');
            if (isFromIframe && !req.url.includes('environments/proxy')) {
              const newPath = `/api/v1/environments/proxy${req.url}`;
              proxyReq.path = newPath;
              // 确保referer被保留
              if (req.headers.referer) {
                proxyReq.setHeader('referer', req.headers.referer);
              }
            }
          });
        }
      },
      '/api/v1/chart': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        credentials: 'include',
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            const referer = req.headers.referer || '';
            const url = req.url || '';
            const isFromIframe = referer.includes('environments/proxy') || 
                                 url.includes('training_id') || 
                                 url.includes('user_id');
            if (isFromIframe && !req.url.includes('environments/proxy')) {
              const newPath = `/api/v1/environments/proxy${req.url}`;
              proxyReq.path = newPath;
              if (req.headers.referer) {
                proxyReq.setHeader('referer', req.headers.referer);
              }
            }
          });
        }
      },
      '/api/v1/dashboard': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        credentials: 'include',
        rewrite: (path) => {
          // Vite 的 rewrite 函数接收的 path 不包含匹配的前缀（/api/v1）
          // 所以 path 格式是：/dashboard/?q=(...) 或 /dashboard/_info?q=(...)
          // 如果请求已经包含 environments/proxy，则不需要重写
          if (path.includes('environments/proxy')) {
            return path;
          }
          // 重写路径：/dashboard/... -> /api/v1/environments/proxy/dashboard/...
          // 注意：后端代理端点期望的路径是 dashboard/...（不包含 /api/v1/ 前缀）
          return `/api/v1/environments/proxy/dashboard${path}`;
        },
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            const referer = req.headers.referer || '';
            const url = req.url || '';
            
            // 关键修复：从 referer 中提取 training_id 和 user_id
            // referer 可能是：http://localhost:3000/dashboard/list/... 或 http://localhost:3000/api/v1/environments/proxy/superset/welcome/?training_id=3&user_id=3
            let trainingId = null;
            let userId = null;
            
            // 首先从 referer 中提取
            const refererTrainingMatch = referer.match(/training_id=(\d+)/);
            const refererUserMatch = referer.match(/user_id=(\d+)/);
            if (refererTrainingMatch) {
              trainingId = refererTrainingMatch[1];
            }
            if (refererUserMatch) {
              userId = refererUserMatch[1];
            }
            
            // 如果 referer 中没有，尝试从 URL 中提取（可能已经被 XHR 拦截器添加）
            if (!trainingId || !userId) {
              const urlTrainingMatch = url.match(/training_id=(\d+)/);
              const urlUserMatch = url.match(/user_id=(\d+)/);
              if (urlTrainingMatch) {
                trainingId = urlTrainingMatch[1];
              }
              if (urlUserMatch) {
                userId = urlUserMatch[1];
              }
            }
            
            // 如果仍然没有，尝试从父窗口的 iframe src 中提取（通过检查 document）
            // 注意：这是一个后备方案，可能不够可靠
            if (!trainingId || !userId) {
              try {
                // 在 Node.js 环境中，无法直接访问 document，所以这个方案不可行
                // 但我们可以通过检查是否有其他方式传递这些参数
              } catch (e) {
                // 忽略错误
              }
            }
            
            // 如果找到了参数，添加到 URL 中（如果还没有）
            if (trainingId && userId && !proxyReq.path.includes('training_id')) {
              const separator = proxyReq.path.includes('?') ? '&' : '?';
              proxyReq.path = `${proxyReq.path}${separator}training_id=${trainingId}&user_id=${userId}`;
            }
            
            // 确保referer被保留
            if (req.headers.referer) {
              proxyReq.setHeader('referer', req.headers.referer);
            }
            
            // 关键修复：添加 x-iframe-src 头部，包含 iframe 的原始 URL（如果可以从父窗口获取）
            // 注意：在 Vite 代理中，我们无法直接访问父窗口的 iframe，所以这个头部可能为空
            // 但我们可以尝试从 referer 中提取 iframe 的原始 URL
            const iframeSrcMatch = referer.match(/\/api\/v1\/environments\/proxy\/[^?]*\?[^&]*training_id=(\d+)[^&]*user_id=(\d+)/);
            if (iframeSrcMatch && (!trainingId || !userId)) {
              trainingId = iframeSrcMatch[1];
              userId = iframeSrcMatch[2];
              if (trainingId && userId && !proxyReq.path.includes('training_id')) {
                const separator = proxyReq.path.includes('?') ? '&' : '?';
                proxyReq.path = `${proxyReq.path}${separator}training_id=${trainingId}&user_id=${userId}`;
              }
            }
            
            console.log('[Vite Proxy] Rewriting dashboard API request:', {
              original: req.url,
              new: proxyReq.path,
              referer: referer.substring(0, 100),
              trainingId,
              userId
            });
          });
        }
      },
      '/api/v1/dataset': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        credentials: 'include',
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            const referer = req.headers.referer || '';
            const url = req.url || '';
            const isFromIframe = referer.includes('environments/proxy') || 
                                 url.includes('training_id') || 
                                 url.includes('user_id');
            if (isFromIframe && !req.url.includes('environments/proxy')) {
              const newPath = `/api/v1/environments/proxy${req.url}`;
              proxyReq.path = newPath;
              if (req.headers.referer) {
                proxyReq.setHeader('referer', req.headers.referer);
              }
            }
          });
        }
      },
      // 代理 Superset 的其他路径（如 /superset/log/, /superset/welcome/ 等）
      '/superset': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        credentials: 'include',
        rewrite: (path) => {
          // path 格式是：/log/?explode=events 或 /welcome/
          // 如果请求已经包含 environments/proxy，则不需要重写
          if (path.includes('environments/proxy')) {
            return path;
          }
          // 重写路径：/log/... -> /api/v1/environments/proxy/superset/log/...
          return `/api/v1/environments/proxy/superset${path}`;
        },
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            const referer = req.headers.referer || '';
            const url = req.url || '';
            
            // 从referer中提取training_id和user_id，添加到URL中（如果还没有）
            const trainingMatch = referer.match(/training_id=(\d+)/);
            const userMatch = referer.match(/user_id=(\d+)/);
            if (trainingMatch && userMatch && !url.includes('training_id')) {
              const separator = proxyReq.path.includes('?') ? '&' : '?';
              proxyReq.path = `${proxyReq.path}${separator}training_id=${trainingMatch[1]}&user_id=${userMatch[1]}`;
            }
            
            // 确保referer被保留
            if (req.headers.referer) {
              proxyReq.setHeader('referer', req.headers.referer);
            }
          });
        }
      },
      '/api/v1': {
        target: 'http://localhost:8000',  // 后端API地址
        changeOrigin: true,
        credentials: 'include',
        // 关键修复：使用 bypass 函数排除已经被更具体规则处理的路径
        bypass: (req, _res, _options) => {
          const url = req.url || '';
          // 如果请求已经被更具体的规则处理（如 /api/v1/dashboard），则跳过这个规则
          if (url.startsWith('/api/v1/dashboard') || 
              url.startsWith('/api/v1/chart') || 
              url.startsWith('/api/v1/dataset') ||
              url.startsWith('/api/v1/database')) {
            return null; // 继续代理，让更具体的规则处理
          }
          return null; // 继续代理
        },
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            const referer = req.headers.referer || '';
            const url = req.url || '';
            // 检查是否是Superset的API请求（但不是我们的environments/proxy端点）
            // 注意：这里不应该处理 dashboard/chart/dataset/database，因为它们有专门的规则
            const isSupersetApi = (url.startsWith('/api/v1/query') ||
                                  url.startsWith('/api/v1/explore') ||
                                  url.startsWith('/api/v1/security') ||
                                  url.startsWith('/api/v1/csrf')) &&
                                 !url.includes('environments/proxy');
            // 如果referer包含environments/proxy，说明是来自iframe的Superset请求
            const isFromIframe = referer.includes('environments/proxy') || 
                                referer.includes('/api/v1/environments/proxy');
            if (isSupersetApi && isFromIframe && !req.url.includes('environments/proxy')) {
              const newPath = `/api/v1/environments/proxy${req.url}`;
              proxyReq.path = newPath;
              // 确保referer被保留，并添加training_id和user_id参数（如果referer中有）
              if (req.headers.referer) {
                proxyReq.setHeader('referer', req.headers.referer);
                // 从referer中提取training_id和user_id，添加到URL中
                const trainingMatch = referer.match(/training_id=(\d+)/);
                const userMatch = referer.match(/user_id=(\d+)/);
                if (trainingMatch && userMatch) {
                  const separator = req.url.includes('?') ? '&' : '?';
                  proxyReq.path = `${newPath}${separator}training_id=${trainingMatch[1]}&user_id=${userMatch[1]}`;
                }
              }
            }
          });
        }
      },
      // 试题库/试卷库路径重写：前端使用 /api/exam/*，后端注册在 /api/v1/question-library/* 和 /api/v1/paper-library/*
      '/api/exam/questions': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/exam\/questions/, '/api/v1/question-library/questions'),
      },
      '/api/exam/papers': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/exam\/papers/, '/api/v1/paper-library/papers'),
      },
      '/api': {
    	  target: 'http://localhost:8000',  // 后端API地址
    	  changeOrigin: true,  // 是否修改请求头中的Origin
    	  credentials: 'include',  // 允许跨域请求包含Cookie
    	  // 不重写路径，保留/api前缀
    	  // 但是需要排除Superset的API请求（这些请求应该通过代理端点）
    	  bypass: (req, _res, _options) => {
    	    const referer = req.headers.referer || '';
    	    const url = req.url || '';
    	    // 如果referer包含environments/proxy，说明是来自iframe的Superset请求
    	    // 需要特殊处理，让/api/v1规则处理
    	    if (referer.includes('environments/proxy')) {
    	      return null; // 继续代理，让/api/v1规则处理
    	    }
    	    // 否则，这是正常的后端API请求，直接代理
    	    return null;
    	  }
    	},
      '/v1': {
        target: 'http://localhost:8000',  // 后端API地址
        changeOrigin: true,  // 是否修改请求头中的Origin
        credentials: 'include',  // 允许跨域请求包含Cookie
        rewrite: (path) => path.replace(/^\/v1/, '/api/v1'),  // 重写路径：/v1 -> /api/v1
      },
      // 静态文件代理到后端 StaticFiles（修复PPTX/PDF等大文件下载截断Bug）
      // 注意：此处的 rewrite 补上前缀，因为 Vite 会 strip 掉 '/static'
      // 后端 StaticFiles 挂载在 /static/resources，代理目标: /static/resources/*
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        credentials: 'include',
        rewrite: (path) => `/static${path}`,
      }
    }
  }
})
