<template>
  <!-- ========== 修改：传递 showPanoramaUpload prop ========== -->
  <CourseForm
      :course="course"
      editMode="update"
      separatePage="true"
      :showPanoramaUpload="true"
  />
</template>

<script>
import {getCategoriesOfCourse, getCourse} from '../../utils/api'
import CourseForm from '../../components/Course-Form.vue'

export default {
    name: "Course-Update",
    components: {CourseForm},
    data() {
        return {
            courseId: this.$route.query.courseId,
            course: {}
        }
    },
    created() {
        this.getCourse()
    },
    methods: {
        getCourse() {
            getCourse(this.courseId).then(result => {
                if (result.code === '0000') {
                    this.course = result.data
                    getCategoriesOfCourse(this.courseId).then(result => {
                        if (result.code === '0000') {
                            this.course.categories = result.data
                        }
                    })
                }
            })
        }
    }
}
</script>

<style>
</style>