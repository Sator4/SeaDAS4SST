<template>
	<!-- <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootswatch/5.3.3/pulse/bootstrap.min.css"> -->
	<center>
		<h1>Добро пожаловать в SeaDAS4SST!</h1>
		<h2>Для начала работы войдите в аккаунт.</h2>
		<br>
		<br>

		<input class="input" type="text" placeholder="Логин" v-model="login">
		<input class="input" type="password" placeholder="Пароль" v-model="password">

		<p v-if="errorMessage" style="color:red">{{ errorMessage }}</p>
		<p v-if="successMessage" style="color:green">{{ successMessage }}</p>
		<button type="button" class="btn btn-primary" @click="loginRequest({'login': login, 'password': password})">Войти</button>
		<br>
		<button type="buton" class="btn btn-secondary" @click="registerRequest({'login': login, 'password': password})">Зарегистрироваться</button>
	</center>
</template>


<script>
import { routeLocationKey } from 'vue-router'
import axios from 'axios'
import router from '../router'

export default {
	name: 'Authentication',
	data() {
		return {
			login: "",
			password: "",
			errorMessage: "",
			successMessage: ""
		}
	},
	methods: {
		loginRequest(userData) {
			this.errorMessage = ''
			this.successMessage = ''
			const path = 'http://localhost:5000/login'
			axios.post(path, userData)
			.then((res) => {
				router.push(res.data.link)
				this.errorMessage = res.data.errorMessage
			})
			.catch((error) => {
				console.log(error)
			})
		},
		registerRequest(userData) {
			this.errorMessage = ''
			this.successMessage = ''
			const path = 'http://localhost:5000/register'
			axios.post(path, userData)
			.then((res) => {
				this.errorMessage = res.data.errorMessage
				this.successMessage = res.data.successMessage
			})
			.catch((error) => {
				console.log(error)
			})
		}
	},
}
</script>

<style scoped>
.btn {
	width: 250px;
	margin-left: 10px;
}
.input {
	height: 38px;
}
</style>