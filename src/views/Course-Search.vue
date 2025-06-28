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

  <!-- 推荐课程区域 (只有在图像搜索没有结果时才显示) -->
  <div v-if="showRecommended" class="recommended-section">
    <h3>推荐的旅游项目</h3>
    <el-row :gutter="20">
      <el-col v-for="course in recommendedCourses" :key="course.id" :xs="24" :sm="6" class="course-card">
        <router-link :to="{ name: 'Course-Content', params: { id: course.id } }">
          <el-card :body-style="{ 'padding': '0px', 'min-height': '300px' }">
            <el-image :src="course.coverPicture" class="card-cover-picture"/>
            <div class="card-text">
              <div class="card-course-name">{{ course.name }}</div>
              <div class="card-course-price" v-if="course.price !== 0">
                ￥{{ course.price }}
              </div>
              <div class="card-course-price free" v-else>免费</div>
            </div>
          </el-card>
        </router-link>
      </el-col>
    </el-row>
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
import { Search, Picture } from '@element-plus/icons-vue'
// 导入图片压缩库
import imageCompression from 'browser-image-compression';

export default {
  name: 'Course-Search',
  components: {
    Search,
    Picture
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
      recommendedCourses: [], // 存放推荐的课程
      showRecommended: false // 控制推荐课程的显示
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
            this.fetchRecommendedCourses(); // 搜索无结果时加载推荐课程
            this.showRecommended = true; // 显示推荐课程区域
          } else {
            this.showRecommended = false; // 隐藏推荐课程区域
          }
        } else {
          this.courses = [];
          this.size = 0;
          this.showRecommended = false; // 隐藏推荐课程区域
        }
      })
    },

    // 页码变化时触发
    handlePageChange(pageNum) {
      this.pageNum = pageNum;
      this.searchCourse();
    },

    // 点击“以图搜图”时，触发图片上传
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

      // 2. 使用压缩后的图片进行搜索
      this.courses = [];
      this.size = 0;
      this.emptyDescription = '没有找到相关旅游项目，试试其它关键词或图片吧';
      this.keyword = `正在搜索与 [${compressedFile.name}] 相似的旅游项目...`;

      try {
        const formData = new FormData();
        formData.append('image', compressedFile);
        const searchResponse = await axios.post('http://localhost:5001/search', formData);

        // 获取相似课程结果
        if (searchResponse.data && Array.isArray(searchResponse.data.results) && searchResponse.data.results.length > 0) {
          this.keyword = `找到了与 [${compressedFile.name}] 相似的旅游项目`;
          this.courses = searchResponse.data.results.map(course => ({
            ...course,
            coverPicture: course.cover_picture
          }));
          this.showRecommended = false; // 隐藏推荐课程区域
        } else {
          this.keyword = `没有找到与 [${compressedFile.name}] 相似的旅游项目`;
          this.courses = [];
          this.fetchRecommendedCourses(); // 搜索无结果时加载推荐课程
          this.showRecommended = true; // 显示推荐课程区域
        }
      } catch (error) {
        console.error('图片搜索过程中发生错误:', error);
        this.$message.error('服务出现问题，请稍后再试。');
        this.courses = [];
        this.emptyDescription = '搜索服务出现异常，请稍后再试。';
      } finally {
        this.$refs.imageUploader.value = null;
        setTimeout(() => {
          this.keyword = '';
        }, 3000);
      }
    },

    // 从 localStorage 获取推荐课程并加载
    fetchRecommendedCourses() {
      const recommendedIdsRaw = localStorage.getItem('user_recommendations');
      if (!recommendedIdsRaw) {
        this.recommendedCourses = [];
        return;
      }

      try {
        const recommendedIds = JSON.parse(recommendedIdsRaw);
        if (!Array.isArray(recommendedIds) || recommendedIds.length === 0) {
          this.recommendedCourses = [];
          return;
        }

        // 使用您 api.js 中已有的 getCourse 函数
        const coursePromises = recommendedIds.map(id => getCourse(id));

        Promise.all(coursePromises).then(results => {
          this.recommendedCourses = results
              .filter(result => result && result.code === '0000' && result.data)
              .map(result => result.data);
        });

      } catch (error) {
        console.error('解析或获取推荐课程失败:', error);
        this.recommendedCourses = [];
      }
    }
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
</style>
