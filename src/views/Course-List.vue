<template>
    <div class="flex-between mb-1">
        <el-radio-group v-model="orderBy" size="small" @change="handleOrderChange">
            <el-radio-button label="create_time">最新</el-radio-button>
            <el-radio-button label="average_score">推荐</el-radio-button>
        </el-radio-group>
        <el-pagination :page-size="20" layout="sizes" @size-change="handleSizeChange" />
    </div>
    <el-tabs>
        <el-tab-pane label="全部">
            <el-button size="small" @click="handleCategoryChange()">
                全部
            </el-button>
        </el-tab-pane>
        <el-tab-pane v-for="category in categories" :label="category.name">
            <el-button size="small" v-for="child in category.children" @click="handleCategoryChange(child.id)">
                {{ child.name }}
            </el-button>
        </el-tab-pane>
    </el-tabs>
    <el-row :gutter="20">
        <el-col v-for="course in courses" :xs="24" :sm="6" class="course-card">
            <router-link :to="{ name: 'Course-Content', params: { id: course.id } }">
                <el-card :body-style="{ 'padding': '0px', 'min-height': '300px' }">
                    <el-image :src="course.coverPicture" class="card-cover-picture" />
                    <div class="card-text">
                        <div class="card-course-name">
                            {{ course.name }}
                        </div>
                        <div class="card-course-price" v-if="course.price !== 0">
                            ￥{{ course.price }}
                        </div>
                        <div class="card-course-price free" v-else>
                            免费
                        </div>
                    </div>
                </el-card>
            </router-link>
        </el-col>
    </el-row>
    <div class="pagination">
        <el-pagination background layout="prev, pager, next" :pager-count="5" :total="size" :page-size="20"
            :hide-on-single-page="true" @current-change="handlePageChange">
        </el-pagination>
    </div>
</template>

<script>

// 1. 修改 import 语句：将 getCourseById 替换为 getCourse
import { getCategories, getCourses, getCourse } from '../utils/api'
import { buildTree } from '../utils/processing'

export default {
  name: "Course-List",
  data() {
    return {
      categories: [],
      courses: [],
      size: 0,
      categoryId: null,
      pageNum: null,
      pageSize: 20,
      orderBy: 'create_time'
    }
  },
  created() {
    this.getCategories()
    this.getCourses()
  },
  methods: {
    // ... getCategories, getCourses, getStandardCourses 方法保持不变 ...
    getCategories() {
      getCategories().then(result => {
        if (result.code === '0000') {
          this.categories = buildTree(result.data)
        }
      })
    },

    getCourses() {
      if (this.orderBy === 'average_score') {
        this.getRecommendedCourses();
      } else {
        this.getStandardCourses();
      }
    },

    getStandardCourses() {
      getCourses({
        pageSize: this.pageSize,
        pageNum: this.pageNum,
        orderBy: this.orderBy,
        categoryId: this.categoryId
      }).then(result => {
        if (result.code === '0000') {
          this.courses = result.data.list
          this.size = result.data.size
        }
      })
    },

    // 2. 修改 getRecommendedCourses 方法中的函数调用
    async getRecommendedCourses() {
      const recommendedIdsRaw = localStorage.getItem('user_recommendations');

      if (!recommendedIdsRaw) {
        this.courses = [];
        this.size = 0;
        console.warn("localStorage 中没有找到 'user_recommendations'。");
        return;
      }

      try {
        const recommendedIds = JSON.parse(recommendedIdsRaw);
        if (!Array.isArray(recommendedIds) || recommendedIds.length === 0) {
          this.courses = [];
          this.size = 0;
          return;
        }

        // 使用您 api.js 中已有的 getCourse 函数
        // 每个 id 会作为 pathVariable 传入
        const coursePromises = recommendedIds.map(id => getCourse(id));

        const results = await Promise.all(coursePromises);

        const recommendedCourses = results
            .filter(result => result && result.code === '0000' && result.data)
            .map(result => result.data);

        this.courses = recommendedCourses;
        this.size = recommendedCourses.length;

      } catch (error) {
        console.error("解析或获取推荐课程失败:", error);
        this.courses = [];
        this.size = 0;
      }
    },

    // ... handleCategoryChange, handleOrderChange, handleSizeChange, handlePageChange 方法保持不变 ...
    handleCategoryChange(categoryId) {
      this.categoryId = categoryId;
      this.orderBy = 'create_time';
      this.getCourses();
    },

    handleOrderChange(orderBy) {
      this.orderBy = orderBy;
      this.pageNum = 1;
      this.categoryId = null;
      this.getCourses();
    },

    handleSizeChange(pageSize) {
      this.pageSize = pageSize
      this.getCourses()
    },

    handlePageChange(pageNum) {
      this.pageNum = pageNum
      this.getCourses()
    }
  }
}
</script>

<style>
.course-card {
    margin-top: 20px;
}

.card-text {
    margin: 10px;
}

.card-cover-picture {
    height: 200px;
    width: 100%;
}

.card-course-price {
    font-size: 14px;
    color: #f56c6c;
    margin-top: 10px;
}

.card-course-price.free {
    color: #67C23A;
}
</style>