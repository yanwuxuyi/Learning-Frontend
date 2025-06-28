<template>
  <div class="flight-search-container">
    <el-card class="flight-card">
      <template #header>
        <div class="card-header">
          <span>机票搜索</span>
          <el-button type="text" @click="clearForm">清空</el-button>
        </div>
      </template>
      
      <el-form :model="flightForm" :rules="rules" ref="flightForm" label-width="80px" class="search-form">
        <div class="form-row">
          <el-form-item label="出发地" prop="departure" class="form-item">
            <el-input 
              v-model="flightForm.departure" 
              placeholder="请输入出发城市"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="目的地" prop="arrival" class="form-item">
            <el-input 
              v-model="flightForm.arrival" 
              placeholder="请输入到达城市"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="出发日期" prop="departureDate" class="form-item">
            <el-date-picker
              v-model="flightForm.departureDate"
              type="date"
              placeholder="选择出发日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :disabled-date="disabledDate"
              style="width: 100%"
            />
          </el-form-item>
        </div>
        
        <div class="form-row">
          <el-form-item label="返回日期" prop="returnDate" class="form-item">
            <el-date-picker
              v-model="flightForm.returnDate"
              type="date"
              placeholder="选择返回日期（可选）"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :disabled-date="disabledReturnDate"
              style="width: 100%"
            />
          </el-form-item>
        </div>
        
        <el-form-item>
          <el-button 
            type="primary" 
            @click="searchFlights" 
            :loading="isSearching"
            class="search-button"
          >
            <i class="el-icon-search"></i>
            {{ isSearching ? '搜索中...' : '搜索航班' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 搜索结果 -->
    <div v-if="flightResults.length > 0 || isSearching" class="results-container">
      <div class="results-header">
        <i class="el-icon-plane"></i>
        搜索结果 ({{ flightResults.length }} 个航班)
      </div>
      
      <el-table :data="flightResults" style="width: 100%" v-loading="isSearching" class="flight-table">
        <el-table-column prop="airline" label="航空公司" width="120" class-name="airline-column">
          <template #default="scope">
            <span class="airline-column">{{ scope.row.airline }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="departureAirport" label="出发机场" width="120" class-name="airport-column">
          <template #default="scope">
            <span class="airport-column">{{ scope.row.departureAirport }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="departureTime" label="出发时间" width="100" class-name="time-column">
          <template #default="scope">
            <span class="time-column">{{ scope.row.departureTime }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="arrivalAirport" label="到达机场" width="120" class-name="airport-column">
          <template #default="scope">
            <span class="airport-column">{{ scope.row.arrivalAirport }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="arrivalTime" label="到达时间" width="100" class-name="time-column">
          <template #default="scope">
            <span class="time-column">{{ scope.row.arrivalTime }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="price" label="价格" width="100" class-name="price-column">
          <template #default="scope">
            <span class="price-column">¥{{ scope.row.price }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="cabin" label="舱位" width="100" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small" 
              @click="bookFlight(scope.row)"
              class="book-button"
            >
              <i class="el-icon-shopping-cart-2"></i>
              预订
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 无结果提示 -->
    <div v-else-if="hasSearched && !isSearching" class="no-results">
      <i class="el-icon-warning-outline" style="font-size: 48px; color: #909399; margin-bottom: 16px;"></i>
      <p>未找到符合条件的航班</p>
      <p style="color: #909399; font-size: 14px;">请尝试调整搜索条件</p>
    </div>
  </div>
</template>

<script>
import { searchFlights, getFlightSearchStatus } from '../utils/api'

export default {
  name: 'Flight-Search',
  data() {
    return {
      flightForm: {
        departure: '',
        arrival: '',
        departureDate: '',
        returnDate: ''
      },
      rules: {
        departure: [
          { required: true, message: '请输入出发地', trigger: 'blur' }
        ],
        arrival: [
          { required: true, message: '请输入目的地', trigger: 'blur' }
        ],
        departureDate: [
          { required: true, message: '请选择出发日期', trigger: 'change' }
        ]
      },
      isSearching: false,
      flightResults: [],
      hasSearched: false
    }
  },
  mounted() {
    this.checkFlightSearchStatus()
  },
  methods: {
    // 检查机票搜索功能状态
    async checkFlightSearchStatus() {
      try {
        const response = await getFlightSearchStatus()
        if (!response.data.available) {
          this.$message.warning('机票搜索功能暂时不可用，将显示模拟数据')
        }
      } catch (error) {
        console.log('机票搜索功能状态检查失败，将使用模拟数据')
      }
    },
    
    // 禁用过去的日期
    disabledDate(time) {
      return time.getTime() < Date.now() - 8.64e7
    },
    
    // 禁用返回日期（必须晚于出发日期）
    disabledReturnDate(time) {
      if (!this.flightForm.departureDate) {
        return time.getTime() < Date.now() - 8.64e7
      }
      return time.getTime() <= new Date(this.flightForm.departureDate).getTime()
    },
    
    // 搜索机票
    async searchFlights() {
      try {
        await this.$refs.flightForm.validate()
        
        this.isSearching = true
        this.hasSearched = true
        
        console.log('开始搜索机票:', this.flightForm)
        
        // 调用后端API搜索机票
        const response = await searchFlights({
          departure: this.flightForm.departure,
          arrival: this.flightForm.arrival,
          departureDate: this.flightForm.departureDate,
          returnDate: this.flightForm.returnDate
        })
        
        console.log('API响应:', response)
        
        if (response && response.success) {
          this.flightResults = response.flights || []
          this.$message.success(response.message || `找到 ${this.flightResults.length} 个航班`)
        } else {
          this.flightResults = []
          this.$message.warning(response.message || '搜索失败')
        }
        
      } catch (error) {
        console.error('搜索机票失败:', error)
        
        // 处理不同类型的错误
        if (error.message && error.message.includes('Failed to fetch')) {
          this.$message.error('无法连接到机票搜索服务器，请检查服务器是否启动')
        } else if (error.message) {
          this.$message.error(`搜索失败: ${error.message}`)
        } else {
          this.$message.error('搜索失败，请稍后重试')
        }
        
        this.flightResults = []
      } finally {
        this.isSearching = false
      }
    },
    
    // 预订机票
    bookFlight(flight) {
      try {
        // 构建携程机票搜索URL
        let url = 'https://flights.ctrip.com/online/list/'
        
        // 获取城市代码（简化处理）
        const getCityCode = (cityName) => {
          const cityMapping = {
            '北京': 'bjs', '上海': 'sha', '广州': 'can', '深圳': 'szx',
            '杭州': 'hgh', '南京': 'nkg', '成都': 'ctu', '重庆': 'ckg',
            '西安': 'sia', '武汉': 'wuh', '长沙': 'csx', '青岛': 'tao',
            '厦门': 'xmn', '大连': 'dlc', '天津': 'tsn', '沈阳': 'she',
            '哈尔滨': 'hrb', '济南': 'tna', '郑州': 'cgo', '昆明': 'kmg',
            '贵阳': 'kwe', '南宁': 'nng', '海口': 'hak', '三亚': 'syx',
            '福州': 'foc', '南昌': 'khn', '合肥': 'hfe', '太原': 'tyn',
            '石家庄': 'sjw', '呼和浩特': 'het', '兰州': 'lhw', '西宁': 'xnn',
            '银川': 'inc', '乌鲁木齐': 'urc', '拉萨': 'lxa'
          }
          return cityMapping[cityName] || cityName.toLowerCase()
        }
        
        // 从航班信息中提取出发地和目的地
        const departure = this.flightForm.departure
        const arrival = this.flightForm.arrival
        const departureDate = this.flightForm.departureDate
        
        if (!departure || !arrival || !departureDate) {
          this.$message.error('缺少必要的航班信息')
          return
        }
        
        const fromCode = getCityCode(departure)
        const toCode = getCityCode(arrival)
        const depdate = new Date(departureDate).toISOString().split('T')[0]
        
        // 构建单程机票URL
        url += `oneway-${fromCode}-${toCode}?depdate=${depdate}&cabin=y_s_c_f&adult=1&child=0&infant=0`
        
        // 在新窗口中打开携程机票页面
        window.open(url, '_blank')
        
        this.$message.success(`正在跳转到携程预订 ${flight.airline} 航班`)
        
      } catch (error) {
        console.error('预订机票失败:', error)
        this.$message.error('预订失败，请稍后重试')
      }
    },
    
    // 清空表单
    clearForm() {
      this.$refs.flightForm.resetFields()
      this.flightResults = []
      this.hasSearched = false
    },
    
    // 设置路线（供外部调用）
    setRoute(departure, arrival) {
      this.flightForm.departure = departure
      this.flightForm.arrival = arrival
      // 自动设置出发日期为明天
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      this.flightForm.departureDate = tomorrow.toISOString().split('T')[0]
    }
  }
}
</script>

<style scoped>
.flight-search-container {
  margin-bottom: 20px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px;
  box-sizing: border-box;
}

.flight-card {
  margin-bottom: 20px;
  width: 100%;
  max-width: 1200px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-card {
  margin-top: 20px;
  width: 100%;
  max-width: 1200px;
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
  width: 100%;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

.flight-results {
  margin-top: 20px;
  width: 100%;
  max-width: 1200px;
  display: flex;
  justify-content: center;
}

/* 确保表格占满容器宽度 */
:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table__body-wrapper) {
  width: 100% !important;
}

/* 确保表格内容完整显示 */
:deep(.el-table__body) {
  width: 100% !important;
}

:deep(.el-table__header) {
  width: 100% !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .flight-search-container {
    padding: 0 10px;
  }
  
  .el-col {
    margin-bottom: 10px;
  }
  
  /* 在小屏幕上调整表格列宽 */
  :deep(.el-table .cell) {
    padding: 8px 4px;
  }
  
  .flight-card,
  .results-card {
    max-width: 100%;
  }
}

/* 确保卡片内容占满宽度 */
:deep(.el-card__body) {
  padding: 20px;
  width: 100%;
  box-sizing: border-box;
}

:deep(.el-form) {
  width: 100%;
}

.search-form {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
  width: 100%;
  box-sizing: border-box;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  width: 100%;
}

.form-item {
  flex: 1;
  min-width: 0;
}

.search-button {
  width: 100%;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.search-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.search-button:active {
  transform: translateY(0);
}

.results-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  width: 100%;
  max-width: 1200px;
}

.results-header {
  padding: 16px 24px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.flight-table {
  width: 100%;
}

.flight-table .el-table__header {
  background: #f8f9fa;
}

.flight-table .el-table__row:hover {
  background: #f0f9ff;
}

.book-button {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  border: none;
  border-radius: 6px;
  color: white;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.book-button:hover {
  background: linear-gradient(135deg, #ee5a24 0%, #ff6b6b 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(238, 90, 36, 0.3);
}

.book-button:active {
  transform: translateY(0);
}

.book-button i {
  font-size: 14px;
}

.loading-container {
  text-align: center;
  padding: 40px;
}

.price-column {
  font-weight: 600;
  color: #ff6b6b;
}

.airline-column {
  font-weight: 500;
  color: #2c3e50;
}

.time-column {
  font-weight: 500;
  color: #34495e;
}

.airport-column {
  color: #7f8c8d;
  font-size: 12px;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .flight-search-container {
    padding: 0 10px;
  }
  
  .search-form {
    padding: 16px;
  }
  
  .results-container {
    max-width: 100%;
  }
}
</style> 