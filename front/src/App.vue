<script setup lang="ts">
import MyTest from "./components/MyTest.vue";
import SearchBox from "./components/SearchBox.vue";
import GetTradesBox from "./components/GetTradesBox.vue";
import CheckStooq from "./components/CheckStooq.vue";
import axios from "axios";
import {ref} from "vue";

const txt = ref<string>("dummy2")
const clicked = () => {
  axios.get("/api/index.json").then(res => {
    console.log(res)
    txt.value = res.data
  })
}
const toggleSearchBox = ref<boolean>(false)
const toggleGetTradeBox = ref<boolean>(false)
const switchToggleSearchBox = () => {
  toggleSearchBox.value = !toggleSearchBox.value
  toggleGetTradeBox.value = false
}
const switchGetTradeBox = () => {
  toggleGetTradeBox.value = !toggleGetTradeBox.value
  toggleSearchBox.value = false
}
</script>

<template>
  <div id="wrapper">
    <nav id="header">
      <ul>
        <li><a href="api/analyze">analyze</a></li>
        <li><a href="">home</a></li>
        <li><a href="http://localhost:8000/admin/">管理サイト</a></li>
        <li><a href="" @click.prevent="switchToggleSearchBox">search切り替え</a></li>
        <li><a href="" @click.prevent="switchGetTradeBox">GetTradeBox切り替え</a></li>
      </ul>
    </nav>
    <div id="main">
      <SearchBox v-if="toggleSearchBox"/>
      <GetTradesBox v-if="toggleGetTradeBox"/>
      <CheckStooq/>
    </div>
    <!--    <div id="main" v-if="txt !=='dummy2'" v-html="txt" style="width: 640px; height: 480px;"></div>-->
  </div>
</template>

<style scoped>
#wrapper {
  min-height: 800px;
  display: grid;
  grid-template:
        "header  header header" 60px
        "main    main   main  " 1fr
        /150px   1fr;
  gap: 5px;
}

#header {
  grid-area: header;
  border: 1px solid black;
  padding: 20px;
}

#left {
  grid-area: left;
  border: 1px solid black;
  text-align: center;
}

#main {
  grid-area: main;
  border: 1px solid black;
}
</style>