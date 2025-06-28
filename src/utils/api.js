import request from '../utils/request'
import axios from "axios";

export function uploadVrProfile(data) {
    // 注意：这里的URL必须指向你的Python Flask应用
    // 如果你的前端和Python后端不在同一个域或端口，需要配置代理或使用完整URL
    // 假设Python后端运行在 http://localhost:5001
    const pythonApiUrl = 'http://localhost:5001/vr/upload';

    return axios.post(pythonApiUrl, data, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });
}
export function updateCourseInVectorDBxu(course) {
    // 这里的URL需要指向您的Python后端用于更新向量数据库的端点
    // 假设端点是 /update-vector
    const pythonApiUrl = 'http://localhost:5001/update-vector';
    return fetch(pythonApiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(course),
    });
}
export function getVrProfileByName(params) {
    // 这里的URL必须指向你的Python Flask应用中用于查询VR资料的端点
    const pythonApiUrl = 'http://localhost:5001/vr/profile';

    // 根据你api.js文件的风格，你可能使用axios或request
    // 这是一个使用axios的例子，因为它在你的文件中已经被导入
    return axios.get(pythonApiUrl, { params });
}
export function getAuthUser() {
    return request({
        url: '/oauth/user',
        method: 'get'
    })
}

export function registerUser(data) {
    return request({
        url: '/oauth/user',
        method: 'post',
        data
    })
}
//新增邮箱验证码
export function sendEmailCode(data) {
    return request({
        url: '/oauth/user/sendEmailCode',
        method: 'post',
        data
    })
}

export function getUsers(params) {
    return request({
        url: '/users',
        method: 'get',
        params
    })
}

export function getUser(pathVariable, params) {
    return request({
        url: '/users/' + pathVariable,
        method: 'get',
        params
    })
}

export function createUser(data) {
    return request({
        url: '/users',
        method: 'post',
        data
    })
}

export function updateUser(data) {
    return request({
        url: '/users',
        method: 'put',
        data
    })
}

export function deleteUser(pathVariable) {
    return request({
        url: '/users/' + pathVariable,
        method: 'delete'
    })
}

export function getRoles(params) {
    return request({
        url: '/roles',
        method: 'get',
        params
    })
}

export function getRole(pathVariable, params) {
    return request({
        url: '/roles/' + pathVariable,
        method: 'get',
        params
    })
}

export function createRole(data) {
    return request({
        url: '/roles',
        method: 'post',
        data
    })
}

export function updateRole(data) {
    return request({
        url: '/roles',
        method: 'put',
        data
    })
}

export function deleteRole(pathVariable) {
    return request({
        url: '/roles/' + pathVariable,
        method: 'delete'
    })
}

export function getCategories(params) {
    return request({
        url: '/categories',
        method: 'get',
        params
    })
}

export function createCategory(data) {
    return request({
        url: '/categories',
        method: 'post',
        data
    })
}

export function updateCategory(data) {
    return request({
        url: '/categories',
        method: 'put',
        data
    })
}

export function deleteCategory(pathVariable) {
    return request({
        url: '/categories/' + pathVariable,
        method: 'delete'
    })
}

export function getCourses(params) {
    return request({
        url: '/courses',
        method: 'get',
        params
    })
}

export function getCourse(pathVariable, params) {
    return request({
        url: '/courses/' + pathVariable,
        method: 'get',
        params
    })
}

export function createCourse(data) {
    return request({
        url: '/courses',
        method: 'post',
        data
    })
}

export function updateCourse(data) {
    return request({
        url: '/courses',
        method: 'put',
        data
    })
}

export function updateRegistrationOfCourse(params) {
    return request({
        url: '/courses/registration',
        method: 'put',
        params
    })
}

export function deleteCourse(pathVariable) {
    return request({
        url: '/courses/' + pathVariable,
        method: 'delete'
    })
}

export function searchCourse(params) {
    return request({
        url: '/courses/search',
        method: 'get',
        params
    })
}

export function getChaptersOfCourse(pathVariable, params) {
    return request({
        url: '/courses/' + pathVariable + '/chapters',
        method: 'get',
        params
    })
}

export function getCategoriesOfCourse(pathVariable, params) {
    return request({
        url: '/courses/' + pathVariable + '/categories',
        method: 'get',
        params
    })
}

export function getQuestionsOfCourse(pathVariable, params) {
    return request({
        url: '/courses/' + pathVariable + '/questions',
        method: 'get',
        params
    })
}

