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

export function generate(userMessage, systemPrompt) {
    return aiRequest({
        url: "/generate",
        method: 'post',
        data: {
            model: "deepseek-r1:1.5b",
            prompt: systemPrompt,
            stream: false,
            temperature: 0.1
        },
        headers: {
            'Content-Type': 'application/json'
        }
    })
}

export async function generateStream(userMessage, systemPrompt, onData, onDone, onError) {
    try {
        const response = await fetch('/ai-api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: "deepseek-r1:1.5b",
                prompt: `${systemPrompt}\n用户：${userMessage}`,
                stream: true,
                temperature: 0.1
            })
        });
        const reader = response.body.getReader();
        let fullText = '';
        let decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            let lines = buffer.split('\n');
            buffer = lines.pop(); // 最后一行可能不完整，留到下次
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const json = JSON.parse(line);
                    if (json.response) {
                        fullText += json.response;
                        onData && onData(json.response, fullText);
                    }
                } catch (e) {
                    // 忽略解析失败的行
                }
            }
        }
        onDone && onDone(fullText);
    } catch (err) {
        onError && onError(err);
    }
}