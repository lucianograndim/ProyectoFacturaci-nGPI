<template>
	<v-footer dense>
		<v-container>
			<v-col class="text-center">
				{{ new Date().getFullYear() }} —
				<strong> Alloxentric  </strong>
			</v-col>
		</v-container>
	</v-footer>
</template>
<script lang="ts">
	import { Component, Vue } from 'vue-property-decorator';
	@Component({
		name: 'AppFooter',
	})
	export default class AppFooter extends Vue {

	}
</script>
