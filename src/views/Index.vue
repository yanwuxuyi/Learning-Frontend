<template>
    <div class="text-center recommend-title">
        推荐旅游项目
    </div>
    <el-carousel ref="carousel" type="card" height="400px" arrow="always" autoplay>
        <el-carousel-item v-for="course in carousel" :key="course.id">
            <router-link :to="{ name: 'Course-Content', params: { id: course.id } }">
                <el-image :src="course.coverPicture" class="carousel-picture" lazy
                    :preview-src-list="[course.coverPicture]" :fit="'cover'">
                    <template #placeholder>
                        <div class="image-placeholder">加载中...</div>
                    </template>
                </el-image>
            </router-link>
        </el-carousel-item>
    </el-carousel>


    <BarCard style="margin-top: 30px;"
        imgSrc="https://dynamic-media-cdn.tripadvisor.com/media/photo-o/08/48/2f/eb/mahamrityunjay-temple.jpg?w=300&h=300&s=1"
        title="Discover Darwin" description="Find out why travelers like you are raving about Darwin"
        cardColor="#dfd3ee" buttonContent="Explore now" />

    <el-tabs class="category-list">
        <el-tab-pane label="全部">
            <el-button size="small" @click="onChangeCategory()">
                全部
            </el-button>
        </el-tab-pane>
        <el-tab-pane v-for="category in categories" :label="category.name">
            <el-button size="small" v-for="child in category.children" @click="onChangeCategory(child.id)">
                {{ child.name }}
            </el-button>
        </el-tab-pane>
    </el-tabs>

    <el-row :gutter="20" justify="start">
        <template v-if="courses.length">
            <el-col v-for="course in courses" :key="course.id" :xs="24" :sm="6" class="course-card">
                <router-link :to="{ name: 'Course-Content', params: { id: course.id } }">
                    <el-card :body-style="{ padding: '0px', minHeight: '350px' }" class="course-card-item">
                        <el-image :src="course.coverPicture" class="card-cover-picture" lazy>
                            <template #placeholder>
                                <div class="image-placeholder">加载中...</div>
                            </template>
                        </el-image>
                        <div class="card-text">
                            <div class="card-course-name">{{ course.name }}</div>
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
        </template>
        <template v-else>
            <div class="empty-container">
                <el-empty description="暂无相关项目" />
            </div>
        </template>
    </el-row>
</template>

<script>
import { getCategories, getCourses } from '../utils/api'
import { buildTree } from '../utils/processing'
import BarCard from '../components/BarCard.vue'

export default {
    name: 'Index',
    components: {
        BarCard,  // 确保 BarCard 被正确注册
    },
    data() {
        return {
            value: 0,
            categories: [],
            courses: [],
            carousel: [],
            selectedCategoryId: null
        }
    },
    created() {
        this.getCategories()
        this.getCourses()
    },
    methods: {
        getCategories() {
            getCategories().then(result => {
                this.categories = buildTree(result.data)
            })
        },
        getCourses(categoryId) {
            getCourses({ pageSize: 8, categoryId, orderBy: 'average_score' }).then(result => {
                if (result.code === '0000') {
                    this.courses = result.data.list
                    if (this.carousel.length === 0) {
                        this.carousel = this.courses.slice(0, 5)
                        this.$nextTick(() => {
                            if (this.$refs['carousel']) {
                                this.$refs['carousel'].setActiveItem(0)
                            }
                        })
                    }
                }
            })
        },
        onChangeCategory(categoryId) {
            this.selectedCategoryId = categoryId || null
            this.getCourses(categoryId)
        }
    }
}
</script>

<style scoped>
.carousel-picture {
    height: 100%;
    width: 100%;
    object-fit: cover;
    border-radius: 10px;
}

.image-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #bbb;
    font-size: 16px;
    background: #f5f7fa;
}

.recommend-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 30px;
    color: #333;
}

.course-card-item {
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.course-card-item:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
}

.card-cover-picture {
    width: 100%;
    height: 200px;
    object-fit: cover;
}

.card-text {
    padding: 10px;
    text-align: center;
}

.card-course-name {
    font-size: 16px;
    font-weight: bold;
    color: #333;
}

.card-course-price {
    font-size: 14px;
    color: #e44d26;
    margin-top: 10px;
}

.card-course-price.free {
    color: #52c41a;
    font-weight: bold;
}

.category-list {
    margin-top: 30px;
}

.tab-button:hover {
    background-color: #409eff;
    color: white;
    transform: scale(1.05);
}

.tab-button:focus {
    outline: none;
}

.empty-container {
    display: flex;
    justify-content: center;
    /* 水平居中 */
    align-items: center;
    /* 垂直居中 */
    height: 300px;
    /* 高度设为你需要的值 */
    width: 100%;
    /* 使容器占满父元素的宽度 */
}
</style>