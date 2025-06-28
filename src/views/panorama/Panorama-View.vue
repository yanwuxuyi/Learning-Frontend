<!-- src/views/panorama/Panorama-View.vue -->
<template>
  <div class="panorama-container">
    <!-- A-Frame 场景将在这里构建 -->
    <!-- 我们使用 v-if="panoramaUrl" 来确保在URL获取到之后才渲染场景 -->
    <a-scene v-if="panoramaUrl" embedded>
      <a-sky :src="panoramaUrl" rotation="0 -90 0"></a-sky>
    </a-scene>

    <!-- 加载和错误状态显示 -->
    <div v-if="isLoading" class="status-overlay">
      <p>正在加载全景资源...</p>
    </div>
    <div v-if="error" class="status-overlay">
      <p>错误: {{ error }}</p>
      <el-button @click="$router.back()" type="primary" round>返回</el-button>
    </div>
  </div>
</template>

<script>
import { getVrProfileByName } from '../../utils/api'; // 确保这个API函数存在

export default {
  name: 'Panorama-View',
  data() {
    return {
      courseName: this.$route.query.name || '',
      panoramaUrl: null, // 用于存储全景图片的URL
      isLoading: true,
      error: null,
    };
  },
  mounted() {
    // 动态加载 A-Frame 脚本
    this.loadAFrameScript().then(() => {
      // 脚本加载成功后，获取全景图数据
      this.fetchPanoramaData();
    }).catch(err => {
      this.isLoading = false;
      this.error = "无法加载A-Frame框架，请检查网络连接。";
      console.error(err);
    });
  },
  methods: {
    loadAFrameScript() {
      return new Promise((resolve, reject) => {
        // 如果脚本已经存在，则直接成功
        if (window.AFRAME) {
          resolve();
          return;
        }
        const script = document.createElement('script');
        script.src = 'https://aframe.io/releases/1.3.0/aframe.min.js'; // 使用较新版本
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    },
    async fetchPanoramaData() {
      if (!this.courseName) {
        this.isLoading = false;
        this.error = "未提供项目名称。";
        return;
      }

      try {
        const response = await getVrProfileByName({ name: this.courseName });

        // 同样，假设Python后端返回的数据结构是 { profile_picture: 'http://...' }
        if (response && response.data.profile_picture) {
          this.panoramaUrl = response.data.profile_picture;
        } else {
          this.error = `未找到名为“${this.courseName}”的全景资源。`;
        }
      } catch (err) {
        this.error = "加载全景资源失败，请稍后再试。";
        console.error("加载全景图失败:", err);
      } finally {
        this.isLoading = false;
      }
    },
  },
};
</script>

<style scoped>
.panorama-container {
  width: 100vw;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
  background-color: #000;
}

/* a-scene默认不是100%宽高，需要设置 */
a-scene {
  height: 100%;
  width: 100%;
}

.status-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 24px;
  text-align: center;
  z-index: 10;
}
.status-overlay p {
  margin-bottom: 20px;
}
</style>