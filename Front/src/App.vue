<template>
	<v-app>
		<v-main>
			<v-container fluid>
				<router-view :keycloak="keycloak"></router-view>
			</v-container>
		</v-main>
	</v-app>
</template>

<script lang="ts">
	import { Component, Vue, Prop} from 'vue-property-decorator';

	@Component({
		name: 'App',
	})
	export default class App extends Vue {
		@Prop() readonly keycloak!: string
	}
</script>
