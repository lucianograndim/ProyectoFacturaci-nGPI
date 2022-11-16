<template>
   <div class>
		<v-row justify="center" class="text-center">
			<v-col col="12" sm="6" md="6" >
				<h1>{{ message }}</h1>
			</v-col>
		</v-row>
		<v-row justify="center" align="center">
			<v-col col="12" sm="6" md="6">
				<v-img
					contain
					alt="Alloxentric Logo"
					src="@/assets/Alloxentric-logomark.png"
					max-height="250"
				></v-img>
			</v-col>
		</v-row>
	</div>
</template>
<script lang="ts">
	import { Component, Vue } from 'vue-property-decorator';
	@Component({
		name: 'MainInicio',
	})
	export default class MainInicio extends Vue {
		public message = this.$t("Main.message");

	}
</script>
