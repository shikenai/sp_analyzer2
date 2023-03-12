<script setup lang="ts">
import axios from "axios";
import {ref} from "vue";
const get_trades_from_stooq = () => {
  console.log('higu higu')
  axios.get('api/get_trades_from_stooq').then(res => {
    console.log(res)
  })
}

const get_brands_from_tse = () => {
  axios.get('api/get_brands_from_tse').then(res => {
  })
}

const get_initial_brands_from_tse = () => {
  axios.get('api/get_initial_brands_from_tse').then(res =>{
    console.log(res.data)
  })
}
const get_initial_trades_from_csv = ()=>{
  axios.get('api/get_initial_trades_from_csv').then(res =>{
    console.log('initial')
  })
}

</script>
<template>
  <div class="main">
    <div class="left_bar">
      <a href="" class="btn" @click.prevent="get_brands_from_tse">Get Brands From TSE</a><br>
      <a href="" class="btn" @click.prevent="get_trades_from_stooq">Get Trades From STOOQ</a><br>
<!--      <a href="" class="btn" @click.prevent="get_initial_brands_from_tse">get initial brands</a><br>-->
      <a href="" class="btn" @click.prevent="get_initial_trades_from_csv">get initial trades from csv</a><br>
    </div>
    <div class="drawing">
    </div>
  </div>
</template>

<style scoped>

.main {
  display: flex;
}

.left_bar {
  width: 200px;
  padding-top: 5px;
  border: solid black 1px;
  min-height: 800px;
}

.drawing {
  border: solid black 1px;
  min-height: 800px;
}
</style>