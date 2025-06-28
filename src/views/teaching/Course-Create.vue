<template>
    <div class="page">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>新增旅游项目</h2>
                </div>
            </template>
            <Course-Form :course="course" editMode="create" @submit-success="onCourseSubmit"/>
        </el-card>
    </div>
</template>

<script>
import CourseForm from '../../components/Course-Form.vue'
import {addCourseToVectorDB} from '../../utils/api'

export default {
    name: "Course-Create",
    components: {
        CourseForm
    },
    data() {
        return {
            course: {}
        }
    },
    methods: {
        onCourseSubmit(course) {
            // 课程已经在Course-Form中创建成功，现在同步到向量数据库
            addCourseToVectorDB(course)
                .then(res => res.json())
                .then(data => {
                    if (data.message) {
                        this.$message.success('课程已成功同步到AI知识库！');
                    } else {
                        this.$message.error(data.error || '同步到AI知识库失败。');
                    }
                })
                .catch(err => {
                    console.error("同步到向量数据库时出错:", err);
                    this.$message.error('同步到AI知识库时网络错误。');
                });
        }
    }
}
</script>

<style>
</style>