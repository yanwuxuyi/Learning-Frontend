import axios from 'axios'

const aiRequest = axios.create({
    baseURL: '/ai-api',
    timeout: 60000 // AI responses can take longer
})

// 清理响应文本，移除固定前缀
function cleanResponse(text) {
    // 移除所有 <think></think> 标签及其内容，包括可能的换行和空格
    text = text.replace(/\s*<think>[\s\S]*?<\/think>\s*/g, '');
    
    // 移除开头的空白字符
    text = text.trim();
    
    return text;
}

aiRequest.interceptors.response.use(
    response => {
        if (response.data && response.data.response) {
            // 在返回响应前清理文本
            response.data.response = cleanResponse(response.data.response);
        }
        return response.data;
    },
    error => {
        console.error("AI service error:", error);
        return Promise.reject(error);
    }
);

export function generate(prompt) {
    return aiRequest({
        url: "/generate",
        method: 'post',
        data: {
            "model": "deepseek-r1:1.5b",
            "prompt": prompt,
            "stream": false,
            'temperature': 0.1
        }
    })
} 