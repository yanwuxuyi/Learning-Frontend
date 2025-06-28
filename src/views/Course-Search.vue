<template>
  <!-- 搜索输入框 -->
  <div class="el-form-item">
    <el-input v-model.trim="keyword" placeholder="关键词搜索或点击右侧图标搜图">
      <template #append>
        <el-button-group>
          <el-button title="以图搜图" :icon="Picture" @click="handleImageSearchClick"/>
          <el-button title="文本搜索" :icon="Search" @click="searchCourse()"/>
        </el-button-group>
      </template>
    </el-input>

    <!-- 隐藏的文件上传输入框 -->
    <input
        ref="imageUploader"
        type="file"
        accept="image/png, image/jpeg, image/gif"
        style="display: none"
        @change="handleImageSelected"
    >
  </div>

  <!-- 课程展示区域 -->
  <el-row v-if="courses && courses.length > 0" :gutter="20">
    <el-col v-for="course in courses" :key="course.id" :xs="24" :sm="6" class="course-card">
      <router-link :to="{ name: 'Course-Content', params: { id: course.id }}">
        <el-card :body-style="{ 'padding': '0px', 'min-height': '275px' }">
          <el-image :src="course.coverPicture" class="card-cover-picture"/>
          <div class="card-text">
            <div class="card-course-name">
              {{ course.name }}
            </div>
          </div>
        </el-card>
      </router-link>
    </el-col>
  </el-row>

  <!-- 空状态显示区域 -->
  <el-empty v-else :description="emptyDescription"/>

  <!-- AI识别区域 (替换原来的推荐课程区域) -->
  <div v-if="showAI" class="ai-section">
    <h3>AI图片识别</h3>
    
    <!-- 图片预览和识别结果 -->
    <div v-if="selectedImage" class="image-preview-section">
      <el-card class="image-preview-card">
        <template #header>
          <div class="card-header">
            <span>上传的图片</span>
            <el-button type="text" @click="clearImage">清除</el-button>
          </div>
        </template>
        <div class="image-container">
          <img :src="selectedImage" alt="上传的图片" class="preview-image"/>
        </div>
        
        <!-- AI识别按钮 -->
        <div class="ai-actions" v-if="!aiResult && !isProcessing">
          <el-button type="primary" @click="recognizeCurrentImage" :disabled="!compressedImageFile">
            使用AI识别图片中的地点
          </el-button>
        </div>
        
        <div v-if="aiResult" class="ai-result">
          <el-alert
            :title="`AI识别结果: ${aiResult}`"
            type="success"
            :closable="false"
            show-icon
          />
          <div class="ai-actions">
            <el-button type="primary" @click="searchByAIResult">使用识别结果搜索</el-button>
            <el-button @click="recognizeCurrentImage" :disabled="!compressedImageFile">重新识别</el-button>
          </div>
        </div>
        <div v-if="isProcessing" class="processing">
          <p>正在识别图片中的地点...</p>
        </div>
      </el-card>
    </div>
    
    <!-- 如果没有图片，显示提示 -->
    <div v-else class="no-image-section">
      <el-empty description="请先使用图片搜索功能上传图片，然后进行AI识别">
        <el-button type="primary" @click="handleImageSearchClick">上传图片</el-button>
      </el-empty>
    </div>
  </div>

  <!-- 分页组件 (仅在文本搜索时显示) -->
  <div v-if="size > 0" class="pagination">
    <el-pagination background layout="prev, pager, next" :pager-count="5" :total="size" :page-size="20"
                   :hide-on-single-page="true" @current-change="handlePageChange">
    </el-pagination>
  </div>
</template>

<script>
import { searchCourse, getCourse } from '../utils/api'
import axios from 'axios'
import { Search, Picture, UploadFilled } from '@element-plus/icons-vue'
// 导入图片压缩库
import imageCompression from 'browser-image-compression';

