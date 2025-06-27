<template>
    <div v-for="(chapter, index) in chapters" :key="index" class="chapter-content-block">
        <h3>第{{ index + 1 }}个项目：{{ chapter.title }}</h3>
        <video v-if="chapter.videoUrl" :src="chapter.videoUrl" height="405" width="720"
               controls controlslist="nodownload" disablePictureInPicture style="margin-bottom: 16px;"/>
        <pre v-if="chapter.textContent" class="text-content">
            {{ chapter.textContent }}
        </pre>
    </div>
</template>

<script>
import {getChaptersOfCourse} from '../utils/api'

export default {
    name: "Course-Chapter",
    props: [],
    data() {
        return {
            courseId: this.$route.params.id,
            chapters: []
        }
    },
    created() {
        this.getChapters()
    },
    methods: {
        getChapters() {
            getChaptersOfCourse(this.courseId).then(result => {
                if (result.code === '0000') {
                    this.chapters = result.data
                }
            })
        }
    }
}
</script>

<style>
.chapter-icon i {
    font-size: 20px;
}

.text-content {
    line-height: 2;
    font-size: 16px;
    color: #303133;
    white-space: pre-wrap;
    margin-bottom: 16px;
}
.chapter-content-block {
    margin-bottom: 32px;
    padding: 16px;
    background: #fafbfc;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
</style>