<template>
  <el-form :model="course" :rules="rules" ref="course" label-width="80px">
    <el-form-item prop="name" label="名称">
      <el-input type="text" v-model="course.name" maxlength="100" show-word-limit/>
    </el-form-item>
    <el-form-item prop="description" label="简介">
      <el-input type="textarea" v-model="course.description" :autosize="{minRows: 2}"
                maxlength="500" show-word-limit/>
    </el-form-item>
    <el-form-item prop="price" label="价格">
      <el-input-number v-model="course.price" :precision="2" :step="0.1" :min="0" style="width: 200px;"/>
      <el-button @click="getSmartPriceStream" :loading="loadingPrice" type="primary" style="margin-left:10px;">
        智能价格建议
      </el-button>
    </el-form-item>
    <div class="ai-reply-bubble-area">
      <div v-for="(msg, idx) in aiMessages" :key="idx" class="ai-bubble ai">
        <img class="bubble-avatar" src="/pet01.jpg" alt="AI"/>
        <div class="bubble">{{ msg }}</div>
      </div>
      <div v-if="aiReply" class="ai-bubble ai">
        <img class="bubble-avatar" src="/pet01.jpg" alt="AI"/>
        <div class="bubble">{{ aiReply }}</div>
      </div>
    </div>
    <el-form-item prop="categories" label="标签">
      <el-select v-model="course.categories" value-key="id" multiple>
        <el-option-group v-for="parent in categories" :label="parent.name">
          <el-option v-for="child in parent.children" :label="child.name" :value="child">
          </el-option>
        </el-option-group>
      </el-select>
    </el-form-item>
    <el-form-item v-if="includeStatus" label="审核通过">
      <el-switch v-model="course.approved" active-color="#13CE66" inactive-color="#FF4949"/>
    </el-form-item>
    <el-form-item prop="coverPicture" label="封面图片">
      <el-upload class="cover-picture-uploader" action="" :show-file-list="false"
                 :http-request="uploadCoverPicture">
        <img v-if="course.coverPicture" :src="course.coverPicture" class="form-cover-picture" alt="封面">
        <el-icon v-else class="picture-uploader-icon">
          <plus/>
        </el-icon>
      </el-upload>
    </el-form-item>

    <!-- 全景照片上传 (v-if 控制显示) -->
    <el-form-item v-if="showPanoramaUpload" prop="panoramaPicture" label="全景照片">
      <el-upload class="cover-picture-uploader" action="" :show-file-list="false"
                 :http-request="handlePanoramaUpload">
        <img v-if="panoramaPictureUrl" :src="panoramaPictureUrl" class="form-cover-picture" alt="全景照片预览">
        <el-icon v-else class="picture-uploader-icon">
          <plus/>
        </el-icon>
      </el-upload>
    </el-form-item>

    <el-form-item class="text-right">
      <el-button size="small" @click="onSubmit('course')" type="primary" :loading="loading">
        确认
      </el-button>
      <el-button v-if="editMode" size="small" @click="onCancel">
        取消
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script>
// --- 合并后的 import ---
// 包含了向量数据库、全景图功能和原有功能的所有API
import {
  createCourse,
  getCategories,
  updateCourse,
  uploadCoverPicture,
  updateCourseInVectorDBxu, // 来自远程仓库
  uploadVrProfile,        // 来自你的本地修改
  getVrProfileByName      // 来自你的本地修改
} from '../utils/api';

import {buildTree} from '../utils/processing'
import { generateStreamForPrice } from '../utils/ai.js'
// import axios from 'axios' // axios已在api.js中使用，这里通常不需要再导入

