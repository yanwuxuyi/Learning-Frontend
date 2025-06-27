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

export async function generateStream(fullPrompt, onData, onDone, onError) {
    try {
        const response = await fetch('/ai-api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: "deepseek-r1:1.5b",
                prompt: fullPrompt,
                stream: true,
                temperature: 0.1
            })
        });

        if (!response.ok) {
            throw new Error(`AI service request failed with status ${response.status}`);
        }

        const reader = response.body.getReader();
        let fullText = '';
        let decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 最后一行可能不完整，留到下次
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const json = JSON.parse(line);
                    if (json.response) {
                        fullText += json.response;
                        onData && onData(fullText);
                    }
                } catch (e) {
                    console.error("Failed to parse stream line:", line, e);
                }
            }
        }
        
        // 当数据流结束后，处理可能残留在缓冲区中的最后一部分数据
        if (buffer.trim()) {
            try {
                const json = JSON.parse(buffer);
                if (json.response) {
                    fullText += json.response;
                    onData && onData(fullText);
                }
            } catch (e) {
                console.error("Failed to parse final stream buffer:", buffer, e);
            }
        }
        
        // 最终，确认所有数据处理完毕，正确调用 onDone 回调
        onDone && onDone();

    } catch (err) {
        onError && onError(err);
    }
}

export async function generateStreamForPrice(payload, onData, onDone, onError) {
    try {
        const response = await fetch('/api/price_suggestion_stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`AI service request failed with status ${response.status}`);
        }

        const reader = response.body.getReader();
        let fullText = '';
        let decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const json = JSON.parse(line);
                    if (json.response) {
                        fullText += json.response;
                        onData && onData(fullText);
                    }
                } catch (e) {
                    // 不是JSON就直接拼接
                    fullText += line;
                    onData && onData(fullText);
                }
            }
        }
        if (buffer.trim()) {
            try {
                const json = JSON.parse(buffer);
                if (json.response) {
                    fullText += json.response;
                    onData && onData(fullText);
                }
            } catch (e) {
                fullText += buffer;
                onData && onData(fullText);
            }
        }
        onDone && onDone();
    } catch (err) {
        onError && onError(err);
    }
}