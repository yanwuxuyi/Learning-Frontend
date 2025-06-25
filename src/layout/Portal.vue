<template>
    <el-container>
        <el-container>
            <el-affix>
                <el-header>
                    <Header/>
                </el-header>
            </el-affix>
            <el-main>
                <router-view/>
            </el-main>
            <el-footer>
                <Footer/>
            </el-footer>
        </el-container>
        <CustomerService/>
    </el-container>
</template>

<script>
import Header from '../components/Header.vue'
import Footer from '../components/Footer.vue'
import CustomerService from '../components/Customer-Service.vue'

export default {
    name: "Portal",
    components: {
        Header,
        Footer,
        CustomerService
    }
}
</script>