export default {
  name: 'Course-Search',
  components: {
    Search,
    Picture,
    UploadFilled
  },
  data() {
    return {
      keyword: "",
      courses: [],
      size: 0,
      pageNum: 1,
      Search: Search,
      Picture: Picture,
      emptyDescription: '没有找到相关旅游项目，试试其它关键词或图片吧',
      showAI: false,
      selectedImage: null,
      aiResult: null,
      isProcessing: false,
      compressedImageFile: null
    }
  },
  methods: {
    // 文本搜索功能
    searchCourse() {
      if (this.keyword.trim() === '') return;
      this.emptyDescription = '没有找到相关旅游项目，试试其它关键词或图片吧';
      searchCourse({ keyword: this.keyword, pageNum: this.pageNum - 1 }).then(result => {
        if (result.code === '0000') {
          this.courses = result.data.list;
          this.size = result.data.size;
          if (this.courses.length === 0) {
            this.showAI = true; // 搜索无结果时显示AI识别区域
          } else {
            this.showAI = false; // 有结果时隐藏AI识别区域
          }
        } else {
          this.courses = [];
          this.size = 0;
          this.showAI = true; // 搜索失败时显示AI识别区域
        }
      })
    },

    // 页码变化时触发
    handlePageChange(pageNum) {
      this.pageNum = pageNum;
      this.searchCourse();
    },

    // 点击"以图搜图"时，触发图片上传
    handleImageSearchClick() {
      this.$refs.imageUploader.click();
    },

    // 处理图片选择后的操作
    async handleImageSelected(event) {
      const originalFile = event.target.files[0];
      if (!originalFile) return;

      // 1. 压缩图片
      this.keyword = `正在压缩图片 [${originalFile.name}]...`;
      let compressedFile;
      try {
        compressedFile = await imageCompression(originalFile, {
          maxSizeMB: 1,
          maxWidthOrHeight: 1024,
          useWebWorker: true
        });
        console.log(`图片压缩成功: 从 ${(originalFile.size / 1024 / 1024).toFixed(2)} MB 压缩到 ${(compressedFile.size / 1024 / 1024).toFixed(2)} MB`);
      } catch (error) {
        console.error('图片压缩失败:', error);
        this.$message.error('图片压缩失败，请尝试换一张图片。');
        this.keyword = '';
        this.$refs.imageUploader.value = null;
        return;
      }

      // 2. 保存压缩后的图片用于AI识别
      this.compressedImageFile = compressedFile;
      
      // 3. 使用FileReader将图片转为base64用于预览
      const reader = new FileReader();
      reader.readAsDataURL(compressedFile);
      reader.onload = (e) => {
        this.selectedImage = e.target.result;
      };

      // 4. 使用压缩后的图片进行搜索
      this.courses = [];
      this.size = 0;
      this.emptyDescription = '没有找到相关旅游项目，试试其它关键词或图片吧';
      this.keyword = `正在搜索与 [${compressedFile.name}] 相似的旅游项目...`;

      try {
        console.log('开始发送图片搜索请求到后端...');
        const formData = new FormData();
        formData.append('image', compressedFile);
        
        // 添加请求超时和更详细的错误处理
        const searchResponse = await axios.post('http://localhost:5000/search', formData, {
          timeout: 30000, // 30秒超时
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        console.log('后端响应:', searchResponse.data);

        // 获取相似课程结果
        if (searchResponse.data && Array.isArray(searchResponse.data.results) && searchResponse.data.results.length > 0) {
          console.log(`找到 ${searchResponse.data.results.length} 个相似结果`);
          this.keyword = `找到了与 [${compressedFile.name}] 相似的旅游项目`;
          this.courses = searchResponse.data.results.map(course => ({
            ...course,
            coverPicture: course.cover_picture
          }));
          this.showAI = false; // 有结果时隐藏AI识别区域
          console.log('课程数据已更新:', this.courses);
        } else {
          console.log('没有找到相似结果');
          this.keyword = `没有找到与 [${compressedFile.name}] 相似的旅游项目`;
          this.courses = [];
          this.showAI = true; // 搜索无结果时显示AI识别区域
        }
      } catch (error) {
        console.error('图片搜索过程中发生错误:', error);
        
        // 更详细的错误信息
        if (error.code === 'ECONNREFUSED') {
          this.$message.error('无法连接到后端服务，请确保后端服务已启动在 http://localhost:5000');
          this.keyword = '后端服务未启动，请先启动后端服务';
        } else if (error.code === 'ECONNABORTED') {
          this.$message.error('请求超时，请稍后重试');
          this.keyword = '搜索请求超时';
        } else if (error.response) {
          this.$message.error(`服务器错误: ${error.response.status} - ${error.response.data?.error || '未知错误'}`);
          this.keyword = `服务器错误: ${error.response.status}`;
        } else {
          this.$message.error('网络错误，请检查网络连接');
          this.keyword = '网络连接错误';
        }
        
        this.courses = [];
        this.emptyDescription = '搜索服务出现异常，请稍后再试。';
        this.showAI = true; // 显示AI识别区域作为备选方案
      } finally {
        this.$refs.imageUploader.value = null;
        setTimeout(() => {
          this.keyword = '';
        }, 5000); // 延长显示时间到5秒
      }
    },

    // 清除图片和识别结果
    clearImage() {
      this.selectedImage = null;
      this.aiResult = null;
      this.isProcessing = false;
      this.compressedImageFile = null;
    },

    // 使用AI识别结果搜索
    searchByAIResult() {
      if (!this.aiResult) {
        this.$message.error('请先上传图片并获取识别结果');
        return;
      }
      this.keyword = this.aiResult;
      this.searchCourse();
    },

    // 使用已上传的图片进行AI识别
    recognizeCurrentImage() {
      if (!this.compressedImageFile) {
        this.$message.error('请先上传图片');
        return;
      }
      
      // 重新生成base64用于AI识别
      const reader = new FileReader();
      reader.readAsDataURL(this.compressedImageFile);
      reader.onload = (e) => {
        this.selectedImage = e.target.result;
        this.aiResult = null;
        this.isProcessing = true;
        
        // 调用AI识别
        this.recognizeImage(this.compressedImageFile);
      };
    },

    // AI识别图片
    async recognizeImage(file) {
      try {
        console.log('开始AI识别流程...');
        this.$message.info('正在识别图片中的地点，请耐心等待...');
        
        // 检查Ollama服务是否可用
        console.log('检查Ollama服务状态...');
        try {
          const healthCheck = await axios.get('http://127.0.0.1:11434/api/tags', {
            timeout: 5000
          });
          console.log('Ollama服务可用，可用模型:', healthCheck.data);
          
          // 检查是否有llava模型
          const models = healthCheck.data.models || [];
          const hasLlava = models.some(model => model.name && model.name.includes('llava'));
          if (!hasLlava) {
            this.$message.warning('未找到llava模型，使用备用识别方案');
            this.useFallbackRecognition(file);
            return;
          }
        } catch (healthError) {
          console.error('Ollama服务不可用:', healthError);
          this.$message.warning('Ollama服务不可用，使用备用识别方案');
          this.useFallbackRecognition(file);
          return;
        }
        
        console.log('开始调用AI识别API...');
        
        // 调用AI识别API (这里使用Ollama的视觉模型)
        const response = await axios.post('http://127.0.0.1:11434/api/generate', {
          model: 'llava:7b', // 使用llava视觉模型
          prompt: '请识别这张图片中的地点，只返回地点名称，不要其他描述。',
          images: [this.selectedImage.split(',')[1]], // 去掉base64前缀
          stream: false, // 不使用流式响应
          options: {
            temperature: 0.1, // 降低温度以获得更稳定的结果
            top_p: 0.9,
            num_predict: 50 // 限制输出长度
          }
        }, {
          timeout: 120000, // 增加到2分钟超时
          headers: {
            'Content-Type': 'application/json'
          }
        });

        console.log('AI识别API响应:', response.data);

        if (response.data && response.data.response) {
          this.aiResult = response.data.response.trim();
          console.log('AI识别成功，结果:', this.aiResult);
          this.$message.success(`识别成功: ${this.aiResult}`);
        } else {
          console.log('AI识别响应格式异常:', response.data);
          throw new Error('AI识别失败 - 响应格式异常');
        }
      } catch (error) {
        console.error('AI识别错误:', error);
        
        // 更详细的错误处理
        if (error.code === 'ECONNREFUSED') {
          this.$message.error('无法连接到Ollama服务，使用备用识别方案');
          this.useFallbackRecognition(file);
        } else if (error.code === 'ECONNABORTED') {
          this.$message.warning('AI识别超时，可能是模型加载较慢，使用备用识别方案');
          this.useFallbackRecognition(file);
        } else if (error.response) {
          if (error.response.status === 404) {
            this.$message.warning('llava模型未安装，使用备用识别方案');
            this.useFallbackRecognition(file);
          } else {
            this.$message.error(`AI服务错误: ${error.response.status}，使用备用识别方案`);
            this.useFallbackRecognition(file);
          }
        } else if (error.message.includes('connect')) {
          this.$message.warning('AI服务不可用，使用备用识别方案');
          this.useFallbackRecognition(file);
        } else {
          this.$message.error('图片识别失败，使用备用识别方案');
          this.useFallbackRecognition(file);
        }
      } finally {
        console.log('AI识别流程结束，isProcessing设置为false');
        this.isProcessing = false;
      }
    },

    // 使用备用识别方案
    useFallbackRecognition(file) {
      console.log('使用备用识别方案...');
      
      // 简单的文件名分析
      const fileName = file.name.toLowerCase();
      const commonPlaces = [
        'beijing', 'shanghai', 'guangzhou', 'shenzhen', 'hangzhou', 'suzhou', 'nanjing',
        'xian', 'chengdu', 'chongqing', 'wuhan', 'tianjin', 'qingdao', 'dalian',
        '北京', '上海', '广州', '深圳', '杭州', '苏州', '南京', '西安', '成都', '重庆', '武汉', '天津', '青岛', '大连',
        'mountain', 'sea', 'beach', 'forest', 'park', 'temple', 'museum', 'palace',
        '山', '海', '海滩', '森林', '公园', '寺庙', '博物馆', '宫殿'
      ];
      
      let detectedPlace = null;
      for (const place of commonPlaces) {
        if (fileName.includes(place)) {
          detectedPlace = place;
          break;
        }
      }
      
      if (detectedPlace) {
        this.aiResult = `检测到地点: ${detectedPlace}`;
        this.$message.info(`备用识别结果: ${detectedPlace}`);
      } else {
        this.aiResult = '无法识别地点，请手动输入关键词搜索';
        this.$message.info('无法自动识别，请手动输入搜索关键词');
      }
      
      this.isProcessing = false;
    },
  }
}
</script>

<style scoped>
/* 样式保持不变 */
.el-form-item { margin-bottom: 20px; }
.course-card { margin-bottom: 20px; }
.card-cover-picture { width: 100%; height: 180px; object-fit: cover; display: block; }
.card-text { padding: 14px; }
.card-course-name { font-size: 16px; color: #303133; line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pagination { display: flex; justify-content: center; margin-top: 20px; }

/* 推荐课程的样式 */
.recommended-section {
  margin-top: 30px;
}

/* AI识别区域的样式 */
.ai-section {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.upload-section {
  margin-bottom: 20px;
}

.image-preview-section {
  margin-top: 20px;
}

.image-preview-card {
  max-width: 600px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.image-container {
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  object-fit: cover;
}

.ai-result {
  margin-top: 15px;
}

.ai-actions {
  margin-top: 15px;
  text-align: center;
}

.processing {
  margin-top: 20px;
  text-align: center;
}

.processing p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

/* 没有图片时的样式 */
.no-image-section {
  margin-top: 20px;
  text-align: center;
}
</style>
