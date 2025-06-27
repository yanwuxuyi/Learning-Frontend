<template>
    <div class="mt-1 mb-1">
        <el-button type="primary" size="small" @click="openDialog" plain round>
            评价
        </el-button>
    </div>
    <ul>
        <li v-for="evaluation in evaluations" class="list"
            :class="{ 'pending-review': evaluation.moderation !== 'approved' }">
            <div class="flex-start">
                <el-avatar :src="evaluation.author.profilePicture">
                    {{ evaluation.author.fullName }}
                </el-avatar>
                <div class="evaluation-info">
                    <div class="flex-between">
                        <div v-if="evaluation.author.username" class="user-name">
                            <router-link
                                :to="{ name: 'User-Homepage', params: { username: evaluation.author.username } }">
                                {{ evaluation.author.fullName }}
                            </router-link>
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: flex-end;">
                            <el-tag :type="evaluation.moderation === 'approved' ? 'success' : 'warning'" size="small"
                                effect="light" style="margin-top: 4px; font-size: 12px; padding: 2px 6px;">
                                {{
                                    evaluation.moderation === 'approved'
                                        ? '审核通过'
                                        : '审核中'
                                }}
                            </el-tag>
                            <el-rate v-model="evaluation.score" show-score disabled />
                        </div>
                    </div>
                    <div class="create-time">
                        {{ evaluation.createTime }}
                    </div>
                    <div class="evaluation-comment">
                        {{ evaluation.comment }}
                    </div>
                </div>
            </div>
        </li>
    </ul>
    <div class="pagination">
        <el-pagination :hide-on-single-page="true" :pager-count="5" :total="size" background layout="prev, pager, next"
            @current-change="handlePageChange">
        </el-pagination>
    </div>
    <el-dialog title="评价" v-model="dialogVisible" center>
        <el-form ref="evaluation" :model="evaluation" :rules="rules">
            <el-form-item>
                <el-rate v-model="evaluation.score" />
            </el-form-item>
            <el-form-item prop="comment">
                <el-input type="textarea" v-model.trim="evaluation.comment" :autosize="{ minRows: 4, maxRows: 10 }"
                    placeholder="请输入内容" minlength="5" maxlength="500" show-word-limit />
            </el-form-item>
            <el-form-item>
                <el-button class="button-long" type="primary" @click="createEvaluation('evaluation')" :loading="loading"
                    round>
                    评价
                </el-button>
            </el-form-item>
        </el-form>
    </el-dialog>
</template>

<script>
import { mapState } from 'vuex'
import { createEvaluation, getEvaluationsOfCourse } from '../utils/api'
import { moderateComment } from '../utils/ai'

export default {
    name: "Course-Evaluation",
    data() {
        return {
            courseId: this.$route.params.id,
            evaluations: [],
            size: 0,
            pageNum: null,
            evaluation: {},
            dialogVisible: false,
            loading: false,
            rules: {
                comment: [
                    { required: true, message: '请输入内容', trigger: 'blur' },
                    { min: 2, max: 1000, message: '长度在2到1000个字符', trigger: 'blur' }
                ]
            }
        }
    },
    computed: mapState([
        'auth'
    ]),
    created() {
        this.getEvaluations()
    },
    methods: {
        getEvaluations() {
            getEvaluationsOfCourse(this.courseId, { pageNum: this.pageNum }).then(result => {
                if (result.code === '0000') {
                    // 👇 批量设置 moderation = 'approved'
                    this.evaluations = result.data.list.map(ev => ({
                        ...ev,
                        moderation: 'approved',
                    }));
                    this.size = result.data.size;
                }
            });
        },
        async createEvaluation(formName) {
            this.$refs[formName].validate(async (valid) => {
                if (!valid) return;

                this.loading = true;

                const tempId = `temp-${Date.now()}`;
                const tempEval = {
                    id: tempId,
                    author: {
                        username: this.auth.user?.username || '',
                        fullName: this.auth.user?.fullName || '匿名用户',
                        profilePicture: this.auth.user?.profilePicture || '',
                    },
                    comment: this.evaluation.comment,
                    score: this.evaluation.score,
                    moderation: 'pending',
                    createTime: new Date().toLocaleString(),
                };

                // 1️⃣ 本地立即显示“审核中”评论
                this.evaluations.unshift(tempEval);

                this.dialogVisible = false;
                this.$message.success('评论已提交，等待审核中...');
                this.$refs[formName].resetFields();

                try {
                    // 2️⃣ 审核流程：local + AI 检测
                    const moderation = await moderateComment(tempEval.comment);

                    if (moderation.ok) {
                        // 3️⃣ 审核通过，提交后端
                        const result = await createEvaluation({
                            comment: tempEval.comment,
                            score: tempEval.score,
                            courseId: this.courseId,
                        });

                        if (result.code === '0000') {
                            const approvedEval = {
                                ...result.data,
                                moderation: 'approved', // ✅ 明确告诉前端这是审核通过的
                            };
                            this.evaluations = this.evaluations.map((ev) =>
                                ev.id === tempId ? approvedEval : ev
                            );
                        } else {
                            throw new Error('后端保存失败，请稍后重试');
                        }
                    } else {
                        throw new Error(moderation.reason || '评论未通过审核');
                    }
                } catch (err) {
                    // 4️⃣ 审核或保存失败：移除该条临时评论
                    this.evaluations = this.evaluations.filter((ev) => ev.id !== tempId);
                    this.$message.error(err.message || '审核失败，请稍后再试');
                } finally {
                    this.loading = false;
                }
            });
        },
        openDialog() {
            if (this.auth) {
                this.dialogVisible = true
            } else {
                this.$router.push({ name: 'Login' })
            }
        },
        handlePageChange(pageNum) {
            this.pageNum = pageNum
            this.getEvaluations()
        }
    }
}
</script>

<style>
.evaluation-info {
    width: 100%;
    margin-left: 10px;
}

.evaluation-comment {
    margin-top: 10px;
}
</style>