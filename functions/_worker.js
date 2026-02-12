export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // 如果请求的是 matt-shumer.html，直接返回该文件
    if (url.pathname === '/matt-shumer.html' || url.pathname === '/matt-shumer') {
      return fetch(new Request('https://raw.githubusercontent.com/zhongyi-byte/life-briefing/main/matt-shumer.html', request));
    }
    
    // 如果请求的是 article/ 目录
    if (url.pathname === '/article/' || url.pathname === '/article') {
      return fetch(new Request('https://raw.githubusercontent.com/zhongyi-byte/life-briefing/main/article/index.html', request));
    }
    
    // 其他请求走默认处理
    return env.ASSETS.fetch(request);
  }
};
