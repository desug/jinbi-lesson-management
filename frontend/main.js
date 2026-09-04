import App from './App'

// #ifndef VUE3
import Vue from 'vue'
import './uni.promisify.adaptor'
import config from '@/config'
import storage from '@/utils/storage'
import * as constants from '@/utils/constants'
import * as authApi from '@/api/auth'
import * as studentApi from '@/api/student'
import * as adminApi from '@/api/admin'
import * as recordApi from '@/api/record'

Vue.config.productionTip = false

// 这几行是“全局挂载”：挂到 Vue.prototype 后，每个页面组件里都可以通过 this.$api、this.$storage 访问。
// 好处是页面不用重复 import 一堆工具，适合小项目快速统一调用入口。
Vue.prototype.$config = config
Vue.prototype.$storage = storage
Vue.prototype.$constants = constants
Vue.prototype.$api = {
  auth: authApi,
  student: studentApi,
  admin: adminApi,
  record: recordApi
}

App.mpType = 'app'
// uni-app 的 Vue2 启动方式：把 App.vue 作为根组件创建出来，然后挂载到应用容器。
const app = new Vue({
  ...App
})
app.$mount()
// #endif

// #ifdef VUE3
import { createSSRApp } from 'vue'
export function createApp() {
  // Vue3 模式下由 uni-app 调用 createApp，这里返回根应用实例。
  const app = createSSRApp(App)
  return {
    app
  }
}
// #endif
