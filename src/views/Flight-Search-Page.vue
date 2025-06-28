<template>
  <div class="flight-search-page">
    <div class="page-header">
      <h1>机票搜索</h1>
      <p>搜索最优惠的机票价格，开启您的旅行之旅</p>
    </div>
    
    <div class="search-container">
      <Flight-Search ref="flightSearch" />
    </div>
    
    <!-- 旅行贴士和搜索建议 -->
    <div class="travel-tips">
      <h2>旅行贴士</h2>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="tip in travelTips" :key="tip.id">
          <el-card class="tip-card">
            <div class="tip-icon">
              <el-icon :size="32" :color="tip.color">
                <component :is="tip.icon" />
              </el-icon>
            </div>
            <div class="tip-content">
              <h3>{{ tip.title }}</h3>
              <p>{{ tip.description }}</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script>
import FlightSearch from '../components/Flight-Search.vue'
import { 
  Clock, 
  Calendar, 
  Location, 
  InfoFilled, 
  Star, 
  Wallet 
} from '@element-plus/icons-vue'

export default {
  name: 'Flight-Search-Page',
  components: {
    FlightSearch,
    Clock,
    Calendar,
    Location,
    InfoFilled,
    Star,
    Wallet
  },
  data() {
    return {
      travelTips: [
        { 
          id: 1, 
          icon: 'Clock', 
          color: '#409EFF', 
          title: '最佳预订时间', 
          description: '提前2-3周预订机票通常能获得更优惠的价格' 
        },
        { 
          id: 2, 
          icon: 'Calendar', 
          color: '#67C23A', 
          title: '灵活出行日期', 
          description: '避开周末和节假日出行，价格往往更便宜' 
        },
        { 
          id: 3, 
          icon: 'Location', 
          color: '#E6A23C', 
          title: '机场选择', 
          description: '考虑周边机场，有时能节省不少费用' 
        },
        { 
          id: 4, 
          icon: 'InfoFilled', 
          color: '#F56C6C', 
          title: '行李限制', 
          description: '注意各航空公司的行李重量和尺寸限制' 
        },
        { 
          id: 5, 
          icon: 'Star', 
          color: '#909399', 
          title: '会员优惠', 
          description: '注册航空公司会员可享受积分和优惠' 
        },
        { 
          id: 6, 
          icon: 'Wallet', 
          color: '#9C27B0', 
          title: '价格比较', 
          description: '建议比较多个航空公司的价格后再做选择' 
        }
      ]
    }
  },
  methods: {
    // 移除热门航线搜索方法
  }
}
</script>

<style scoped>
.flight-search-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 32px;
  color: #303133;
  margin-bottom: 10px;
}

.page-header p {
  font-size: 16px;
  color: #606266;
}

.search-container {
  margin-bottom: 50px;
}

.travel-tips {
  margin-top: 50px;
}

.travel-tips h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 20px;
  text-align: center;
}

.tip-card {
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;
  height: 180px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.tip-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.tip-icon {
  text-align: center;
  margin-bottom: 15px;
}

.tip-content {
  text-align: center;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.tip-content h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 8px;
  font-weight: 600;
}

.tip-content p {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .flight-search-page {
    padding: 10px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .tip-content {
    text-align: left;
  }
}

.flight-search-container {
  margin-bottom: 20px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.flight-card {
  margin-bottom: 20px;
  width: 100%;
  max-width: 800px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-card {
  margin-top: 20px;
  width: 100%;
  max-width: 800px;
}

.result-count {
  font-size: 14px;
  color: #666;
}

.price {
  color: #f56c6c;
  font-weight: bold;
  font-size: 16px;
}

.no-results {
  margin-top: 20px;
  text-align: center;
}

.flight-results {
  margin-top: 20px;
  width: 100%;
  display: flex;
  justify-content: center;
}
</style> 