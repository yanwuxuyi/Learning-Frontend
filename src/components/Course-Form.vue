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
                <img class="bubble-avatar" src="/pet01.jpg" alt="AI" />
                <div class="bubble">{{ msg }}</div>
            </div>
            <div v-if="aiReply" class="ai-bubble ai">
                <img class="bubble-avatar" src="/pet01.jpg" alt="AI" />
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
import {createCourse, getCategories, updateCourse, uploadCoverPicture} from '../utils/api'
import {buildTree} from '../utils/processing'
import axios from 'axios'
import { generateStreamForPrice } from '../utils/ai.js'

export default {
    name: "Course-Form",
    props: [
        'course',
        'editMode',
        'includeStatus',
        'separatePage'
    ],
    data() {
        return {
            categories: [],
            loading: false,
            loadingPrice: false,
            aiReply: "",
            aiMessages: [],
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
    created() {
        this.getCategories()
    },
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
        onSubmit(user) {
            this.$refs[user].validate((valid) => {
                if (valid) {
                    this.loading = true
                    if (this.editMode === 'create') {
                        createCourse(this.course).then(result => {
                            if (result.code === '0000') {
                                this.$message.success("新增成功！")
                                this.$emit('submit-success', this.course);
                                this.$refs[user].resetFields()
                            }
                        }).finally(() => this.loading = false)
                    }
                    if (this.editMode === 'update') {
                        updateCourse(this.course).then(result => {
                            if (result.code === '0000') {
                                this.$message.success('更新成功！')
                            }
                        }).finally(() => this.loading = false)
                    }
                }
            })
        },
        onCancel() {
            if (this.separatePage) {
                this.$router.back()
            } else {
                this.$emit('cancel')
            }
        },
        async getSmartPriceStream() {
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
}

.is-error .cover-picture-uploader > .el-upload {
    border: 1px dashed #F56C6C;
}

.cover-picture-uploader .el-upload {
    border-radius: 6px;
    border: 1px dashed #D9D9D9;
}

.cover-picture-uploader .el-icon-plus {
    font-size: 32px;
    color: #8c939d;
    width: 100px;
    line-height: 100px;
}

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