<template>
    <div class="box-card box-middle">
        <el-card>
            <template #header>
                <div class="card-title">登录</div>
            </template>
            <el-form ref="user" :model="user" :rules="rules">
                <el-form-item prop="username">
                    <el-input v-model="user.username" placeholder="用户名" type="text"/>
                </el-form-item>
                <el-form-item prop="password">
                    <el-input v-model="user.password" placeholder="密码" type="password"
                              @keyup.enter.native="onSubmit('user')"/>
                </el-form-item>
                <el-form-item>
                    <router-link :to="{name: 'Register'}">
                        注册账号
                    </router-link>
                </el-form-item>
                <el-form-item>
                    <el-button class="button-long" type="primary" @click="onSubmit('user')" :loading="loading" round>
                        登录
                    </el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script>
import {getAuthUser} from '../utils/api'
import {setAuth, setToken} from '../utils/auth'
import axios from 'axios'

export default {
    name: 'Login',
    data() {
        return {
            user: {},
            rules: {
                username: [
                    {required: true, message: '请输入用户名', trigger: 'blur'}
                ],
                password: [
                    {required: true, message: '请输入密码', trigger: 'blur'}
                ]
            },
            loading: false
        }
    },
    methods: {
      async fetchAndStoreRecommendations(userId) {
        console.log(`开始为用户 ${userId} 获取推荐数据...`);
        // 推荐系统API的地址
        const recommenderApiUrl = `http://127.0.0.1:8000/recommend/${userId}?top_n=10`;

        try {
          // 使用 axios 发送 GET 请求
          const response = await axios.get(recommenderApiUrl);
          const recommendedIds = response.data; // 返回的是一个ID数组, e.g., ["101", "205"]
          // console.log('');
          if (recommendedIds && recommendedIds.length > 0) {
            console.log('成功获取推荐列表:', recommendedIds);
            // 将数组转换为 JSON 字符串并存储到 localStorage
            // 键名可以自定义，例如 'user_recommendations'
            localStorage.setItem('user_recommendations', JSON.stringify(recommendedIds));
          } else {
            console.log('该用户没有推荐数据，清空旧的缓存。');
            // 如果没有推荐，最好也清理一下旧的缓存
            localStorage.removeItem('user_recommendations');
          }
        } catch (error) {
          console.error('调用推荐API失败:', error);
          // 即使推荐失败，也不应该影响登录流程，所以只在控制台打印错误
          // 同样，清理一下可能存在的旧缓存
          localStorage.removeItem('user_recommendations');
        }
      },
        onSubmit(user) {
            this.$refs[user].validate((valid) => {
                if (valid) {
                    this.loading = true
                    let auth = {username: 'linter', password: 'linter'}
                    let params = new URLSearchParams()
                    params.append('grant_type', 'password')
                    params.append('username', this.user.username)
                    params.append('password', this.user.password)
                    let baseUrl = import.meta.env.VITE_BASE_API_URL
                    axios.post(baseUrl + '/oauth/token', params, {auth}).then(response => {
                        let data = response.data
                        setToken(data.token_type + ' ' + data.access_token)
                        getAuthUser().then(result => {
                            if (result.code === '0000') {
                              const loggedInUserId = result.data.id;
                              if (loggedInUserId) {
                                // 调用新方法获取并存储推荐数据
                                // 我们把它放在这里，不阻塞页面跳转
                                console.log("loggedInUserId"+loggedInUserId);
                                this.fetchAndStoreRecommendations(loggedInUserId);
                              } else {
                                console.warn("无法从用户信息中获取ID，跳过推荐获取步骤。");
                              }
                                setAuth(result.data)
                                let redirect = this.$route.query.redirect
                                if (redirect) {
                                    this.$router.push({path: String(redirect)})
                                } else {
                                    this.$router.push({name: 'Index'})
                                }

                            }
                        })
                    }).catch(error => {
                        this.$message.error(error.response.data.error_description)
                    }).finally(() =>
                        this.loading = false
                    )
                }
            })
        }
    }
}
</script>