export default {
  name: "Course-Form",
  // --- 合并后的 props ---
  props: {
    course: { type: Object, required: true },
    editMode: String,
    includeStatus: Boolean,
    separatePage: Boolean,
    showPanoramaUpload: { // 来自你的本地修改
      type: Boolean,
      default: true
    }
  },
  // --- 合并后的 data ---
  data() {
    return {
      categories: [],
      loading: false,
      loadingPrice: false,
      aiReply: "",
      aiMessages: [],
      panoramaFile: null,         // 来自你的本地修改
      panoramaPictureUrl: '',     // 来自你的本地修改
      rules: {
        name: [
          {required: true, message: '请输入名称', trigger: 'blur'},
          {min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur'}
        ],
        description: [
          {required: true, message: '请输入简介', trigger: 'blur'},
          {min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur'}
        ],
        price: [
          {required: true, message: '请选择价格', trigger: 'change'}
        ],
        categories: [
          {type: 'array', required: true, message: '请选择标签', trigger: 'change'}
        ],
        coverPicture: [
          {required: true, message: '请上传封面图片', trigger: 'change'}
        ]
      }
    }
  },
  // --- 合并后的 watch ---
  watch: {
    course: {
      handler(newCourse) {
        if (newCourse && newCourse.name && this.editMode === 'update' && this.showPanoramaUpload) {
          this.fetchExistingPanorama(newCourse.name);
        }
      },
      deep: true,
      immediate: true
    }
  },
  created() {
    this.getCategories()
  },
  // --- 合并后的 methods ---
  methods: {
    getCategories() {
      getCategories().then(result => {
        if (result.code === '0000') {
          this.categories = buildTree(result.data)
        }
      })
    },
    uploadCoverPicture(params) {
      let formData = new FormData()
      formData.append('multipartFile', params.file)
      uploadCoverPicture(formData).then(result => {
        if (result.code === '0000') {
          this.$message.success('上传成功！')
          this.course.coverPicture = result.data
          this.$refs['course'].clearValidate('coverPicture')
        }
      })
    },
    // --- 以下是全景图相关的方法 (来自你的本地修改) ---
    async fetchExistingPanorama(courseName) {
      try {
        const response = await getVrProfileByName({ name: courseName });
        if (response && response.data && response.data.profile_picture) {
          this.panoramaPictureUrl = response.data.profile_picture;
        } else {
          this.panoramaPictureUrl = '';
        }
      } catch (error) {
        if (error.response && error.response.status === 404) {
          console.log(`课程 "${courseName}" 没有关联的全景图。`);
        } else {
          console.error("查询全景图时发生错误:", error);
        }
        this.panoramaPictureUrl = '';
      }
    },
    handlePanoramaUpload(params) {
      this.panoramaFile = params.file;
      this.panoramaPictureUrl = URL.createObjectURL(params.file);
    },
    uploadVrProfile() {
      if (!this.panoramaFile) {
        return;
      }
      const formData = new FormData();
      formData.append('name', this.course.name);
      formData.append('profile_picture', this.panoramaFile);
      uploadVrProfile(formData).then(response => {
        if (response.data && response.data.status === 'success') {
          this.$message.success('全景照片已成功同步！');
        } else {
          const errorMsg = response.data.error || '未知错误';
          this.$message.error(`全景照片同步失败: ${errorMsg}`);
        }
      }).catch(error => {
        console.error("上传VR资料失败:", error);
        this.$message.error('上传全景照片到VR服务时发生网络错误。');
      });
    },
    // --- 合并后的 onSubmit 方法 ---
    onSubmit(user) {
      this.$refs[user].validate((valid) => {
        if (valid) {
          this.loading = true
          if (this.editMode === 'create') {
            createCourse(this.course).then(result => {
              if (result.code === '0000') {
                this.course.id = result.data.id
                this.$message.success("新增成功！")
                this.uploadVrProfile(); // 上传全景图
                this.$emit('submit-success', this.course);
                this.$nextTick(() => { // 使用$nextTick保证安全重置
                  this.$refs[user].resetFields();
                  this.panoramaFile = null;
                  this.panoramaPictureUrl = '';
                });
              }
            }).finally(() => this.loading = false)
          }
          if (this.editMode === 'update') {
            updateCourse(this.course).then(result => {
              if (result.code === '0000') {
                this.$message.success('更新成功！')
                // 同时调用两个异步更新
                this.uploadVrProfile(); // 更新全景图
                this.syncVectorDB();   // 更新向量数据库
              }
            }).finally(() => this.loading = false)
          }
        }
      })
    },
    // --- 新增: 抽离出向量数据库同步逻辑 (来自远程仓库) ---
    syncVectorDB() {
      updateCourseInVectorDBxu(this.course)
          .then(res => res.json())
          .then(data => {
            if (data.message) {
              this.$message.success('课程已成功同步更新到AI知识库！');
            } else {
              this.$message.error(data.error || '同步更新到AI知识库失败。');
            }
          })
          .catch(err => {
            console.error("同步更新到向量数据库时出错:", err);
            this.$message.error('同步更新到AI知识库时网络错误。');
          });
    },

    onCancel() {
      if (this.separatePage) {
        this.$router.back()
      } else {
        this.$emit('cancel')
      }
    },
    async getSmartPriceStream() {
      // ... (此方法保持不变)
      if (!this.course.name) {
        this.$message.warning('请先填写名称');
        return;
      }
      const rating = this.course.user_rating || 4.5;
      const product_name = this.course.name;
      const current_price = this.course.price;
      this.loadingPrice = true;
      this.aiReply = "";
      try {
        await generateStreamForPrice(
            { rating, product_name, current_price },
            (fullText) => {
              let cleanText = fullText.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
              this.aiReply = cleanText;
              this.$forceUpdate();
            },
            () => {
              const match = this.aiReply.match(/\d+\.?\d*/);
              if (match) {
                this.course.price = parseFloat(match[0]);
                this.$message.success('已获取智能建议价格');
              } else {
                this.$message.error('未获取到建议价格');
              }
              if (this.aiReply) {
                this.aiMessages.push(this.aiReply);
              }
              this.aiReply = "";
              this.loadingPrice = false;
            },
            (err) => {
              this.$message.error('获取智能价格失败');
              this.loadingPrice = false;
            }
        );
      } catch (e) {
        this.$message.error('获取智能价格失败');
        this.loadingPrice = false;
      }
    }
  }
}
</script>

<style>
.form-cover-picture {
  width: 350px;
  height: 200px;
  display: block;
  object-fit: cover; /* 让图片不变形地填充容器 */
}

/* 确保两个上传组件样式一致 */
.is-error .cover-picture-uploader > .el-upload {
  border: 1px dashed #F56C6C;
}

.cover-picture-uploader .el-upload {
  border-radius: 6px;
  border: 1px dashed #D9D9D9;
  cursor: pointer; /* ========== 新增：鼠标指针样式 ========== */
  overflow: hidden; /* ========== 新增：隐藏超出边框的内容 ========== */
  position: relative; /* ========== 新增：用于定位icon ========== */
}
.cover-picture-uploader .el-upload:hover {
  border-color: #409EFF; /* ========== 新增：悬浮高亮 ========== */
}

.cover-picture-uploader .el-icon-plus, /* ========== 修改：合并选择器 ========== */
.picture-uploader-icon {
  font-size: 32px;
  color: #8c939d;
  width: 350px;  /* ========== 修改：与图片宽度一致 ========== */
  height: 200px; /* ========== 修改：与图片高度一致 ========== */
  line-height: 200px; /* ========== 修改：垂直居中 ========== */
  text-align: center; /* ========== 新增：水平居中 ========== */
}

/* ... (保留AI气泡等其他样式) ... */
.ai-reply-bubble-area {
  margin: 20px 0 0 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.ai-bubble {
  display: flex;
  align-items: flex-end;
  margin-bottom: 10px;
}
.bubble {
  padding: 12px 18px;
  border-radius: 18px;
  max-width: 90%;
  font-size: 15px;
  line-height: 1.7;
  box-shadow: 0 2px 12px rgba(255, 193, 7, 0.10);
  word-break: break-all;
  position: relative;
  background: #fff;
  color: #b28704;
  border: 1.5px solid #ffe082;
  margin-left: 8px;
}
.bubble-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #fff;
  border: 1.5px solid #ffe082;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.10);
  object-fit: cover;
}
</style>