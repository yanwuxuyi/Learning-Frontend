<template>
    <div class="box-card box-middle">
        <el-card>
            <template #header>
                <div class="card-title">注册</div>
            </template>
            <el-form ref="user" :model="user" :rules="rules">
                <el-form-item prop="emailAddress">
                    <el-input type="email" v-model="user.emailAddress" placeholder="邮箱" />
                </el-form-item>
                <!-- 获取验证码按钮 -->
                <el-form-item>
                    <el-row>
                        <el-col :span="16">
                            <el-input type="text" v-model="user.verificationCode" placeholder="请输入验证码" />
                        </el-col>
                        <el-col :span="8">
                            <el-button :disabled="isCodeSent" @click="sendVerificationCode" type="primary" round
                                style="margin-left: 10px; width: 100px;">
                                {{ isCodeSent ? countdown + '秒' : '获取验证码' }}
                            </el-button>
                        </el-col>
                    </el-row>
                </el-form-item>

                <el-form-item prop="username">
                    <el-input type="text" v-model="user.username" placeholder="用户名" />
                </el-form-item>
                <el-form-item prop="password">
                    <el-input type="password" v-model="user.password" placeholder="密码" />
                </el-form-item>
                <el-form-item>
                    <el-button class="button-long" type="primary" @click="onSubmit('user')" :loading="loading" round>
                        注册
                    </el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script>
import { registerUser } from '../utils/api'
import { sendEmailCode } from '../utils/api'

export default {
    name: 'Register',
    data() {
        return {
            user: {
                emailAddress: '',
                verificationCode: '', // 验证码字段
                username: '',
                password: ''
            },
            rules: {
                emailAddress: [
                    { type: 'email', required: true, message: '请输入正确的邮箱', trigger: 'blur' }
                ],
                username: [
                    { required: true, message: '请输入用户名', trigger: 'blur' },
                    { min: 2, max: 10, message: '长度在2到10个字符', trigger: 'blur' }
                ],
                password: [
                    { required: true, message: '请输入密码', trigger: 'blur' },
                    { min: 6, max: 20, message: '长度在6到20个字符', trigger: 'blur' }
                ],
                verificationCode: [
                    { required: true, message: '请输入验证码', trigger: 'blur' },
                    { len: 6, message: '验证码长度为6位', trigger: 'blur' }
                ]
            },
            isCodeSent: false,
            countdown: 60,
            timer: null,
            loading: false
        }
    },
    methods: {
        //新增邮箱验证码
        async sendVerificationCode() {
            console.log('[验证码请求] 触发发送验证码');
            const email = this.user.emailAddress;
            if (!email || !/^[\w-]+@([\w-]+\.)+[\w-]{2,4}$/.test(email)) {
                console.warn('[验证码请求] 邮箱格式不正确：', email);
                this.$message.warning('请输入有效的邮箱地址');
                return;
            }
            console.log('[验证码请求] 正在发送验证码到邮箱：', email);
            // 先禁用按钮
            this.isCodeSent = true;
            this.startCountdown();
            try {
                const res = await sendEmailCode({ email });
                console.log('[验证码请求] 接口响应：', res);
                if (res.code === '0000') {
                    this.$message.success('验证码已发送');
                } else {
                    console.warn('[验证码请求] 返回错误信息：', res.data.message);
                    this.$message.error(res.data.message || '验证码发送失败');
                }
            } catch (err) {
                console.error('[验证码请求] 请求异常：', err);
                this.$message.error('验证码发送异常');
            }
        },



        startCountdown() {
            this.countdown = 60;
            this.timer = setInterval(() => {
                this.countdown--;
                if (this.countdown <= 0) {
                    clearInterval(this.timer);
                    this.isCodeSent = false;
                }
            }, 1000);
        },

        onSubmit(user) {
            this.$refs[user].validate((valid) => {
                if (valid) {
                    this.loading = true
                    registerUser(this.user).then(result => {
                        console.log('[注册请求] 接口响应：', result);
                        if (result.code === '0000') {
                            this.$message.success("注册成功！")
                            this.$router.push({ name: 'Login' })
                        }
                    }).finally(() =>
                        this.loading = false
                    )
                }
            })
        }
    }
}
</script>