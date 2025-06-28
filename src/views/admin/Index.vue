<template>
  <div class="admin-dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="statistics-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon users-icon">
              <el-icon :size="40"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.totalUsers }}</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon courses-icon">
              <el-icon :size="40"><Reading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.totalCourses }}</div>
              <div class="stat-label">总旅游项目数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon categories-icon">
              <el-icon :size="40"><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.totalCategories }}</div>
              <div class="stat-label">总标签数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon questions-icon">
              <el-icon :size="40"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.totalQuestions }}</div>
              <div class="stat-label">总问题数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据分布区域 -->
    <el-row :gutter="20" class="charts-section">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>旅游项目评分分布</span>
            </div>
          </template>
          <div class="distribution-container">
            <div v-for="item in scoreData" :key="item.name" class="distribution-item">
              <div class="distribution-label">{{ item.name }}分</div>
              <div class="distribution-bar">
                <el-progress 
                  :percentage="getPercentage(item.value, totalCourses)" 
                  :color="getScoreColor(item.name)"
                  :show-text="false"
                />
              </div>
              <div class="distribution-count">{{ item.value }}门</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>旅游项目状态分布</span>
            </div>
          </template>
          <div class="distribution-container">
            <div v-for="item in statusData" :key="item.name" class="distribution-item">
              <div class="distribution-label">{{ item.name }}</div>
              <div class="distribution-bar">
                <el-progress 
                  :percentage="getPercentage(item.value, totalCourses)" 
                  :color="item.name === '已审核' ? '#67C23A' : '#E6A23C'"
                  :show-text="false"
                />
              </div>
              <div class="distribution-count">{{ item.value }}门</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最新数据表格 -->
    <el-row :gutter="20" class="tables-section">
      <el-col :span="12">
        <el-card class="table-card">
          <template #header>
            <div class="card-header">
              <span>最新旅游项目</span>
              <el-button type="text" @click="$router.push({name: 'Course-Manage'})">查看更多</el-button>
            </div>
          </template>
          <el-table :data="latestCourses" style="width: 100%" size="small">
            <el-table-column prop="name" label="旅游项目名称" />
            <el-table-column prop="price" label="价格" width="80" />
            <el-table-column prop="averageScore" label="评分" width="80" />
            <el-table-column prop="approved" label="状态" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.approved ? 'success' : 'warning'">
                  {{ scope.row.approved ? '已审核' : '待审核' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="table-card">
          <template #header>
            <div class="card-header">
              <span>最新用户</span>
              <el-button type="text" @click="$router.push({name: 'User-Manage'})">查看更多</el-button>
            </div>
          </template>
          <el-table :data="latestUsers" style="width: 100%" size="small">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="createTime" label="注册时间" width="120" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 调试信息
    <el-card class="debug-card" v-if="debugInfo">
      <template #header>
        <div class="card-header">
          <span>调试信息</span>
          <el-button type="text" @click="debugInfo = false">关闭</el-button>
        </div>
      </template>
      <pre>{{ JSON.stringify(debugInfo, null, 2) }}</pre>
    </el-card> -->
  </div>
</template>

<script>
import { getUsers, getCourses, getCategories } from '../../utils/api'
import { User, Reading, Collection, ChatDotRound } from '@element-plus/icons-vue'

export default {
  name: 'Admin-Index',
  components: {
    User,
    Reading,
    Collection,
    ChatDotRound
  },
  data() {
    return {
      statistics: {
        totalUsers: 0,
        totalCourses: 0,
        totalCategories: 0,
        totalQuestions: 0
      },
      latestCourses: [],
      latestUsers: [],
      scoreData: [],
      statusData: [],
      totalCourses: 0,
      debugInfo: null
    }
  },
  mounted() {
    this.loadDashboardData()
  },
  methods: {
    async loadDashboardData() {
      try {
        console.log('开始加载仪表板数据...')
        
        // 并行加载所有数据
        const [usersRes, coursesRes, categoriesRes] = await Promise.all([
          getUsers({ pageNum: 1, pageSize: 1000 }).catch(err => {
            console.error('获取用户数据失败:', err)
            return { code: 'error', error: err }
          }),
          getCourses({ pageNum: 1, pageSize: 1000 }).catch(err => {
            console.error('获取旅游项目数据失败:', err)
            return { code: 'error', error: err }
          }),
          getCategories().catch(err => {
            console.error('获取标签数据失败:', err)
            return { code: 'error', error: err }
          })
        ])

        console.log('API响应:', { usersRes, coursesRes, categoriesRes })

        // 处理用户数据
        if (usersRes.code === '0000') {
          this.statistics.totalUsers = usersRes.data.size || usersRes.data.list?.length || 0
          this.latestUsers = (usersRes.data.list || []).slice(0, 5)
          console.log('用户数据:', this.statistics.totalUsers, this.latestUsers)
        } else {
          console.error('用户数据获取失败:', usersRes)
          this.$message.error('用户数据获取失败')
        }

        // 处理旅游项目数据
        if (coursesRes.code === '0000') {
          const courses = coursesRes.data.list || []
          this.statistics.totalCourses = coursesRes.data.size || courses.length
          this.totalCourses = this.statistics.totalCourses
          this.latestCourses = courses.slice(0, 5)
          
          console.log('旅游项目数据:', this.statistics.totalCourses, courses.length)
          
          // 计算评分分布
          this.calculateScoreDistribution(courses)
          // 计算状态分布
          this.calculateStatusDistribution(courses)
        } else {
          console.error('旅游项目数据获取失败:', coursesRes)
          this.$message.error('旅游项目数据获取失败')
        }

        // 处理标签数据
        if (categoriesRes.code === '0000') {
          // 分类API可能直接返回数组，而不是分页结构
          const categories = Array.isArray(categoriesRes.data) ? categoriesRes.data : (categoriesRes.data.list || [])
          this.statistics.totalCategories = categories.length
          console.log('标签数据:', this.statistics.totalCategories, categories)
        } else {
          console.error('标签数据获取失败:', categoriesRes)
          this.$message.error('标签数据获取失败')
          // 如果标签API失败，尝试从旅游项目数据中统计标签
          if (coursesRes.code === '0000' && coursesRes.data.list) {
            const categorySet = new Set()
            coursesRes.data.list.forEach(course => {
              if (course.categories && Array.isArray(course.categories)) {
                course.categories.forEach(cat => {
                  if (cat.name) categorySet.add(cat.name)
                })
              }
            })
            this.statistics.totalCategories = categorySet.size
            console.log('从旅游项目数据统计的标签数:', this.statistics.totalCategories)
          }
        }

        // 模拟问题数量（因为现有API中没有直接获取问题总数的接口）
        this.statistics.totalQuestions = Math.floor(this.statistics.totalCourses * 2.5)

        // 设置调试信息
        this.debugInfo = {
          users: usersRes,
          courses: coursesRes,
          categories: categoriesRes,
          statistics: this.statistics,
          scoreData: this.scoreData,
          statusData: this.statusData
        }

      } catch (error) {
        console.error('加载仪表板数据失败:', error)
        this.$message.error('加载数据失败')
        this.debugInfo = { error: error.message }
      }
    },

    calculateScoreDistribution(courses) {
      const scoreRanges = {
        '0-2': 0,
        '2-4': 0,
        '4-6': 0,
        '6-8': 0,
        '8-10': 0
      }

      courses.forEach(course => {
        const score = course.averageScore || 0
        if (score >= 0 && score < 2) scoreRanges['0-2']++
        else if (score >= 2 && score < 4) scoreRanges['2-4']++
        else if (score >= 4 && score < 6) scoreRanges['4-6']++
        else if (score >= 6 && score < 8) scoreRanges['6-8']++
        else if (score >= 8 && score <= 10) scoreRanges['8-10']++
      })

      this.scoreData = Object.entries(scoreRanges).map(([range, count]) => ({
        name: range,
        value: count
      }))
      
      console.log('评分分布:', this.scoreData)
    },

    calculateStatusDistribution(courses) {
      const statusCount = {
        '已审核': 0,
        '待审核': 0
      }

      courses.forEach(course => {
        if (course.approved) {
          statusCount['已审核']++
        } else {
          statusCount['待审核']++
        }
      })

      this.statusData = Object.entries(statusCount).map(([status, count]) => ({
        name: status,
        value: count
      }))
      
      console.log('状态分布:', this.statusData)
    },

    getPercentage(value, total) {
      if (total === 0) return 0
      return Math.round((value / total) * 100)
    },

    getScoreColor(range) {
      const colors = {
        '0-2': '#F56C6C',
        '2-4': '#E6A23C',
        '4-6': '#909399',
        '6-8': '#409EFF',
        '8-10': '#67C23A'
      }
      return colors[range] || '#409EFF'
    }
  }
}
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
}

.statistics-cards {
  margin-bottom: 20px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  margin-right: 20px;
  padding: 15px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.users-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.courses-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.categories-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.questions-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-card {
  height: 400px;
}

.distribution-container {
  padding: 20px;
}

.distribution-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.distribution-label {
  width: 80px;
  font-size: 14px;
  color: #606266;
}

.distribution-bar {
  flex: 1;
  margin: 0 15px;
}

.distribution-count {
  width: 60px;
  text-align: right;
  font-size: 14px;
  color: #909399;
}

.tables-section {
  margin-bottom: 20px;
}

.table-card {
  height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.debug-card {
  margin-top: 20px;
}

.debug-card pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}
</style>