export function getNotesOfCourse(pathVariable, params) {
    return request({
        url: '/courses/' + pathVariable + '/notes',
        method: 'get',
        params
    })
}

export function getEvaluationsOfCourse(pathVariable, params) {
    return request({
        url: '/courses/' + pathVariable + '/evaluations',
        method: 'get',
        params
    })
}

export function getChapter(pathVariable, params) {
    return request({
        url: '/chapters/' + pathVariable,
        method: 'get',
        params
    })
}

export function createChapter(data) {
    return request({
        url: '/chapters',
        method: 'post',
        data
    })
}

export function updateChapter(data) {
    return request({
        url: '/chapters',
        method: 'put',
        data
    })
}

export function deleteChapter(pathVariable) {
    return request({
        url: '/chapters/' + pathVariable,
        method: 'delete'
    })
}

export function getQuestion(pathVariable, params) {
    return request({
        url: '/questions/' + pathVariable,
        method: 'get',
        params
    })
}

export function createQuestion(data) {
    return request({
        url: '/questions',
        method: 'post',
        data
    })
}

export function updateQuestion(data) {
    return request({
        url: '/questions',
        method: 'put',
        data
    })
}

export function deleteQuestion(pathVariable) {
    return request({
        url: '/questions/' + pathVariable,
        method: 'delete'
    })
}

export function getAnswersOfQuestion(pathVariable, params) {
    return request({
        url: '/questions/' + pathVariable + '/answers',
        method: 'get',
        params
    })
}

export function createAnswer(data) {
    return request({
        url: '/answers',
        method: 'post',
        data
    })
}

export function updateAnswer(data) {
    return request({
        url: '/answers',
        method: 'put',
        data
    })
}

export function deleteAnswer(pathVariable) {
    return request({
        url: '/answers/' + pathVariable,
        method: 'delete'
    })
}

export function createNote(data) {
    return request({
        url: '/notes',
        method: 'post',
        data
    })
}

export function updateNote(data) {
    return request({
        url: '/notes',
        method: 'put',
        data
    })
}

export function deleteNote(pathVariable) {
    return request({
        url: '/notes/' + pathVariable,
        method: 'delete'
    })
}

export function createEvaluation(data) {
    return request({
        url: '/evaluations',
        method: 'post',
        data
    })
}

export function updateEvaluation(data) {
    return request({
        url: '/evaluations',
        method: 'put',
        data
    })
}

export function deleteEvaluation(pathVariable) {
    return request({
        url: '/evaluations/' + pathVariable,
        method: 'delete'
    })
}

export function getCoursesOfUser(pathVariable, params) {
    return request({
        url: '/users/' + pathVariable + '/courses',
        method: 'get',
        params
    })
}

export function getNotesOfUser(pathVariable, params) {
    return request({
        url: '/users/' + pathVariable + '/notes',
        method: 'get',
        params
    })
}

export function createOrder(data) {
    return request({
        url: '/orders',
        method: 'post',
        data
    })
}

export function updateOrder(data) {
    return request({
        url: '/orders',
        method: 'put',
        data
    })
}

export function payOrder(params) {
    return request({
        url: '/payments',
        method: 'get',
        params
    })
}

export function uploadProfilePicture(data) {
    return request({
        url: '/profile-pictures',
        method: 'post',
        headers: {
            'Content-Type': 'multipart/form-data'
        },
        data
    })
}

export function uploadCoverPicture(data) {
    return request({
        url: '/cover-pictures',
        method: 'post',
        headers: {
            'Content-Type': 'multipart/form-data'
        },
        data
    })
}

export function uploadVideo(data, onUploadProgress) {
    return request({
        url: '/videos',
        method: 'post',
        headers: {
            'Content-Type': 'multipart/form-data'
        },
        onUploadProgress,
        data
    })
}

export function addCourseToVectorDB(courseData) {
    // 这个函数调用我们的Python后端来向量化课程
    return fetch('/api/add_course', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(courseData)
    });
}

export function updateCourseInVectorDB(courseData) {
    // 这个函数调用我们的Python后端来更新向量数据库中的课程
    return fetch('/api/update_course', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(courseData)
    });
}

export function deleteCourseFromVectorDB(courseId) {
    // 这个函数调用我们的Python后端来从向量数据库中删除课程
    return fetch('/api/delete_course', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: courseId })
    });
}

// 机票搜索相关API
export function searchFlights(data) {
    return fetch('http://localhost:5000/api/flights/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(response => response.json())
}

export function getFlightSearchStatus() {
    return fetch('http://localhost:5000/api/flights/status', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
}