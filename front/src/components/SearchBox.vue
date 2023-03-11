<script setup lang="ts">
import axios from "axios";
import {ref} from "vue";

let companies = ref({"keyword": "", "brands": <object>[]})
const get_brands = () => {
  axios.get("api/get_brand_list.json").then(res => {
    companies.value.brands = res.data
  })
}
window.onload = () => {
  get_brands()
}

const txt = ref<string>("dummy2")
const onKeyPressEnter = () => {
  axios.defaults.xsrfCookieName = 'csrftoken'
  axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"
  axios.post("api/get_trade_data.json", postData.value).then(res => {
    console.log(res)
    txt.value = res.data
  })
}
let postData = ref({brand_code: "", days: 0})

</script>
<template>
  <div class="main">
    <!--  <button @click="get_brands">botan</button>-->
    <div class="left_bar">
      <label for="brand_code">銘 柄 名：</label>
      <input id="brand_code" type="text" v-model="postData.brand_code" @keypress.enter="onKeyPressEnter"><br>
      <label for="days">取得日数：</label>
      <input id="days" type="text" v-model="postData.days" @keypress.enter="onKeyPressEnter">
      <!--    <table>-->
      <!--      <tr v-for="c in companies.brands" :key="c.code">-->
      <!--        <td v-text="c.code"></td>-->
      <!--        <td v-text="c.brand_name"></td>-->
      <!--      </tr>-->
      <!--    </table>-->
    </div>
    <div class="drawing">
      <div id="main" v-if="txt !=='dummy2'" v-html="txt" style="width: 640px; height: 480px;"></div>
    </div>
  </div>
</template>

<style scoped>

.main {
  display: flex;
}

.left_bar {
  width: 150px;
  padding-top: 5px;
  border: solid black 1px;
  min-height: 800px;
}

.drawing {
  border: solid black 1px;
  min-height: 800px;
}

input {
  width: 50px;
}
</style>