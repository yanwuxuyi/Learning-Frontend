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
        <div class="pet-customer-wrapper">
            <img
                v-if="!showCustomerService"
                src="/pet.gif"
                alt="pet"
                class="pet-avatar"
                @click="showCustomerService = true"
            />
            <CustomerService v-if="showCustomerService" @close="showCustomerService = false"/>
        </div>
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
    },
    data() {
        return {
            showCustomerService: false
        }
    }
}
</script>

<style scoped>
.pet-customer-wrapper {
    position: fixed;
    right: 30px;
    bottom: 30px;
    z-index: 1100;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}
.pet-avatar {
    width: 80px;
    height: 85px;
    cursor: pointer;
    border-radius: 50%;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    background: #fff;
    transition: transform 0.2s;
    object-fit: cover;
    margin-bottom: 10px;
}
.pet-avatar:hover {
    transform: scale(1.08) rotate(-5deg);
}
::v-deep .customer-service {
    position: static !important;
    margin-bottom: 0;
    box-shadow: 0 2px 16px rgba(0,0,0,0.18);
}
</style>